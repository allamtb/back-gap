#!/usr/bin/env python3
"""
Gap Trader Backend 启动脚本
启动统一的 FastAPI 服务器（包含 HTTP API 和 WebSocket）
"""

import logging
import uvicorn
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """主函数：启动统一服务器"""
    logger.info("=" * 60)
    logger.info("Gap Trader Backend - 启动统一服务器...")
    logger.info("=" * 60)
    logger.info(f"HTTP API: http://{Config.HOST}:{Config.PORT}")
    logger.info(f"WebSocket: ws://{Config.HOST}:{Config.PORT}/ws")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=False,
            log_level=Config.LOG_LEVEL.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Shutdown requested by user")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Server stopped")

if __name__ == "__main__":
    main()

