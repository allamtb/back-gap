"""
Backpack 交易所适配器

Backpack 不被 CCXT 官方支持，需要自研适配器直接对接 REST API

官方 API 文档：https://docs.backpack.exchange/

认证方式：
- 使用 ED25519 密钥对签名
- 请求头：X-Timestamp, X-Window, X-API-Key, X-Signature
- Base64 编码的公钥和签名
"""

import time
import json
import logging
import base64
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode
import requests
from decimal import Decimal, ROUND_DOWN

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False
    
from .adapter_interface import AdapterInterface, AdapterCapability

logger = logging.getLogger(__name__)


class BackpackAdapter(AdapterInterface):
    """
    Backpack 交易所适配器（非 CCXT）
    
    说明：
        - Backpack 未被 CCXT 支持，需要直接对接 REST API
        - 使用 ED25519 签名认证
        - 支持现货和合约交易
        - 直接继承 AdapterInterface，完全自定义实现
    """
    
    # Instruction 类型映射（根据官方文档）
    INSTRUCTION_MAP = {
        'balanceQuery': 'balanceQuery',
        'orderExecute': 'orderExecute',
        'orderCancel': 'orderCancel',
        'orderCancelAll': 'orderCancelAll',
        'orderQuery': 'orderQuery',
        'orderQueryAll': 'orderQueryAll',
        'orderHistoryQueryAll': 'orderHistoryQueryAll',
        'fillHistoryQueryAll': 'fillHistoryQueryAll',
        'positionQuery': 'positionQuery',
        'depositQueryAll': 'depositQueryAll',
        'withdrawalQueryAll': 'withdrawalQueryAll',
    }
    
    def __init__(self, market_type: str, config: dict):
        """
        初始化 Backpack 适配器
        
        Args:
            market_type: 市场类型 ('spot' 或 'futures')
            config: 配置字典 {
                'apiKey': 'Base64编码的公钥' (可选，仅私有API需要),
                'secret': 'Base64编码的私钥' (可选，仅私有API需要),
                ...
            }
        
        Note:
            - 公开API（如K线、市场数据）不需要凭证
            - 私有API（如下单、查询余额）需要提供 apiKey 和 secret
        """
        self.api_key = config.get('apiKey') or config.get('api_key')
        self.secret = config.get('secret')
        
        # 只在提供了凭证时才初始化签名密钥
        if self.api_key and self.secret:
            if not HAS_CRYPTO:
                raise ImportError(
                    "❌ Backpack 私有API需要 cryptography 库进行 ED25519 签名\n"
                    "请安装：pip install cryptography"
                )
            
            # 初始化 ED25519 签名密钥（使用 cryptography 库，官方推荐）
            try:
                # secret 应该是 Base64 编码的私钥（32字节）
                secret_bytes = base64.b64decode(self.secret)
                self.private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
                logger.info("✅ ED25519 签名密钥加载成功（支持私有API）")
            except Exception as e:
                raise ValueError(f"❌ 无效的 Backpack secret (应为 Base64 编码的 ED25519 私钥): {e}")
        else:
            # 无凭证模式：仅支持公开 API
            self.private_key = None
            logger.info("⚠️ Backpack 适配器以无认证模式初始化（仅支持公开API：K线、市场数据等）")
        
        # Backpack API 基础 URL
        self.base_url = config.get('baseUrl', 'https://api.backpack.exchange')
        
        # HTTP 会话
        self.session = requests.Session()
        self.timeout = int(config.get('timeout', 10000)) / 1000  # 毫秒转秒
        
        # 🌐 配置代理（参考 DefaultAdapter 实现）
        self.proxies = None
        
        # 优先使用 config 中的 proxies 配置
        if config.get('proxies'):
            raw_proxies = config.get('proxies')
            # 自动处理代理协议（与 DefaultAdapter 保持一致）
            self.proxies = {}
            for key, value in raw_proxies.items():
                if key in ['http', 'https']:
                    # REST API 使用 http:// 协议
                    self.proxies[key] = self._process_proxy_url(value, protocol='http')
                else:
                    self.proxies[key] = value
            logger.debug(f"✅ Backpack 使用用户提供的代理配置")
        else:
            # 从环境变量读取代理配置（与币安保持一致）
            import os
            proxy_url = os.getenv('PROXY_URL', '').strip()
            if proxy_url:
                processed_url = self._process_proxy_url(proxy_url, protocol='http')
                self.proxies = {
                    'http': processed_url,
                    'https': processed_url,
                }
                logger.info(f"🌐 Backpack 已自动配置代理（从环境变量）: {proxy_url}")
            else:
                logger.debug(f"ℹ️ Backpack 未配置代理（直连）")
        
        # 应用代理到 session
        if self.proxies:
            self.session.proxies.update(self.proxies)
            logger.info(f"🌐 Backpack 代理已应用: {self.proxies}")
        
        # 不调用父类的 __init__（因为 Backpack 不使用 CCXT）
        self.market_type = market_type
        self.config = config
        self.exchange_id = 'backpack'
        self.exchange = None  # 不使用 CCXT
        
        # 声明支持的功能
        self._supported_capabilities = {
            AdapterCapability.TEST_CONNECTIVITY,
            AdapterCapability.LOAD_MARKETS,
            AdapterCapability.FETCH_OHLCV,
            AdapterCapability.FETCH_PRICES,
            AdapterCapability.FETCH_SPOT_BALANCE,
            AdapterCapability.FETCH_FUTURES_POSITIONS,
            AdapterCapability.FETCH_SPOT_ORDERS,
            AdapterCapability.FETCH_FUTURES_ORDERS,
            AdapterCapability.CREATE_ORDER,
        }
        
        # 不使用市场数据缓存
        self._market_cache = None
        
        logger.info(f"✅ Backpack 适配器初始化成功 (market_type={market_type})")
    
    def _get_exchange_id(self) -> str:
        """返回交易所 ID"""
        return 'backpack'
    
    def _initialize_exchange(self):
        """
        Backpack 不使用 CCXT，跳过初始化
        """
        pass

    def get_exchange(self):
        """
        为了兼容共用的下单流程，返回自身作为“交易所”实例。
        Backpack 不依赖 CCXT，这里仅用于占位，确保调用链不中断。
        """
        return self
    
    def _process_proxy_url(self, proxy_url: str, protocol: str = 'http') -> str:
        """
        处理代理 URL，自动添加协议前缀（与 DefaultAdapter 保持一致）
        
        Args:
            proxy_url: 代理 URL，可以是：
                - 简化格式: "127.0.0.1:1080"
                - 完整格式: "http://127.0.0.1:7890"
            protocol: 默认协议（当 proxy_url 没有协议时使用）
        
        Returns:
            完整的代理 URL（带协议前缀）
        """
        if '://' in proxy_url:
            # 已经有协议前缀，直接返回
            return proxy_url
        
        # 添加协议前缀
        return f"{protocol}://{proxy_url}"

    # ==================== 数值格式化 ====================

    @staticmethod
    def _format_quantity(amount: float, max_decimals: int = 6) -> str:
        """
        将数量格式化为字符串，限制小数位，避免 "Quantity decimal too long"。
        默认 6 位小数，向下取整。
        """
        q = Decimal(str(amount))
        quantized = q.quantize(Decimal(f"1e-{max_decimals}"), rounding=ROUND_DOWN)
        return format(quantized.normalize(), 'f')

    # ==================== 账户限额查询 ====================

    def get_max_order_quantity(
        self,
        symbol: str,
        side: str,
        price: Optional[float] = None,
        reduceOnly: Optional[bool] = None,
        autoBorrow: Optional[bool] = None,
        autoBorrowRepay: Optional[bool] = None,
        autoLendRedeem: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        查询最大可下单数量（instruction: maxOrderQuantity）
        """
        payload = {
            "symbol": symbol.replace('/', '_'),
            "side": "Bid" if side.lower() == "buy" else "Ask",
        }

        if price is not None:
            payload["price"] = str(price)
        if reduceOnly is not None:
            payload["reduceOnly"] = bool(reduceOnly)
        if autoBorrow is not None:
            payload["autoBorrow"] = bool(autoBorrow)
        if autoBorrowRepay is not None:
            payload["autoBorrowRepay"] = bool(autoBorrowRepay)
        if autoLendRedeem is not None:
            payload["autoLendRedeem"] = bool(autoLendRedeem)

        result = self._request(
            "POST",
            "/api/v1/order",
            data={
                "instruction": "maxOrderQuantity",
                "payload": payload
            },
            private=True
        )

        return result
    
    # ==================== 签名与鉴权 ====================
    
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
        生成 Backpack API 签名
        
        签名规则（根据官方文档）：
        1. 参数按字母顺序排列并转换为查询字符串格式
        2. 拼接 instruction 前缀和 timestamp/window 后缀
        3. 使用 ED25519 私钥签名
        4. Base64 编码签名结果
        
        签名字符串格式：
            instruction=<instruction>&<key1>=<value1>&<key2>=<value2>&timestamp=<ts>&window=<window>
        
        Args:
            instruction: API 指令类型（如 'balanceQuery', 'orderExecute'）
            params: 请求参数（dict）
            window: 请求有效时间窗口（毫秒，默认5000，最大60000）
        
        Returns:
            请求头字典
        """
        # 检查是否已初始化私钥
        if not self.private_key or not self.api_key:
            raise ValueError(
                "❌ 调用私有API需要提供 apiKey 和 secret\n"
                "请在初始化 BackpackAdapter 时提供正确的凭证"
            )
        
        timestamp = self._timestamp_ms()
        
        # 1. 构建签名字符串
        sign_str_parts = [f"instruction={instruction}"]
        
        # 2. 添加排序后的参数
        if params:
            # 按字母顺序排序参数
            sorted_params = sorted(params.items())
            for key, value in sorted_params:
                if value is not None:  # 跳过 None 值
                    sign_str_parts.append(f"{key}={value}")
        
        # 3. 添加 timestamp 和 window
        sign_str_parts.append(f"timestamp={timestamp}")
        sign_str_parts.append(f"window={window}")
        
        # 4. 拼接完整签名字符串
        sign_str = "&".join(sign_str_parts)
        
        # 5. ED25519 签名（使用 cryptography 库）
        signature_bytes = self.private_key.sign(sign_str.encode('utf-8'))
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        # 6. 构建请求头
        headers = {
            "X-API-Key": self.api_key,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8",
        }
        
        logger.debug(f"🔐 签名字符串: {sign_str}")
        
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
        发送 HTTP 请求到 Backpack API
        
        Args:
            method: HTTP 方法（GET/POST/DELETE）
            path: API 路径（如 '/api/v1/markets'）
            params: 请求参数（GET 用查询参数，POST 用请求体）
            instruction: 指令类型（私有接口必需，如 'balanceQuery'）
            private: 是否为私有接口（需要签名）
        
        Returns:
            API 响应（JSON 解析后的 dict/list）
        """
        # 构建完整 URL
        url = self.base_url + path
        
        # 请求头
        headers = {"Content-Type": "application/json"}
        
        # 私有接口：需要签名
        if private:
            if not instruction:
                raise ValueError("❌ 私有接口必须指定 instruction 参数")
            headers = self._sign_request(instruction, params)
        
        # 发送请求
        try:
            if method.upper() == 'GET':
                # GET 请求：参数放在 URL 查询字符串
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == 'POST':
                # POST 请求：参数放在请求体
                response = self.session.post(
                    url,
                    json=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == 'DELETE':
                # DELETE 请求：参数放在 URL 查询字符串
                response = self.session.delete(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"❌ 不支持的 HTTP 方法: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.HTTPError as e:
            logger.error(f"❌ Backpack API HTTP 错误: {method} {url}")
            logger.error(f"   状态码: {e.response.status_code}")
            logger.error(f"   响应: {e.response.text}")
            raise
        except requests.RequestException as e:
            logger.error(f"❌ Backpack API 请求失败: {method} {url}, 错误: {e}")
            raise
    
    # ==================== 实现标准接口 ====================
    
    def load_markets(self, reload: bool = False) -> Dict[str, Any]:
        """
        加载市场数据（交易对信息）
        
        Backpack 不需要预加载市场数据，直接返回空字典
        
        Args:
            reload: 是否强制重新加载（忽略缓存）
        
        Returns:
            空字典（Backpack 不需要预加载市场数据）
        """
        # Backpack 不需要预加载市场数据
        # 所有交易对信息都是按需获取的
        logger.debug(f"{self.exchange_id} load_markets() 被调用，返回空字典（不需要预加载）")
        return {}
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        测试连通性和鉴权有效性（参考币安实现）
        
        测试方法：
            通过获取账户余额验证 API Key 和签名是否正确
            
        API: GET /api/v1/capital (instruction=balanceQuery)
        
        Returns:
            包含测试结果和余额数据的字典
        """
        try:
            start_time = time.time()
            
            # 🔑 通过获取余额验证鉴权（与币安、Gate.io保持一致）
            # 使用 fetch_balance 方法获取余额数据
            balance = self.fetch_balance()
            
            latency_ms = (time.time() - start_time) * 1000
            
            # 提取余额信息（只包含有余额的币种）
            balance_data = {}
            for currency, amount in balance.get('total', {}).items():
                if amount and float(amount) > 0:
                    balance_data[currency] = str(amount)
            
            return {
                'ok': True,
                'serverTime': int(time.time() * 1000),
                'accountId': None,  # Backpack API 不直接返回 accountId
                'latencyMs': round(latency_ms, 2),
                'balance': balance_data  # 返回余额数据
            }
        except Exception as e:
            logger.error(f"❌ Backpack 连通性测试失败: {e}")
            return {
                'ok': False,
                'error': str(e),
                'serverTime': int(time.time() * 1000)
            }
    
    def fetch_symbols(self, quote: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取交易对列表
        
        API: GET /api/v1/markets
        
        响应示例（根据文档）：
        [
            {
                "symbol": "SOL_USDC",
                "baseSymbol": "SOL",
                "quoteSymbol": "USDC",
                "filters": {
                    "price": {"minPrice": "0.01", "maxPrice": "1000000", "tickSize": "0.01"},
                    "quantity": {"minQty": "0.1", "maxQty": "1000000", "stepSize": "0.1"}
                }
            },
            ...
        ]
        """
        try:
            markets_data = self._request("GET", "/api/v1/markets", private=False)
            
            if not isinstance(markets_data, list):
                logger.warning(f"⚠️ 意外的 markets 响应格式: {type(markets_data)}")
                return []
            
            symbols_list = []
            
            for m in markets_data:
                # 根据实际响应结构解析
                symbol = m.get('symbol', '')  # 如 "SOL_USDC" 或 "SOL_USDC_PERP"
                base = m.get('baseSymbol', m.get('base', ''))
                q = m.get('quoteSymbol', m.get('quote', ''))
                
                # 如果没有 base/quote，尝试从 symbol 分割
                if not base or not q:
                    # 处理合约符号：SOL_USDC_PERP → SOL, USDC
                    if symbol.endswith('_PERP'):
                        clean_symbol = symbol[:-5]  # 去掉 _PERP
                    else:
                        clean_symbol = symbol
                    
                    parts = clean_symbol.split('_')
                    if len(parts) == 2:
                        base, q = parts
                
                # 过滤报价币种
                if quote and q != quote:
                    continue
                
                # 解析精度和限制
                filters = m.get('filters', {})
                price_filter = filters.get('price', {})
                qty_filter = filters.get('quantity', {})
                
                symbols_list.append({
                    'symbol': f"{base}/{q}",
                    'base': base,
                    'quote': q,
                    'status': 'TRADING',  # Backpack 不返回 status，假设都在交易
                    'precision': {
                        'price': self._get_precision(price_filter.get('tickSize', '0.01')),
                        'amount': self._get_precision(qty_filter.get('stepSize', '0.1'))
                    },
                    'limits': {
                        'minQty': float(qty_filter.get('minQty', 0)),
                        'minNotional': 0  # Backpack 不返回 minNotional
                    }
                })
                
                # 数量限制
                if limit and len(symbols_list) >= limit:
                    break
            
            logger.info(f"✅ 获取到 {len(symbols_list)} 个交易对")
            return symbols_list
            
        except Exception as e:
            logger.error(f"❌ Backpack 获取交易对失败: {e}")
            return []
    
    @staticmethod
    def _get_precision(step_size: str) -> int:
        """从 stepSize 计算精度（小数位数）"""
        try:
            step = float(step_size)
            if step >= 1:
                return 0
            # 计算小数位数
            precision = len(str(step).rstrip('0').split('.')[1]) if '.' in str(step) else 0
            return precision
        except:
            return 8  # 默认精度
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str = '15m',
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[List[Any]]:
        """
        获取 K线数据
        
        API: GET /api/v1/klines
        
        参数：
            symbol: BTC/USDC (标准格式，斜杠分隔)
            interval: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1month
            startTime: 起始时间（秒级时间戳，必需）
            endTime: 结束时间（秒级时间戳）
        
        实际响应格式：
        [
            {
                "start": "2024-09-11T12:00:00Z",  // K线开始时间 (ISO 8601)
                "end": "2024-09-11T12:15:00Z",    // K线结束时间
                "open": "18.75",                  // 开盘价
                "high": "19.80",                  // 最高价
                "low": "18.50",                   // 最低价
                "close": "19.25",                 // 收盘价
                "volume": "32123",                // 成交量（基础资产）
                "quoteVolume": "600000",          // 成交量（计价资产）
                "trades": "1234"                  // 成交笔数
            },
            ...
        ]
        """
        try:
            # 🎯 格式转换：BTC/USDC → BTC_USDC 或 BTC_USDC_PERP
            if '/' not in symbol:
                # 如果没有 '/'，说明可能是旧格式，给出警告
                logger.warning(f"⚠️ Symbol 格式不正确，期望完整交易对（如 'BTC/USDC'），收到: {symbol}")
                # 兼容处理：假设是 USDC 计价
                market_symbol = f"{symbol}_USDC"
            else:
                # 标准格式：BTC/USDC → BTC_USDC
                market_symbol = symbol.replace('/', '_')
            
            # 🔮 合约交易对需要添加 _PERP 后缀
            if self.market_type.lower() in ['futures', 'future', 'swap'] and not market_symbol.endswith('_PERP'):
                market_symbol = f"{market_symbol}_PERP"
            
            logger.debug(f"🔄 Symbol格式转换 ({self.market_type}): {symbol} → {market_symbol}")
            
            # 转换时间间隔格式
            interval_map = {
                '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
                '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1month'
            }
            backpack_interval = interval_map.get(interval, interval)
            
            # 构建时间范围（Backpack 要求 startTime 和 endTime，秒级时间戳）
            from datetime import datetime, timedelta
            
            if since:
                # since 是毫秒时间戳，转换为秒
                start_time = since // 1000
                end_time = int(datetime.utcnow().timestamp())
            elif not since:
                # 默认查询最近 1 天的数据（与 example 保持一致）
                end_dt = datetime.utcnow()
                start_dt = end_dt - timedelta(days=1)
                start_time = int(start_dt.timestamp())
                end_time = int(end_dt.timestamp())
            else:
                # 使用当前时间
                end_time = int(datetime.utcnow().timestamp())
                start_time = end_time - 86400  # 默认1天
            
            params = {
                'symbol': market_symbol,
                'interval': backpack_interval,
                'startTime': start_time,
                'endTime': end_time
            }
            
            klines_data = self._request("GET", "/api/v1/klines", params=params, private=False)
            
            if not isinstance(klines_data, list):
                logger.warning(f"⚠️ 意外的 klines 响应格式: {type(klines_data)}")
                return []
            
            # 标准化为 [[timestamp, open, high, low, close, volume], ...]
            klines = []
            for k in klines_data:
                # 解析 ISO 8601 时间戳（使用 start 字段）
                timestamp = self._parse_iso_time(k.get('start', ''))
                
                klines.append([
                    timestamp,
                    float(k.get('open', 0)),   # open
                    float(k.get('high', 0)),   # high
                    float(k.get('low', 0)),    # low
                    float(k.get('close', 0)),  # close
                    float(k.get('volume', 0))  # volume
                ])
            
            # 限制返回数量（取最新的）
            if limit and len(klines) > limit:
                klines = klines[-limit:]
            
            logger.debug(f"✅ 获取到 {len(klines)} 条K线数据")
            return klines
            
        except Exception as e:
            logger.error(f"❌ Backpack 获取K线失败 {symbol}/{interval}: {e}")
            return []
    
    @staticmethod
    def _parse_iso_time(time_str: str) -> int:
        """解析 ISO 8601 时间字符串为毫秒时间戳"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except:
            return int(time.time() * 1000)
    
    def fetch_prices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取价格
        
        API: GET /api/v1/tickers (获取所有ticker)
        或: GET /api/v1/ticker?symbol=<symbol> (单个ticker)
        
        响应示例（/api/v1/tickers）：
        [
            {
                "s": "SOL_USD",     // Symbol
                "o": "18.75",       // First price (24h)
                "c": "19.24",       // Last price
                "h": "19.80",       // High price
                "l": "18.50",       // Low price
                "v": "32123",       // Base asset volume
                "V": "928190",      // Quote asset volume
                "n": 93828          // Number of trades
            },
            ...
        ]
        """
        try:
            # 前端已经传来正确格式的 symbol，直接使用
            symbol_mapping = {symbol: symbol for symbol in symbols}
            logger.debug(f"📥 批量价格请求 symbols: {symbols}")
            
            # 获取所有 ticker
            tickers_data = self._request("GET", "/api/v1/tickers", private=False)
            
            if not isinstance(tickers_data, list):
                logger.warning(f"⚠️ 意外的 tickers 响应格式: {type(tickers_data)}")
                return {s: {'last': 0, 'bid': 0, 'ask': 0, 'mark': 0} for s in symbols}
            
            # 构建交易对映射（Backpack格式 → 价格）
            ticker_map = {}
            for t in tickers_data:
                raw_symbol = t.get('s', '')  # 如 "SOL_USDC" 或 "SOL_USDC_PERP"
                
                # 转换为标准格式 "SOL/USDC"
                # 处理合约符号：SOL_USDC_PERP → SOL/USDC
                if raw_symbol.endswith('_PERP'):
                    base_symbol = raw_symbol[:-5]  # 去掉 _PERP
                    standard_symbol = base_symbol.replace('_', '/')
                else:
                    standard_symbol = raw_symbol.replace('_', '/')
                
                ticker_map[standard_symbol] = {
                    'last': float(t.get('c', 0)),  # close price
                    'bid': 0,  # Backpack tickers 不提供 bid/ask
                    'ask': 0,
                    'mark': float(t.get('c', 0))  # 用 close 代替 mark
                }
            
            # 填充请求的交易对（使用映射后的symbol查找）
            result = {}
            for original_symbol in symbols:
                mapped_symbol = symbol_mapping[original_symbol]
                
                if mapped_symbol in ticker_map:
                    # 使用原始symbol作为key返回
                    result[original_symbol] = ticker_map[mapped_symbol]
                else:
                    # 尝试单独获取
                    try:
                        single_ticker = self._fetch_single_ticker(mapped_symbol)
                        result[original_symbol] = single_ticker
                    except:
                        result[original_symbol] = {'last': 0, 'bid': 0, 'ask': 0, 'mark': 0}
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Backpack 批量获取价格失败: {e}")
            return {s: {'last': 0, 'bid': 0, 'ask': 0, 'mark': 0} for s in symbols}
    
    def _fetch_single_ticker(self, symbol: str) -> Dict[str, Any]:
        """获取单个交易对的 ticker（与 example 保持一致的字段处理）"""
        market_symbol = symbol.replace('/', '_')
        ticker = self._request("GET", "/api/v1/ticker", params={'symbol': market_symbol}, private=False)
        
        # 字段优先级：lastPrice > c（根据实际 API 响应调整）
        last_price = float(ticker.get('lastPrice', ticker.get('c', 0)))
        
        return {
            'last': last_price,
            'bid': float(ticker.get('bidPrice', 0)),
            'ask': float(ticker.get('askPrice', 0)),
            'mark': last_price  # 使用 lastPrice 作为标记价格
        }
    
    def fetch_balance(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取账户余额（兼容 CCXT 格式）
        
        此方法用于兼容 position_service.py 中的调用
        返回格式与 CCXT 的 fetch_balance() 一致
        
        API: GET /api/v1/capital (instruction=balanceQuery)
        
        Args:
            symbols: 可选的币种列表（如 ['BTC', 'ETH']），用于过滤查询
                    Backpack API 不支持按币种过滤，此参数会在返回后过滤
        
        Returns:
            {
                'info': {...},  # 原始数据
                'free': {'BTC': 1.2, 'USDC': 1000, ...},
                'used': {'BTC': 0.1, 'USDC': 100, ...},
                'total': {'BTC': 1.3, 'USDC': 1100, ...}
            }
        """
        try:
            balances_data = self._request(
                "GET",
                "/api/v1/capital",
                instruction="balanceQuery",
                private=True
            )
            
            # 构建 CCXT 格式的余额数据
            result = {
                'info': balances_data,
                'free': {},
                'used': {},
                'total': {}
            }
            
            # 如果提供了 symbols，转换为大写集合用于快速匹配
            symbol_set = None
            if symbols:
                symbol_set = {s.upper() for s in symbols}
            
            # 根据实际 API 响应格式解析（可能是 dict 或 list）
            if isinstance(balances_data, dict):
                # 格式: {asset: {available, locked, staked}}
                for asset, balance in balances_data.items():
                    # 如果指定了 symbols，进行过滤
                    if symbol_set and asset.upper() not in symbol_set:
                        continue
                    
                    available = float(balance.get('available', 0))
                    locked = float(balance.get('locked', 0))
                    staked = float(balance.get('staked', 0))
                    total = available + locked + staked
                    
                    if total > 0:
                        result['free'][asset] = available
                        result['used'][asset] = locked + staked
                        result['total'][asset] = total
                        
            elif isinstance(balances_data, list):
                # 格式: [{asset, available, locked, staked}, ...]
                for b in balances_data:
                    asset = b.get('asset', b.get('currency', ''))
                    
                    # 如果指定了 symbols，进行过滤
                    if symbol_set and asset.upper() not in symbol_set:
                        continue
                    
                    available = float(b.get('available', 0))
                    locked = float(b.get('locked', 0))
                    staked = float(b.get('staked', 0))
                    total = available + locked + staked
                    
                    if total > 0:
                        result['free'][asset] = available
                        result['used'][asset] = locked + staked
                        result['total'][asset] = total
            
            logger.debug(f"✅ Backpack fetch_balance: {len(result['total'])} 个币种" + 
                        (f" (过滤: {symbols})" if symbols else ""))
            return result
            
        except Exception as e:
            logger.error(f"❌ Backpack 获取余额失败: {e}")
            # 返回空余额而不是抛异常
            return {
                'info': {},
                'free': {},
                'used': {},
                'total': {}
            }
    
    def fetch_positions(self, symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        获取持仓（现货为余额，合约为持仓）
        
        API:
            现货: GET /api/v1/capital (instruction=balanceQuery)
            合约: GET /api/v1/open (instruction=positionQuery) - 获取未平仓位置
        
        官方文档：https://docs.backpack.exchange/
        
        注意：此方法主要用于合约持仓，现货余额请使用 fetch_balance()
        """
        try:
            if self.market_type == 'spot':
                # 现货：获取余额（调用 fetch_balance 并转换为持仓格式）
                # 传递 symbols 参数以支持过滤
                balance = self.fetch_balance(symbols=symbols)
                positions = []
                
                for currency, amount in balance.get('total', {}).items():
                    if amount > 0:
                        positions.append({
                            'exchange': 'backpack',
                            'type': 'spot',
                            'symbol': currency,
                            'free': balance.get('free', {}).get(currency, 0),
                            'used': balance.get('used', {}).get(currency, 0),
                            'staked': 0,
                            'total': amount
                        })
                return positions
                
            else:
                # 合约：获取持仓（使用 /api/v1/open 端点）
                params = {}
                if symbols and len(symbols) == 1:
                    params['symbol'] = symbols[0].replace('/', '_')
                
                positions_data = self._request(
                    "GET",
                    "/api/v1/open",
                    params=params if params else None,
                    instruction="positionQuery",
                    private=True
                )
                
                if not isinstance(positions_data, list):
                    logger.warning(f"⚠️ 意外的 positions 响应格式: {type(positions_data)}")
                    return []
                
                positions = []
                for p in positions_data:
                    sym = p.get('symbol', '')  # 如 "SOL_USDC_PERP"
                    contracts = float(p.get('positionAmt', p.get('contracts', 0)))
                    
                    # 过滤交易对
                    if symbols:
                        standard_symbol = sym.replace('_', '/')
                        if not any(s in standard_symbol for s in symbols):
                            continue
                    
                    if contracts != 0:
                        # 转换为标准格式
                        standard_symbol = sym.replace('_', '/')
                        
                        positions.append({
                            'exchange': 'backpack',
                            'type': 'futures',
                            'symbol': standard_symbol,
                            'positionSide': p.get('side', 'BOTH'),
                            'size': contracts,
                            'entryPrice': float(p.get('entryPrice', 0)),
                            'markPrice': float(p.get('markPrice', 0)),
                            'leverage': int(p.get('leverage', 1)),
                            'marginMode': p.get('marginType', 'cross'),
                            'unrealizedPnl': float(p.get('unrealizedPnl', 0)),
                            'isolatedMargin': float(p.get('isolatedMargin', 0)),
                            'updateTime': p.get('updateTime')
                        })
                
                return positions
                
        except Exception as e:
            logger.error(f"❌ Backpack 获取持仓失败: {e}")
            return []
    
    def fetch_orders(
        self,
        symbol: Optional[str] = None,
        since: Optional[int] = None,
        limit: int = 500,
        base_currencies: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        获取订单（按交易对）
        
        API: GET /api/v1/orders (instruction=orderQueryAll)
        或: GET /api/v1/order (instruction=orderQuery) - 按 orderId 查询
        """
        try:
            params = {}
            
            # 如果指定了交易对
            if symbol:
                params['symbol'] = symbol.replace('/', '_')
            
            # 时间范围（Backpack API 可能不支持，需根据实际调整）
            if since:
                params['startTime'] = since // 1000  # 转换为秒
            
            # 获取订单历史
            orders_data = self._request(
                "GET",
                "/wapi/v1/history/orders",  # 订单历史接口
                params=params,
                instruction="orderHistoryQueryAll",
                private=True
            )
            
            if not isinstance(orders_data, list):
                logger.warning(f"⚠️ 意外的 orders 响应格式: {type(orders_data)}")
                return []
            
            # 标准化订单数据
            normalized = []
            for o in orders_data:
                raw_symbol = o.get('symbol', '')  # 如 "SOL_USDC"
                standard_symbol = raw_symbol.replace('_', '/')
                
                raw_side = str(o.get('side', '')).lower()
                side_normalized = 'buy' if raw_side in ['buy', 'bid'] else 'sell' if raw_side in ['sell', 'ask'] else raw_side

                # 时间字段
                order_ts = o.get('timestamp') or o.get('createdAt') or o.get('ts')
                update_ts = o.get('lastUpdateTime') or o.get('updatedAt') or order_ts

                normalized.append({
                    'orderId': str(o.get('id', o.get('orderId', ''))),
                    'exchange': 'backpack',
                    'marketType': self.market_type,
                    'order_type': self.market_type,
                    'symbol': standard_symbol,
                    'side': side_normalized,
                    'type': o.get('orderType', o.get('type', '')).lower(),
                    'price': self._safe_float(o.get('price'), 0),
                    'amount': self._safe_float(o.get('quantity', o.get('origQty')), 0),
                    'filled': self._safe_float(o.get('executedQuantity', o.get('executedQty')), 0),
                    'remaining': self._safe_float(o.get('quantity'), 0) - self._safe_float(o.get('executedQuantity'), 0),
                    'total': self._safe_float(o.get('quoteQuantity', o.get('cost')), 0),
                    'fee': 0,  # Backpack 需要单独查询 fee
                    'feeCurrency': '',
                    'status': o.get('status', 'unknown').lower(),
                    # 原始时间戳（毫秒），前端直接格式化
                    'orderTime': order_ts,
                    'updateTime': update_ts,
                    'timestamp': order_ts,
                    'lastUpdateTime': update_ts,
                })
            
            # 数量限制
            if limit and len(normalized) > limit:
                normalized = normalized[-limit:]
            
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Backpack 获取订单失败: {e}")
            return []
    
    def fetch_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        print("暂未实现")
        return []

    def create_order(
        self,
        symbol: str,
        type: str,  # CCXT 风格参数名，order_routes 会传入此字段
        side: str,
        amount: float,
        price: Optional[float] = None,
        params: Optional[dict] = None,
        timeInForce: Optional[str] = None,
        reduceOnly: Optional[bool] = None,
        clientOrderId: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建订单
        
        API: POST /api/v1/order (instruction=orderExecute)
        
        参数（根据文档）：
            symbol: 交易对，如 "SOL_USDC"
            side: "Bid" 或 "Ask"
            orderType: "Limit", "Market"
            quantity: 数量（字符串）
            price: 价格（可选，限价单必需）
            timeInForce: "GTC", "IOC", "FOK" (可选)
            clientId: 客户端订单 ID (可选)
            postOnly: 是否只做 Maker (可选)
        """
        try:
            market_symbol = symbol.replace('/', '_')
            # 合约交易需使用 PERP 后缀
            if self.market_type != 'spot' and not market_symbol.endswith('_PERP'):
                market_symbol = f"{market_symbol}_PERP"
            
            # Backpack 仅接受 "Market" / "Limit"
            order_type_raw = (type or '').strip().lower()
            if order_type_raw not in ['market', 'limit']:
                order_type_raw = 'market'  # 兜底
            order_type = 'Market' if order_type_raw == 'market' else 'Limit'
            side_norm = side.lower()
            is_buy = side_norm == 'buy'
            
            # 构建订单参数
            order_payload = {
                'symbol': market_symbol,
                'side': 'Bid' if is_buy else 'Ask',
                'orderType': order_type,  # "Market" / "Limit"
                # Backpack 对数量的小数位有限制，默认保留 6 位，向下取整
                'quantity': self._format_quantity(amount, max_decimals=6)
            }
            # 兜底：确保 orderType 不为空
            if not order_payload['orderType']:
                order_payload['orderType'] = 'Market'
            
            # 限价单需要价格
            if price is not None:
                order_payload['price'] = str(price)
            
            # 可选参数
            if timeInForce:
                order_payload['timeInForce'] = timeInForce
            if clientOrderId:
                order_payload['clientId'] = clientOrderId
            if reduceOnly is not None:
                order_payload['reduceOnly'] = bool(reduceOnly)
            
            # 合并附加参数（不覆盖关键字段）
            if params:
                for k, v in params.items():
                    if k in ['symbol', 'side', 'orderType', 'quantity', 'price']:
                        continue
                    order_payload[k] = v
            
            # 发送订单（符合官方格式：instruction + payload）
            logger.info(f"📤 Backpack 下单 payload: {order_payload}")
            order_resp = self._request(
                "POST",
                "/api/v1/order",
                params={
                    "instruction": "orderExecute",
                    "payload": order_payload
                },
                instruction="orderExecute",
                private=True
            )
            
            # 解析响应
            side_normalized = 'buy' if side_norm == 'buy' else 'sell'

            return {
                'id': order_resp.get('id', order_resp.get('orderId')),
                'clientOrderId': order_resp.get('clientId', order_resp.get('clientOrderId')),
                'status': order_resp.get('status', '').lower(),
                'filled': float(order_resp.get('executedQuantity', 0)),
                'remaining': float(order_resp.get('quantity', 0)) - float(order_resp.get('executedQuantity', 0)),
                'avgPrice': float(order_resp.get('price', 0) or 0),
                'ts': order_resp.get('timestamp', int(time.time() * 1000)),
                'timestamp': order_resp.get('timestamp', int(time.time() * 1000)),  # 与 order_routes 对齐
                'orderTime': order_resp.get('timestamp', int(time.time() * 1000)),  # 前端时间展示
                'side': side_normalized,
                'symbol': symbol,
                'type': order_type
            }
            
        except Exception as e:
            logger.error(f"❌ Backpack 创建订单失败: {e}")
            raise
    
    @staticmethod
    def _format_timestamp(timestamp: Optional[int]) -> str:
        """格式化时间戳"""
        if not timestamp:
            return '-'
        try:
            from datetime import datetime
            return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return '-'
    
    @staticmethod
    def _safe_float(value, default=0):
        """安全转换为 float"""
        if value is None:
            return default
        return float(value)


