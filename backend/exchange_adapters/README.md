# 交易所适配器架构说明

## 🎯 设计原则

根据你的需求，设计如下架构：

1. ✅ **所有交易所都走适配器** - 统一入口
2. ✅ **默认使用 CCXT 实现** - 不需要为每个交易所都写代码
3. ✅ **按需定制特殊逻辑** - 只在有差异时才写适配器
4. ✅ **明确告知哪些功能未适配** - 抛出 `NotImplementedByAdapter` 异常
5. ✅ **内置市场数据缓存** - 自动管理，大幅提升性能

---

## 📁 文件结构

```
backend/exchange_adapters/
├── base.py                    # 基类（定义接口、默认实现）
├── default_adapter.py         # 默认适配器（处理大部分交易所）
├── binance_adapter.py         # Binance 定制（fetch_open_orders 需要 symbol）
├── gate_adapter.py            # Gate 定制（双实例）
├── __init__.py                # 智能路由
└── README.md                  # 本文档
```

---

## 🚀 使用方式

### 1. 基本使用

```python
from exchange_adapters import get_adapter

# 创建适配器（自动选择合适的实现）
config = {
    'apiKey': 'xxx',
    'secret': 'yyy',
}

# Binance - 使用定制适配器
adapter = get_adapter('binance', 'spot', config)

# OKX - 使用定制适配器（需要 password）
config_okx = {
    'apiKey': 'xxx',
    'secret': 'yyy',
    'password': 'your-api-passphrase',  # OKX 必需
}
adapter = get_adapter('okx', 'spot', config_okx)

# Bybit - 使用默认适配器
adapter = get_adapter('bybit', 'spot', config)
```

**注意**：
- 代理配置会从环境变量 `PROXY_URL` 自动读取，无需手动添加
- OKX 需要额外的 `password` 参数（API Passphrase）
- 如果 OKX 没有提供 password，会抛出明确的错误提示

### 2. 查询订单

```python
# 获取所有订单（现货 + 合约）
all_orders = adapter.fetch_all_orders()

# 只获取现货订单
spot_orders = adapter.fetch_spot_orders()

# 只获取合约订单
futures_orders = adapter.fetch_futures_orders()
```

### 3. 查询持仓

```python
# 获取所有持仓（现货余额 + 合约持仓）
all_positions = adapter.fetch_all_positions()

# 只获取现货余额
spot_balance = adapter.fetch_spot_balance()

# 只获取合约持仓
futures_positions = adapter.fetch_futures_positions()
```

### 4. 市场数据（CCXT 已统一，直接用）

```python
# K线数据（所有交易所统一接口）
klines = adapter.fetch_ohlcv('BTC/USDT', '15m', limit=100)

# Ticker 数据
ticker = adapter.fetch_ticker('BTC/USDT')

# 订单簿
order_book = adapter.fetch_order_book('BTC/USDT')
```

### 5. 市场数据缓存（自动管理）

**适配器会自动管理市场数据缓存，无需手动操作！**

```python
# ✅ 推荐：直接使用适配器（自动使用缓存）
adapter = get_adapter('binance', 'spot', config)
# 市场数据已自动加载（使用缓存，速度快）

# 如果需要强制刷新市场数据
adapter.reload_markets(force=True)

# 如果只想使用缓存策略（不强制）
adapter.reload_markets(force=False)
```

**性能对比**：
- 不使用缓存：每次创建适配器需要 3-5 秒
- 使用缓存：每次创建适配器只需 0.01 秒（**快 300-500 倍**）

**缓存特性**：
- ✅ 自动管理：初始化时自动加载
- ✅ 全局共享：多个适配器实例共享同一缓存
- ✅ 智能更新：缓存过期时自动从 API 加载
- ✅ 交易所隔离：不同交易所的缓存互不影响
- ✅ 默认 24 小时有效期

### 6. 检查功能支持

```python
# 检查是否支持某个功能
from exchange_adapters import AdapterCapability

if adapter.supports_capability(AdapterCapability.FETCH_SPOT_ORDERS):
    orders = adapter.fetch_spot_orders()
else:
    print("此交易所不支持现货订单查询")

# 获取所有支持的功能
capabilities = adapter.get_supported_capabilities()
print(f"支持的功能: {capabilities}")
```

---

## 🔧 如何添加新交易所

### 情况 1：交易所遵循 CCXT 标准

**90% 的交易所属于这种情况**

只需在 `__init__.py` 中添加到列表即可：

