"""
代理和网络连接诊断工具
帮助你快速定位 Backpack WebSocket 连接失败的原因
"""
import asyncio
import websockets
import sys
import socket
import urllib.request
import urllib.error

# 常见代理端口配置
PROXY_CONFIGS = [
    ("http://127.0.0.1:7890", "Clash 默认端口"),
    ("http://127.0.0.1:1080", "V2Ray/SSR 默认端口"),
    ("http://127.0.0.1:7891", "Clash 备用端口"),
    ("http://127.0.0.1:10809", "Clash Meta 端口"),
]

API_WS = "wss://ws.backpack.exchange/"
TEST_HTTP_URL = "https://www.google.com"


def test_proxy_http(proxy_url):
    """测试 HTTP 代理是否可用"""
    try:
        proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        response = opener.open(TEST_HTTP_URL, timeout=5)
        return response.status == 200
    except Exception as e:
        return False


def test_port_open(host, port):
    """测试端口是否开放"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


async def test_ws_direct():
    """测试直连 Backpack WebSocket"""
    try:
        print("🔄 测试直连...")
        ws = await asyncio.wait_for(
            websockets.connect(API_WS, ping_interval=20),
            timeout=5
        )
        await ws.close()
        return True
    except asyncio.TimeoutError:
        print("   ❌ 连接超时")
        return False
    except ConnectionResetError:
        print("   ❌ 连接被重置（可能需要代理）")
        return False
    except Exception as e:
        print(f"   ❌ {type(e).__name__}: {e}")
        return False


async def test_ws_with_proxy(proxy_url):
    """测试通过代理连接 WebSocket"""
    try:
        from websockets.proxy import Proxy
        proxy = Proxy.from_url(proxy_url)
        ws = await asyncio.wait_for(
            websockets.connect(API_WS, proxy=proxy, ping_interval=20),
            timeout=10
        )
        await ws.close()
        return True
    except asyncio.TimeoutError:
        return False
    except Exception as e:
        return False


async def main():
    print("=" * 60)
    print("🔍 Backpack WebSocket 连接诊断工具")
    print("=" * 60)
    print()
    
    # 1. 测试直连
    print("【步骤 1】测试直连 Backpack")
    print("-" * 60)
    direct_ok = await test_ws_direct()
    if direct_ok:
        print("   ✅ 直连成功！你可以不使用代理")
        print("\n💡 建议配置:")
        print("   USE_PROXY = False")
        return
    else:
        print("   ℹ️  直连失败，需要使用代理\n")
    
    # 2. 检测代理端口
    print("【步骤 2】检测本地代理端口")
    print("-" * 60)
    available_proxies = []
    
    for proxy_url, desc in PROXY_CONFIGS:
        host, port = "127.0.0.1", int(proxy_url.split(":")[-1])
        port_open = test_port_open(host, port)
        
        if port_open:
            print(f"   ✅ 端口 {port} 开放 ({desc})")
            available_proxies.append((proxy_url, desc))
        else:
            print(f"   ❌ 端口 {port} 未开放 ({desc})")
    
    if not available_proxies:
        print("\n❌ 没有检测到可用的代理端口！")
        print("\n🔧 解决方案:")
        print("   1. 启动你的代理软件 (Clash/V2Ray/SSR)")
        print("   2. 确认代理软件正在运行")
        print("   3. 检查代理端口设置")
        print("\n常见代理软件:")
        print("   • Clash: 通常使用 7890 端口")
        print("   • V2Ray: 通常使用 1080 端口")
        print("   • Shadowsocks: 通常使用 1080 端口")
        return
    
    print()
    
    # 3. 测试代理 HTTP 连接
    print("【步骤 3】测试代理 HTTP 连接")
    print("-" * 60)
    working_proxies = []
    
    for proxy_url, desc in available_proxies:
        http_ok = test_proxy_http(proxy_url)
        if http_ok:
            print(f"   ✅ {proxy_url} - HTTP 代理工作正常")
            working_proxies.append((proxy_url, desc))
        else:
            print(f"   ❌ {proxy_url} - HTTP 代理不可用")
    
    if not working_proxies:
        print("\n❌ 代理端口开放，但无法正常工作！")
        print("\n🔧 解决方案:")
        print("   1. 检查代理软件的配置")
        print("   2. 确认代理软件已连接到服务器")
        print("   3. 尝试在浏览器中测试代理")
        return
    
    print()
    
    # 4. 测试 WebSocket 连接
    print("【步骤 4】测试 WebSocket 连接")
    print("-" * 60)
    success_proxy = None
    
    for proxy_url, desc in working_proxies:
        print(f"   🔄 测试 {proxy_url}...")
        ws_ok = await test_ws_with_proxy(proxy_url)
        if ws_ok:
            print(f"   ✅ WebSocket 连接成功！")
            success_proxy = (proxy_url, desc)
            break
        else:
            print(f"   ❌ WebSocket 连接失败")
    
    print()
    print("=" * 60)
    
    if success_proxy:
        proxy_url, desc = success_proxy
        print("🎉 诊断完成 - 找到可用配置！")
        print("=" * 60)
        print(f"\n✅ 可用代理: {proxy_url} ({desc})")
        print("\n💡 请在 backpack_example.py 中使用以下配置:")
        print("-" * 60)
        print(f"USE_PROXY = True")
        print(f'PROXY = "{proxy_url}"')
        print("-" * 60)
    else:
        print("❌ 所有代理测试失败")
        print("=" * 60)
        print("\n🔧 进一步排查:")
        print("   1. 确认代理软件已成功连接到服务器")
        print("   2. 在代理软件中测试连接")
        print("   3. 尝试在浏览器中访问 Google 测试代理")
        print("   4. 检查防火墙设置")
        print("   5. 尝试重启代理软件")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")

