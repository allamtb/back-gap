# Gate.io 完整交易示例使用说明

## 📦 安装依赖

```bash
pip install ccxt
```

## 🔑 配置 API 凭证

编辑 `gate_complete_example.py`，填入你的 API 凭证：

```python
API_KEY = "你的_API_KEY"
SECRET = "你的_SECRET"
```

## 🎯 使用方法

### 1. 现货交易演示

```python
# 修改 main() 函数中的 choice
choice = "1"  # 现货交易

# 运行
python gate_complete_example.py
```

功能包括：
- ✅ 查询现货账户余额
- ✅ 查询当前价格
- ✅ 查询未成交订单
- ✅ 下单（限价单/市价单）
- ✅ 监控余额和订单变化

### 2. 合约交易演示

```python
# 修改 main() 函数中的 choice
choice = "2"  # 合约交易

# 运行
python gate_complete_example.py
```

功能包括：
- ✅ 查询合约账户余额
- ✅ 查询当前持仓
- ✅ 查询未成交订单
- ✅ 开仓（做多/做空）
- ✅ 平仓（单个/全部）
- ✅ 监控余额、订单和持仓变化

## 💡 代码示例

### 初始化客户端

```python
from gate_complete_example import GateTrading

# 现货交易
client = GateTrading(
    api_key="YOUR_API_KEY",
    secret="YOUR_SECRET",
    market_type='spot',
    proxy=None  # 可选代理
)

# 合约交易
client = GateTrading(
    api_key="YOUR_API_KEY",
    secret="YOUR_SECRET",
    market_type='futures',
    proxy="http://127.0.0.1:1080"  # 可选代理
)
```

### 查询余额

```python
# 查询并打印余额
client.print_balance()

# 或获取原始数据
balance = client.get_balance()
```

### 下单

```python
# 限价买单
order = client.create_limit_order(
    symbol='BTC/USDT',
    side='buy',
    amount=0.001,
    price=40000
)

# 市价卖单
order = client.create_market_order(
    symbol='BTC/USDT',
    side='sell',
    amount=0.001
)
```

### 查询订单

```python
# 查询未成交订单
open_orders = client.get_open_orders('BTC/USDT')
client.print_orders(open_orders)

# 查询历史订单
closed_orders = client.get_closed_orders('BTC/USDT', limit=100)
```

### 查询持仓（合约）

```python
# 查询并打印持仓
client.print_positions()

# 或获取原始数据
positions = client.get_positions()
```

### 平仓（合约）

```python
# 平掉指定持仓
order = client.close_position(
    symbol='BTC/USDT:USDT',
    side='long'  # 或 'short'
)

# 一键平所有仓
orders = client.close_all_positions()
```

### 实时监控

```python
import asyncio

# 监控余额（每5秒更新）
await client.monitor_balance(interval=5)

# 监控订单（每2秒更新）
await client.monitor_orders(symbol='BTC/USDT', interval=2)

# 监控持仓（每3秒更新，仅合约）
await client.monitor_positions(interval=3)

# 同时监控多个
tasks = [
    client.monitor_balance(interval=5),
    client.monitor_orders(symbol='BTC/USDT', interval=2),
    client.monitor_positions(interval=3)
]
await asyncio.gather(*tasks)
```

## 🔒 安全提示

1. ⚠️ **不要将 API 凭证提交到代码仓库**
2. ⚠️ **建议使用子账户或限制权限的 API Key**
3. ⚠️ **下单前请仔细检查参数（价格、数量等）**
4. ⚠️ **示例中的下单代码已注释，使用时需手动取消注释**

## 🌐 代理配置

如果需要使用代理：

```python
client = GateTrading(
    api_key="YOUR_API_KEY",
    secret="YOUR_SECRET",
    market_type='spot',
    proxy="http://127.0.0.1:1080"  # HTTP 代理
)
```

## 📊 交易对格式

### 现货
- 标准格式：`BTC/USDT`
- Gate.io 自动处理

### 合约
- 标准格式：`BTC/USDT:USDT`
- 代码会自动转换

## 🐛 常见问题

### 1. 连接超时
- 检查网络连接
- 尝试配置代理
- 增加超时时间

### 2. 签名错误
- 检查 API Key 和 Secret 是否正确
- 检查时间同步（Gate.io 对时间敏感）

### 3. 权限不足
- 检查 API Key 是否有交易权限
- 合约交易需要开通合约账户

### 4. 余额不足
- 检查账户余额是否充足
- 现货和合约账户是分开的

## 📚 更多资源

- Gate.io API 文档：https://www.gate.io/docs/developers/apiv4/
- CCXT 文档：https://docs.ccxt.com/
- Gate.io 交易规则：https://www.gate.io/help

## 🎓 学习建议

1. 先在**小额资金**下测试
2. 熟悉 API 返回的数据格式
3. 了解交易规则（最小下单量、手续费等）
4. 实施风险管理策略
5. 使用监控功能实时跟踪

## ⚡ 性能优化

1. 使用 `get_open_orders()` 不传 symbol 可一次获取所有订单
2. 合理设置监控间隔，避免请求过于频繁
3. 使用 `fetch_balance()` 时注意频率限制

## 💬 联系支持

如有问题，请查阅：
- Gate.io 官方文档
- CCXT GitHub Issues
- 本项目 README

