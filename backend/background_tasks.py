"""
后台任务模块

负责：
1. 市场数据更新任务
2. 特朗普情绪分析任务
"""

import logging
import time
import threading

from trump.sentiment_analyzer import TrumpSentimentAnalyzer
from trump.post_archiver import TrumpPostArchiver

logger = logging.getLogger(__name__)


def update_markets_in_background():
    """
    后台线程更新市场数据（新架构：Adapter自管理）
    
    在新的 Adapter 架构中，每个 Adapter 实例会自动管理自己的市场数据缓存：
    - 首次调用时自动加载
    - 使用缓存机制避免重复加载
    - TTL过期后自动重新加载
    
    这个函数保留用于主动预热缓存，避免首次请求时的延迟
    """
    from app_config import PRIORITY_EXCHANGES, market_cache, PROXY_CONFIG
    from exchange_adapters import get_adapter
    
    updated_count = 0
    skipped_count = 0
    
    for exchange_id in PRIORITY_EXCHANGES:
        try:
            # 检查缓存是否需要更新
            if not market_cache.is_cache_valid(exchange_id):
                # 创建临时 Adapter 实例来加载市场数据
                # Adapter 会自动使用 market_cache
                # 将代理配置合并到 config 中
                temp_config = {
                    'apiKey': '', 
                    'secret': '',  # 不需要真实的 API Key
                }
                # 如果有代理配置，添加到 config 中
                if PROXY_CONFIG:
                    temp_config['proxies'] = PROXY_CONFIG
                
                adapter = get_adapter(
                    exchange_id, 
                    'spot',  # 使用 spot 类型加载市场数据
                    temp_config
                )
                
                # 触发市场数据加载（Adapter内部会自动缓存）
                markets = adapter.load_markets()
                updated_count += 1
            else:
                skipped_count += 1
                
        except Exception as e:
            logger.error(f"❌ {exchange_id} 市场数据预热失败: {e}")
    
    if updated_count > 0:
        logger.info(f"✅ 市场数据预热完成: 更新 {updated_count} 个交易所")


def trump_sentiment_background_task():
    """
    特朗普情绪分析后台任务
    
    功能：
    1. 初始化：批量分析所有历史帖子
    2. 监控：持续监控新帖子并自动分析
    """
    from app_config import sentiment_analyzer, post_archiver
    import app_config
    
    try:
        # 初始化情绪分析器（静默模式）
        app_config.sentiment_analyzer = TrumpSentimentAnalyzer(
            rate_limit_seconds=60,  # 每分钟1次API调用
            max_retries=3
        )
        
        # 初始化帖子存档器（静默模式）
        app_config.post_archiver = TrumpPostArchiver()
        
        # 批量分析所有历史帖子（静默模式）
        app_config.sentiment_analyzer.batch_analyze_all_posts()
        logger.info("✅ 特朗普情绪分析服务已启动")
        
        # 持续监控新帖子
        while True:
            try:
                # 1. 更新帖子存档（获取最新帖子）
                new_post_count = app_config.post_archiver.fetch_and_archive_all()
                
                if new_post_count > 0:
                    logger.info(f"🆕 发现 {new_post_count} 条新帖子")
                    
                    # 2. 分析新帖子
                    posts = app_config.post_archiver.get_all_posts()
                    for post in posts[:new_post_count]:  # 只分析新帖子
                        post_id = post['id']
                        if post_id not in app_config.sentiment_analyzer.analyses:
                            app_config.sentiment_analyzer.analyze_single_post(post_id, post)
                            app_config.sentiment_analyzer.save_analyses()
                            
                            # API速率限制
                            if new_post_count > 1:
                                time.sleep(60)
                
                # 3. 等待下一次检查（30秒）
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"❌ 监控循环出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
        
    except KeyboardInterrupt:
        logger.info("⛔ 特朗普情绪分析服务已停止")
    except Exception as e:
        logger.error(f"❌ 特朗普情绪分析服务出错: {e}")
        import traceback
        traceback.print_exc()


def start_background_tasks():
    """启动所有后台任务"""
    # 启动市场数据更新线程
    update_thread = threading.Thread(
        target=update_markets_in_background,
        daemon=True,
        name="MarketUpdater"
    )
    update_thread.start()
    
    # 启动特朗普情绪分析后台任务
    trump_thread = threading.Thread(
        target=trump_sentiment_background_task,
        daemon=True,
        name="TrumpSentimentAnalyzer"
    )
    trump_thread.start()

