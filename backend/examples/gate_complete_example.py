"""
Gate.io 交易所简化示例

功能：
1. 现货买入
2. 现货卖出
3. 合约做多
4. 合约做空
5. 合约平仓
"""

import ccxt
import logging
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class GateTrading:
    """Gate.io 交易客户端 - 简化版"""
    
    def __init__(
        self,
        api_key: str,
        secret: str,
        market_type: str = 'spot',  # 'spot' 或 'futures'
        proxy: Optional[str] = None
    ):
        """
        初始化 Gate.io 交易客户端
        
        Args:
            api_key: API Key
            secret: API Secret
            market_type: 市场类型（'spot' 现货，'futures' 合约）
            proxy: 代理地址，如 "http://127.0.0.1:1080"
        """
        self.api_key = api_key
        self.secret = secret
        self.market_type = market_type
        self.proxy = proxy
        
        # 初始化 ccxt 交易所实例
        self._init_exchange()
        
        logger.info(f"✅ Gate.io 客户端初始化成功 (市场类型: {market_type})")
    
    def _init_exchange(self):
        """初始化交易所实例"""
        config = {
            'apiKey': self.api_key,
            'secret': self.secret,
            'enableRateLimit': True,
            'timeout': 30000,
        }
        
        # 配置代理
        if self.proxy:
            config['proxies'] = {
                'http': self.proxy,
                'https': self.proxy
            }
            logger.info(f"🌐 使用代理: {self.proxy}")
        
        # 根据市场类型设置
        if self.market_type == 'futures':
            config['options'] = {'defaultType': 'swap'}  # Gate.io 合约使用 swap
        else:
            config['options'] = {'defaultType': 'spot'}
        
        self.exchange = ccxt.gate(config)
        
        # 加载市场数据
        try:
            self.exchange.load_markets()
            logger.info(f"✅ 市场数据加载成功，共 {len(self.exchange.markets)} 个交易对")
        except Exception as e:
            logger.error(f"❌ 市场数据加载失败: {e}")
    
    # ==================== 核心功能 ====================
    
    def spot_buy(self, symbol: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        现货买入
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            amount: 买入数量
            price: 价格（不指定则市价买入）
        
        Returns:
            订单信息
        """
        if self.market_type != 'spot':
            raise ValueError("请使用现货客户端进行现货交易")
        
        try:
            if price is None:
                # 市价买入
                logger.info(f"📝 现货市价买入: {symbol} 数量={amount}")
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                # 限价买入
                logger.info(f"📝 现货限价买入: {symbol} 数量={amount} 价格={price}")
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 现货买入失败: {e}")
            raise
    
    def spot_sell(self, symbol: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        现货卖出
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            amount: 卖出数量
            price: 价格（不指定则市价卖出）
        
        Returns:
            订单信息
        """
        if self.market_type != 'spot':
            raise ValueError("请使用现货客户端进行现货交易")
        
        try:
            if price is None:
                # 市价卖出
                logger.info(f"📝 现货市价卖出: {symbol} 数量={amount}")
                order = self.exchange.create_market_sell_order(symbol, amount)
            else:
                # 限价卖出
                logger.info(f"📝 现货限价卖出: {symbol} 数量={amount} 价格={price}")
                order = self.exchange.create_limit_sell_order(symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 现货卖出失败: {e}")
            raise
    
    def futures_long(self, symbol: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        合约做多（开多仓）
        
        Args:
            symbol: 交易对，如 'BTC/USDT' 或 'BTC/USDT:USDT'
            amount: 合约数量（张数）
            price: 价格（不指定则市价开仓）
        
        Returns:
            订单信息
        """
        if self.market_type != 'futures':
            raise ValueError("请使用合约客户端进行合约交易")
        
        try:
            # 标准化交易对格式
            if ':' not in symbol:
                symbol = f"{symbol}:USDT"
            
            if price is None:
                # 市价做多
                logger.info(f"📝 合约市价做多: {symbol} 数量={amount}张")
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                # 限价做多
                logger.info(f"📝 合约限价做多: {symbol} 数量={amount}张 价格={price}")
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 合约做多失败: {e}")
            raise
    
    def futures_short(self, symbol: str, amount: float, price: Optional[float] = None) -> Dict:
        """
        合约做空（开空仓）
        
        Args:
            symbol: 交易对，如 'BTC/USDT' 或 'BTC/USDT:USDT'
            amount: 合约数量（张数）
            price: 价格（不指定则市价开仓）
        
        Returns:
            订单信息
        """
        if self.market_type != 'futures':
            raise ValueError("请使用合约客户端进行合约交易")
        
        try:
            # 标准化交易对格式
            if ':' not in symbol:
                symbol = f"{symbol}:USDT"
            
            if price is None:
                # 市价做空
                logger.info(f"📝 合约市价做空: {symbol} 数量={amount}张")
                order = self.exchange.create_market_sell_order(symbol, amount)
            else:
                # 限价做空
                logger.info(f"📝 合约限价做空: {symbol} 数量={amount}张 价格={price}")
                order = self.exchange.create_limit_sell_order(symbol, amount, price)
            
            logger.info(f"✅ 订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 合约做空失败: {e}")
            raise
    
    def futures_close(self, symbol: str, side: str, amount: Optional[float] = None) -> Dict:
        """
        合约平仓
        
        Args:
            symbol: 交易对，如 'BTC/USDT' 或 'BTC/USDT:USDT'
            side: 平仓方向 ('long' 平多仓, 'short' 平空仓)
            amount: 平仓数量（不指定则查询持仓后全部平仓）
        
        Returns:
            订单信息
        """
        if self.market_type != 'futures':
            raise ValueError("请使用合约客户端进行合约交易")
        
        try:
            # 标准化交易对格式
            if ':' not in symbol:
                symbol = f"{symbol}:USDT"
            
            # 如果没有指定数量，查询持仓
            if amount is None:
                positions = self.exchange.fetch_positions([symbol])
                position = None
                for pos in positions:
                    if pos.get('symbol') == symbol and pos.get('side') == side:
                        position = pos
                        break
                
                if not position:
                    logger.warning(f"⚠️ 未找到持仓: {symbol} {side}")
                    return {}
                
                amount = abs(float(position.get('contracts', 0)))
                if amount == 0:
                    logger.warning(f"⚠️ 持仓数量为0: {symbol} {side}")
                    return {}
            
            # 平仓方向相反：平多仓用卖，平空仓用买
            if side == 'long':
                logger.info(f"📝 合约平多仓: {symbol} 数量={amount}张")
                order = self.exchange.create_market_sell_order(symbol, amount)
            elif side == 'short':
                logger.info(f"📝 合约平空仓: {symbol} 数量={amount}张")
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                raise ValueError(f"无效的平仓方向: {side}，应为 'long' 或 'short'")
            
            logger.info(f"✅ 平仓订单创建成功，订单ID: {order.get('id')}")
            return order
        except Exception as e:
            logger.error(f"❌ 合约平仓失败: {e}")
            raise


# ==================== 使用示例 ====================

def example_spot():
    """现货交易示例"""
    print("\n" + "=" * 60)
    print("  📊 现货交易示例")
    print("=" * 60 + "\n")
    
    # 配置
    API_KEY = "your_api_key"
    SECRET = "your_secret"
    PROXY = "http://127.0.0.1:1080"
    
    # 初始化现货客户端
    client = GateTrading(API_KEY, SECRET, 'spot', PROXY)
    
    # 示例1：市价买入
    order = client.spot_buy('BTC/USDT', amount=0.0001)
    print(f"订单ID: {order['id']}")
    
    # 示例2：限价买入
    # order = client.spot_buy('BTC/USDT', amount=0.001, price=40000)
    # print(f"订单ID: {order['id']}")
    
    # 示例3：市价卖出
    # order = client.spot_sell('BTC/USDT', amount=0.001)
    # print(f"订单ID: {order['id']}")
    
    # 示例4：限价卖出
    # order = client.spot_sell('BTC/USDT', amount=0.001, price=50000)
    # print(f"订单ID: {order['id']}")
    
    print("提示: 取消注释以执行交易")


def example_futures():
    """合约交易示例"""
    print("\n" + "=" * 60)
    print("  📊 合约交易示例")
    print("=" * 60 + "\n")
    
    # 配置
    API_KEY = "a324a7f1a8b7c3fa9fb6713eaceb666a"
    SECRET = "6b23c0e76ae8c4785c0b1eef867a46e9685c8e796d38bf2a8b79e1543b3afe1e"
    PROXY = "http://127.0.0.1:1080"
    
    # 初始化合约客户端
    client = GateTrading(API_KEY, SECRET, 'futures', PROXY)
    
    # 示例1：市价做多
    # order = client.futures_long('BTC/USDT', amount=1)
    # print(f"订单ID: {order['id']}")
    
    # 示例2：限价做多
    # order = client.futures_long('BTC/USDT', amount=1, price=40000)
    # print(f"订单ID: {order['id']}")
    
    # 示例3：市价做空
    # order = client.futures_short('BTC/USDT', amount=1)
    # print(f"订单ID: {order['id']}")
    
    # 示例4：限价做空
    # order = client.futures_short('BTC/USDT', amount=1, price=50000)
    # print(f"订单ID: {order['id']}")
    
    # 示例5：平多仓（自动查询持仓数量）
    # order = client.futures_close('BTC/USDT', side='long')
    # print(f"订单ID: {order['id']}")
    
    # 示例6：平空仓（指定数量）
    # order = client.futures_close('BTC/USDT', side='short', amount=1)
    # print(f"订单ID: {order['id']}")
    
    print("提示: 取消注释以执行交易")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  🚀 Gate.io 交易示例")
    print("=" * 60 + "\n")
    
    print("请选择示例:")
    print("  1 - 现货交易示例")
    print("  2 - 合约交易示例")
    
    # 这里可以接收用户输入
    # choice = input("请输入选项 (1/2): ")
    
    example_spot()
    # example_futures()
    
    # print("\n提示: 请在代码中配置 API Key 后运行\n")
