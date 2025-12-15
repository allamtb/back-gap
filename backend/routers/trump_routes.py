"""
特朗普情绪分析路由

负责特朗普情绪分析相关接口：
- 情绪分析列表
- 情绪分析详情
- 统计信息
- 帖子列表
- 服务状态
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/api/trump/sentiment/list")
async def get_sentiment_list(
    limit: int = Query(100, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    sentiment_type: Optional[str] = Query(None, description="情绪类型筛选：bullish/bearish/neutral")
):
    """
    获取情绪分析列表
    
    参数：
        limit: 返回数量限制（默认100）
        offset: 偏移量（默认0）
        sentiment_type: 情绪类型筛选（bullish=利好, bearish=利空, neutral=中性）
    """
    from app_config import sentiment_analyzer
    
    try:
        if sentiment_analyzer is None:
            raise HTTPException(status_code=503, detail="情绪分析服务未初始化")
        
        # 获取所有分析结果
        all_analyses = sentiment_analyzer.get_all_analyses()
        
        # 筛选
        if sentiment_type:
            if sentiment_type == 'bullish':
                all_analyses = [a for a in all_analyses if a['analysis'].get('is_bullish') is True]
            elif sentiment_type == 'bearish':
                all_analyses = [a for a in all_analyses if a['analysis'].get('is_bullish') is False]
            elif sentiment_type == 'neutral':
                all_analyses = [a for a in all_analyses if a['analysis'].get('is_bullish') is None]
        
        # 分页
        total = len(all_analyses)
        paginated = all_analyses[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取情绪分析列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trump/sentiment/{post_id}")
async def get_sentiment_by_id(post_id: str):
    """获取单条情绪分析详情"""
    from app_config import sentiment_analyzer
    
    try:
        if sentiment_analyzer is None:
            raise HTTPException(status_code=503, detail="情绪分析服务未初始化")
        
        analysis = sentiment_analyzer.get_analysis_by_id(post_id)
        
        if analysis is None:
            raise HTTPException(status_code=404, detail=f"未找到帖子 {post_id} 的分析结果")
        
        return {
            "success": True,
            "data": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取情绪分析详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trump/sentiment/stats")
async def get_sentiment_stats():
    """获取情绪分析统计信息"""
    from app_config import sentiment_analyzer
    
    try:
        if sentiment_analyzer is None:
            raise HTTPException(status_code=503, detail="情绪分析服务未初始化")
        
        stats = sentiment_analyzer.get_statistics()
        
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ 获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trump/sentiment/latest")
async def get_sentiment_latest(limit: int = Query(10, description="返回数量")):
    """获取最新N条情绪分析"""
    from app_config import sentiment_analyzer
    
    try:
        if sentiment_analyzer is None:
            raise HTTPException(status_code=503, detail="情绪分析服务未初始化")
        
        all_analyses = sentiment_analyzer.get_all_analyses()
        latest = all_analyses[:limit]
        
        return {
            "success": True,
            "data": latest,
            "total": len(all_analyses)
        }
    except Exception as e:
        logger.error(f"❌ 获取最新分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trump/posts/list")
async def get_trump_posts(
    limit: int = Query(100, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """获取特朗普帖子列表（原始数据）"""
    from app_config import post_archiver
    
    try:
        if post_archiver is None:
            raise HTTPException(status_code=503, detail="帖子存档服务未初始化")
        
        all_posts = post_archiver.get_all_posts()
        total = len(all_posts)
        paginated = all_posts[offset:offset + limit]
        
        return {
            "success": True,
            "data": paginated,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"❌ 获取帖子列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trump/status")
async def get_trump_service_status():
    """获取特朗普情绪分析服务状态"""
    from app_config import sentiment_analyzer, post_archiver
    
    return {
        "sentiment_analyzer_initialized": sentiment_analyzer is not None,
        "post_archiver_initialized": post_archiver is not None,
        "total_analyses": len(sentiment_analyzer.analyses) if sentiment_analyzer else 0,
        "total_posts": len(post_archiver.posts_dict) if post_archiver else 0,
        "timestamp": datetime.now().isoformat()
    }

