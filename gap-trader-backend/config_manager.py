"""
配置管理模块 - 使用 JSON 文件存储配置
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from datetime import datetime

class ConfigManager:
    def __init__(self, config_path: str = "data/config.json"):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认 data/config.json
        """
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / "backups"
        
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Optional[Dict]:
        """
        加载配置文件
        
        Returns:
            配置字典，如果文件不存在返回 None
        """
        if not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
        except Exception as e:
            raise RuntimeError(f"读取配置文件失败: {e}")
    
    def save_config(self, config: Dict, create_backup: bool = True) -> None:
        """
        保存配置（全量替换）
        
        Args:
            config: 配置字典，格式: { "accounts": [...] }
            create_backup: 是否创建备份，默认 True
        """
        # 验证数据结构
        self._validate_config(config)
        
        # 如果配置文件已存在，先备份
        if create_backup and self.config_path.exists():
            self._create_backup()
        
        # 写入新配置（全量替换）
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存配置文件失败: {e}")
    
    def _validate_config(self, config: Dict) -> None:
        """
        验证配置数据结构
        
        Args:
            config: 配置字典
            
        Raises:
            ValueError: 数据格式错误
        """
        if not isinstance(config, dict):
            raise ValueError("配置必须是字典类型")
        
        if "accounts" not in config:
            raise ValueError("配置必须包含 'accounts' 字段")
        
        if not isinstance(config["accounts"], list):
            raise ValueError("'accounts' 必须是数组类型")
        
        # 验证每个账户
        account_names = set()
        for i, account in enumerate(config["accounts"]):
            if not isinstance(account, dict):
                raise ValueError(f"账户 {i} 必须是对象类型")
            
            # 必须有 name
            if "name" not in account or not account["name"]:
                raise ValueError(f"账户 {i} 缺少 'name' 字段")
            
            # 账户名不能重复
            if account["name"] in account_names:
                raise ValueError(f"账户名 '{account['name']}' 重复")
            account_names.add(account["name"])
            
            # 必须有 exchanges
            if "exchanges" not in account:
                raise ValueError(f"账户 '{account['name']}' 缺少 'exchanges' 字段")
            
            if not isinstance(account["exchanges"], list):
                raise ValueError(f"账户 '{account['name']}' 的 'exchanges' 必须是数组")
            
            # 验证每个交易所配置
            exchange_names = set()
            for j, exchange in enumerate(account["exchanges"]):
                if not isinstance(exchange, dict):
                    raise ValueError(f"账户 '{account['name']}' 的交易所 {j} 必须是对象类型")
                
                # 必需字段
                required_fields = ["exchange", "apiKey", "apiSecret"]
                for field in required_fields:
                    if field not in exchange or not exchange[field]:
                        raise ValueError(
                            f"账户 '{account['name']}' 的交易所 {j} 缺少 '{field}' 字段"
                        )
                
                # 同一账户下交易所不能重复
                ex_name = exchange["exchange"]
                if ex_name in exchange_names:
                    raise ValueError(
                        f"账户 '{account['name']}' 下交易所 '{ex_name}' 重复配置"
                    )
                exchange_names.add(ex_name)
    
    def _create_backup(self) -> None:
        """
        创建配置备份
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"config_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.config_path, backup_path)
            
            # 只保留最近 10 个备份
            self._cleanup_old_backups(keep=10)
        except Exception as e:
            print(f"警告: 创建备份失败: {e}")
    
    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """
        清理旧备份文件
        
        Args:
            keep: 保留最近几个备份，默认 10
        """
        backups = sorted(self.backup_dir.glob("config_backup_*.json"))
        
        if len(backups) > keep:
            for backup in backups[:-keep]:
                try:
                    backup.unlink()
                except Exception as e:
                    print(f"警告: 删除旧备份失败 {backup}: {e}")
    
    def get_account_exchanges(self, account_name: str) -> List[str]:
        """
        获取指定账户下配置的交易所列表
        
        Args:
            account_name: 账户名称
            
        Returns:
            该账户下的交易所名称列表
            
        Raises:
            ValueError: 账户不存在
        """
        config = self.load_config()
        
        if config is None:
            raise ValueError("配置文件不存在")
        
        # 查找指定账户
        for account in config.get("accounts", []):
            if account.get("name") == account_name:
                # 返回该账户下的交易所列表
                exchanges = [
                    ex.get("exchange") 
                    for ex in account.get("exchanges", [])
                    if ex.get("exchange")
                ]
                return exchanges
        
        # 账户不存在
        raise ValueError(f"账户 '{account_name}' 不存在")
    
    def get_all_accounts(self) -> List[Dict]:
        """
        获取所有账户信息（不包含敏感的API密钥）
        
        Returns:
            账户列表，每个账户包含 name 和 exchanges 列表
        """
        config = self.load_config()
        
        if config is None:
            return []
        
        accounts = []
        for account in config.get("accounts", []):
            accounts.append({
                "name": account.get("name"),
                "exchanges": [
                    ex.get("exchange") 
                    for ex in account.get("exchanges", [])
                    if ex.get("exchange")
                ]
            })
        
        return accounts


# ===== 使用示例 =====

if __name__ == "__main__":
    # 创建配置管理器
    manager = ConfigManager("data/config.json")
    
    # 示例配置数据
    example_config = {
        "accounts": [
            {
                "name": "主账户",
                "exchanges": [
                    {
                        "exchange": "binance",
                        "apiKey": "binance_api_key_here",
                        "apiSecret": "binance_api_secret_here"
                    },
                    {
                        "exchange": "bybit",
                        "apiKey": "bybit_api_key_here",
                        "apiSecret": "bybit_api_secret_here"
                    }
                ]
            },
            {
                "name": "备用账户",
                "exchanges": [
                    {
                        "exchange": "okx",
                        "apiKey": "okx_api_key_here",
                        "apiSecret": "okx_api_secret_here"
                    }
                ]
            }
        ]
    }
    
    # 保存配置
    try:
        manager.save_config(example_config)
        print("✅ 配置保存成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
    
    # 加载配置
    config = manager.load_config()
    if config:
        print(f"✅ 加载配置成功，共 {len(config['accounts'])} 个账户")
        for acc in config['accounts']:
            print(f"  - {acc['name']}: {len(acc['exchanges'])} 个交易所")
    else:
        print("⚠️  配置文件不存在")
    
    # 获取所有账户
    accounts = manager.get_all_accounts()
    print(f"✅ 所有账户: {accounts}")
    
    # 获取指定账户的交易所
    try:
        exchanges = manager.get_account_exchanges("主账户")
        print(f"✅ '主账户' 的交易所: {', '.join(exchanges)}")
    except ValueError as e:
        print(f"❌ {e}")

