#!/usr/bin/env python3
"""
特朗普帖子情绪分析服务
功能：
1. 批量分析历史帖子
2. 实时监控新帖子并自动分析
3. 智谱AI调用（带重试机制）
4. 数据持久化
"""

import json
import logging
import time
import re
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import os
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 智谱AI客户端（延迟导入避免启动时失败）
try:
    import zai
    from zai import ZhipuAiClient
    ZAI_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ zai 模块未安装，情绪分析功能将不可用")
    ZAI_AVAILABLE = False


class TrumpSentimentAnalyzer:
    """特朗普帖子情绪分析器"""
    
    # 高风险关键词列表（黑天鹅事件相关）
    HIGH_RISK_KEYWORDS = [
        # 地缘政治
        '中国', 'china', 'chinese', '台湾', 'taiwan',
        '俄罗斯', 'russia', 'russian', '乌克兰', 'ukraine',
        '朝鲜', 'north korea', '伊朗', 'iran',
        
        # 经济战
        '关税', 'tariff', 'tariffs', '贸易战', 'trade war',
        '制裁', 'sanction', 'sanctions', '禁令', 'ban',
        
        # 军事/战争
        '战争', 'war', '军事', 'military', '核', 'nuclear',
        '导弹', 'missile', '轰炸', 'bomb', '攻击', 'attack',
        
        # 其他黑天鹅
        '紧急', 'emergency', '危机', 'crisis', '冲突', 'conflict'
    ]
    
    def __init__(
        self, 
        api_key: str = "59bec590a9174c5d9d0b57aaf8e3aecd.MkYPI9ZuWOqrRrWP",
        posts_file: str = None,
        output_file: str = None,
        rate_limit_seconds: int = 10,
        max_retries: int = 3
    ):
        """
        初始化分析器
        
        Args:
            api_key: 智谱AI API密钥
            posts_file: 帖子存档文件路径
            output_file: 分析结果输出文件路径
            rate_limit_seconds: API调用间隔（秒）
            max_retries: 最大重试次数
        """
        # 设置文件路径 - 使用脚本所在目录的绝对路径
        base_dir = Path(__file__).parent
        self.posts_file = str(posts_file or base_dir / 'trump_posts_archive.json')
        self.output_file = str(output_file or base_dir / 'sentiment_analysis.json')
        
        self.rate_limit_seconds = rate_limit_seconds
        self.max_retries = max_retries
        
        # 初始化智谱AI客户端
        if ZAI_AVAILABLE:
            try:
                self.client = ZhipuAiClient(api_key=api_key)
            except Exception as e:
                logger.error(f"❌ 智谱AI客户端初始化失败: {e}")
                self.client = None
        else:
            self.client = None
        
        # 加载分析结果
        self.analyses = {}
        self.load_analyses()
        
        # 统计信息
        self.stats = {
            'total_analyzed': 0,
            'success_count': 0,
            'error_count': 0,
            'last_analysis_time': None
        }
    
    def _is_low_quality_post(self, post_text: str) -> Tuple[bool, str]:
        """
        检测低质量帖子（无实质内容）
        
        Args:
            post_text: 帖子文本
            
        Returns:
            (是否为低质量帖子, 过滤原因)
        """
        text_clean = post_text.strip()
        
        # 情况1：[No Title] 开头（通常是无内容的帖子）
        if text_clean.startswith('[No Title]'):
            return True, "no_title"
        
        # 情况2：纯URL（只有链接，没有文字描述）
        # 匹配形如: https://t.co/xxxxx 或 http://example.com
        url_only_pattern = r'^https?://[^\s]+$'
        if re.match(url_only_pattern, text_clean):
            return True, "url_only"
        
        # 情况3：内容太短（少于10个字符，排除有意义的短句）
        if len(text_clean) < 10:
            return True, "too_short"
        
        return False, ""
    
    def is_high_risk_post(self, post_text: str) -> bool:
        """
        检测帖子是否包含高风险关键词
        
        Args:
            post_text: 帖子文本
            
        Returns:
            是否为高风险帖子
        """
        text_lower = post_text.lower()
        return any(keyword.lower() in text_lower for keyword in self.HIGH_RISK_KEYWORDS)
    
    def load_analyses(self):
        """加载已有的分析结果"""
        try:
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.analyses = data.get('analyses', {})
            else:
                self.analyses = {}
        except Exception as e:
            logger.error(f"❌ 加载分析结果失败: {e}")
            self.analyses = {}
    
    def save_analyses(self):
        """保存分析结果"""
        try:
            # 按时间排序
            sorted_analyses = dict(sorted(
                self.analyses.items(),
                key=lambda x: x[1].get('post_timestamp', ''),
                reverse=True
            ))
            
            data = {
                'total_analyzed': len(sorted_analyses),
                'last_updated': datetime.now().isoformat(),
                'stats': self.stats,
                'analyses': sorted_analyses
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            logger.error(f"❌ 保存分析结果失败: {e}")
            return False
    
    def load_posts(self) -> Dict:
        """加载帖子数据"""
        try:
            if not os.path.exists(self.posts_file):
                logger.error(f"❌ 帖子文件不存在: {self.posts_file}")
                return {}
            
            with open(self.posts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                posts = data.get('posts', {})
                return posts
        except Exception as e:
            logger.error(f"❌ 加载帖子失败: {e}")
            return {}
    
    def analyze_post_with_ai(self, post_text: str) -> Optional[Dict]:
        """
        使用智谱AI分析单条帖子（带重试机制）
        
        Args:
            post_text: 帖子文本
            
        Returns:
            分析结果字典，失败返回 None
        """
        if not self.client:
            logger.error("❌ 智谱AI客户端未初始化")
            return None
        
        # 检测是否为高风险帖子
        is_high_risk = self.is_high_risk_post(post_text)
        
        # 根据风险等级选择不同的 system prompt 和 temperature
        if is_high_risk:
            system_prompt = (
                "你是一个专业的地缘政治与金融风险分析师，擅长识别可能引发市场黑天鹅事件的信号。\n\n"
                "⚠️ 当前分析的是特朗普关于【地缘政治/战争/关税/中国】等高风险话题的发言。\n\n"
                "🔍 分析要点：\n"
                "1. 这类话题对市场的影响通常是【显著且持久的】\n"
                "2. 关税/制裁 → 直接影响供应链、企业利润和国际贸易\n"
                "3. 战争/军事冲突 → 触发避险情绪，资金流向黄金/美元/比特币\n"
                "4. 中国/俄罗斯相关 → 全球经济秩序变化，波及全球市场\n"
                "5. 此类话题通常应给出【4-5星】的高影响评级\n\n"
                "请严格按照以下格式输出结果：\n\n"
                "【主题】：简述发言的主要内容\n"
                "【情绪】：判断整体情绪（威胁、强硬、愤怒、焦虑、乐观等）\n"
                "【股市潜在影响】：详细分析对币圈、美股的具体影响路径和可能的连锁反应\n"
                "【总结】：20字以内的总结，按星级总结整体市场影响倾向（利好/利空/中性），总星是5星。"
                "如果利好，那么就是星级越多越好。如果利空，那么星级越多越利空。"
            )
            temperature = 0.3  # 更低的温度，保持分析的严肃性
        else:
            system_prompt = (
                "你是一个专业的政治与金融分析师，擅长分析特朗普的发言对股市的影响。\n\n"
                "请严格按照以下格式输出结果：\n\n"
                "【主题】：简述发言的主要内容\n"
                "【情绪】：判断整体情绪（乐观、积极、愤怒、威胁、焦虑、悲观等）\n"
                "【股市潜在影响】：对币圈、美股的影响\n"
                "【总结】：20字以内的总结，按星级总结整体市场影响倾向（利好/利空/中性），总星是5星。"
                "如果利好，那么就是星级越多越好。如果利空，那么星级越多越利空。"
                "常规政治言论通常给出【1-3星】的影响评级。"
            )
            temperature = 0.5  # 标准温度
        
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                # 创建聊天请求
                response = self.client.chat.completions.create(
                    model="GLM-4.6",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": f"特朗普最新发言如下：\n{post_text}\n请按上述格式分析。"
                        }
                    ],
                    temperature=temperature
                )
                
                # 解析AI响应
                ai_content = response.choices[0].message.content
                parsed_result = self._parse_ai_response(ai_content)
                
                if parsed_result:
                    return parsed_result
                else:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        time.sleep(10 * retry_count)  # 指数退避
                    continue
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if retry_count <= self.max_retries:
                    wait_time = 10 * retry_count  # 指数退避: 10s, 20s, 40s
                    time.sleep(wait_time)
        
        logger.error(f"❌ AI分析失败: {last_error}")
        return None
    
    def _parse_ai_response(self, ai_content: str) -> Optional[Dict]:
        """
        解析AI返回的文本内容
        
        预期格式：
        【主题】：xxx
        【情绪】：xxx
        【股市潜在影响】：xxx
        【总结】：xxx，利好/利空，★★★★☆
        """
        try:
            result = {
                'theme': '',
                'emotion': '',
                'market_impact': '',
                'summary': '',
                'rating_stars': 3,  # 默认3星
                'is_bullish': None,  # True=利好, False=利空, None=中性
                'confidence': 'medium',
                'raw_response': ai_content
            }
            
            # 解析各个字段
            lines = ai_content.split('\n')
            for line in lines:
                line = line.strip()
                
                if '【主题】' in line or '主题：' in line:
                    result['theme'] = line.split('】')[-1].strip().lstrip('：:').strip()
                
                elif '【情绪】' in line or '情绪：' in line:
                    result['emotion'] = line.split('】')[-1].strip().lstrip('：:').strip()
                
                elif '【股市潜在影响】' in line or '股市潜在影响：' in line:
                    result['market_impact'] = line.split('】')[-1].strip().lstrip('：:').strip()
                
                elif '【总结】' in line or '总结：' in line:
                    summary_text = line.split('】')[-1].strip().lstrip('：:').strip()
                    result['summary'] = summary_text
                    
                    # 判断利好/利空
                    if '利好' in summary_text:
                        result['is_bullish'] = True
                    elif '利空' in summary_text:
                        result['is_bullish'] = False
                    else:
                        result['is_bullish'] = None
                    
                    # 提取星级（统计★数量）
                    star_count = summary_text.count('★') + summary_text.count('⭐')
                    if star_count > 0:
                        result['rating_stars'] = min(star_count, 5)
            
            # 验证必填字段
            if not result['theme'] or not result['emotion']:
                return None
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 解析AI响应失败: {e}")
            return None
    
    def analyze_single_post(self, post_id: str, post_data: Dict) -> bool:
        """
        分析单条帖子
        
        Args:
            post_id: 帖子ID
            post_data: 帖子数据
            
        Returns:
            是否成功
        """
        try:
            # 检查是否已分析
            if post_id in self.analyses:
                return True
            
            post_text = post_data.get('text', '')
            if not post_text:
                return False
            
            # 🆕 检查是否为低质量帖子
            is_low_quality, reason = self._is_low_quality_post(post_text)
            if is_low_quality:
                return False
            
            # 调用AI分析
            analysis_result = self.analyze_post_with_ai(post_text)
            
            if analysis_result:
                # 检测是否为高风险帖子
                is_high_risk = self.is_high_risk_post(post_text)
                
                # 保存分析结果
                self.analyses[post_id] = {
                    'post_id': post_id,
                    'post_text': post_text,
                    'post_url': post_data.get('url', ''),
                    'post_timestamp': post_data.get('timestamp', ''),
                    'is_high_risk': is_high_risk,  # 标记是否为高风险帖子
                    'analysis': analysis_result,
                    'analyzed_at': datetime.now().isoformat(),
                    'retry_count': 0
                }
                
                self.stats['success_count'] += 1
                self.stats['last_analysis_time'] = datetime.now().isoformat()
                
                risk_label = "⚠️高风险" if is_high_risk else "常规"
                logger.info(f"✅ [{risk_label}] {analysis_result['theme'][:30]} | {'利好' if analysis_result['is_bullish'] else '利空' if analysis_result['is_bullish'] is False else '中性'}{'★' * analysis_result['rating_stars']}")
                
                return True
            else:
                self.stats['error_count'] += 1
                return False
                
        except Exception as e:
            self.stats['error_count'] += 1
            logger.error(f"❌ 分析帖子 {post_id} 时出错: {e}")
            return False
    
    def batch_analyze_all_posts(self):
        """批量分析所有帖子（初始化模式）"""
        # 加载帖子
        posts = self.load_posts()
        if not posts:
            return
        
        total_posts = len(posts)
        analyzed_count = 0
        
        # 按时间倒序排列（最新的先分析）
        sorted_posts = sorted(
            posts.items(),
            key=lambda x: x[1].get('timestamp', ''),
            reverse=True
        )
        
        for i, (post_id, post_data) in enumerate(sorted_posts, 1):
            try:
                # 检查是否已分析
                if post_id in self.analyses:
                    continue
                
                # 分析帖子
                success = self.analyze_single_post(post_id, post_data)
                
                if success:
                    analyzed_count += 1
                    # 立即保存（防止中断导致数据丢失）
                    self.save_analyses()
                    
                    # ✅ 只有成功分析（调用了API）才需要等待
                    if i < total_posts:
                        time.sleep(self.rate_limit_seconds)
                
            except KeyboardInterrupt:
                self.save_analyses()
                break
            except Exception as e:
                logger.error(f"❌ 处理帖子 {post_id} 时出错: {e}")
        
        # 最终保存
        self.save_analyses()
    
    def monitor_and_analyze_new_posts(self, check_interval: int = 60):
        """
        监控并分析新帖子（持续运行模式）
        
        Args:
            check_interval: 检查间隔（秒）
        """
        try:
            while True:
                # 加载最新的帖子数据
                posts = self.load_posts()
                
                # 检查是否有新帖子
                new_posts = []
                for post_id, post_data in posts.items():
                    if post_id not in self.analyses:
                        new_posts.append((post_id, post_data))
                
                if new_posts:
                    # 分析新帖子
                    for post_id, post_data in new_posts:
                        success = self.analyze_single_post(post_id, post_data)
                        if success:
                            self.save_analyses()
                        
                        # API速率限制
                        if len(new_posts) > 1:
                            time.sleep(self.rate_limit_seconds)
                
                # 等待下一次检查
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.save_analyses()
        except Exception as e:
            logger.error(f"❌ 监控出错: {e}")
            self.save_analyses()
    
    def get_all_analyses(self) -> List[Dict]:
        """获取所有分析结果（按时间倒序）"""
        analyses_list = list(self.analyses.values())
        analyses_list.sort(key=lambda x: x.get('post_timestamp', ''), reverse=True)
        return analyses_list
    
    def get_analysis_by_id(self, post_id: str) -> Optional[Dict]:
        """根据ID获取分析结果"""
        return self.analyses.get(post_id)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.analyses:
            return {
                'total_analyzed': 0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0,
                'high_risk_count': 0,
                'average_rating': 0,
                'emotion_distribution': {},
                'last_updated': None
            }
        
        analyses_list = list(self.analyses.values())
        
        # 统计利好/利空/中性
        bullish_count = sum(1 for a in analyses_list if a['analysis'].get('is_bullish') is True)
        bearish_count = sum(1 for a in analyses_list if a['analysis'].get('is_bullish') is False)
        neutral_count = len(analyses_list) - bullish_count - bearish_count
        
        # 统计高风险帖子数量
        high_risk_count = sum(1 for a in analyses_list if a.get('is_high_risk', False))
        
        # 计算平均星级
        total_stars = sum(a['analysis'].get('rating_stars', 3) for a in analyses_list)
        average_rating = total_stars / len(analyses_list) if analyses_list else 0
        
        # 情绪分布
        emotion_distribution = {}
        for analysis in analyses_list:
            emotion = analysis['analysis'].get('emotion', '未知')
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
        
        # 获取最新更新时间
        timestamps = [a.get('analyzed_at') for a in analyses_list if a.get('analyzed_at')]
        last_updated = max(timestamps) if timestamps else None
        
        return {
            'total_analyzed': len(analyses_list),
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'high_risk_count': high_risk_count,  # 新增：高风险帖子数量
            'high_risk_percentage': round(high_risk_count / len(analyses_list) * 100, 2) if analyses_list else 0,
            'average_rating': round(average_rating, 2),
            'emotion_distribution': emotion_distribution,
            'last_updated': last_updated,
            'success_rate': round(self.stats['success_count'] / max(self.stats['total_analyzed'], 1) * 100, 2) if self.stats['total_analyzed'] > 0 else 0
        }


