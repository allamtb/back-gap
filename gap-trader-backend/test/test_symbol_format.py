#!/usr/bin/env python3
"""
测试各交易所在现货和合约市场中对币种的识别差异

这个脚本会测试：
1. 各交易所的符号格式（Symbol Format）
2. 现货和合约的符号是否统一
3. 如何正确使用符号来获取数据
"""

import ccxt
import json
import os



# 代理配置（可以从环境变量读取，或使用默认值）
PROXY_CONFIG = {
    'http': os.getenv('PROXY_URL', 'http://127.0.0.1:1080'),
    'https': os.getenv('PROXY_URL', 'http://127.0.0.1:1080'),
}

# 是否启用代理（设置为 False 可以禁用代理）
USE_PROXY = False  # 改为 True 可以启用代理


def test_exchange_symbol_format(exchange_id: str, test_symbol_base: str = 'BTC/USDT', verbose: bool = False):
    """
    测试单个交易所的符号格式
    
    Args:
        exchange_id: 交易所ID
        test_symbol_base: 基础测试符号（现货格式）
        verbose: 是否显示详细输出
    """
    if verbose:
        print(f"\n{'=' * 80}")
        print(f"测试交易所: {exchange_id.upper()}")
        print(f"{'=' * 80}")
    
    results = {
        'exchange': exchange_id,
        'spot': {},
        'futures': {},
        'perpetual_swap': {},
        'unified': False,
        'notes': []
    }
    
    try:
        # ========== 1. 测试现货市场 ==========
        if verbose:
            print("\n[1] 现货市场 (Spot Market)")
            print("-" * 80)
        
        # 构建配置
        config = {
            'enableRateLimit': True,
            'timeout': 30000,  # 30秒超时
            'options': {
                'defaultType': 'spot'
            }
        }
        
        # 添加代理配置
        if USE_PROXY:
            config['proxies'] = PROXY_CONFIG
            if verbose:
                print(f"  使用代理: {PROXY_CONFIG.get('http', 'N/A')}")
        
        spot_exchange = getattr(ccxt, exchange_id)(config)
        
        # 加载现货市场
        spot_markets = spot_exchange.load_markets()
        
        # 查找BTC相关的现货交易对
        btc_spot_symbols = [s for s in spot_markets.keys() if 'BTC' in s and 'USDT' in s][:5]
        
        if verbose:
            print(f"找到的BTC现货交易对示例 ({len(btc_spot_symbols)}):")
        
        for symbol in btc_spot_symbols:
            market = spot_markets[symbol]
            if verbose:
                print(f"  - 符号: {symbol}")
                print(f"    ID: {market.get('id', 'N/A')}")
                print(f"    Base: {market.get('base', 'N/A')}, Quote: {market.get('quote', 'N/A')}")
                print(f"    Type: {market.get('type', 'N/A')}")
                print(f"    Spot: {market.get('spot', 'N/A')}")
                print(f"    Linear: {market.get('linear', 'N/A')}")
                print(f"    Settle: {market.get('settle', 'N/A')}")
                print()
            
            # 保存第一个符号作为示例
            if not results['spot']:
                results['spot'] = {
                    'symbol': symbol,
                    'id': market.get('id', 'N/A'),
                    'base': market.get('base', 'N/A'),
                    'quote': market.get('quote', 'N/A'),
                    'type': market.get('type', 'N/A')
                }
        
        # ========== 2. 测试合约市场 ==========
        if verbose:
            print("\n[2] 合约市场 (Futures/Perpetual Swap)")
            print("-" * 80)
        
        # 不同交易所可能使用不同的类型
        for market_type in ['future', 'swap', 'delivery', 'linear', 'inverse']:
            try:
                # 构建配置
                futures_config = {
                    'enableRateLimit': True,
                    'timeout': 30000,
                    'options': {
                        'defaultType': market_type
                    }
                }
                
                # 添加代理配置
                if USE_PROXY:
                    futures_config['proxies'] = PROXY_CONFIG
                
                futures_exchange = getattr(ccxt, exchange_id)(futures_config)
                
                futures_markets = futures_exchange.load_markets()
                btc_futures_symbols = [s for s in futures_markets.keys() if 'BTC' in s and ('USDT' in s or 'USD' in s)][:3]
                
                if btc_futures_symbols:
                    if verbose:
                        print(f"\n  市场类型: {market_type.upper()}")
                        print(f"  找到的BTC合约交易对示例 ({len(btc_futures_symbols)}):")
                    
                    for symbol in btc_futures_symbols:
                        market = futures_markets[symbol]
                        if verbose:
                            print(f"    - 符号: {symbol}")
                            print(f"      ID: {market.get('id', 'N/A')}")
                            print(f"      Base: {market.get('base', 'N/A')}, Quote: {market.get('quote', 'N/A')}")
                            print(f"      Type: {market.get('type', 'N/A')}")
                            print(f"      Swap: {market.get('swap', 'N/A')}")
                            print(f"      Future: {market.get('future', 'N/A')}")
                            print(f"      Linear: {market.get('linear', 'N/A')}")
                            print(f"      Settle: {market.get('settle', 'N/A')}")
                            print()
                        
                        # 保存示例
                        if market_type not in results:
                            results[market_type] = {}
                        if not results[market_type]:
                            results[market_type] = {
                                'symbol': symbol,
                                'id': market.get('id', 'N/A'),
                                'base': market.get('base', 'N/A'),
                                'quote': market.get('quote', 'N/A'),
                                'type': market.get('type', 'N/A')
                            }
                        
            except Exception as e:
                if verbose:
                    print(f"  市场类型 {market_type} 不支持或出错: {str(e)[:100]}")
                continue
        
        # ========== 3. 分析符号格式统一性 ==========
        if verbose:
            print("\n[3] 符号格式分析")
            print("-" * 80)
        
        spot_symbol = results['spot'].get('symbol', '')
        futures_symbols = []
        
        for mtype in ['future', 'swap', 'delivery', 'linear', 'inverse']:
            if mtype in results and results[mtype]:
                futures_symbols.append(results[mtype].get('symbol', ''))
        
        if verbose:
            print(f"现货符号格式: {spot_symbol}")
            print(f"合约符号格式: {', '.join(futures_symbols) if futures_symbols else '无'}")
        
        # 判断是否统一
        if spot_symbol and futures_symbols:
            # 检查格式是否相似
            if spot_symbol in futures_symbols:
                results['unified'] = True
                results['notes'].append("✅ 现货和合约使用相同的符号格式")
            elif any(':' in fs for fs in futures_symbols):
                results['unified'] = False
                results['notes'].append("❌ 合约使用特殊符号格式（带冒号）")
            else:
                results['unified'] = False
                results['notes'].append("❌ 现货和合约符号格式不同")
        
        if verbose:
            print(f"\n符号格式是否统一: {'✅ 是' if results['unified'] else '❌ 否'}")
            for note in results['notes']:
                print(f"  {note}")
        
    except Exception as e:
        if verbose:
            print(f"❌ 测试失败: {str(e)}")
        results['error'] = str(e)
    
    return results


