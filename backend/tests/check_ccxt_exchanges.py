#!/usr/bin/env python3
"""
检查 CCXT 支持的交易所列表
"""
import ccxt

print("=" * 60)
print("CCXT 版本信息")
print("=" * 60)
print(f"CCXT 版本: {ccxt.__version__}")

print("\n" + "=" * 60)
print("查找 backpack 相关的交易所")
print("=" * 60)

all_exchanges = ccxt.exchanges
print(f"\n总共支持 {len(all_exchanges)} 个交易所\n")

# 查找包含 backpack 的交易所
backpack_related = [ex for ex in all_exchanges if 'backpack' in ex.lower()]

if backpack_related:
    print("找到以下相关交易所:")
    for ex in backpack_related:
        print(f"  - {ex}")
else:
    print("❌ 没有找到 backpack 交易所")
    print("\n可能的原因:")
    print("  1. CCXT 版本太旧，不支持 backpack")
    print("  2. backpack 交易所名称不同")
    print("  3. backpack 尚未被 CCXT 支持")

print("\n" + "=" * 60)
print("其他常见交易所 (供参考)")
print("=" * 60)
common = ['binance', 'okx', 'bybit', 'bitget', 'gateio', 'huobi', 'kucoin']
available_common = [ex for ex in common if ex in all_exchanges]
print(f"可用: {', '.join(available_common)}")

print("\n提示: 如需升级 CCXT，运行: pip install --upgrade ccxt")

