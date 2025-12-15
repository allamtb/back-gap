#!/usr/bin/env python3
"""
测试文件路径配置
验证 post_archiver 和 sentiment_analyzer 使用相同的文件路径
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from trump.post_archiver import TrumpPostArchiver
from trump.sentiment_analyzer import TrumpSentimentAnalyzer

def test_file_paths():
    """测试文件路径是否一致"""
    print("=" * 80)
    print("🔍 测试文件路径配置")
    print("=" * 80)
    
    # 初始化存档器
    print("\n1️⃣ 初始化帖子存档器...")
    archiver = TrumpPostArchiver()
    
    # 初始化分析器
    print("\n2️⃣ 初始化情绪分析器...")
    analyzer = TrumpSentimentAnalyzer()
    
    # 比较路径
    print("\n" + "=" * 80)
    print("📊 路径比较结果")
    print("=" * 80)
    
    print(f"\n存档器的帖子文件路径：")
    print(f"  {archiver.archive_file}")
    
    print(f"\n分析器的帖子文件路径：")
    print(f"  {analyzer.posts_file}")
    
    print(f"\n分析器的结果文件路径：")
    print(f"  {analyzer.output_file}")
    
    # 验证是否一致
    if archiver.archive_file == analyzer.posts_file:
        print("\n✅ 路径配置一致！两个模块使用相同的文件路径。")
    else:
        print("\n❌ 路径配置不一致！")
        print(f"   存档器: {archiver.archive_file}")
        print(f"   分析器: {analyzer.posts_file}")
    
    # 检查文件是否存在
    print("\n" + "=" * 80)
    print("📂 文件存在性检查")
    print("=" * 80)
    
    posts_exists = Path(archiver.archive_file).exists()
    analysis_exists = Path(analyzer.output_file).exists()
    
    print(f"\n帖子存档文件: {'✅ 存在' if posts_exists else '❌ 不存在'}")
    print(f"  {archiver.archive_file}")
    
    print(f"\n分析结果文件: {'✅ 存在' if analysis_exists else '❌ 不存在'}")
    print(f"  {analyzer.output_file}")
    
    if posts_exists:
        import json
        with open(archiver.archive_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n  📊 帖子总数: {data.get('total_posts', 0)}")
            print(f"  📅 最后更新: {data.get('last_updated', '未知')}")
    
    if analysis_exists:
        import json
        with open(analyzer.output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"\n  📊 分析总数: {data.get('total_analyzed', 0)}")
            print(f"  📅 最后更新: {data.get('last_updated', '未知')}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_file_paths()

