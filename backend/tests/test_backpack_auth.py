"""
测试 Backpack 适配器的认证和 API 调用

使用 ED25519 签名（cryptography 库）
根据官方文档：https://support.backpack.exchange/exchange/api-and-developer-docs/backpack-exchange-python-api-guide
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import time
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519

# 测试用的 API 密钥（请替换为真实密钥）
API_KEY = "5+yQgwU0ZdJ/9s+GXfuPFfo7yQQpl9CgvQedJXne30o="  # Base64 编码的公钥
SECRET_KEY = "TDSkv44jf/iD/QCKkyCdixO+p1sfLXxk+PZH7mW/ams="  # Base64 编码的私钥

def test_ed25519_signature():
    """测试 ED25519 签名功能"""
    print("=" * 60)
    print("测试 ED25519 签名")
    print("=" * 60)
    
    try:
        # 1. 加载私钥
        secret_bytes = base64.b64decode(SECRET_KEY)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
        print("✅ ED25519 私钥加载成功")
        
        # 2. 构建签名字符串
        timestamp = int(time.time() * 1000)
        window = 5000
        instruction = "balanceQuery"
        
        sign_str = f"instruction={instruction}&timestamp={timestamp}&window={window}"
        print(f"📝 签名字符串: {sign_str}")
        
        # 3. 签名
        signature_bytes = private_key.sign(sign_str.encode('utf-8'))
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        print(f"🔐 签名结果 (Base64): {signature_b64[:50]}...")
        
        # 4. 构建请求头
        headers = {
            "X-API-Key": API_KEY,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8",
        }
        print(f"📤 请求头: {headers}")
        
        print("\n✅ ED25519 签名测试通过！")
        return headers
        
    except Exception as e:
        print(f"❌ 签名测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_backpack_balance():
    """测试获取余额 API"""
    print("\n" + "=" * 60)
    print("测试 Backpack 获取余额 API")
    print("=" * 60)
    
    import requests
    
    try:
        # 1. 生成签名
        timestamp = int(time.time() * 1000)
        window = 5000
        instruction = "balanceQuery"
        
        sign_str = f"instruction={instruction}&timestamp={timestamp}&window={window}"
        
        # 2. ED25519 签名
        secret_bytes = base64.b64decode(SECRET_KEY)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
        signature_bytes = private_key.sign(sign_str.encode('utf-8'))
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        # 3. 构建请求
        url = "https://api.backpack.exchange/api/v1/capital"
        headers = {
            "X-API-Key": API_KEY,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8",
        }
        
        print(f"📤 请求 URL: {url}")
        print(f"📤 请求头: X-API-Key={API_KEY[:20]}...")
        print(f"📤 签名字符串: {sign_str}")
        
        # 4. 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取余额成功！")
            print(f"📊 账户余额:")
            
            # 处理不同的响应格式
            if isinstance(data, dict):
                for asset, balance in data.items():
                    available = balance.get("available", 0)
                    locked = balance.get("locked", 0)
                    staked = balance.get("staked", 0)
                    print(f"  {asset}: 可用={available}, 冻结={locked}, 质押={staked}")
            elif isinstance(data, list):
                for item in data:
                    asset = item.get('asset', item.get('currency', ''))
                    available = item.get("available", 0)
                    locked = item.get("locked", 0)
                    print(f"  {asset}: 可用={available}, 冻结={locked}")
            else:
                print(f"  响应数据: {data}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_backpack_positions():
    """测试获取持仓 API (期货/合约)"""
    print("\n" + "=" * 60)
    print("测试 Backpack 获取持仓 API (GET /api/v1/open)")
    print("=" * 60)
    
    import requests
    
    try:
        # 1. 生成签名
        timestamp = int(time.time() * 1000)
        window = 5000
        instruction = "positionQuery"
        
        sign_str = f"instruction={instruction}&timestamp={timestamp}&window={window}"
        
        # 2. ED25519 签名
        secret_bytes = base64.b64decode(SECRET_KEY)
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(secret_bytes)
        signature_bytes = private_key.sign(sign_str.encode('utf-8'))
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        
        # 3. 构建请求
        url = "https://api.backpack.exchange/api/v1/open"
        headers = {
            "X-API-Key": API_KEY,
            "X-Signature": signature_b64,
            "X-Timestamp": str(timestamp),
            "X-Window": str(window),
            "Content-Type": "application/json; charset=utf-8",
        }
        
        print(f"📤 请求 URL: {url}")
        print(f"📤 签名字符串: {sign_str}")
        
        # 4. 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📥 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取持仓成功！")
            print(f"📊 持仓数据: {data}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def test_backpack_adapter():
    """测试完整的 Backpack 适配器"""
    print("\n" + "=" * 60)
    print("测试 Backpack 适配器类")
    print("=" * 60)
    
    try:
        from exchange_adapters.backpack_adapter import BackpackAdapter
        
        # 配置
        config = {
            'apiKey': API_KEY,
            'secret': SECRET_KEY,
            'timeout': 10000
        }
        
        # 创建适配器（现货）
        print("\n📊 测试现货适配器...")
        spot_adapter = BackpackAdapter('spot', config)
        print("✅ 现货适配器创建成功")
        
        # 测试连通性
        print("\n🔗 测试连通性...")
        connectivity = spot_adapter.test_connectivity()
        print(f"连通性测试结果: {connectivity}")
        
        # 测试获取余额
        print("\n💰 测试获取余额...")
        positions = spot_adapter.fetch_positions()
        print(f"获取到 {len(positions)} 个余额项")
        for pos in positions[:5]:  # 只显示前5个
            print(f"  {pos}")
        
        # 创建适配器（合约）
        print("\n📊 测试合约适配器...")
        futures_adapter = BackpackAdapter('futures', config)
        print("✅ 合约适配器创建成功")
        
        # 测试获取持仓
        print("\n📈 测试获取持仓...")
        positions = futures_adapter.fetch_positions()
        print(f"获取到 {len(positions)} 个持仓项")
        for pos in positions:
            print(f"  {pos}")
        
        print("\n✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 适配器测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Backpack 适配器认证测试")
    print("使用 ED25519 签名（cryptography 库）")
    print("=" * 60)
    
    # 1. 测试签名
    test_ed25519_signature()
    
    # 2. 测试余额 API
    test_backpack_balance()
    
    # 3. 测试持仓 API
    test_backpack_positions()
    
    # 4. 测试完整适配器
    test_backpack_adapter()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)

