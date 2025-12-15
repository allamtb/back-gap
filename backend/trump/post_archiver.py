#!/usr/bin/env python3
"""
特朗普帖子存档器
功能：
1. 获取并存档所有历史帖子
2. 实时监控新帖子
3. 提供帖子查询和遍历功能
"""

import feedparser
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import re
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('post_archiver.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TrumpPostArchiver:
    """特朗普帖子存档器"""
    
    def __init__(self, rss_url: str = "https://trumpstruth.org/feed", archive_file: str = None):
        self.rss_url = rss_url
        # 使用脚本所在目录的绝对路径，确保文件位置固定
        base_dir = Path(__file__).parent
        self.archive_file = archive_file or str(base_dir / 'trump_posts_archive.json')
        self.posts_dict = {}  # 使用字典存储，key为post_id
        self.load_archive()
    
    def load_archive(self):
        """加载已存档的帖子"""
        try:
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.posts_dict = data.get('posts', {})
        except Exception as e:
            logger.error(f"❌ 加载存档失败: {e}")
            self.posts_dict = {}
    
    def save_archive(self):
        """保存帖子存档"""
        try:
            # 按时间排序帖子
            sorted_posts = dict(sorted(
                self.posts_dict.items(),
                key=lambda x: x[1].get('timestamp', ''),
                reverse=True
            ))
            
            data = {
                'total_posts': len(sorted_posts),
                'last_updated': datetime.now().isoformat(),
                'posts': sorted_posts
            }
            
            with open(self.archive_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ 保存存档失败: {e}")
    
    def fetch_rss_feed(self) -> Optional[feedparser.FeedParserDict]:
        """获取RSS Feed"""
        try:
            feed = feedparser.parse(self.rss_url)
            
            if feed.bozo:
                logger.warning(f"⚠️ RSS解析警告: {feed.bozo_exception}")
            
            return feed
            
        except Exception as e:
            logger.error(f"❌ 获取RSS Feed失败: {e}")
            return None
    
    def extract_post_data(self, entry) -> Optional[Dict]:
        """从RSS条目提取帖子数据"""
        try:
            # 提取帖子ID
            post_id = None
            if hasattr(entry, 'link'):
                match = re.search(r'/statuses/(\d+)', entry.link)
                if match:
                    post_id = match.group(1)
                else:
                    # 备用方案：使用内容哈希
                    post_id = f"hash_{abs(hash(entry.title + entry.description))}"
            
            if not post_id:
                return None
            
            # 提取帖子文本
            post_text = ""
            if hasattr(entry, 'description'):
                # 清理CDATA标签
                post_text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', entry.description)
                # 移除HTML标签
                post_text = re.sub(r'<[^>]+>', '', post_text)
                post_text = post_text.strip()
            
            # 如果是空标题或无内容，尝试使用title
            if not post_text or len(post_text) < 10:
                if hasattr(entry, 'title'):
                    post_text = entry.title
            
            # 提取时间戳
            timestamp = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                timestamp = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'published'):
                timestamp = entry.published
            
            # 提取URL
            post_url = entry.link if hasattr(entry, 'link') else None
            
            # 检查是否为转发
            is_retweet = post_text.startswith('RT @realDonaldTrump')
            
            if post_text:
                return {
                    'id': post_id,
                    'text': post_text,
                    'timestamp': timestamp,
                    'url': post_url,
                    'is_retweet': is_retweet,
                    'scraped_at': datetime.now().isoformat(),
                    'character_count': len(post_text)
                }
        
        except Exception as e:
            logger.error(f"❌ 提取帖子数据失败: {e}")
        
        return None
    
    def fetch_and_archive_all(self) -> int:
        """获取并存档所有当前可见的帖子"""
        feed = self.fetch_rss_feed()
        if not feed:
            return 0
        
        new_count = 0
        updated_count = 0
        
        for entry in feed.entries:
            post_data = self.extract_post_data(entry)
            if post_data:
                post_id = post_data['id']
                
                if post_id not in self.posts_dict:
                    # 新帖子
                    self.posts_dict[post_id] = post_data
                    new_count += 1
                else:
                    # 更新现有帖子
                    self.posts_dict[post_id].update(post_data)
                    updated_count += 1
        
        self.save_archive()
        return new_count
    
    def monitor_new_posts(self, interval: int = 30, callback=None):
        """实时监控新帖子"""
        try:
            while True:
                feed = self.fetch_rss_feed()
                if feed:
                    new_posts = []
                    
                    for entry in feed.entries:
                        post_data = self.extract_post_data(entry)
                        if post_data:
                            post_id = post_data['id']
                            
                            if post_id not in self.posts_dict:
                                # 发现新帖子
                                self.posts_dict[post_id] = post_data
                                new_posts.append(post_data)
                    
                    if new_posts:
                        self.save_archive()
                        
                        # 如果提供了回调函数，调用它
                        if callback:
                            for post in new_posts:
                                callback(post)
                        
                        # 显示新帖子
                        for post in new_posts:
                            self.display_post(post)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.save_archive()
        except Exception as e:
            logger.error(f"❌ 监控出错: {e}")
            self.save_archive()
    
    def display_post(self, post: Dict):
        """显示帖子详情"""
        print("\n" + "=" * 80)
        print("🆕 新帖子")
        print("=" * 80)
        print(f"🆔 ID: {post['id']}")
        print(f"📅 时间: {post.get('timestamp', '未知')}")
        print(f"🔗 链接: {post['url']}")
        print(f"🔄 转发: {'是' if post.get('is_retweet') else '否'}")
        print(f"📏 字数: {post['character_count']}")
        print("=" * 80)
        print("📝 内容:")
        print("-" * 80)
        print(post['text'])
        print("=" * 80)
        print(f"📊 存档总数: {len(self.posts_dict)}")
        print("=" * 80 + "\n")
    
    def get_all_posts(self) -> List[Dict]:
        """获取所有帖子（按时间倒序）"""
        posts = list(self.posts_dict.values())
        posts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return posts
    
    def get_post_by_id(self, post_id: str) -> Optional[Dict]:
        """根据ID获取帖子"""
        return self.posts_dict.get(post_id)
    
    def search_posts(self, keyword: str) -> List[Dict]:
        """搜索包含关键词的帖子"""
        results = []
        keyword_lower = keyword.lower()
        
        for post in self.posts_dict.values():
            if keyword_lower in post['text'].lower():
                results.append(post)
        
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results
    
    def get_posts_by_date(self, date_str: str) -> List[Dict]:
        """获取指定日期的帖子（格式：YYYY-MM-DD）"""
        results = []
        
        for post in self.posts_dict.values():
            if post.get('timestamp', '').startswith(date_str):
                results.append(post)
        
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return results
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        posts = list(self.posts_dict.values())
        
        if not posts:
            return {
                'total_posts': 0,
                'retweets': 0,
                'original_posts': 0
            }
        
        retweets = sum(1 for p in posts if p.get('is_retweet'))
        total_chars = sum(p.get('character_count', 0) for p in posts)
        
        # 获取最早和最新的时间戳
        timestamps = [p.get('timestamp') for p in posts if p.get('timestamp')]
        timestamps.sort()
        
        return {
            'total_posts': len(posts),
            'retweets': retweets,
            'original_posts': len(posts) - retweets,
            'average_length': total_chars / len(posts) if posts else 0,
            'earliest_post': timestamps[0] if timestamps else None,
            'latest_post': timestamps[-1] if timestamps else None
        }
    
    def export_to_text(self, output_file: str = 'trump_posts_export.txt'):
        """导出所有帖子到文本文件"""
        try:
            posts = self.get_all_posts()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("特朗普Truth Social帖子存档\n")
                f.write("=" * 80 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"总帖子数: {len(posts)}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, post in enumerate(posts, 1):
                    f.write(f"\n{'=' * 80}\n")
                    f.write(f"帖子 #{i}\n")
                    f.write(f"{'=' * 80}\n")
                    f.write(f"ID: {post['id']}\n")
                    f.write(f"时间: {post.get('timestamp', '未知')}\n")
                    f.write(f"链接: {post['url']}\n")
                    f.write(f"类型: {'转发' if post.get('is_retweet') else '原创'}\n")
                    f.write(f"{'-' * 80}\n")
                    f.write(f"{post['text']}\n")
                    f.write(f"{'=' * 80}\n")
            
            logger.info(f"✅ 已导出 {len(posts)} 条帖子到 {output_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 导出失败: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='特朗普帖子存档器')
    parser.add_argument('--mode', choices=['archive', 'monitor', 'stats', 'export'], 
                       default='archive',
                       help='运行模式：archive(存档), monitor(监控), stats(统计), export(导出)')
    parser.add_argument('--interval', type=int, default=30,
                       help='监控模式下的检查间隔（秒）')
    parser.add_argument('--search', type=str,
                       help='搜索关键词')
    parser.add_argument('--date', type=str,
                       help='查询指定日期的帖子（格式：YYYY-MM-DD）')
    
    args = parser.parse_args()
    
    archiver = TrumpPostArchiver()
    
    if args.mode == 'archive':
        # 存档模式：获取所有当前可见的帖子
        print("\n📥 存档模式")
        archiver.fetch_and_archive_all()
        
    elif args.mode == 'monitor':
        # 监控模式：实时监控新帖子
        print("\n🔄 监控模式")
        archiver.monitor_new_posts(interval=args.interval)
        
    elif args.mode == 'stats':
        # 统计模式：显示统计信息
        print("\n📊 统计信息")
        print("=" * 60)
        stats = archiver.get_statistics()
        print(f"总帖子数: {stats['total_posts']}")
        print(f"原创帖子: {stats['original_posts']}")
        print(f"转发帖子: {stats['retweets']}")
        print(f"平均长度: {stats['average_length']:.0f} 字符")
        print(f"最早帖子: {stats['earliest_post']}")
        print(f"最新帖子: {stats['latest_post']}")
        print("=" * 60)
        
        if args.search:
            # 搜索功能
            print(f"\n🔍 搜索关键词: '{args.search}'")
            results = archiver.search_posts(args.search)
            print(f"找到 {len(results)} 条匹配的帖子")
            for i, post in enumerate(results[:10], 1):
                print(f"\n{i}. [{post['id']}] {post.get('timestamp', '未知')}")
                print(f"   {post['text'][:100]}...")
        
        if args.date:
            # 日期查询
            print(f"\n📅 查询日期: {args.date}")
            results = archiver.get_posts_by_date(args.date)
            print(f"找到 {len(results)} 条帖子")
            for i, post in enumerate(results, 1):
                print(f"\n{i}. [{post['id']}] {post.get('timestamp', '未知')}")
                print(f"   {post['text'][:100]}...")
    
    elif args.mode == 'export':
        # 导出模式：导出到文本文件
        print("\n📤 导出模式")
        archiver.export_to_text()


if __name__ == "__main__":
    main()

