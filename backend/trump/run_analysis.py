#!/usr/bin/env python3
"""
运行情感分析脚本 - 删除旧结果并重新分析
"""

import os
import json
from pathlib import Path

def main():
    # 删除旧的分析结果文件（如果存在）
    files_to_delete = [
        'sentiment_analysis.json',
        'sentiment_analysis_backup.json',
    ]
    
    print("🗑️  删除旧的分析结果文件...")
    for filename in files_to_delete:
        filepath = Path(__file__).parent / filename
        if filepath.exists():
            filepath.unlink()
            print(f"   ✓ 已删除: {filename}")
        else:
            print(f"   - 不存在: {filename}")
    
    print("\n📊 开始重新分析...")
    print("=" * 60)
    
    # 导入并运行分析器
    from sentiment_analyzer import main as analyze_main
    analyze_main()
    
    print("\n" + "=" * 60)
    print("✅ 分析完成！")

if __name__ == "__main__":
    main()

