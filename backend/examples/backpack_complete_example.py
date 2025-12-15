"""
Backpack 交易所完整示例

功能：
1. K线数据查询（支持多种时间周期）
2. 最新价格查询（ticker）
3. 订单簿深度查询
4. 账户余额查询
5. 历史订单查询（带统计分析）
6. 成交历史查询（fills）
7. WebSocket 实时数据订阅
   - K线实时更新
   - 价格实时更新
   - 订单簿深度实时更新

官方文档：https://docs.backpack.exchange/
API: https://api.backpack.exchange/
WebSocket: wss://ws.backpack.exchange/
"""

import json
import time
import base64
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import requests
import websockets

# 需要安装的依赖：
# pip install cryptography requests websockets

from cryptography.hazmat.primitives.asymmetric import ed25519

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BackpackAPI:
    """Backpack 交易所 API 客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        proxy: Optional[str] = None
    ):
        """
        初始化 Backpack API 客户端
        
        Args:
            api_key: Base64 编码的公钥（私有 API 需要）
            secret: Base64 编码的私钥（私有 API 需要）
            proxy: 代理地址，如 "http://127.0.0.1:1080"
        """
        self.api_key = api_key
        self.secret = secret
        self.base_url = "https://api.backpack.exchange"
        self.ws_url = "wss://ws.backpack.exchange/"
        
        # 初始化私钥（用于签名）
        self.private_key = None
        if api_key and secret:
            try:
                secret_bytes = base64.b64decode(secret)
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
                logger.info("✅ ED25519 签名密钥加载成功")
            except Exception as e:
                logger.error(f"❌ 私钥加载失败: {e}")
        
        # 配置代理
        self.proxies = None
        if proxy:
            self.proxies = {
                'http': proxy,
                'https': proxy
            }
            logger.info(f"🌐 使用代理: {proxy}")
        
        # HTTP 会话
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)
    
    def _timestamp_ms(self) -> int:
        """获取当前时间戳（毫秒）"""
        return int(time.time() * 1000)
    
    def _sign_request(
        self,
        instruction: str,
        params: Optional[Dict[str, Any]] = None,
        window: int = 5000
    ) -> Dict[str, str]:
        """
        生成签名请求头
        
        Args:
            instruction: API 指令类型
            params: 请求参数
            window: 请求有效时间窗口（毫秒）
        
        Returns:
            包含签名的请求头字典
        """
        if not self.private_key or not self.api_key:
            raise ValueError("❌ 私有 API 需要提供 api_key 和 secret")
        
        timestamp = self._timestamp_ms()
        
        # 构建签名字符串
        sign_str_parts = [f"instruction={instruction}"]
        
        # 添加排序后的参数
        if params:
            sorted_params = sorted(params.items())
            for key, value in sorted_params:
                if value is not None:
                    sign_str_parts.append(f"{key}={value}")
        
        # 添加 timestamp 和 window
        sign_str_parts.append(f"timestamp={timestamp}")
        sign_str_parts.append(f"window={window}")
        
        # 拼接签名字符串
        sign_str = "&".join(sign_str_parts)
        
        # ED25519 签名
        signature_bytes = self.private_key.sign(sign_str.encode('utf-8'))
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        # 构建请求头
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8",
        }
        
        return headers
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        instruction: Optional[str] = None,
        private: bool = False
    ) -> Any:
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法（GET/POST/DELETE）
            path: API 路径
            params: 请求参数
            instruction: 指令类型（私有接口必需）
            private: 是否为私有接口
        
        Returns:
            API 响应（JSON）
        """
        url = self.base_url + path
        
        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if private:
            if not instruction:
                raise ValueError("❌ 私有接口必须指定 instruction")
            headers = self._sign_request(instruction, params)
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=params, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"❌ 不支持的 HTTP 方法: {method}")
            
            response.raise_for_status()
            return response.json()
        
        except requests.HTTPError as e:
            logger.error(f"❌ API 错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"❌ 请求失败: {e}")
            raise
    
    # ==================== REST API 方法 ====================
    
    def get_balance(self) -> Dict:
        """
        获取账户余额
        
        API: GET /api/v1/capital
        文档: https://docs.backpack.exchange/#get-balances
        """
        logger.info("📊 查询账户余额...")
        result = self._request(
            "GET",
            "/api/v1/capital",
            instruction="balanceQuery",
            private=True
        )
        logger.info(f"✅ 余额查询成功")
        return result
    
    def get_order_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        获取历史订单
        
        API: GET /api/v1/history/orders
        文档: https://docs.backpack.exchange/#get-order-history
        
        Args:
            symbol: 交易对（如 "SOL_USDC"），不指定则返回所有
            limit: 返回订单数量（最大 1000）
            offset: 分页偏移量
        
        返回格式:
            [
                {
                    "id": "123456",
                    "orderId": "order_abc",
                    "symbol": "SOL_USDC",
                    "side": "Bid" / "Ask",
                    "orderType": "Limit" / "Market",
                    "price": "100.50",
                    "quantity": "10.0",
                    "executedQuantity": "8.0",
                    "executedQuoteQuantity": "804.00",
                    "status": "Filled" / "Cancelled" / "New",
                    "timeInForce": "GTC",
                    "createdAt": 1234567890,
                    "timestamp": 1234567890
                },
                ...
            ]
        """
        logger.info(f"📋 查询历史订单 (symbol={symbol or '全部'}, limit={limit}, offset={offset})...")
        
        params = {
            'limit': min(limit, 1000),  # API 最大限制
            'offset': offset
        }
        # if symbol:
        #     params['symbol'] = symbol
        
        result = self._request(
            "GET",
            "/wapi/v1/history/orders",
            params=params,
            instruction="orderHistoryQueryAll",
            private=True
        )
        
        logger.info(f"✅ 订单查询成功，共 {len(result)} 条")
        return result
    
    def get_fills(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        获取成交历史（已成交的订单）
        
        注意: Backpack 使用 orderHistoryQueryAll 来获取所有历史订单，
        包括已成交的订单。这个方法会自动过滤出已成交的订单。
        
        API: GET /wapi/v1/history/orders
        文档: https://docs.backpack.exchange/#order-history
        Instruction: orderHistoryQueryAll
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
            limit: 返回记录数量（最大 1000）
            offset: 分页偏移量
        
        返回格式:
            [
                {
                    "id": "123456",
                    "orderId": "order_abc",
                    "symbol": "SOL_USDC",
                    "side": "Bid" / "Ask",
                    "orderType": "Market" / "Limit",
                    "price": "100.50",
                    "quantity": "2.0",
                    "executedQuantity": "2.0",
                    "executedQuoteQuantity": "201.00",
                    "status": "Filled",
                    "createdAt": "2024-01-01T12:00:00Z",
                    ...
                },
                ...
            ]
        """
        logger.info(f"💱 查询成交历史 (symbol={symbol or '全部'}, limit={limit})...")
        
        # 使用 get_order_history，然后过滤出已成交的订单
        all_orders = self.get_order_history(
            symbol=symbol,
            limit=limit,
            offset=offset
        )
        
        # 过滤出已成交的订单（Filled 状态）
        filled_orders = [
            order for order in all_orders 
            if order.get('status') == 'Filled'
        ]
        
        logger.info(f"✅ 成交历史查询成功，共 {len(filled_orders)} 条（从 {len(all_orders)} 条订单中过滤）")
        return filled_orders
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "15m",
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        price_type: Optional[str] = None
    ) -> list:
        """
        获取 K 线数据
        
        API: GET /api/v1/klines
        文档: https://docs.backpack.exchange/#get-k-lines
        
        Args:
            symbol: 交易对（如 "BTC_USDC"）
            interval: 时间周期（1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1month）
            start_time: 起始时间（秒级时间戳，必需）
            end_time: 结束时间（秒级时间戳，不提供则使用当前时间）
            price_type: 价格类型（"Last", "Index", "Mark"）
        
        返回格式:
            [
                {
                    "start": "2024-01-01T12:00:00Z",
                    "end": "2024-01-01T12:15:00Z",
                    "open": "43500.50",
                    "high": "43600.00",
                    "low": "43400.00",
                    "close": "43550.00",
                    "volume": "123.45",
                    "quoteVolume": "5370000.00",
                    "trades": "1234"
                },
                ...
            ]
        """
        logger.info(f"📈 查询 K 线数据 ({symbol}, {interval})...")
        
        # 如果没有提供时间范围，默认查询最近 1 天
        if not start_time:
            from datetime import datetime, timedelta
            end_dt = datetime.utcnow()
            start_dt = end_dt - timedelta(days=1)
            start_time = int(start_dt.timestamp())
            end_time = int(end_dt.timestamp())
        elif not end_time:
            from datetime import datetime
            end_time = int(datetime.utcnow().timestamp())
        
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_time,
            'endTime': end_time
        }
        
        if price_type:
            params['priceType'] = price_type
        
        result = self._request("GET", "/api/v1/klines", params=params, private=False)
        
        logger.info(f"✅ K 线查询成功，共 {len(result)} 条")
        return result
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        获取最新价格（ticker）
        
        API: GET /api/v1/ticker
        文档: https://docs.backpack.exchange/#get-ticker
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
        """
        logger.info(f"💰 查询价格 ({symbol})...")
        
        result = self._request(
            "GET",
            "/api/v1/ticker",
            params={'symbol': symbol},
            private=False
        )
        
        logger.info(f"✅ 价格查询成功: {result.get('lastPrice', result.get('c'))}")
        return result
    
    def get_depth(self, symbol: str) -> Dict:
        """
        获取订单簿深度
        
        API: GET /api/v1/depth
        文档: https://docs.backpack.exchange/#get-depth
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
        """
        logger.info(f"📖 查询订单簿 ({symbol})...")
        
        result = self._request(
            "GET",
            "/api/v1/depth",
            params={'symbol': symbol},
            private=False
        )
        
        bids = len(result.get('bids', []))
        asks = len(result.get('asks', []))
        logger.info(f"✅ 订单簿查询成功 (买单: {bids}, 卖单: {asks})")
        return result


class BackpackWebSocket:
    """Backpack WebSocket 客户端"""
    
    def __init__(self, proxy: Optional[str] = None):
        """
        初始化 WebSocket 客户端
        
        Args:
            proxy: 代理地址（格式：host:port）
        """
        self.ws_url = "wss://ws.backpack.exchange/"
        self.proxy = proxy
        self.connections = {}
    
    async def subscribe_kline(
        self,
        symbol: str,
        interval: str = "15m",
        callback=None
    ):
        """
        订阅 K 线数据
        
        Stream: kline.<interval>.<symbol>
        文档: https://docs.backpack.exchange/#k-line
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
            interval: 时间周期（15m）
            callback: 回调函数
        """
        stream = f"kline.{interval}.{symbol}"
        await self._subscribe(stream, callback)
    
    async def subscribe_ticker(self, symbol: str, callback=None):
        """
        订阅价格更新（ticker）
        
        Stream: ticker.<symbol>
        文档: https://docs.backpack.exchange/#ticker
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
            callback: 回调函数
        """
        stream = f"ticker.{symbol}"
        await self._subscribe(stream, callback)
    
    async def subscribe_depth(self, symbol: str, callback=None):
        """
        订阅订单簿深度
        
        Stream: depth.<symbol>
        文档: https://docs.backpack.exchange/#depth
        
        Args:
            symbol: 交易对（如 "SOL_USDC"）
            callback: 回调函数
        """
        stream = f"depth.{symbol}"
        await self._subscribe(stream, callback)
    
    async def _subscribe(self, stream: str, callback=None):
        """
        订阅 WebSocket 流
        
        Args:
            stream: 流名称
            callback: 数据回调函数
        """
        try:
            # 配置 WebSocket 连接参数
            extra_headers = {}
            
            # 如果使用代理，需要配置
            # 注意：websockets 库的代理支持可能需要额外配置
            uri = self.ws_url
            
            logger.info(f"🔌 连接 WebSocket: {stream}")
            
            async with websockets.connect(
                uri,
                extra_headers=extra_headers,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                # 订阅流
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": [stream]
                }
                await websocket.send(json.dumps(subscribe_msg))
                logger.info(f"✅ 订阅成功: {stream}")
                
                # 接收消息
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # 处理数据
                        if callback:
                            callback(data)
                        else:
                            self._default_handler(stream, data)
                    
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ JSON 解析失败: {e}")
                    except Exception as e:
                        logger.error(f"❌ 消息处理失败: {e}")
        
        except Exception as e:
            logger.error(f"❌ WebSocket 连接失败: {e}")
    
    def _default_handler(self, stream: str, data: Dict):
        """默认消息处理器"""
        event = data.get('e', 'unknown')
        
        if event == 'kline':
            # K 线数据
            # WebSocket 返回的 kline 数据格式（需要根据实际测试确认）
            logger.info(
                f"📈 [K线] {data.get('s')} - "
                f"时间: {data.get('t')}, "
                f"开: {data.get('o')}, "
                f"高: {data.get('h')}, "
                f"低: {data.get('l')}, "
                f"收: {data.get('c')}, "
                f"量: {data.get('v')}"
            )
        
        elif event == 'ticker':
            # Ticker 数据
            logger.info(
                f"💰 [价格] {data.get('s')} - "
                f"最新: {data.get('c')}, "
                f"24h高: {data.get('h')}, "
                f"24h低: {data.get('l')}, "
                f"成交量: {data.get('v')}"
            )
        
        elif event == 'depth':
            # 订单簿数据
            bids = data.get('b', [])
            asks = data.get('a', [])
            logger.info(
                f"📖 [深度] {data.get('s')} - "
                f"买单更新: {len(bids)}, "
                f"卖单更新: {len(asks)}, "
                f"更新ID: {data.get('u')}"
            )
        
        else:
            logger.info(f"📨 [{stream}] {json.dumps(data, indent=2)}")


# ==================== 示例代码 ====================

def print_section(title: str):
    """打印分隔符"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def format_timestamp(ts):
    """格式化时间戳"""
    if not ts:
        return "N/A"
    try:
        # 处理毫秒时间戳
        if ts > 1e12:
            ts = ts / 1000
        dt = datetime.fromtimestamp(ts)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(ts)