# 全局单例实例
_analyzer_instance = None


def get_analyzer() -> TrumpSentimentAnalyzer:
    """获取分析器单例"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = TrumpSentimentAnalyzer()
    return _analyzer_instance


# 命令行测试
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='特朗普帖子情绪分析器')
    parser.add_argument('--mode', choices=['init', 'monitor', 'stats'], 
                       default='init',
                       help='运行模式：init(初始化分析), monitor(监控新帖), stats(查看统计)')
    parser.add_argument('--interval', type=int, default=60,
                       help='API调用间隔（秒），默认60秒')
    
    args = parser.parse_args()
    
    analyzer = TrumpSentimentAnalyzer(rate_limit_seconds=args.interval)
    
    if args.mode == 'init':
        analyzer.batch_analyze_all_posts()
    elif args.mode == 'monitor':
        analyzer.monitor_and_analyze_new_posts()
    elif args.mode == 'stats':
        stats = analyzer.get_statistics()
        print("\n" + "=" * 60)
        print("📊 统计信息")
        print("=" * 60)
        print(f"总分析数: {stats['total_analyzed']}")
        print(f"利好: {stats['bullish_count']} ({stats['bullish_count']/max(stats['total_analyzed'],1)*100:.1f}%)")
        print(f"利空: {stats['bearish_count']} ({stats['bearish_count']/max(stats['total_analyzed'],1)*100:.1f}%)")
        print(f"中性: {stats['neutral_count']} ({stats['neutral_count']/max(stats['total_analyzed'],1)*100:.1f}%)")
        print(f"平均星级: {stats['average_rating']}/5")
        print(f"最后更新: {stats['last_updated']}")
        print("=" * 60)
        print("\n情绪分布:")
        for emotion, count in sorted(stats['emotion_distribution'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {emotion}: {count}")
        print("=" * 60)