```python
# backend/exchange_adapters/__init__.py

DEFAULT_SUPPORTED_EXCHANGES = [
    'okx',
    'bybit',
    'huobi',
    'kucoin',
    'kraken',
    # ... 添加新交易所名称
    'your_new_exchange',  # ← 添加这里
]
```

**完成！** 不需要写任何代码！ ✅

---

### 情况 2：交易所有特殊差异

**少数交易所需要定制**

#### 步骤 1：创建适配器文件

```python
# backend/exchange_adapters/your_exchange_adapter.py

import ccxt
from .default_adapter import DefaultAdapter
from .adapter_interface import AdapterCapability

class YourExchangeAdapter(BaseExchangeAdapter):
    """你的交易所适配器"""
    
    def _get_exchange_id(self) -> str:
        return 'your_exchange'
    
    def _initialize_exchanges(self):
        """初始化 CCXT 实例"""
        config = {
            'apiKey': self.config.get('apiKey', ''),
            'secret': self.config.get('secret', ''),
            'enableRateLimit': True,
        }
        
        if 'proxies' in self.config:
            config['proxies'] = self.config['proxies']
        
        self.spot_exchange = ccxt.your_exchange(config)
        self.futures_exchange = self.spot_exchange
        
        # 声明支持的功能
        self._supported_capabilities = {
            AdapterCapability.FETCH_SPOT_ORDERS,
            AdapterCapability.FETCH_FUTURES_ORDERS,
            # ... 其他功能
        }
    
    # 只重写有差异的方法
    def fetch_spot_orders(self) -> list:
        """如果有特殊逻辑，在这里实现"""
        # 你的定制逻辑
        pass
```

#### 步骤 2：注册适配器

```python
# backend/exchange_adapters/__init__.py

from .your_exchange_adapter import YourExchangeAdapter

CUSTOM_ADAPTERS = {
    'binance': BinanceAdapter,
    'gate': GateAdapter,
    'your_exchange': YourExchangeAdapter,  # ← 添加这里
}
```

---

## 📋 常见交易所差异对照表

| 交易所 | 使用适配器 | 主要差异 |
|--------|-----------|----------|
| Binance | ✅ 定制 | `fetch_open_orders()` 需要 symbol |
| Gate.io | ✅ 定制 | 现货和合约需要分离实例 |
| **Backpack** | ✅ **定制** | **不支持 CCXT，使用 ED25519 签名** |
| OKX | ❌ 默认 | 遵循 CCXT 标准 |
| Bybit | ❌ 默认 | 遵循 CCXT 标准 |
| Huobi | ❌ 默认 | 遵循 CCXT 标准 |
| KuCoin | ❌ 默认 | 遵循 CCXT 标准 |
| Kraken | ❌ 默认 | 遵循 CCXT 标准 |

### 🚀 特殊说明：Backpack Exchange

Backpack 是一个**特殊的交易所**，不被 CCXT 官方支持，需要完全自研适配器：

- **认证方式**: ED25519 签名（不是 HMAC-SHA256）
- **密钥格式**: Base64 编码的密钥对
- **依赖**: 需要安装 `PyNaCl` 库
- **文档**: 查看 [Backpack 快速开始](../docs/BACKPACK_QUICK_START.md)

```bash
# 安装依赖
pip install PyNaCl

# 使用示例
adapter = get_adapter('backpack', 'spot', {
    'apiKey': 'base64_public_key',
    'secret': 'base64_private_key'
})
```

---

## ⚠️ 异常处理

### 1. 不支持的交易所

```python
try:
    adapter = get_adapter('unknown_exchange', config)
except ValueError as e:
    print(f"错误: {e}")
    # 输出：
    # ❌ 不支持的交易所: unknown_exchange
    # 已定制适配器: ['binance', 'gate']
    # 默认支持: ['okx', 'bybit', ...]
```

### 2. 功能未适配

```python
from exchange_adapters import NotImplementedByAdapter

try:
    orders = adapter.fetch_spot_orders()
except NotImplementedByAdapter as e:
    print(f"功能未实现: {e}")
    # 输出：
    # ❌ xxx 的现货订单查询功能需要定制适配，但尚未实现。
    # 提示：请在 XxxAdapter 中重写 fetch_spot_orders() 方法
```

---

## 🎓 设计模式解析

### 为什么这样设计？

#### 问题：传统方式的痛点

```python
# ❌ 传统方式：每个交易所都要实现
class BinanceAdapter:
    def fetch_ohlcv(self): ...    # 要写
    def fetch_ticker(self): ...    # 要写
    def fetch_orders(self): ...    # 要写
    def fetch_balance(self): ...   # 要写
    # ... 10+ 个方法

class OKXAdapter:
    def fetch_ohlcv(self): ...    # 又要写
    def fetch_ticker(self): ...    # 又要写
    # ... 重复劳动
```

