#!/usr/bin/env python3
"""
测试K线数据API端点
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_klines_api():
    """测试K线数据API"""
    print("🚀 开始测试K线数据API...")
    
    # 测试参数
    test_cases = [
        {
            "name": "币安BTC/USDT 15分钟K线",
            "params": {
                "exchange": "binance",
                "symbol": "BTC/USDT",
                "interval": "15m",
                "limit": 10
            }
        },
        {
            "name": "Bybit ETH/USDT 1小时K线",
            "params": {
                "exchange": "bybit",
                "symbol": "ETH/USDT",
                "interval": "1h",
                "limit": 5
            }
        },
        {
            "name": "OKX BTC/USDT 1分钟K线",
            "params": {
                "exchange": "okx",
                "symbol": "BTC/USDT",
                "interval": "1m",
                "limit": 20
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📊 测试: {test_case['name']}")
        print(f"参数: {test_case['params']}")
        
        try:
            # 发送请求
            response = requests.get(
                f"{BASE_URL}/api/klines",
                params=test_case['params'],
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功! 状态码: {response.status_code}")
                print(f"📈 数据条数: {data['data']['count']}")
                print(f"⏰ 时间戳: {data['timestamp']}")
                
                # 显示前3条K线数据
                if data['data']['klines']:
                    print("📋 前3条K线数据:")
                    for i, kline in enumerate(data['data']['klines'][:3]):
                        print(f"  {i+1}. 时间: {kline['time']}, "
                              f"开盘: {kline['open']}, "
                              f"最高: {kline['high']}, "
                              f"最低: {kline['low']}, "
                              f"收盘: {kline['close']}, "
                              f"成交量: {kline['volume']}")
            else:
                print(f"❌ 失败! 状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
        
        # 等待1秒避免请求过快
        time.sleep(1)

def test_error_cases():
    """测试错误情况"""
    print("\n🔍 测试错误情况...")
    
    error_cases = [
        {
            "name": "不支持的交易所",
            "params": {
                "exchange": "invalid_exchange",
                "symbol": "BTC/USDT",
                "interval": "15m"
            }
        },
        {
            "name": "缺少必需参数",
            "params": {
                "exchange": "binance"
                # 缺少symbol参数
            }
        },
        {
            "name": "无效的交易对",
            "params": {
                "exchange": "binance",
                "symbol": "INVALID/PAIR",
                "interval": "15m"
            }
        }
    ]
    
    for test_case in error_cases:
        print(f"\n🚫 测试: {test_case['name']}")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/klines",
                params=test_case['params'],
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            if response.status_code != 200:
                error_data = response.json()
                print(f"错误信息: {error_data.get('detail', '未知错误')}")
            else:
                print("⚠️  意外成功!")
                
        except Exception as e:
            print(f"异常: {e}")

def test_health_check():
    """测试健康检查"""
    print("\n🏥 测试健康检查...")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务健康: {data['status']}")
            print(f"⏰ 时间戳: {data['timestamp']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")

def test_proxy_status():
    """测试代理状态"""
    print("\n🌐 测试代理状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/proxy", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"📡 代理状态: {data.get('status', 'Unknown')}")
            print(f"🔗 HTTP代理: {data.get('http_proxy', '未设置')}")
            print(f"🔒 HTTPS代理: {data.get('https_proxy', '未设置')}")
            
            # 判断代理是否启用
            if data.get('http_proxy') or data.get('https_proxy'):
                print("✅ 代理已启用 - 交易所API请求将通过代理")
            else:
                print("⚠️  代理未启用 - 交易所API请求将直连")
        else:
            print(f"❌ 获取代理状态失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取代理状态异常: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 K线数据API测试工具")
    print("=" * 60)
    
    # 测试健康检查
    test_health_check()
    
    # 测试代理状态
    test_proxy_status()
    
    # 测试正常情况
    test_klines_api()
    
    # 测试错误情况
    test_error_cases()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