def main():
    """主测试函数"""
    print("=" * 80)
    print("CCXT 交易所符号格式统一性测试")
    print("=" * 80)
    print("\n目的：验证各交易所在现货和合约市场中，对同一币种的符号识别是否统一")
    
    # 显示代理配置信息
    if USE_PROXY:
        print(f"\n🌐 代理配置:")
        print(f"   - HTTP: {PROXY_CONFIG.get('http', 'N/A')}")
        print(f"   - HTTPS: {PROXY_CONFIG.get('https', 'N/A')}")
        print(f"   - 状态: ✅ 已启用")
    else:
        print(f"\n🌐 代理配置: ❌ 未启用")
    
    print(f"\n💡 提示: 可以通过设置环境变量来配置代理：")
    print(f"   - PROXY_URL=http://127.0.0.1:1080")
    print(f"   - USE_PROXY=true/false")
    
    # 从 ccxt 获取所有支持的交易所列表
    all_exchanges = ccxt.exchanges
    print(f"\n✅ CCXT 支持的交易所总数: {len(all_exchanges)}")
    
    # 优先测试主流交易所（放在前面）
    priority_exchanges = [
        'binance', 'okx', 'bybit', 'gate', 'huobi', 'kucoin',
        'coinbase', 'kraken', 'bitfinex', 'cryptocom'
    ]
    
    # 构建测试列表：优先交易所 + 其他交易所
    test_exchanges = []
    for ex in priority_exchanges:
        if ex in all_exchanges:
            test_exchanges.append(ex)
    
    for ex in all_exchanges:
        if ex not in test_exchanges:
            test_exchanges.append(ex)
    
    print(f"✅ 将测试 {len(test_exchanges)} 个交易所")
    print(f"   - 优先测试: {', '.join(priority_exchanges[:6])}")
    print(f"   - 其他交易所: {len(test_exchanges) - len([e for e in priority_exchanges if e in all_exchanges])} 个")
    
    user_input = input("\n是否继续测试所有交易所？(y/n，直接回车默认只测试前10个): ").strip().lower()
    
    if user_input == 'n':
        print("测试已取消")
        return
    elif user_input != 'y':
        # 默认只测试前10个
        test_exchanges = test_exchanges[:10]
        print(f"\n✅ 将只测试前 {len(test_exchanges)} 个交易所: {', '.join(test_exchanges)}")
    
    all_results = {}
    total = len(test_exchanges)
    
    print(f"\n{'=' * 80}")
    print("开始测试...")
    print(f"{'=' * 80}\n")
    
    # 默认不显示详细输出（测试所有交易所时）
    verbose_mode = len(test_exchanges) <= 10
    
    for index, exchange_id in enumerate(test_exchanges, 1):
        try:
            print(f"\n进度: [{index}/{total}] 正在测试 {exchange_id}...")
            result = test_exchange_symbol_format(exchange_id, verbose=verbose_mode)
            all_results[exchange_id] = result
            
            # 简要显示结果
            if 'error' not in result:
                unified = '✅' if result.get('unified', False) else '❌'
                spot_sym = result.get('spot', {}).get('symbol', 'N/A')
                futures_sym = 'N/A'
                for mtype in ['swap', 'future', 'linear']:
                    if mtype in result and result[mtype]:
                        futures_sym = result[mtype].get('symbol', 'N/A')
                        break
                print(f"  结果: {unified} | 现货: {spot_sym} | 合约: {futures_sym}")
            
        except KeyboardInterrupt:
            print(f"\n\n⚠️  用户中断测试")
            print(f"已完成 {index-1}/{total} 个交易所的测试")
            break
        except Exception as e:
            print(f"  ❌ 测试失败: {str(e)[:100]}")
            all_results[exchange_id] = {'error': str(e)}
    
    # ========== 汇总结果 ==========
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    print("\n交易所符号格式对比表：")
    print("-" * 80)
    print(f"{'交易所':<12} {'现货格式':<25} {'合约格式':<25} {'是否统一':<10}")
    print("-" * 80)
    
    for exchange_id, result in all_results.items():
        if 'error' in result:
            print(f"{exchange_id:<12} {'错误':<25} {'错误':<25} {'N/A':<10}")
            continue
        
        spot_symbol = result.get('spot', {}).get('symbol', 'N/A')
        
        # 获取第一个可用的合约符号
        futures_symbol = 'N/A'
        for mtype in ['future', 'swap', 'delivery', 'linear', 'inverse']:
            if mtype in result and result[mtype]:
                futures_symbol = result[mtype].get('symbol', 'N/A')
                break
        
        unified = '✅ 是' if result.get('unified', False) else '❌ 否'
        
        print(f"{exchange_id:<12} {spot_symbol:<25} {futures_symbol:<25} {unified:<10}")
    
    # ========== 关键发现 ==========
    print("\n" + "=" * 80)
    print("关键发现")
    print("=" * 80)
    
    successful_tests = [r for r in all_results.values() if 'error' not in r]
    failed_tests = [r for r in all_results.values() if 'error' in r]
    unified_count = sum(1 for r in successful_tests if r.get('unified', False))
    total_count = len(successful_tests)
    
    print(f"\n📊 测试统计：")
    print(f"   - 总测试数: {len(all_results)}")
    print(f"   - 成功: {total_count}")
    print(f"   - 失败: {len(failed_tests)}")
    
    print(f"\n1. 符号格式统一性：{unified_count}/{total_count} 个交易所的现货和合约符号格式统一")
    print(f"   - 统一比例: {unified_count/total_count*100:.1f}%" if total_count > 0 else "   - 无数据")
    
    print("\n2. 常见的符号格式模式：")
    print("   - 统一格式：BTC/USDT（现货和合约相同）")
    print("   - 带结算货币：BTC/USDT:USDT（合约特有，冒号后是结算货币）")
    print("   - 无斜杠格式：BTCUSDT（某些交易所的内部ID）")
    print("   - 带日期格式：BTC/USDT-230630（季度合约）")
    
    print("\n3. 使用建议：")
    print("   ✅ 推荐使用 load_markets() 获取准确的符号列表")
    print("   ✅ 使用 exchange.market(symbol) 验证符号是否存在")
    print("   ✅ 根据 market.type 判断市场类型（spot/future/swap）")
    print("   ⚠️  不要假设所有交易所使用相同的符号格式")
    print("   ⚠️  切换市场类型时需要重新加载市场数据")
    
    # 保存详细结果到JSON文件
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'symbol_format_results.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 详细结果已保存到: {output_file}")
    except Exception as e:
        print(f"\n⚠️  无法保存结果文件: {str(e)}")
        print(f"   尝试保存到当前目录...")
        try:
            output_file = 'symbol_format_results.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, ensure_ascii=False)
            print(f"   ✅ 已保存到: {os.path.abspath(output_file)}")
        except Exception as e2:
            print(f"   ❌ 保存失败: {str(e2)}")


if __name__ == "__main__":
    main()

