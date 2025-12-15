import { useState, useCallback, useEffect, useRef } from 'react';

/**
 * 可拖动抽屉的 resize hook
 * @param {Object} options - 配置选项
 * @param {string} options.storageKey - localStorage 键名（用于保存宽度）
 * @param {number} options.defaultWidth - 默认宽度（默认 300）
 * @param {number} options.minWidth - 最小宽度（默认 80）
 * @param {number} options.maxWidth - 最大宽度（默认 300）
 * @param {number} options.siderWidth - Sider 宽度（默认 200）
 * @returns {Object} { drawerWidth, isResizing, resizeRef, startResizing, stopResizing }
 */
export function useDrawerResize({
  storageKey = 'drawer_width',
  defaultWidth = 300,
  minWidth = 80,
  maxWidth = 300,
  siderWidth = 200
} = {}) {
  const [drawerWidth, setDrawerWidth] = useState(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const width = parseInt(saved);
        if (!isNaN(width)) {
          return Math.max(minWidth, Math.min(width, maxWidth));
        }
      }
    } catch (error) {
      console.error('加载抽屉宽度失败:', error);
    }
    return Math.max(minWidth, Math.min(defaultWidth, maxWidth));
  });

  const [isResizing, setIsResizing] = useState(false);
  const resizeRef = useRef(null);

  // 保存宽度到 localStorage
  useEffect(() => {
    try {
      localStorage.setItem(storageKey, drawerWidth.toString());
    } catch (error) {
      console.error('保存抽屉宽度失败:', error);
    }
  }, [drawerWidth, storageKey]);

  const startResizing = useCallback(() => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e) => {
    if (isResizing) {
      // 计算相对于内容区的位置（减去 Sider 宽度）
      const newWidth = e.clientX - siderWidth;
      // 允许双向拖动，限制在最小和最大宽度之间
      const clampedWidth = Math.max(minWidth, Math.min(newWidth, maxWidth));
      setDrawerWidth(clampedWidth);
    }
  }, [isResizing, siderWidth, minWidth, maxWidth]);

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize);
      window.addEventListener('mouseup', stopResizing);
    } else {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    }
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  return {
    drawerWidth,
    isResizing,
    resizeRef,
    startResizing,
    stopResizing
  };
}


