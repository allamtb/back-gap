#!/usr/bin/env python3
"""
测试 get_klines API 的代理功能
"""

import requests
import json
import time

def test_klines_with_proxy():
    """测试K线API的代理功能"""
    
    # 测试URL
    url = "http://localhost:8000/api/klines"
    
    # 测试参数
    params = {
        'exchange': 'binance',
        'symbol': 'BTC/USDT',
        'interval': '1m',
        'limit': 1
    }
    
    print("=== 测试 get_klines API 代理功能 ===\n")
    
    try:
        print(f"请求URL: {url}")
        print(f"请求参数: {json.dumps(params, indent=2)}")
        print("\n发送请求...")
        
        # 发送请求
        response = requests.get(url, params=params, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 请求成功!")
            print(f"交易所: {data['data']['exchange']}")
            print(f"交易对: {data['data']['symbol']}")
            print(f"数据条数: {len(data['data']['klines'])}")
            
            if data['data']['klines']:
                kline = data['data']['klines'][0]
                print(f"最新K线数据:")
                print(f"  时间: {kline['time']}")
                print(f"  收盘价: {kline['close']} USDT")
        else:
            print(f"❌ 请求失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

def test_proxy_status():
    """测试代理状态API"""
    
    print("\n=== 测试代理状态 ===\n")
    
    try:
        # 获取代理状态
        response = requests.get("http://localhost:8000/api/proxy", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("当前代理配置:")
            print(f"  HTTP代理: {data.get('http_proxy', '未设置')}")
            print(f"  HTTPS代理: {data.get('https_proxy', '未设置')}")
            print(f"  状态: {data.get('status', 'Unknown')}")
        else:
            print(f"❌ 获取代理状态失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 获取代理状态失败: {e}")

def main():
    print("请确保服务已启动 (python main.py)")
    print("按回车键开始测试...")
    input()
    
    # 测试代理状态
    test_proxy_status()
    
    # 测试K线API
    test_klines_with_proxy()
    
    print("\n=== 测试完成 ===")
    print("\n提示:")
    print("1. 如果看到 '代理: 已启用' 的日志，说明代理正在工作")
    print("2. 如果请求成功，说明代理配置正确")
    print("3. 如果请求失败，请检查代理设置和网络连接")

if __name__ == "__main__":
    main()
