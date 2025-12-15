"""
Cookie 数据服务

负责：
1. 数据库连接管理
2. Cookie 数据的 CRUD 操作
3. 以 AFD_IP 作为去重键
"""

import logging
import json
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models import Base, BaiduCookieData, BaiduCookieRequest, BaiduCookieResponse

logger = logging.getLogger(__name__)


class CookieService:
    """Cookie 数据服务"""
    
    def __init__(self, db_path: str = "data/baidu_cookies.db"):
        """
        初始化 Cookie 服务
        
        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=False,  # 生产环境关闭 SQL 日志
            connect_args={"check_same_thread": False}  # SQLite 多线程支持
        )
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # 初始化数据库表
        self._init_database()
        
        logger.info(f"✅ Cookie 服务初始化完成，数据库路径: {db_path}")
    
    def _init_database(self):
        """创建数据库表（如果不存在）"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ 数据库表已创建/验证")
        except Exception as e:
            logger.error(f"❌ 数据库初始化失败: {e}")
            raise
    
    def get_db(self) -> Session:
        """获取数据库会话（依赖注入）"""
        db = self.SessionLocal()
        try:
            return db
        finally:
            pass  # 会话由调用者关闭
    
    def _convert_to_response(self, db_obj: BaiduCookieData) -> BaiduCookieResponse:
        """
        将数据库对象转换为响应对象（处理 headers 的 JSON 反序列化）
        
        Args:
            db_obj: 数据库对象
            
        Returns:
            响应对象
        """
        # 解析 headers（JSON 字符串 -> dict）
        headers_dict = None
        if db_obj.headers:
            try:
                headers_dict = json.loads(db_obj.headers)
            except json.JSONDecodeError:
                logger.warning(f"⚠️ 无法解析 headers JSON: {db_obj.headers[:50]}...")
                headers_dict = None
        
        return BaiduCookieResponse(
            id=db_obj.id,
            afd_ip=db_obj.afd_ip,
            baidulocnew=db_obj.baidulocnew,
            url=db_obj.url,
            timestamp=db_obj.timestamp,
            headers=headers_dict,
            proxy_ip=db_obj.proxy_ip,
            proxy_port=db_obj.proxy_port,
            proxy_city=db_obj.proxy_city,
            proxy_addr=db_obj.proxy_addr,
            created_at=db_obj.created_at,
            updated_at=db_obj.updated_at
        )
    
    def save_cookie_data(
        self, 
        cookie_request: BaiduCookieRequest
    ) -> Optional[BaiduCookieResponse]:
        """
        保存 Cookie 数据（以 AFD_IP 作为去重键）
        
        Args:
            cookie_request: Cookie 请求数据
            
        Returns:
            保存后的 Cookie 数据（如果成功）
        """
        db = self.SessionLocal()
        try:
            # 检查 AFD_IP 是否为空
            if not cookie_request.afd_ip:
                logger.warning("⚠️ AFD_IP 为空，无法保存")
                return None
            
            # 查询是否已存在相同的 AFD_IP
            existing = db.query(BaiduCookieData).filter(
                BaiduCookieData.afd_ip == cookie_request.afd_ip
            ).first()
            
            if existing:
                # 更新现有记录
                existing.baidulocnew = cookie_request.baidulocnew
                existing.url = cookie_request.url
                existing.timestamp = cookie_request.timestamp
                existing.headers = json.dumps(cookie_request.headers, ensure_ascii=False) if cookie_request.headers else None
                # 更新代理 IP 信息
                existing.proxy_ip = cookie_request.proxy_ip
                existing.proxy_port = cookie_request.proxy_port
                existing.proxy_city = cookie_request.proxy_city
                existing.proxy_addr = cookie_request.proxy_addr
                existing.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(existing)
                
                logger.info(f"✅ Cookie 数据已更新（AFD_IP: {cookie_request.afd_ip[:20]}...）")
                return self._convert_to_response(existing)
            else:
                # 创建新记录
                new_cookie = BaiduCookieData(
                    afd_ip=cookie_request.afd_ip,
                    baidulocnew=cookie_request.baidulocnew,
                    url=cookie_request.url,
                    timestamp=cookie_request.timestamp,
                    headers=json.dumps(cookie_request.headers, ensure_ascii=False) if cookie_request.headers else None,
                    # 保存代理 IP 信息
                    proxy_ip=cookie_request.proxy_ip,
                    proxy_port=cookie_request.proxy_port,
                    proxy_city=cookie_request.proxy_city,
                    proxy_addr=cookie_request.proxy_addr
                )
                
                db.add(new_cookie)
                db.commit()
                db.refresh(new_cookie)
                
                logger.info(f"✅ Cookie 数据已保存（AFD_IP: {cookie_request.afd_ip[:20]}...）")
                return self._convert_to_response(new_cookie)
                
        except IntegrityError as e:
            db.rollback()
            logger.error(f"❌ 数据库完整性错误（可能重复）: {e}")
            return None
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 保存 Cookie 数据失败: {e}")
            return None
        finally:
            db.close()
    
    def get_all_cookies(self, limit: int = 100) -> List[BaiduCookieResponse]:
        """
        获取所有 Cookie 数据（按创建时间降序）
        
        Args:
            limit: 返回数量限制
            
        Returns:
            Cookie 数据列表
        """
        db = self.SessionLocal()
        try:
            cookies = db.query(BaiduCookieData)\
                .order_by(BaiduCookieData.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [self._convert_to_response(c) for c in cookies]
        except Exception as e:
            logger.error(f"❌ 查询 Cookie 数据失败: {e}")
            return []
        finally:
            db.close()
    
    def get_cookie_by_afd_ip(self, afd_ip: str) -> Optional[BaiduCookieResponse]:
        """
        根据 AFD_IP 查询 Cookie 数据
        
        Args:
            afd_ip: AFD_IP Cookie 值
            
        Returns:
            Cookie 数据（如果存在）
        """
        db = self.SessionLocal()
        try:
            cookie = db.query(BaiduCookieData).filter(
                BaiduCookieData.afd_ip == afd_ip
            ).first()
            
            if cookie:
                return self._convert_to_response(cookie)
            return None
        except Exception as e:
            logger.error(f"❌ 查询 Cookie 数据失败: {e}")
            return None
        finally:
            db.close()
    
    def delete_cookie(self, cookie_id: int) -> bool:
        """
        删除 Cookie 数据
        
        Args:
            cookie_id: Cookie ID
            
        Returns:
            是否删除成功
        """
        db = self.SessionLocal()
        try:
            cookie = db.query(BaiduCookieData).filter(
                BaiduCookieData.id == cookie_id
            ).first()
            
            if cookie:
                db.delete(cookie)
                db.commit()
                logger.info(f"✅ Cookie 数据已删除（ID: {cookie_id}）")
                return True
            
            logger.warning(f"⚠️ Cookie 数据不存在（ID: {cookie_id}）")
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"❌ 删除 Cookie 数据失败: {e}")
            return False
        finally:
            db.close()
    
    def get_cookie_count(self) -> int:
        """
        获取 Cookie 数据总数
        
        Returns:
            数据总数
        """
        db = self.SessionLocal()
        try:
            count = db.query(BaiduCookieData).count()
            return count
        except Exception as e:
            logger.error(f"❌ 查询 Cookie 数据总数失败: {e}")
            return 0
        finally:
            db.close()


# 全局单例实例
cookie_service = CookieService()

