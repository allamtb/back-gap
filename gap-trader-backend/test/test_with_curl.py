#!/usr/bin/env python3
"""
使用 subprocess 调用 curl 命令测试 api/klines
"""

import subprocess
import json
import sys

def test_with_curl():
    """使用curl命令测试API"""
    
    print("🌐 使用 curl 命令测试 K线API")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "name": "币安 BTC/USDT 1分钟K线",
            "url": "http://localhost:8000/api/klines?exchange=binance&symbol=BTC/USDT&interval=1m&limit=3"
        },
        {
            "name": "Bybit ETH/USDT 15分钟K线", 
            "url": "http://localhost:8000/api/klines?exchange=bybit&symbol=ETH/USDT&interval=15m&limit=2"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 测试 {i}: {test_case['name']}")
        print("-" * 40)
        print(f"🔗 URL: {test_case['url']}")
        
        try:
            # 执行curl命令
            result = subprocess.run([
                "curl", "-s", "-w", 
                "HTTP状态码: %{http_code}\n响应时间: %{time_total}s\n",
                test_case['url']
            ], capture_output=True, text=True, timeout=30)
            
            print("📋 curl 输出:")
            print(result.stdout)
            
            if result.stderr:
                print("⚠️  错误信息:")
                print(result.stderr)
                
            # 尝试解析JSON响应
            try:
                # 提取JSON部分（去掉curl的统计信息）
                lines = result.stdout.strip().split('\n')
                json_lines = []
                for line in lines:
                    if line.startswith('{') or line.startswith('[') or line in json_lines:
                        json_lines.append(line)
                
                if json_lines:
                    json_str = '\n'.join(json_lines)
                    data = json.loads(json_str)
                    
                    if 'data' in data and 'klines' in data['data']:
                        print("✅ JSON解析成功!")
                        print(f"📈 数据条数: {data['data']['count']}")
                        
                        for j, kline in enumerate(data['data']['klines']):
                            print(f"  {j+1}. {kline['time']} - 收盘: {kline['close']} USDT")
                    else:
                        print("⚠️  JSON格式异常")
                        
            except json.JSONDecodeError:
                print("⚠️  无法解析JSON响应")
                
        except subprocess.TimeoutExpired:
            print("❌ 请求超时")
        except FileNotFoundError:
            print("❌ curl命令未找到 - 请安装curl或使用其他测试脚本")
            break
        except Exception as e:
            print(f"❌ 执行错误: {e}")

def test_health_with_curl():
    """使用curl测试健康检查"""
    print("\n🏥 使用 curl 测试健康检查")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            "curl", "-s", "http://localhost:8000/health"
        ], capture_output=True, text=True, timeout=10)
        
        print("📋 健康检查结果:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  错误信息:")
            print(result.stderr)
            
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")

def main():
    """主函数"""
    print("🧪 使用 curl 测试 K线数据API")
    print("=" * 60)
    
    # 测试健康检查
    test_health_with_curl()
    
    # 测试K线API
    test_with_curl()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成!")
    print("=" * 60)
    
    print("\n💡 手动curl命令示例:")
    print("curl \"http://localhost:8000/api/klines?exchange=binance&symbol=BTC/USDT&interval=1m&limit=1\"")
    print("curl \"http://localhost:8000/health\"")
    print("curl \"http://localhost:8000/api/proxy\"")

if __name__ == "__main__":
    main()
