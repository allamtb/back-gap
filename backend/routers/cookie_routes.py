"""
Cookie 数据路由

负责接收和管理百度 Cookie 数据的 API 接口
"""

from fastapi import APIRouter, HTTPException
from typing import List
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import BaiduCookieRequest, BaiduCookieResponse
from services.cookie_service import cookie_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cookies", tags=["cookies"])


@router.post("/baidu", response_model=BaiduCookieResponse)
async def upload_baidu_cookie(cookie_data: BaiduCookieRequest):
    """
    接收百度 Cookie 数据（来自 mitmproxy）
    
    - 以 AFD_IP 作为去重键
    - 如果 AFD_IP 已存在，则更新数据
    - 如果 AFD_IP 不存在，则创建新记录
    """
    try:
        logger.info(f"📥 接收到 Cookie 数据: AFD_IP={cookie_data.afd_ip[:20] if cookie_data.afd_ip else 'None'}...")
        
        # 检查 AFD_IP 是否为空
        if not cookie_data.afd_ip:
            logger.warning("⚠️ AFD_IP 为空，拒绝保存")
            raise HTTPException(
                status_code=400,
                detail="AFD_IP cannot be empty"
            )
        
        # 保存到数据库
        result = cookie_service.save_cookie_data(cookie_data)
        
        if result:
            logger.info(f"✅ Cookie 数据已保存到数据库（ID: {result.id}）")
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save cookie data"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 保存 Cookie 数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/baidu", response_model=List[BaiduCookieResponse])
async def get_all_cookies(limit: int = 100):
    """
    获取所有百度 Cookie 数据（按创建时间降序）
    
    - limit: 返回数量限制（默认 100）
    """
    try:
        cookies = cookie_service.get_all_cookies(limit=limit)
        logger.info(f"📊 返回 {len(cookies)} 条 Cookie 数据")
        return cookies
    except Exception as e:
        logger.error(f"❌ 查询 Cookie 数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cookie data: {str(e)}"
        )


@router.get("/baidu/{afd_ip}", response_model=BaiduCookieResponse)
async def get_cookie_by_afd_ip(afd_ip: str):
    """
    根据 AFD_IP 查询 Cookie 数据
    """
    try:
        cookie = cookie_service.get_cookie_by_afd_ip(afd_ip)
        
        if cookie:
            logger.info(f"✅ 找到 Cookie 数据（AFD_IP: {afd_ip[:20]}...）")
            return cookie
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Cookie data not found for AFD_IP: {afd_ip}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 查询 Cookie 数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch cookie data: {str(e)}"
        )


@router.delete("/baidu/{cookie_id}")
async def delete_cookie(cookie_id: int):
    """
    删除 Cookie 数据
    """
    try:
        success = cookie_service.delete_cookie(cookie_id)
        
        if success:
            logger.info(f"✅ Cookie 数据已删除（ID: {cookie_id}）")
            return {"message": "Cookie deleted successfully", "id": cookie_id}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Cookie data not found (ID: {cookie_id})"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除 Cookie 数据失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete cookie data: {str(e)}"
        )


@router.get("/baidu/stats/count")
async def get_cookie_count():
    """
    获取 Cookie 数据总数统计
    """
    try:
        count = cookie_service.get_cookie_count()
        return {
            "total_cookies": count,
            "message": f"Total {count} cookie records in database"
        }
    except Exception as e:
        logger.error(f"❌ 查询 Cookie 数据总数失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cookie count: {str(e)}"
        )

