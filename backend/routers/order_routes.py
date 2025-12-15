"""
订单管理路由

负责订单相关接口：
- 获取订单列表
- 按币种筛选订单
- 创建订单
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
import ccxt

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


class OrdersBySymbolsRequest(BaseModel):
    """按币种获取订单的请求体（简化版）"""
    symbols: List[str]  # 币种列表（向后兼容）
    credentials: Optional[List[ExchangeCredentials]] = None
    symbolPairs: Optional[Dict[str, Dict[str, List[str]]]] = None  # 交易对映射 {exchange: {marketType: [symbols]}}
    since: Optional[int] = None
    limit: Optional[int] = 5000


class CreateOrderRequest(BaseModel):
    """创建订单的请求模型"""
    exchange: str
    marketType: str  # 'spot' 或 'futures'
    symbol: str  # 交易对，如 'BTC/USDT'
    type: str  # 'limit' 或 'market'
    side: str  # 'buy' 或 'sell'
    amount: float  # 数量
    price: Optional[float] = None  # 价格（限价单必填）
    credentials: ExchangeCredentials  # 交易所凭证
    closePosition: Optional[str] = None  # 平仓方向：'long' 或 'short'（用于合约平仓）


class MaxOrderQuantityRequest(BaseModel):
    """查询最大可下单数量"""
    exchange: str
    symbol: str  # 标准格式，如 'BTC/USDT'
    side: str  # 'buy' or 'sell'
    price: Optional[float] = None  # 限价单必填
    reduceOnly: Optional[bool] = None
    autoBorrow: Optional[bool] = None
    autoBorrowRepay: Optional[bool] = None
    autoLendRedeem: Optional[bool] = None
    credentials: ExchangeCredentials


# ============================================================================
# 辅助函数
# ============================================================================

# 已删除 _extract_base_from_symbol 和 normalize_symbol_internal 函数
# 现在直接使用前端传来的 symbol，不需要后端重新标准化


# ============================================================================
# 订单管理 API
# ============================================================================

@router.post("/api/orders")
async def get_orders(credentials: List[ExchangeCredentials]):
    """
    获取多个交易所的订单列表
    
    - 统一账户交易所（unifiedAccount=True）：只查询一次，返回现货+合约数据
    - 分离账户交易所（unifiedAccount=False）：分别查询现货和合约
    """
    from app_config import order_service
    
    try:
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
        
        logger.info(f"📋 订单查询: 收到 {len(credentials)} 个交易所凭证，扩展为 {len(expanded_credentials)} 个查询")
        
        # 调用服务层获取订单
        result = await order_service.get_orders(expanded_credentials)
        return result
    except Exception as e:
        logger.error(f"❌ 获取订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单失败: {str(e)}")


@router.post("/api/orders/by-symbols")
async def get_orders_by_symbols(request: OrdersBySymbolsRequest):
    """
    按选择的基础币种列表查询各交易所的订单（简化版）。

    请求体示例:
    {
        "symbols": ["BTC", "ETH", "SOL"],
        "credentials": [
            {"exchange": "binance", "apiKey": "...", "apiSecret": "..."},
            {"exchange": "okx", "apiKey": "...", "apiSecret": "...", "password": "..."}
        ],
        "since": 1710000000000,
        "limit": 50
    }
    """
    from app_config import order_service
    
    try:
        if not request.symbols or len(request.symbols) == 0:
            raise HTTPException(status_code=400, detail="symbols 不能为空")

        if not request.credentials or len(request.credentials) == 0:
            # 前端如未传递凭证，则无法访问私有订单接口
            raise HTTPException(status_code=400, detail="缺少交易所凭证 credentials")

        # 构建币种集合（统一大写）
        symbol_set = set()
        for s in request.symbols:
            if s:
                symbol_set.add(str(s).strip().upper())

        # 根据 unifiedAccount 字段决定是否扩展
        expanded_credentials: List[dict] = []
        for cred in request.credentials:
            c = cred.dict()
            
            if cred.unifiedAccount:
                # 🎯 统一账户：只添加一次，marketType 设为 'unified'
                expanded_credentials.append({**c, "marketType": "unified"})
                logger.info(f"✅ 统一账户: {cred.exchange} (只查询一次)")
            else:
                # 🔄 分离账户：分别添加现货和合约
                expanded_credentials.append({**c, "marketType": "spot"})
                expanded_credentials.append({**c, "marketType": "futures"})
                logger.info(f"🔄 分离账户: {cred.exchange} (查询现货+合约)")

        if len(expanded_credentials) == 0:
            return {"success": True, "data": [], "total": 0, "elapsed": 0.0}

        # 🎯 处理交易对映射（优先使用 symbolPairs，否则使用 symbols）
        symbol_pairs = None
        if request.symbolPairs:
            # 转换前端传递的格式 {exchange: {marketType: [symbols]}} 
            # 为后端使用的格式 {exchange_marketType: [symbols]}
            symbol_pairs = {}
            for cred in expanded_credentials:
                exchange = cred.get('exchange', '').lower()
                market_type = cred.get('marketType', '').lower()
                
                # 统一 market_type 格式
                if market_type == 'future':
                    market_type = 'futures'
                
                if exchange in request.symbolPairs:
                    if market_type in request.symbolPairs[exchange]:
                        key = f"{exchange}_{market_type}"
                        symbol_pairs[key] = request.symbolPairs[exchange][market_type]
                        logger.info(f"📋 使用交易对映射: {key} = {symbol_pairs[key]}")
        
        # 🎯 将币种列表传递给服务层（向后兼容）
        symbols_list = list(symbol_set) if symbol_set else None
        if symbols_list:
            logger.info(f"📋 查询币种（向后兼容）: {symbols_list}")
        
        # 🚀 查询订单（优先使用 symbolPairs，否则使用 symbols）
        result = await order_service.get_orders(expanded_credentials, symbols=symbols_list, symbol_pairs=symbol_pairs)
        if not result or not result.get("success"):
            return result or {"success": False, "data": [], "total": 0}

        orders = result.get("data", [])
        logger.info(f"✅ 查询到 {len(orders)} 个订单")
        
        return {
            "success": True,
            "data": orders,
            "total": len(orders),
            "elapsed": result.get("elapsed")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 按币种获取订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"按币种获取订单失败: {str(e)}")


@router.post("/api/create-order")
async def create_order(request: CreateOrderRequest):
    """
    创建订单（下单）
    
    请求体示例:
    {
        "exchange": "binance",
        "marketType": "spot",
        "symbol": "BTC/USDT",
        "type": "limit",
        "side": "buy",
        "amount": 0.001,
        "price": 50000,
        "credentials": {
            "exchange": "binance",
            "apiKey": "...",
            "apiSecret": "..."
        }
    }
    """
    try:
        logger.info(f"📤 收到下单请求: {request.exchange} {request.marketType} {request.symbol} "
                   f"{request.side} {request.amount} @ {request.price if request.price else 'market'}")
        
        # 验证参数
        if request.type not in ['limit', 'market']:
            raise HTTPException(status_code=400, detail="订单类型必须是 'limit' 或 'market'")
        
        if request.side not in ['buy', 'sell']:
            raise HTTPException(status_code=400, detail="订单方向必须是 'buy' 或 'sell'")
        
        if request.type == 'limit' and request.price is None:
            raise HTTPException(status_code=400, detail="限价单必须提供价格")
        
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="订单数量必须大于 0")
        
        # 🔧 使用交易所适配器层
        from exchange_adapters import get_adapter
        
        # 构建适配器配置
        # 注意：只传递基础配置，特殊配置（如 OKX 的 password）由适配器自己处理
        adapter_config = {
            'apiKey': request.credentials.apiKey,
            'secret': request.credentials.apiSecret,
            'password': getattr(request.credentials, 'password', None),  # 统一传递，由适配器决定是否使用
            'enableRateLimit': True,
        }
        
        # 注意：
        # - 代理配置已由适配器基类自动处理（从环境变量 PROXY_URL 读取）
        # - password 字段由适配器自动处理（OKX 会验证是否提供，其他交易所会忽略）
        
        # 获取适配器实例（自动处理市场类型和特殊逻辑）
        adapter = get_adapter(
            exchange_id=request.exchange,
            market_type=request.marketType,
            config=adapter_config
        )
        
        # 获取底层 CCXT 实例（市场数据已由适配器自动加载并缓存）
        exchange = adapter.get_exchange()
        
        # 直接使用前端传来的 symbol（前端已经根据规则生成了正确格式）
        logger.debug(f"📥 使用前端symbol: {request.symbol} (exchange: {request.exchange}, type: {request.marketType})")
        
        # 构建订单参数
        order_params = {
            'symbol': request.symbol,  # 使用前端传来的符号
            'type': request.type,
            'side': request.side,
            'amount': request.amount,
        }
        
        # 限价单需要价格
        if request.type == 'limit':
            order_params['price'] = request.price
        
        # 对于现货订单，确保不传递合约相关参数（如 positionSide）
        # 这些参数会导致 "Order's position side does not match user's setting" 错误
        params = {}
        if request.marketType in ['futures', 'future']:
            # 合约订单需要 positionSide 参数（币安双向持仓模式要求）
            if request.closePosition:
                # 平仓操作：根据平仓方向设置 positionSide
                # 平多仓：sell + positionSide: 'LONG'
                # 平空仓：buy + positionSide: 'SHORT'
                # 注意：不添加 reduceOnly 参数，因为币安单向持仓模式不需要，且会导致错误
                if request.closePosition.lower() == 'long':
                    params['positionSide'] = 'LONG'  # 平多仓
                elif request.closePosition.lower() == 'short':
                    params['positionSide'] = 'SHORT'  # 平空仓
                logger.info(f"📋 合约平仓订单，closePosition={request.closePosition}, positionSide={params.get('positionSide')}")
            else:
                # 开仓操作：根据买卖方向设置 positionSide
                # buy (买入) → LONG (做多)
                # sell (卖出) → SHORT (做空)
                if request.side.lower() == 'buy':
                    params['positionSide'] = 'LONG'  # 买入 = 做多
                elif request.side.lower() == 'sell':
                    params['positionSide'] = 'SHORT'  # 卖出 = 做空
                logger.info(f"📋 合约开仓订单，添加 positionSide: {params.get('positionSide')}")
        # 现货订单明确不传递任何 params，避免 CCXT 自动添加 positionSide
        
        logger.info(f"🔧 订单参数: {order_params}, params: {params}")
        
        # 通过适配器创建订单（透传机制）
        # 注意：CCXT 的 create_order 是同步方法，不需要 await
        # CCXT create_order 签名: create_order(symbol, type, side, amount, price=None, params={})
        # 对于现货订单，明确传递空的 params 以避免 positionSide 相关错误
        # 对于合约订单，也先传递空的 params，让交易所根据账户模式自动处理
        order = adapter.create_order(
            symbol=order_params['symbol'],
            type=order_params['type'],
            side=order_params['side'],
            amount=order_params['amount'],
            price=order_params.get('price'),
            params=params  # 明确传递 params，现货订单为空字典，避免 positionSide 错误
        )
        
        logger.info(f"✅ 订单创建成功: {order.get('id', 'N/A')}")
        
        # 返回标准化的订单信息
        return {
            "success": True,
            "message": "订单创建成功",
            "data": {
                "orderId": order.get('id'),
                "symbol": order.get('symbol'),
                "type": order.get('type'),
                "side": order.get('side'),
                "price": order.get('price'),
                "amount": order.get('amount'),
                "status": order.get('status'),
                "timestamp": order.get('timestamp'),
                "info": order.get('info', {})
            }
        }
        
    except ccxt.InsufficientFunds as e:
        logger.error(f"❌ 余额不足: {e}")
        raise HTTPException(status_code=400, detail=f"余额不足: {str(e)}")
    
    except ccxt.InvalidOrder as e:
        logger.error(f"❌ 无效订单: {e}")
        raise HTTPException(status_code=400, detail=f"无效订单: {str(e)}")
    
    except ccxt.ExchangeError as e:
        logger.error(f"❌ 交易所错误: {e}")
        raise HTTPException(status_code=400, detail=f"交易所错误: {str(e)}")
    
    except ccxt.NetworkError as e:
        logger.error(f"❌ 网络错误: {e}")
        raise HTTPException(status_code=503, detail=f"网络错误: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ 创建订单失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建订单失败: {str(e)}")


@router.post("/api/backpack/max-order-quantity")
async def get_backpack_max_order_quantity(request: MaxOrderQuantityRequest):
    """
    查询 Backpack 最大可下单数量（instruction: maxOrderQuantity）
    """
    try:
        if request.exchange.lower() != 'backpack':
            raise HTTPException(status_code=400, detail="仅支持 backpack 交易所")

        from exchange_adapters import get_adapter

        adapter = get_adapter(
            exchange_id='backpack',
            market_type='spot',  # Backpack 现货接口
            config={
                'apiKey': request.credentials.apiKey,
                'secret': request.credentials.apiSecret,
                'password': getattr(request.credentials, 'password', None),
                'enableRateLimit': True,
            }
        )

        result = adapter.get_max_order_quantity(
            symbol=request.symbol,
            side=request.side,
            price=request.price,
            reduceOnly=request.reduceOnly,
            autoBorrow=request.autoBorrow,
            autoBorrowRepay=request.autoBorrowRepay,
            autoLendRedeem=request.autoLendRedeem,
        )

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取 Backpack 最大可下单数量失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取最大可下单数量失败: {str(e)}")

