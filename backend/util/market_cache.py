"""
市场数据缓存管理模块

功能：
1. 将交易所市场数据缓存到本地文件
2. 支持过期检查和自动更新
3. 减少应用启动时间和API请求次数
"""

import json
import os
import time
import logging
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class MarketCache:
    """市场数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/market_cache", cache_ttl: int = 86400):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径
            cache_ttl: 缓存过期时间（秒），默认 86400 秒（24小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"市场数据缓存目录: {self.cache_dir.absolute()}")
    
    def _get_cache_file(self, exchange_id: str) -> Path:
        """获取交易所的缓存文件路径"""
        return self.cache_dir / f"{exchange_id}_markets.json"
    
    def _get_meta_file(self, exchange_id: str) -> Path:
        """获取交易所的元数据文件路径（存储缓存时间等）"""
        return self.cache_dir / f"{exchange_id}_meta.json"
    
    def is_cache_valid(self, exchange_id: str) -> bool:
        """
        检查缓存是否有效
        
        Args:
            exchange_id: 交易所 ID
            
        Returns:
            True 如果缓存有效，False 如果过期或不存在
        """
        cache_file = self._get_cache_file(exchange_id)
        meta_file = self._get_meta_file(exchange_id)
        
        if not cache_file.exists() or not meta_file.exists():
            return False
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            
            cached_time = meta.get('timestamp', 0)
            current_time = time.time()
            age = current_time - cached_time
            
            is_valid = age < self.cache_ttl
            
            if is_valid:
                hours = age / 3600
                logger.debug(f"{exchange_id} 缓存有效 (已缓存 {hours:.1f} 小时)")
            else:
                logger.info(f"{exchange_id} 缓存已过期 (已缓存 {age/3600:.1f} 小时)")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"检查缓存有效性失败: {e}")
            return False
    
    def load_from_cache(self, exchange_id: str) -> Optional[Dict]:
        """
        从缓存加载市场数据
        
        Args:
            exchange_id: 交易所 ID
            
        Returns:
            市场数据字典，如果缓存无效返回 None
        """
        if not self.is_cache_valid(exchange_id):
            return None
        
        cache_file = self._get_cache_file(exchange_id)
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                markets = json.load(f)
            
            logger.info(f"✅ 从缓存加载 {exchange_id} 市场数据 ({len(markets)} 个交易对)")
            return markets
            
        except Exception as e:
            logger.error(f"从缓存加载失败: {e}")
            return None
    
    def save_to_cache(self, exchange_id: str, markets: Dict) -> bool:
        """
        保存市场数据到缓存
        
        Args:
            exchange_id: 交易所 ID
            markets: 市场数据字典
            
        Returns:
            True 如果保存成功
        """
        cache_file = self._get_cache_file(exchange_id)
        meta_file = self._get_meta_file(exchange_id)
        
        try:
            # 保存市场数据
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(markets, f, indent=2, ensure_ascii=False)
            
            # 保存元数据
            meta = {
                'timestamp': time.time(),
                'exchange': exchange_id,
                'count': len(markets),
                'ttl': self.cache_ttl
            }
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
            
            logger.info(f"💾 已缓存 {exchange_id} 市场数据 ({len(markets)} 个交易对)")
            return True
            
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
            return False
    
    def clear_cache(self, exchange_id: Optional[str] = None):
        """
        清除缓存
        
        Args:
            exchange_id: 交易所 ID，如果为 None 则清除所有缓存
        """
        if exchange_id:
            # 清除指定交易所的缓存
            cache_file = self._get_cache_file(exchange_id)
            meta_file = self._get_meta_file(exchange_id)
            
            cache_file.unlink(missing_ok=True)
            meta_file.unlink(missing_ok=True)
            logger.info(f"🗑️ 已清除 {exchange_id} 缓存")
        else:
            # 清除所有缓存
            for file in self.cache_dir.glob("*"):
                file.unlink()
            logger.info("🗑️ 已清除所有市场数据缓存")
    
    def get_cache_info(self) -> Dict:
        """
        获取缓存统计信息
        
        Returns:
            缓存信息字典
        """
        cached_exchanges = []
        total_size = 0
        
        for cache_file in self.cache_dir.glob("*_markets.json"):
            exchange_id = cache_file.stem.replace("_markets", "")
            meta_file = self._get_meta_file(exchange_id)
            
            if meta_file.exists():
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    file_size = cache_file.stat().st_size
                    total_size += file_size
                    
                    cached_exchanges.append({
                        'exchange': exchange_id,
                        'cached_at': meta.get('timestamp', 0),
                        'count': meta.get('count', 0),
                        'size': file_size,
                        'valid': self.is_cache_valid(exchange_id)
                    })
                except Exception as e:
                    logger.error(f"读取缓存信息失败: {e}")
        
        return {
            'cache_dir': str(self.cache_dir.absolute()),
            'cache_ttl': self.cache_ttl,
            'cached_exchanges': cached_exchanges,
            'total_exchanges': len(cached_exchanges),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2)
        }


def load_markets_with_cache(exchange, exchange_id: str, cache: MarketCache) -> Dict:
    """
    使用缓存加载市场数据（辅助函数）
    
    Args:
        exchange: ccxt 交易所实例
        exchange_id: 交易所 ID
        cache: 缓存管理器实例
        
    Returns:
        市场数据字典
    """
    # 1. 尝试从缓存加载
    markets = cache.load_from_cache(exchange_id)
    
    if markets:
        # 缓存有效，直接使用
        exchange.markets = markets
        return markets
    
    # 2. 缓存无效，从交易所加载
    logger.info(f"📥 从 {exchange_id} API 加载市场数据...")
    start_time = time.time()
    
    try:
        markets = exchange.load_markets()
        elapsed = time.time() - start_time
        
        logger.info(f"✅ {exchange_id} 市场数据加载完成 (耗时: {elapsed:.2f}秒, {len(markets)} 个交易对)")
        
        # 3. 保存到缓存
        cache.save_to_cache(exchange_id, markets)
        
        return markets
        
    except Exception as e:
        logger.error(f"❌ {exchange_id} 市场数据加载失败: {e}")
        raise



