"""
测试 /api/create-order API 接口

使用方法：
1. 确保后端服务已启动（python backend/main.py）
2. 运行此测试脚本：python backend/tests/test_create_order_api.py
"""

import requests
import json
import time

# ============================================================================
# 配置
# ============================================================================

# 后端 API 地址
API_BASE_URL = "http://16.163.163.204:8000"

# 币安 API 凭证
BINANCE_API_KEY = "lmREE1RBDnZpbO8V6rWrPGxpeVaGkOJ41ZridRsegvgkx9zSQoGRuNeCR4iwaJa3"
BINANCE_API_SECRET = "mhwpXb5L3HfqcFpFPy3oB5DrN4vlg0osrWdRh1ci2ecW5WjMdGz485TIOxFka39a"

# 测试参数
TEST_SYMBOL = "BTC/USDT"
TEST_AMOUNT = 0.001  # 0.001 BTC


# ============================================================================
# 辅助函数
# ============================================================================

def print_section(title):
    """打印分隔线"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def get_current_price():
    """获取当前价格"""
    try:
        # 使用 /api/prices 接口获取价格
        response = requests.post(f"{API_BASE_URL}/api/prices", json={
            "symbols": [
                {
                    "exchange": "binance",
                    "symbol": TEST_SYMBOL
                }
            ]
        }, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # 返回格式: {"BTC/USDT": {"binance": 67890.12}}
            if data and TEST_SYMBOL in data:
                prices = data[TEST_SYMBOL]
                if "binance" in prices:
                    return prices["binance"]
            print(f"⚠️ 未找到价格数据")
            return None
        else:
            print(f"⚠️ 获取价格失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"⚠️ 获取价格异常: {e}")
        return None


def create_order(symbol, side, order_type, amount, price=None):
    """创建订单"""
    payload = {
        "exchange": "binance",
        "marketType": "spot",
        "symbol": symbol,
        "type": order_type,
        "side": side,
        "amount": amount,
        "credentials": {
            "exchange": "binance",
            "apiKey": BINANCE_API_KEY,
            "apiSecret": BINANCE_API_SECRET
        }
    }
    
    if price is not None:
        payload["price"] = price
    
    print(f"\n📤 发送请求:")
    print(f"   URL: {API_BASE_URL}/api/create-order")
    print(f"   交易对: {symbol}")
    print(f"   方向: {side}")
    print(f"   类型: {order_type}")
    print(f"   数量: {amount}")
    if price:
        print(f"   价格: {price}")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/create-order",
            json=payload,
            timeout=30
        )
        
        print(f"\n📥 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功!")
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ 失败!")
            print(f"响应内容: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时")
        return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None


def query_order(order_id):
    """查询订单"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/query-order",
            params={
                "exchange": "binance",
                "marketType": "spot",
                "symbol": TEST_SYMBOL,
                "orderId": order_id
            },
            headers={
                "X-API-Key": BINANCE_API_KEY,
                "X-API-Secret": BINANCE_API_SECRET
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 查询成功!")
            print(f"\n订单信息:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ 查询失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 查询异常: {e}")
        return None


def cancel_order(order_id):
    """取消订单"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/cancel-order",
            json={
                "exchange": "binance",
                "marketType": "spot",
                "symbol": TEST_SYMBOL,
                "orderId": order_id,
                "credentials": {
                    "exchange": "binance",
                    "apiKey": BINANCE_API_KEY,
                    "apiSecret": BINANCE_API_SECRET
                }
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 取消成功!")
            print(f"\n响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        else:
            print(f"❌ 取消失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 取消异常: {e}")
        return None


# ============================================================================
# 测试流程
# ============================================================================

def main():
    """主测试流程"""
    print("\n" + "🚀"*40)
    print("测试 /api/create-order API 接口")
    print("🚀"*40)
    
    # ========================================================================
    # 步骤 1: 检查后端服务
    # ========================================================================
    
    print_section("📡 步骤 1: 检查后端服务")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ 后端服务正常运行")
        else:
            print(f"⚠️ 后端服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到后端服务: {e}")
        print(f"\n请确保后端服务已启动:")
        print(f"   python backend/main.py")
        return
    
    # ========================================================================
    # 步骤 2: 获取当前价格
    # ========================================================================
    
    print_section("📈 步骤 2: 获取当前价格")
    
    current_price = get_current_price()
    
    if current_price:
        print(f"✅ {TEST_SYMBOL} 当前价格: {current_price} USDT")
        
        # 计算测试价格（当前价格的 50%，确保不会成交）
        test_price = round(current_price * 0.5, 2)
        print(f"📝 测试价格: {test_price} USDT (当前价格的 50%，不会成交)")
    else:
        print(f"⚠️ 无法获取价格，使用固定价格")
        test_price = 30000.0  # 固定价格
    
    # ========================================================================
    # 步骤 3: 创建限价买单
    # ========================================================================
    
    print_section("📝 步骤 3: 创建限价买单")
    
    print(f"\n⚠️ 即将创建订单:")
    print(f"   交易对: {TEST_SYMBOL}")
    print(f"   方向: 买入 (buy)")
    print(f"   类型: 限价单 (limit)")
    print(f"   价格: {test_price} USDT")
    print(f"   数量: {TEST_AMOUNT} BTC")
    print(f"\n   注意: 此订单价格很低，不会立即成交")
    
    confirm = input("\n是否继续? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 已取消")
        return
    
    # 创建订单
    order_result = create_order(
        symbol=TEST_SYMBOL,
        side='buy',
        order_type='limit',
        amount=TEST_AMOUNT,
        price=test_price
    )
    
    if not order_result or not order_result.get('success'):
        print("\n❌ 订单创建失败，测试终止")
        return
    
    # 获取订单 ID
    order_data = order_result.get('data', {})
    order_id = order_data.get('id')
    
    if not order_id:
        print("\n⚠️ 未获取到订单 ID")
        return
    
    print(f"\n✅ 订单 ID: {order_id}")
    
    # ========================================================================
    # 步骤 4: 查询订单
    # ========================================================================
    
    print_section(f"🔍 步骤 4: 查询订单 (ID: {order_id})")
    
    time.sleep(2)  # 等待 2 秒
    
    query_order(order_id)
    
    # ========================================================================
    # 步骤 5: 取消订单
    # ========================================================================
    
    print_section(f"❌ 步骤 5: 取消订单 (ID: {order_id})")
    
    confirm = input("\n是否取消订单? (y/n): ").strip().lower()
    if confirm == 'y':
        cancel_order(order_id)
    else:
        print(f"⚠️ 订单未取消，请手动取消 (ID: {order_id})")
    
    # ========================================================================
    # 完成
    # ========================================================================
    
    print_section("🎉 测试完成")
    print("所有步骤执行成功!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