def analyze_orders(orders: list) -> dict:
    """分析订单统计信息"""
    if not orders:
        return {}
    
    stats = {
        'total': len(orders),
        'by_status': {},
        'by_side': {},
        'by_type': {},
        'total_volume': 0,
        'filled_volume': 0,
        'avg_fill_rate': 0
    }
    
    filled_count = 0
    total_fill_rate = 0
    
    for order in orders:
        # 按状态统计
        status = order.get('status', 'Unknown')
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # 按方向统计
        side = order.get('side', 'Unknown')
        stats['by_side'][side] = stats['by_side'].get(side, 0) + 1
        
        # 按类型统计
        order_type = order.get('orderType', order.get('type', 'Unknown'))
        stats['by_type'][order_type] = stats['by_type'].get(order_type, 0) + 1
        
        # 成交量统计
        try:
            qty = float(order.get('quantity', order.get('origQty', 0)))
            executed_qty = float(order.get('executedQuantity', order.get('executedQty', 0)))
            
            stats['total_volume'] += qty
            stats['filled_volume'] += executed_qty
            
            if qty > 0:
                fill_rate = (executed_qty / qty) * 100
                total_fill_rate += fill_rate
                filled_count += 1
        except:
            pass
    
    # 计算平均成交率
    if filled_count > 0:
        stats['avg_fill_rate'] = total_fill_rate / filled_count
    
    return stats


