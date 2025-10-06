import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # CORS配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 数据生成配置
    DATA_INTERVAL = int(os.getenv("DATA_INTERVAL", 1))
    
    # WebSocket配置
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", 100))
    
    # 数据源配置
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    
    # 代理配置
    PROXY_URL = os.getenv("PROXY_URL", "")
    PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
    PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")
    
    # 交易配置
    MIN_GAP_PERCENT = float(os.getenv("MIN_GAP_PERCENT", 0.5))
    MAX_GAP_PERCENT = float(os.getenv("MAX_GAP_PERCENT", 10.0))

