"""
交易网站链接管理路由

负责交易网站链接管理接口：
- 获取链接列表
- 获取单个链接
- 创建链接
- 更新链接
- 删除链接
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import json
import os
import uuid
from pathlib import Path

# 导入数据模型
from models import (
    TradingWebsiteLink,
    TradingWebsiteLinkCreate,
    TradingWebsiteLinkUpdate
)

router = APIRouter()
logger = logging.getLogger(__name__)

# 链接数据存储文件路径
LINKS_DATA_FILE = "data/trading_links.json"

# 确保数据目录存在
Path("data").mkdir(exist_ok=True)


# ============================================================================
# 辅助函数
# ============================================================================

def load_trading_links() -> list:
    """从文件加载交易链接"""
    try:
        if os.path.exists(LINKS_DATA_FILE):
            with open(LINKS_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"加载链接数据失败: {e}")
        return []


def save_trading_links(links: list) -> bool:
    """保存交易链接到文件"""
    try:
        with open(LINKS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存链接数据失败: {e}")
        return False


# ============================================================================
# 交易网站链接管理 API
# ============================================================================

@router.get("/api/trading-links")
async def get_trading_links():
    """获取所有交易网站链接"""
    try:
        links = load_trading_links()
        return {
            "success": True,
            "data": links,
            "total": len(links)
        }
    except Exception as e:
        logger.error(f"❌ 获取链接列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/trading-links/{link_id}")
async def get_trading_link(link_id: str):
    """获取单个交易网站链接"""
    try:
        links = load_trading_links()
        link = next((l for l in links if l['id'] == link_id), None)
        
        if link is None:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {link_id} 的链接")
        
        return {
            "success": True,
            "data": link
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取链接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/trading-links")
async def create_trading_link(link: TradingWebsiteLinkCreate):
    """创建新的交易网站链接"""
    try:
        links = load_trading_links()
        
        # 生成唯一ID
        new_link = {
            "id": str(uuid.uuid4()),
            "name": link.name,
            "url": link.url,
            "description": link.description,
            "category": link.category,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat()
        }
        
        links.append(new_link)
        
        if not save_trading_links(links):
            raise HTTPException(status_code=500, detail="保存链接失败")
        
        logger.info(f"✅ 创建链接成功: {link.name} -> {link.url}")
        
        return {
            "success": True,
            "message": "链接创建成功",
            "data": new_link
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 创建链接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/api/trading-links/{link_id}")
async def update_trading_link(link_id: str, link_update: TradingWebsiteLinkUpdate):
    """更新交易网站链接"""
    try:
        links = load_trading_links()
        link_index = next((i for i, l in enumerate(links) if l['id'] == link_id), None)
        
        if link_index is None:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {link_id} 的链接")
        
        # 更新字段
        if link_update.name is not None:
            links[link_index]['name'] = link_update.name
        if link_update.url is not None:
            links[link_index]['url'] = link_update.url
        if link_update.description is not None:
            links[link_index]['description'] = link_update.description
        if link_update.category is not None:
            links[link_index]['category'] = link_update.category
        
        links[link_index]['updatedAt'] = datetime.now().isoformat()
        
        if not save_trading_links(links):
            raise HTTPException(status_code=500, detail="保存链接失败")
        
        logger.info(f"✅ 更新链接成功: {link_id}")
        
        return {
            "success": True,
            "message": "链接更新成功",
            "data": links[link_index]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 更新链接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/trading-links/{link_id}")
async def delete_trading_link(link_id: str):
    """删除交易网站链接"""
    try:
        links = load_trading_links()
        link_index = next((i for i, l in enumerate(links) if l['id'] == link_id), None)
        
        if link_index is None:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {link_id} 的链接")
        
        deleted_link = links.pop(link_index)
        
        if not save_trading_links(links):
            raise HTTPException(status_code=500, detail="保存链接失败")
        
        logger.info(f"✅ 删除链接成功: {deleted_link['name']}")
        
        return {
            "success": True,
            "message": "链接删除成功",
            "data": deleted_link
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除链接失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