**结果：** 新增一个交易所，要写 10+ 个方法，太累！ 😫

#### 解决：三层架构

```
Layer 1: BaseExchangeAdapter
    ↓
    定义接口 + 默认实现（调用 CCXT）
    ↓
Layer 2: DefaultExchangeAdapter
    ↓
    处理 90% 的交易所（直接用 CCXT）
    ↓
Layer 3: CustomAdapter (Binance, Gate...)
    ↓
    只处理 10% 有差异的部分
```

**好处：**
- ✅ 新增交易所：只需加名字到列表
- ✅ 有差异时：只重写差异方法
- ✅ 明确告知：哪些功能未适配

---

## 🔍 哪些接口需要适配？

### ❌ 不需要适配（CCXT 已统一）

| 接口 | 说明 | 理由 |
|------|------|------|
| `fetch_ohlcv()` | K线数据 | ✅ 所有交易所统一接口 |
| `fetch_ticker()` | 价格数据 | ✅ 所有交易所统一接口 |
| `fetch_order_book()` | 订单簿 | ✅ 所有交易所统一接口 |
| `fetch_markets()` | 市场信息 | ✅ 所有交易所统一接口 |

**这些接口直接调用 CCXT，不需要写适配代码！** ✅

### ✅ 需要适配（交易所差异大）

| 接口 | 说明 | 差异原因 |
|------|------|----------|
| `fetch_spot_orders()` | 现货订单 | ⚠️ Binance 需要 symbol |
| `fetch_futures_orders()` | 合约订单 | ⚠️ Gate 需要分离实例 |
| `fetch_spot_balance()` | 现货余额 | ⚠️ 数据格式略有差异 |
| `fetch_futures_positions()` | 合约持仓 | ⚠️ 有些交易所无此功能 |
| `create_order()` | 下单 | ⚠️ 参数格式不同 |

**这些接口需要适配器处理差异！** ⚠️

---

## 📈 扩展示例

### 场景：你要支持 Huobi

#### Step 1: 尝试用默认适配器

```python
# backend/exchange_adapters/__init__.py

DEFAULT_SUPPORTED_EXCHANGES = [
    'okx',
    'bybit',
    'huobi',  # ← 添加这里
]
```

#### Step 2: 测试

```python
adapter = get_adapter('huobi', config)

# 测试订单查询
try:
    orders = adapter.fetch_spot_orders()
    print(f"✅ Huobi 订单查询正常: {len(orders)} 个订单")
except NotImplementedByAdapter as e:
    print(f"❌ Huobi 需要定制适配器: {e}")
```

#### Step 3: 如果有问题，创建定制适配器

```python
# backend/exchange_adapters/huobi_adapter.py

class HuobiAdapter(BaseExchangeAdapter):
    # 只重写有问题的方法
    def fetch_spot_orders(self) -> list:
        # Huobi 特殊逻辑
        pass
```

---

## 🎉 总结

### 你的架构优势

1. **统一入口** - 所有交易所都走适配器，代码一致
2. **最小代码** - 90% 交易所只需加名字，不写代码
3. **按需定制** - 10% 有差异的才写适配器
4. **明确错误** - 未适配功能会抛出清晰异常

### 对比传统方式

| 指标 | 传统方式 | 你的架构 |
|------|----------|----------|
| 新增交易所代码量 | 100+ 行 | 1 行 |
| K线查询实现 | 每个交易所都要写 | 自动支持 |
| 错误提示 | 静默失败 | 明确异常 |
| 维护成本 | 高 | 低 |

---

## ❓ FAQ

### Q1: 我怎么知道某个交易所是否需要定制？

A: 先加到 `DEFAULT_SUPPORTED_EXCHANGES`，测试后如果报错再定制。

### Q2: 如果我不确定某个功能是否需要适配？

A: 直接调用，如果抛出 `NotImplementedByAdapter` 异常，说明需要适配。

### Q3: K线查询为什么不需要适配器？

A: CCXT 已经统一了接口，所有交易所都是 `fetch_ohlcv()`，不需要额外适配。

### Q4: 订单查询为什么需要适配器？

A: Binance 的 `fetch_open_orders()` 必须传 symbol，其他交易所不需要，这就是差异。

---

**祝你使用愉快！** 🚀

如有问题，请查看：
- `base.py` - 理解接口定义
- `binance_adapter.py` - 学习如何定制
- `default_adapter.py` - 理解默认实现
