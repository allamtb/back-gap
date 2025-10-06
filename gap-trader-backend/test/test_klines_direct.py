#!/usr/bin/env python3
"""
直接通过 requests 调用 api/klines 的测试程序
"""

import requests
import json
import time
from datetime import datetime

# API基础URL
BASE_URL = "http://localhost:8000"

def test_klines_direct():
    """直接测试K线API"""
    print("🚀 直接测试 K线数据API")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "name": "币安 BTC/USDT 1分钟K线",
            "params": {
                "exchange": "binance",
                "symbol": "BTC/USDT", 
                "interval": "1m",
                "limit": 5
            }
        },
        {
            "name": "Bybit ETH/USDT 15分钟K线",
            "params": {
                "exchange": "bybit",
                "symbol": "ETH/USDT",
                "interval": "15m", 
                "limit": 3
            }
        },
        {
            "name": "OKX BTC/USDT 1小时K线",
            "params": {
                "exchange": "okx",
                "symbol": "BTC/USDT",
                "interval": "1h",
                "limit": 2
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 测试 {i}: {test_case['name']}")
        print("-" * 40)
        
        # 构建请求URL
        url = f"{BASE_URL}/api/klines"
        params = test_case['params']
        
        print(f"🔗 请求URL: {url}")
        print(f"📋 请求参数: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        try:
            # 发送GET请求
            print("⏳ 发送请求...")
            start_time = time.time()
            
            response = requests.get(url, params=params, timeout=30)
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            print(f"⏱️  响应时间: {response_time:.2f}ms")
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 解析JSON响应
                data = response.json()
                
                print("✅ 请求成功!")
                print(f"📈 数据条数: {data['data']['count']}")
                print(f"⏰ 响应时间戳: {data['timestamp']}")
                print(f"🏢 交易所: {data['data']['exchange']}")
                print(f"💱 交易对: {data['data']['symbol']}")
                print(f"📅 周期: {data['data']['interval']}")
                
                # 显示K线数据详情
                if data['data']['klines']:
                    print("\n📋 K线数据详情:")
                    for j, kline in enumerate(data['data']['klines']):
                        print(f"  {j+1}. 时间: {kline['time']}")
                        print(f"     开盘: {kline['open']} USDT")
                        print(f"     最高: {kline['high']} USDT") 
                        print(f"     最低: {kline['low']} USDT")
                        print(f"     收盘: {kline['close']} USDT")
                        print(f"     成交量: {kline['volume']}")
                        print()
                else:
                    print("⚠️  没有返回K线数据")
                    
            else:
                print(f"❌ 请求失败!")
                print(f"错误信息: {response.text}")
                
        except requests.exceptions.Timeout:
            print("❌ 请求超时 (30秒)")
        except requests.exceptions.ConnectionError:
            print("❌ 连接错误 - 请确保服务已启动")
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
            print(f"原始响应: {response.text}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
        
        # 等待1秒避免请求过快
        if i < len(test_cases):
            print("⏳ 等待1秒...")
            time.sleep(1)

def test_single_request():
    """测试单个请求"""
    print("\n🎯 单个请求测试")
    print("=" * 50)
    
    # 单个请求参数
    url = f"{BASE_URL}/api/klines"
    params = {
        "exchange": "binance",
        "symbol": "BTC/USDT",
        "interval": "5m",
        "limit": 1
    }
    
    print(f"🔗 URL: {url}")
    print(f"📋 参数: {json.dumps(params, ensure_ascii=False)}")
    
    try:
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            kline = data['data']['klines'][0]
            
            print("✅ 成功获取最新K线数据:")
            print(f"  时间: {kline['time']}")
            print(f"  收盘价: {kline['close']} USDT")
            print(f"  24h变化: {((float(kline['close']) - float(kline['open'])) / float(kline['open']) * 100):.2f}%")
        else:
            print(f"❌ 失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

def test_error_handling():
    """测试错误处理"""
    print("\n🚫 错误处理测试")
    print("=" * 50)
    
    error_cases = [
        {
            "name": "无效交易所",
            "params": {"exchange": "invalid", "symbol": "BTC/USDT", "interval": "1m"}
        },
        {
            "name": "缺少参数",
            "params": {"exchange": "binance"}
        },
        {
            "name": "无效交易对",
            "params": {"exchange": "binance", "symbol": "INVALID/PAIR", "interval": "1m"}
        }
    ]
    
    for case in error_cases:
        print(f"\n🔍 测试: {case['name']}")
        
        try:
            response = requests.get(f"{BASE_URL}/api/klines", params=case['params'], timeout=10)
            print(f"状态码: {response.status_code}")
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    print(f"错误信息: {error_data.get('detail', '未知错误')}")
                except:
                    print(f"错误信息: {response.text}")
            else:
                print("⚠️  意外成功!")
                
        except Exception as e:
            print(f"异常: {e}")

def check_service_status():
    """检查服务状态"""
    print("🏥 检查服务状态")
    print("=" * 50)
    
    try:
        # 检查健康状态
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ 服务健康: {health_data['status']}")
            print(f"⏰ 服务时间: {health_data['timestamp']}")
        else:
            print(f"❌ 健康检查失败: {health_response.status_code}")
            
        # 检查代理状态
        proxy_response = requests.get(f"{BASE_URL}/api/proxy", timeout=5)
        if proxy_response.status_code == 200:
            proxy_data = proxy_response.json()
            print(f"🌐 代理状态: {proxy_data.get('status', 'Unknown')}")
            if proxy_data.get('http_proxy') or proxy_data.get('https_proxy'):
                print("✅ 代理已启用")
            else:
                print("⚠️  代理未启用")
        else:
            print("❌ 无法获取代理状态")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务 - 请确保服务已启动 (python main.py)")
    except Exception as e:
        print(f"❌ 检查服务状态失败: {e}")

def main():
    """主函数"""
    print("🧪 K线数据API直接测试工具")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 目标服务: {BASE_URL}")
    print("=" * 60)
    
    # 1. 检查服务状态
    check_service_status()
    
    # 2. 单个请求测试
    test_single_request()
    
    # 3. 批量测试
    test_klines_direct()
    
    # 4. 错误处理测试
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
    
    print("\n💡 使用提示:")
    print("1. 确保服务已启动: python main.py")
    print("2. 如需设置代理，请设置环境变量后重启服务")
    print("3. 如果请求失败，请检查网络连接和代理设置")

if __name__ == "__main__":
    main()