def print_order_stats(stats: dict):
    """打印订单统计信息"""
    if not stats:
        print("  无订单数据")
        return
    
    print(f"📊 订单统计:")
    print(f"  总订单数: {stats['total']}")
    print(f"  总下单量: {stats['total_volume']:.4f}")
    print(f"  总成交量: {stats['filled_volume']:.4f}")
    print(f"  平均成交率: {stats['avg_fill_rate']:.2f}%")
    
    print(f"\n  按状态分布:")
    for status, count in stats['by_status'].items():
        print(f"    {status}: {count} ({count/stats['total']*100:.1f}%)")
    
    print(f"\n  按方向分布:")
    for side, count in stats['by_side'].items():
        print(f"    {side}: {count} ({count/stats['total']*100:.1f}%)")
    
    print(f"\n  按类型分布:")
    for order_type, count in stats['by_type'].items():
        print(f"    {order_type}: {count} ({count/stats['total']*100:.1f}%)")


async def main():
    """主函数"""
    
    # ========== 配置 ==========
    # 🔑 请填写你的 API 凭证（从 Backpack 交易所获取）
    API_KEY = "whLRx2oL9k6nsNMNrBSX/oKCk6xktT1fkMY8fTrnMYk="  # Base64 编码的公钥
    SECRET = "ueV+p51iQunTdUI4nNpV4xRHCQlxthpn4dqLZiQkShM="   # Base64 编码的私钥（32字节）
    
    # 🌐 代理配置
    PROXY = "http://127.0.0.1:1080"
    
    # 📊 测试交易对
    SYMBOL = "SOL_USDC"  # Backpack 格式（下划线分隔）
    
    print_section("🚀 Backpack API 完整示例")
    
    # ========== REST API 示例 ==========
    api = BackpackAPI(api_key=API_KEY, secret=SECRET, proxy=PROXY)
    
    # 1. 测试公开 API（不需要凭证）
    print_section("1️⃣ 公开 API - K 线查询")
    try:
        klines = api.get_klines(symbol=SYMBOL, interval="15m")
        print(f"最近 {len(klines)} 条 15分钟 K 线：")
        for i, kline in enumerate(klines[-5:], 1):  # 只显示最后 5 条
            # 解析时间字符串
            ts_str = kline.get('start', '')
            try:
                ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                time_display = ts.strftime('%Y-%m-%d %H:%M:%S')
            except:
                time_display = ts_str
            
            print(f"  {i}. 时间: {time_display}, "
                  f"开: {kline.get('open')}, "
                  f"高: {kline.get('high')}, "
                  f"低: {kline.get('low')}, "
                  f"收: {kline.get('close')}, "
                  f"量: {kline.get('volume')}, "
                  f"笔数: {kline.get('trades')}")
    except Exception as e:
        print(f"❌ K 线查询失败: {e}")
    
    print_section("2️⃣ 公开 API - 最新价格查询")
    try:
        ticker = api.get_ticker(symbol=SYMBOL)
        print(f"交易对: {ticker.get('symbol', SYMBOL)}")
        print(f"最新价格: {ticker.get('lastPrice', ticker.get('c'))}")
        print(f"24h 最高: {ticker.get('high', ticker.get('h'))}")
        print(f"24h 最低: {ticker.get('low', ticker.get('l'))}")
        print(f"24h 成交量: {ticker.get('volume', ticker.get('v'))}")
    except Exception as e:
        print(f"❌ 价格查询失败: {e}")
    
    print_section("3️⃣ 公开 API - 订单簿深度查询")
    try:
        depth = api.get_depth(symbol=SYMBOL)
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        
        print(f"最佳买价（前5档）:")
        for i, bid in enumerate(bids[:5], 1):
            print(f"  {i}. 价格: {bid[0]}, 数量: {bid[1]}")
        
        print(f"\n最佳卖价（前5档）:")
        for i, ask in enumerate(asks[:5], 1):
            print(f"  {i}. 价格: {ask[0]}, 数量: {ask[1]}")
    except Exception as e:
        print(f"❌ 订单簿查询失败: {e}")
    
    # 2. 测试私有 API（需要凭证）
    if API_KEY != "你的_BASE64_编码的公钥" and SECRET != "你的_BASE64_编码的私钥":
        print_section("4️⃣ 私有 API - 账户余额查询")
        try:
            balance = api.get_balance()
            print("账户余额:")
            
            # 根据返回格式解析
            if isinstance(balance, dict):
                for asset, details in balance.items():
                    available = details.get('available', 0)
                    locked = details.get('locked', 0)
                    if float(available) > 0 or float(locked) > 0:
                        print(f"  {asset}: "
                              f"可用 {available}, "
                              f"冻结 {locked}")
            elif isinstance(balance, list):
                for item in balance:
                    asset = item.get('asset', item.get('currency'))
                    available = item.get('available', 0)
                    locked = item.get('locked', 0)
                    if float(available) > 0 or float(locked) > 0:
                        print(f"  {asset}: "
                              f"可用 {available}, "
                              f"冻结 {locked}")
        except Exception as e:
            print(f"❌ 余额查询失败: {e}")
        
        print_section("5️⃣ 私有 API - 历史订单查询")
        try:
            # 查询最近的订单
            orders = api.get_order_history(symbol=SYMBOL, limit=20)
            
            if orders:
                # 显示订单统计
                stats = analyze_orders(orders)
                print_order_stats(stats)
                
                # 显示最近几条订单详情
                print(f"\n\n📝 最近 5 条订单详情:")
                for i, order in enumerate(orders[:5], 1):
                    # 提取订单字段
                    order_id = order.get('id', order.get('orderId', 'N/A'))
                    symbol = order.get('symbol', 'N/A')
                    side = order.get('side', 'N/A')
                    order_type = order.get('orderType', order.get('type', 'N/A'))
                    price = order.get('price', 'N/A')
                    quantity = order.get('quantity', order.get('origQty', 'N/A'))
                    executed_qty = order.get('executedQuantity', order.get('executedQty', '0'))
                    executed_quote = order.get('executedQuoteQuantity', order.get('cummulativeQuoteQty', 'N/A'))
                    status = order.get('status', 'N/A')
                    time_in_force = order.get('timeInForce', 'N/A')
                    timestamp = order.get('timestamp', order.get('createdAt', order.get('time')))
                    
                    # 计算成交率
                    try:
                        fill_rate = (float(executed_qty) / float(quantity)) * 100
                        fill_rate_str = f"{fill_rate:.2f}%"
                    except:
                        fill_rate_str = "N/A"
                    
                    print(f"\n  📋 订单 {i}:")
                    print(f"     ID: {order_id}")
                    print(f"     交易对: {symbol}")
                    print(f"     方向: {side} | 类型: {order_type} | 有效期: {time_in_force}")
                    print(f"     价格: {price}")
                    print(f"     数量: {quantity} | 已成交: {executed_qty} ({fill_rate_str})")
                    print(f"     成交额: {executed_quote}")
                    print(f"     状态: {status}")
                    print(f"     时间: {format_timestamp(timestamp)}")
            else:
                print("  暂无历史订单")
        except Exception as e:
            print(f"❌ 订单查询失败: {e}")
            import traceback
            traceback.print_exc()
        
        print_section("6️⃣ 私有 API - 成交历史查询")
        try:
            # 查询成交历史
            fills = api.get_fills(symbol=SYMBOL, limit=10)
            
            if fills:
                print(f"最近 {len(fills)} 条成交记录:\n")
                
                total_qty = 0
                total_fee = 0
                maker_count = 0
                
                for i, fill in enumerate(fills[:10], 1):
                    trade_id = fill.get('id', fill.get('tradeId', 'N/A'))
                    order_id = fill.get('orderId', 'N/A')
                    symbol = fill.get('symbol', 'N/A')
                    side = fill.get('side', 'N/A')
                    price = fill.get('price', 'N/A')
                    quantity = fill.get('quantity', fill.get('qty', 'N/A'))
                    quote_qty = fill.get('quoteQuantity', fill.get('quoteQty', 'N/A'))
                    fee = fill.get('fee', fill.get('commission', '0'))
                    fee_asset = fill.get('feeAsset', fill.get('commissionAsset', 'N/A'))
                    is_maker = fill.get('isMaker', False)
                    timestamp = fill.get('timestamp', fill.get('time'))
                    
                    # 统计
                    try:
                        total_qty += float(quantity)
                        total_fee += float(fee)
                        if is_maker:
                            maker_count += 1
                    except:
                        pass
                    
                    print(f"  💱 成交 {i}:")
                    print(f"     ID: {trade_id} | 订单ID: {order_id}")
                    print(f"     交易对: {symbol} | 方向: {side}")
                    print(f"     价格: {price} | 数量: {quantity}")
                    print(f"     成交额: {quote_qty}")
                    print(f"     手续费: {fee} {fee_asset} | {'Maker' if is_maker else 'Taker'}")
                    print(f"     时间: {format_timestamp(timestamp)}")
                    print()
                
                # 成交统计
                print(f"\n  📊 成交统计:")
                print(f"     总成交笔数: {len(fills)}")
                print(f"     总成交量: {total_qty:.4f}")
                print(f"     总手续费: {total_fee:.6f}")
                print(f"     Maker 比例: {maker_count}/{len(fills)} ({maker_count/len(fills)*100:.1f}%)")
            else:
                print("  暂无成交记录")
        except Exception as e:
            print(f"❌ 成交历史查询失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ 跳过私有 API 测试（请先配置 API_KEY 和 SECRET）")
    
    # ========== WebSocket 示例 ==========
    print_section("7️⃣ WebSocket - 实时数据订阅")
    
    # 注意：WebSocket 使用 socks 代理需要额外配置
    # 这里的代理参数可能不起作用，需要系统级代理或专门的库
    ws = BackpackWebSocket()
    
    print("开始订阅 WebSocket 流（按 Ctrl+C 停止）...")
    print(f"  - K 线（15分钟）: {SYMBOL}")
    print(f"  - 价格更新: {SYMBOL}")
    print(f"  - 订单簿深度: {SYMBOL}")
    print()
    
    try:
        # 创建多个订阅任务
        tasks = [
            ws.subscribe_kline(SYMBOL, "15m"),
            ws.subscribe_ticker(SYMBOL),
            ws.subscribe_depth(SYMBOL)
        ]
        
        # 并发运行所有订阅
        await asyncio.gather(*tasks)
    
    except KeyboardInterrupt:
        print("\n\n⏹️ 停止订阅")
    except Exception as e:
        print(f"\n❌ WebSocket 错误: {e}")
    
    print_section("✅ 示例完成")


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())

