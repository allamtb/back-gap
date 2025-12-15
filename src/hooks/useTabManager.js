import { useState, useEffect, useRef } from 'react';
import { message } from 'antd';

/**
 * Tab 管理 hook
 * @param {Object} options - 配置选项
 * @param {string} options.storageKey - localStorage 键名
 * @param {Function} options.generateTabLabel - 生成 Tab 标签的函数
 * @param {Array} options.defaultExchanges - 默认交易所配置
 * @param {number} options.maxTabs - 最大 Tab 数量（默认 10）
 * @returns {Object} Tab 管理相关的状态和方法
 */
export function useTabManager({
  storageKey,
  generateTabLabel,
  defaultExchanges = [],
  maxTabs = 10
}) {
  // 加载保存的 Tab 配置
  const loadTabsFromStorage = () => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // 兼容旧配置：为没有 market_type 的交易所添加默认值 'spot'
          const migratedTabs = parsed.map(tab => ({
            ...tab,
            exchanges: (tab.exchanges || []).map(ex => ({
              ...ex,
              market_type: ex.market_type || 'spot'
            }))
          }));
          return migratedTabs;
        }
      }
    } catch (error) {
      console.error('加载 Tab 配置失败:', error);
    }
    // 返回默认配置
    return [{
      key: '1',
      label: generateTabLabel(defaultExchanges),
      exchanges: [...defaultExchanges]
    }];
  };

  // 保存 Tab 配置到 localStorage
  const saveTabsToStorage = (tabs) => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(tabs));
    } catch (error) {
      console.error('保存 Tab 配置失败:', error);
    }
  };

  const [tabs, setTabs] = useState(() => loadTabsFromStorage());
  const [activeKey, setActiveKey] = useState(() => {
    const savedTabs = loadTabsFromStorage();
    return savedTabs[0]?.key || '1';
  });
  const [editingKey, setEditingKey] = useState(null);
  const [editingLabel, setEditingLabel] = useState('');
  const newTabIndex = useRef(Math.max(...tabs.map(t => parseInt(t.key) || 0)) + 1);
  const inputRef = useRef(null);

  // 保存 Tab 配置到 localStorage
  useEffect(() => {
    saveTabsToStorage(tabs);
  }, [tabs, storageKey]);

  // 编辑 Tab 名称时自动聚焦
  useEffect(() => {
    if (editingKey && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingKey]);

  // 添加新 Tab
  const addTab = () => {
    if (tabs.length >= maxTabs) {
      message.warning(`最多只能创建 ${maxTabs} 个面板`);
      return;
    }

    const newKey = String(newTabIndex.current);
    const newTab = {
      key: newKey,
      label: generateTabLabel(defaultExchanges),
      exchanges: [...defaultExchanges]
    };

    setTabs([...tabs, newTab]);
    setActiveKey(newKey);
    newTabIndex.current++;
    message.success('已创建新的面板');
  };

  // 删除 Tab
  const removeTab = (targetKey) => {
    if (tabs.length <= 1) {
      message.warning('至少需要保留一个面板');
      return;
    }

    const targetIndex = tabs.findIndex(tab => tab.key === targetKey);
    const newTabs = tabs.filter(tab => tab.key !== targetKey);

    // 如果删除的是当前激活的 Tab，切换到相邻的 Tab
    if (targetKey === activeKey) {
      const newActiveKey = newTabs[targetIndex === 0 ? 0 : targetIndex - 1]?.key;
      setActiveKey(newActiveKey);
    }

    setTabs(newTabs);
    message.success('已删除面板');
  };

  // 处理 Tab 编辑（添加/删除）
  const onEdit = (targetKey, action) => {
    if (action === 'add') {
      addTab();
    } else if (action === 'remove') {
      removeTab(targetKey);
    }
  };

  // 开始编辑 Tab 名称
  const startEdit = (key, currentLabel) => {
    setEditingKey(key);
    setEditingLabel(currentLabel);
  };

  // 完成编辑 Tab 名称
  const finishEdit = () => {
    if (editingKey && editingLabel.trim()) {
      setTabs(tabs.map(tab => 
        tab.key === editingKey 
          ? { ...tab, label: editingLabel.trim() }
          : tab
      ));
    }
    setEditingKey(null);
    setEditingLabel('');
  };

  // 取消编辑
  const cancelEdit = () => {
    setEditingKey(null);
    setEditingLabel('');
  };

  // 更新当前 Tab 的交易所配置
  const updateCurrentTabExchanges = (newExchanges) => {
    setTabs(tabs.map(tab => {
      if (tab.key === activeKey) {
        // 自动更新 Tab 名称（如果用户没有自定义过）
        const newLabel = generateTabLabel(newExchanges);
        return {
          ...tab,
          exchanges: newExchanges,
          label: tab.customLabel || newLabel // 如果有自定义标签则保留
        };
      }
      return tab;
    }));
  };

  // 获取当前激活 Tab 的配置
  const currentTab = tabs.find(tab => tab.key === activeKey);
  const currentExchanges = currentTab?.exchanges || defaultExchanges;

  return {
    tabs,
    setTabs,
    activeKey,
    setActiveKey,
    editingKey,
    editingLabel,
    setEditingLabel,
    inputRef,
    newTabIndex,
    addTab,
    removeTab,
    onEdit,
    startEdit,
    finishEdit,
    cancelEdit,
    updateCurrentTabExchanges,
    currentTab,
    currentExchanges
  };
}


