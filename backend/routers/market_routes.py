"""
市场数据路由

负责市场数据相关接口：
- K线数据
- 交易对列表
- 市场缓存管理
- 价格查询
- 持仓查询
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Union, Dict, Any
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Request Models
# ============================================================================

class ExchangeCredentials(BaseModel):
    """交易所凭证（前端传入格式，不含 marketType）"""
    exchange: str
    apiKey: str
    apiSecret: str
    password: Optional[str] = None
    unifiedAccount: Optional[bool] = False  # 🆕 统一账户标识


class PositionsRequest(BaseModel):
    """持仓查询请求"""
    credentials: List[ExchangeCredentials]
    symbols: Optional[List[str]] = None  # 可选的币种列表，用于过滤持仓（如 ['BTC', 'ETH', 'PEOPLE']）


# ============================================================================
# 市场数据 API
# ============================================================================

@router.get("/api/klines")
async def get_klines(
    exchange: str = Query(..., description="交易所名称"),
    symbol: str = Query(..., description="交易对符号"),
    interval: str = Query("15m", description="K线周期"),
    limit: int = Query(100, description="数据条数限制"),
    market_type: str = Query("spot", description="市场类型 (spot/futures)")
):
    """获取K线数据"""
    from app_config import market_service
    
    try:
        result = await market_service.get_klines(exchange, symbol, interval, limit, market_type)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/api/markets/cache")
async def get_cache_info():
    """获取市场数据缓存统计信息"""
    from app_config import market_service
    
    try:
        return market_service.get_cache_info()
    except Exception as e:
        logger.error(f"获取缓存信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/markets/status")
async def get_markets_status():
    """获取市场数据加载状态"""
    from app_config import market_service
    return market_service.get_markets_status()


@router.get("/api/symbols")
async def get_symbols(
    exchange: str = Query("binance", description="交易所名称"),
    quote: str = Query(None, description="计价币种过滤"),
    limit: int = Query(100, description="返回数量限制")
):
    """获取指定交易所的交易对列表"""
    from app_config import market_service
    
    try:
        result = await market_service.get_symbols(exchange, quote, limit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取交易对失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))




# ============================================================================
# 价格查询 API
# ============================================================================

@router.post("/api/prices")
async def get_prices(request: dict):
    """
    获取多个币种的价格
    
    请求体示例:
    {
        "symbols": [
            {"exchange": "binance", "symbol": "BTC/USDT"},
            {"exchange": "okx", "symbol": "ETH/USDT"}
        ]
    }
    """
    from app_config import price_service
    
    try:
        symbols_list = request.get('symbols', [])
        result = await price_service.get_prices(symbols_list)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取价格失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取价格失败: {str(e)}")


# ============================================================================
# 持仓管理 API
# ============================================================================

@router.post("/api/positions")
async def get_positions(request: Any = Body(...)):
    """
    获取多个交易所的持仓数据
    
    支持两种请求格式：
    1. 新格式（推荐）：{"credentials": [...], "symbols": ["BTC", "ETH"]}
    2. 旧格式（兼容）：[...] 直接传递 credentials 数组
    
    - 统一账户交易所（unifiedAccount=True）：只查询一次，返回现货+合约数据
    - 分离账户交易所（unifiedAccount=False）：分别查询现货和合约
    - symbols: 可选的币种列表，用于过滤持仓，只返回匹配的币种（可以大幅提升查询速度）
    """
    import time
    from app_config import position_service
    
    # 记录接口开始时间
    api_start_time = time.time()
    
    try:
        # 兼容处理：支持新旧两种格式
        if isinstance(request, list):
            # 旧格式：直接传递 credentials 数组
            credentials = [ExchangeCredentials(**cred) if isinstance(cred, dict) else cred for cred in request]
            symbols = None
        elif isinstance(request, dict) and "credentials" in request:
            # 新格式：PositionsRequest 对象
            credentials = [ExchangeCredentials(**cred) if isinstance(cred, dict) else cred for cred in request["credentials"]]
            # 支持两种格式：
            # 1. symbolPairs: {exchange: {marketType: [symbols]}} - 前端生成的交易对映射（推荐）
            # 2. symbols: [base_currencies] - 基础货币列表（向后兼容）
            symbol_pairs = request.get("symbolPairs")
            symbols = request.get("symbols")  # 向后兼容
        else:
            raise HTTPException(status_code=400, detail="无效的请求格式，请使用 {'credentials': [...]} 或 [...] 格式")
        
        # 根据 unifiedAccount 字段决定是否扩展
        expanded_credentials = []
        for cred in credentials:
            cred_dict = cred.dict()
            
            if cred.unifiedAccount:
                # 🎯 统一账户：只添加一次，marketType 设为 'unified'
                unified_cred = {**cred_dict, 'marketType': 'unified'}
                expanded_credentials.append(unified_cred)
                logger.info(f"✅ 统一账户: {cred.exchange} (只查询一次)")
            else:
                # 🔄 分离账户：分别添加现货和合约
                spot_cred = {**cred_dict, 'marketType': 'spot'}
                expanded_credentials.append(spot_cred)
                
                futures_cred = {**cred_dict, 'marketType': 'futures'}
                expanded_credentials.append(futures_cred)
                logger.info(f"🔄 分离账户: {cred.exchange} (查询现货+合约)")
        
        # 将 symbolPairs 转换为每个交易所的 symbols
        # 如果提供了 symbolPairs，使用它；否则使用 symbols（向后兼容）
        expanded_symbols = {}
        if symbol_pairs:
            # 使用前端传递的交易对映射
            for cred in expanded_credentials:
                exchange = cred.get('exchange', '').lower()
                market_type = cred.get('marketType', '').lower()
                
                # 统一 market_type 格式
                if market_type == 'future':
                    market_type = 'futures'
                
                if exchange in symbol_pairs and market_type in symbol_pairs[exchange]:
                    expanded_symbols[f"{exchange}_{market_type}"] = symbol_pairs[exchange][market_type]
        
        if symbol_pairs:
            logger.info(f"📊 持仓查询: 收到 {len(credentials)} 个交易所凭证，扩展为 {len(expanded_credentials)} 个查询，使用前端传递的交易对映射")
        elif symbols:
            logger.info(f"📊 持仓查询: 收到 {len(credentials)} 个交易所凭证，扩展为 {len(expanded_credentials)} 个查询，过滤币种: {symbols}")
        else:
            logger.info(f"📊 持仓查询: 收到 {len(credentials)} 个交易所凭证，扩展为 {len(expanded_credentials)} 个查询（无币种过滤）")
        
        # 调用服务层获取持仓
        # 如果提供了 symbolPairs，传递 expanded_symbols；否则传递 symbols（向后兼容）
        service_start_time = time.time()
        result = await position_service.get_positions(
            expanded_credentials, 
            symbols=symbols if not expanded_symbols else None,  # 如果使用 symbolPairs，不传 symbols
            symbol_pairs=expanded_symbols if expanded_symbols else None  # 传递交易对映射
        )
        service_elapsed = time.time() - service_start_time
        
        # 计算总耗时
        api_elapsed = time.time() - api_start_time
        
        # 打印性能信息
        logger.info(f"⏱️ [性能监控] /api/positions 接口总耗时: {api_elapsed:.3f}秒 (服务层耗时: {service_elapsed:.3f}秒, 路由层耗时: {api_elapsed - service_elapsed:.3f}秒)")
        
        # 如果接口耗时超过1秒，打印警告
        if api_elapsed > 1.0:
            logger.warning(f"⚠️ [性能警告] /api/positions 接口耗时过长: {api_elapsed:.3f}秒 (超过1秒阈值)")
        
        return result
    except Exception as e:
        logger.error(f"❌ 获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取持仓失败: {str(e)}")

