"""
交易所管理服务
处理交易所连接测试、列表获取等
"""

import logging
import time
import asyncio
import ccxt
from typing import Dict, List, Optional, Any
from exchange_adapters import get_adapter

logger = logging.getLogger(__name__)


class ExchangeService:
    """交易所管理服务（基于 Adapter 架构）"""
    
    def __init__(self, proxy_config: Dict[str, str]):
        """
        初始化交易所服务
        
        Args:
            proxy_config: 代理配置
        """
        self.proxy_config = proxy_config
        logger.info("交易所服务初始化完成（Adapter 架构）")
    
    def get_exchange_list(self) -> List[str]:
        """
        获取所有支持的交易所列表
        
        Returns:
            交易所名称列表（定制适配器 + 默认支持）
        """
        from exchange_adapters import CUSTOM_ADAPTERS, DEFAULT_SUPPORTED_EXCHANGES
        # 定制适配器优先（经过优化）
        return list(CUSTOM_ADAPTERS.keys()) + DEFAULT_SUPPORTED_EXCHANGES
    
    async def test_exchange_connection(
        self,
        exchange: str,
        api_key: str,
        api_secret: str,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        测试交易所连接（使用 Adapter 统一接口）
        同时测试现货和合约账户
        
        Args:
            exchange: 交易所名称
            api_key: API Key
            api_secret: API Secret
            password: API 密码（某些交易所需要，如 OKX）
            
        Returns:
            测试结果字典，包含 spot 和 futures 两个市场的测试结果
        """
        exchange_id = exchange.lower()
        
        # 🎯 使用 Adapter 创建交易所实例
        adapter_config = {
            'apiKey': api_key,
            'secret': api_secret,
            'password': password,
            'enableRateLimit': True,
            'timeout': 15000,  # 15秒超时
        }
        
        loop = asyncio.get_event_loop()
        results = {
            'exchange': exchange_id,
            'spot': None,
            'futures': None,
            'timestamp': int(time.time() * 1000)
        }
        
        # 测试现货账户
        try:
            logger.info(f"🔍 测试交易所连接: {exchange_id} 现货 (使用 Adapter)")
            spot_adapter = get_adapter(
                exchange_id=exchange_id,
                market_type='spot',
                config=adapter_config
            )
            spot_result = await loop.run_in_executor(None, spot_adapter.test_connectivity)
            
            if spot_result.get('ok'):
                logger.info(f"✅ {exchange_id} 现货连接测试成功！延迟: {spot_result.get('latencyMs', 0):.2f}ms")
                results['spot'] = {
                    "success": True,
                    "serverTime": spot_result.get('serverTime'),
                    "accountId": spot_result.get('accountId'),
                    "latencyMs": spot_result.get('latencyMs'),
                    "balance": spot_result.get('balance', {})
                }
            else:
                logger.error(f"❌ {exchange_id} 现货连接测试失败: {spot_result.get('error')}")
                results['spot'] = {
                    "success": False,
                    "error": spot_result.get('error', '连接测试失败')
                }
        except ValueError as e:
            logger.error(f"❌ {exchange_id} 现货配置错误: {str(e)}")
            results['spot'] = {
                "success": False,
                "error": f"配置错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ {exchange_id} 现货测试失败: {str(e)}")
            results['spot'] = {
                "success": False,
                "error": f"未知错误: {str(e)}"
            }
        
        # 测试合约账户
        try:
            logger.info(f"🔍 测试交易所连接: {exchange_id} 合约 (使用 Adapter)")
            futures_adapter = get_adapter(
                exchange_id=exchange_id,
                market_type='futures',
                config=adapter_config
            )
            futures_result = await loop.run_in_executor(None, futures_adapter.test_connectivity)
            
            if futures_result.get('ok'):
                logger.info(f"✅ {exchange_id} 合约连接测试成功！延迟: {futures_result.get('latencyMs', 0):.2f}ms")
                results['futures'] = {
                    "success": True,
                    "serverTime": futures_result.get('serverTime'),
                    "accountId": futures_result.get('accountId'),
                    "latencyMs": futures_result.get('latencyMs'),
                    "balance": futures_result.get('balance', {})
                }
            else:
                logger.error(f"❌ {exchange_id} 合约连接测试失败: {futures_result.get('error')}")
                results['futures'] = {
                    "success": False,
                    "error": futures_result.get('error', '连接测试失败')
                }
        except ValueError as e:
            logger.error(f"❌ {exchange_id} 合约配置错误: {str(e)}")
            results['futures'] = {
                "success": False,
                "error": f"配置错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ {exchange_id} 合约测试失败: {str(e)}")
            results['futures'] = {
                "success": False,
                "error": f"未知错误: {str(e)}"
            }
        
        # 判断整体测试结果（至少有一个成功就算成功）
        overall_success = (results['spot'] and results['spot'].get('success')) or \
                         (results['futures'] and results['futures'].get('success'))
        
        return {
            "success": overall_success,
            "data": results
        }

