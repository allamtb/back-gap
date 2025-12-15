#!/usr/bin/env python3
"""
存档器快速测试脚本
用于测试帖子存档功能是否正常工作
"""

from post_archiver import TrumpPostArchiver


def test_archiver():
    """测试存档器功能"""
    print("\n" + "=" * 60)
    print("🧪 存档器功能测试")
    print("=" * 60)
    
    # 创建存档器实例
    print("\n1️⃣ 创建存档器实例...")
    archiver = TrumpPostArchiver()
    print("✅ 存档器实例创建成功")
    
    # 测试RSS Feed获取
    print("\n2️⃣ 测试RSS Feed获取...")
    feed = archiver.fetch_rss_feed()
    if feed:
        print(f"✅ RSS Feed获取成功")
        print(f"   - Feed标题: {feed.feed.get('title', '未知')}")
        print(f"   - 条目数量: {len(feed.entries)}")
    else:
        print("❌ RSS Feed获取失败")
        return
    
    # 测试数据提取
    print("\n3️⃣ 测试数据提取...")
    if feed.entries:
        post_data = archiver.extract_post_data(feed.entries[0])
        if post_data:
            print("✅ 数据提取成功")
            print(f"   - 帖子ID: {post_data['id']}")
            print(f"   - 时间戳: {post_data.get('timestamp', '未知')}")
            print(f"   - 内容长度: {post_data['character_count']} 字符")
            print(f"   - 是否转发: {post_data.get('is_retweet')}")
        else:
            print("❌ 数据提取失败")
            return
    
    # 测试存档功能
    print("\n4️⃣ 测试存档功能...")
    new_count = archiver.fetch_and_archive_all()
    print(f"✅ 存档完成，新增 {new_count} 条帖子")
    
    # 测试统计功能
    print("\n5️⃣ 测试统计功能...")
    stats = archiver.get_statistics()
    print("✅ 统计信息获取成功")
    print(f"   - 总帖子数: {stats['total_posts']}")
    print(f"   - 原创帖子: {stats['original_posts']}")
    print(f"   - 转发帖子: {stats['retweets']}")
    print(f"   - 平均长度: {stats['average_length']:.0f} 字符")
    
    # 测试查询功能
    print("\n6️⃣ 测试查询功能...")
    all_posts = archiver.get_all_posts()
    print(f"✅ 获取所有帖子成功: {len(all_posts)} 条")
    
    if all_posts:
        # 显示最新的3条帖子
        print("\n📝 最新的3条帖子:")
        for i, post in enumerate(all_posts[:3], 1):
            print(f"\n   {i}. [{post['id']}] {post.get('timestamp', '未知')}")
            print(f"      {post['text'][:80]}...")
    
    # 测试搜索功能
    print("\n7️⃣ 测试搜索功能...")
    test_keywords = ["President", "America", "MAGA"]
    for keyword in test_keywords:
        results = archiver.search_posts(keyword)
        print(f"   - 搜索 '{keyword}': 找到 {len(results)} 条结果")
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
    print("\n📊 测试总结:")
    print(f"   ✅ RSS Feed获取: 正常")
    print(f"   ✅ 数据提取: 正常")
    print(f"   ✅ 存档功能: 正常")
    print(f"   ✅ 统计功能: 正常")
    print(f"   ✅ 查询功能: 正常")
    print(f"   ✅ 搜索功能: 正常")
    print("\n💡 提示:")
    print(f"   - 存档文件位置: {archiver.archive_file}")
    print(f"   - 日志文件位置: post_archiver.log")
    print(f"   - 当前存档帖子数: {len(archiver.posts_dict)}")
    print("\n🚀 你现在可以使用以下命令:")
    print("   python run_archive.py          # 交互式菜单")
    print("   python post_archiver.py --mode monitor --interval 30  # 实时监控")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        test_archiver()
    except KeyboardInterrupt:
        print("\n\n⛔ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()



