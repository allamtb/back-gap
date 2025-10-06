#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的K线API测试脚本
"""

import requests
import json

def test_klines():
    """测试K线API"""
    
    # API地址和参数
    url = "http://localhost:8000/api/klines"
    params = {
        "exchange": "binance",
        "symbol": "BTC/USDT", 
        "interval": "1m",
        "limit": 3
    }
    
    print("=== K线API测试 ===")
    print(f"URL: {url}")
    print(f"参数: {json.dumps(params, ensure_ascii=False)}")
    print("-" * 40)
    
    try:
        # 发送请求
        response = requests.get(url, params=params, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("请求成功!")
            print(f"数据条数: {data['data']['count']}")
            
            # 显示K线数据
            for i, kline in enumerate(data['data']['klines']):
                print(f"  {i+1}. {kline['time']} - 收盘: {kline['close']} USDT")
                
        else:
            print(f"请求失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("连接失败 - 请确保服务已启动 (python main.py)")
    except Exception as e:
        print(f"错误: {e}")

def test_health():
    """测试健康检查"""
    print("\n=== 健康检查测试 ===")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"服务状态: {data['status']}")
        else:
            print(f"健康检查失败: {response.text}")
            
    except Exception as e:
        print(f"健康检查错误: {e}")

def test_proxy():
    """测试代理状态"""
    print("\n=== 代理状态测试 ===")
    
    try:
        response = requests.get("http://localhost:8000/api/proxy", timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"代理状态: {data.get('status', 'Unknown')}")
            print(f"HTTP代理: {data.get('http_proxy', '未设置')}")
            print(f"HTTPS代理: {data.get('https_proxy', '未设置')}")
        else:
            print(f"获取代理状态失败: {response.text}")
            
    except Exception as e:
        print(f"代理状态检查错误: {e}")

if __name__ == "__main__":
    print("K线数据API测试工具")
    print("=" * 50)
    
    # 测试健康检查
    test_health()
    
    # 测试代理状态
    test_proxy()
    
    # 测试K线API
    test_klines()
    
    print("\n" + "=" * 50)
    print("测试完成!")
