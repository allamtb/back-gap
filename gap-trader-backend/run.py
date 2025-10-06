#!/usr/bin/env python3
"""
Gap Trader Backend 启动脚本
"""

import uvicorn
from config import Config

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower(),
        access_log=True
    )

