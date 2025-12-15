import asyncio
import json
import aiohttp

API_WS = "wss://ws.backpack.exchange"  # ✅ 去掉末尾的 /
SYMBOL = "SOL_USDC_PERP"
USE_PROXY = True
PROXY = "http://127.0.0.1:1080"

async def subscribe_depth(symbol):
    proxy_url = PROXY if USE_PROXY else None

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            API_WS,
            proxy=proxy_url,
            timeout=aiohttp.ClientTimeout(total=10),
            heartbeat=20
        ) as ws:
            print(f"✅ 已连接 Backpack WebSocket ({'代理' if USE_PROXY else '直连'})")

            # ✅ 按照官方文档格式订阅
            sub_msg = {
                "method": "SUBSCRIBE",
                "params": [f"depth.{symbol}"]
            }
            await ws.send_json(sub_msg)
            print(f"📡 已订阅 {symbol} 实时深度数据")

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    
                    # 🔍 调试：打印所有收到的原始数据
                    print(f"📦 收到数据: {data}")
                    
                    # 处理错误响应
                    if "error" in data:
                        print(f"❌ 订阅失败: {data['error']}")
                        break
                    
                    # 官方格式：{"stream": "depth.SOL_USDC", "data": {...}}
                    if "stream" in data and data["stream"] == f"depth.{symbol}":
                        depth_data = data.get("data", {})
                        # 注意：字段名是 "b" 和 "a"，不是 "bids" 和 "asks"
                        bids = depth_data.get("b", [])
                        asks = depth_data.get("a", [])
                        
                        if bids and asks:
                            best_bid = bids[0][0]
                            best_ask = asks[0][0]
                            spread = float(best_ask) - float(best_bid)
                            print(f"📊 {symbol} | Bid: {best_bid} | Ask: {best_ask} | Spread: {spread:.4f}")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("❌ WebSocket 错误")
                    break

async def subscribe_ticker(symbol):
    """测试 ticker stream（可能不存在）"""
    proxy_url = PROXY if USE_PROXY else None

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            API_WS,
            proxy=proxy_url,
            timeout=aiohttp.ClientTimeout(total=10),
            heartbeat=20
        ) as ws:
            print(f"✅ 已连接 Backpack WebSocket ({'代理' if USE_PROXY else '直连'})")

            # 🧪 尝试 ticker stream（根据官方文档，可能只有 depth）
            sub_msg = {
                "method": "SUBSCRIBE",
                "params": [f"ticker.{symbol}"]  # 尝试 ticker
            }
            await ws.send_json(sub_msg)
            print(f"📡 已订阅 {symbol} Ticker 数据")

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    print(f"📦 收到数据: {data}")
                    
                    # 处理不同格式的响应
                    if "error" in data:
                        print(f"❌ 订阅失败: {data['error']}")
                        break
                    elif "stream" in data:
                        # 官方格式：{"stream": "ticker.SOL_USDC", "data": {...}}
                        stream_data = data.get("data", {})
                        print(f"🎯 Ticker 数据: {stream_data}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print("❌ WebSocket 错误")
                    break


async def main():
    print("Backpack 实时订阅示例")
    print("=" * 40)
    print(f"交易对: {SYMBOL}")
    print(f"使用代理: {USE_PROXY}\n")
    
    # ✅ 使用官方支持的 depth stream
    await subscribe_depth(SYMBOL)
    
    # 🧪 如果想测试 ticker，取消下面的注释
    # await subscribe_ticker(SYMBOL)


if __name__ == "__main__":
    asyncio.run(main())
