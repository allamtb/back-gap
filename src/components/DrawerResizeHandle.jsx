import React from 'react';

/**
 * 可拖动抽屉的手柄组件
 * @param {Object} props
 * @param {React.Ref} props.resizeRef - ref 引用
 * @param {Function} props.onMouseDown - 鼠标按下事件
 * @param {boolean} props.isResizing - 是否正在拖动
 * @param {number} props.drawerWidth - 当前抽屉宽度
 */
export default function DrawerResizeHandle({ resizeRef, onMouseDown, isResizing, drawerWidth }) {
  return (
    <div
      ref={resizeRef}
      onMouseDown={onMouseDown}
      style={{
        width: '8px',
        cursor: 'col-resize',
        backgroundColor: isResizing ? '#1890ff' : '#bfbfbf',
        transition: 'background-color 0.2s',
        position: 'relative',
        flexShrink: 0,
        userSelect: 'none'
      }}
      onMouseEnter={(e) => {
        if (!isResizing) {
          e.currentTarget.style.backgroundColor = '#8c8c8c';
        }
      }}
      onMouseLeave={(e) => {
        if (!isResizing) {
          e.currentTarget.style.backgroundColor = '#bfbfbf';
        }
      }}
    >
      {/* 拖动指示器 */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '4px',
        height: '50px',
        borderLeft: '2px dotted #595959',
        borderRight: '2px dotted #595959',
        pointerEvents: 'none'
      }} />
      {/* 宽度提示（拖动时显示） */}
      {isResizing && (
        <div style={{
          position: 'absolute',
          top: '10px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#1890ff',
          color: '#fff',
          padding: '2px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          whiteSpace: 'nowrap',
          pointerEvents: 'none'
        }}>
          {drawerWidth}px
        </div>
      )}
    </div>
  );
}


