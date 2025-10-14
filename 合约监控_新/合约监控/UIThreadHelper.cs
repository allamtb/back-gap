using System;
using System.Windows.Forms;

namespace FuturesTradeViewer
{
    /// <summary>
    /// UI 线程调用辅助类
    /// 提供线程安全的 UI 更新方法
    /// </summary>
    public static class UIThreadHelper
    {
        /// <summary>
        /// 安全地在 UI 线程上同步执行操作
        /// </summary>
        /// <param name="control">UI 控件</param>
        /// <param name="action">要执行的操作</param>
        public static void SafeInvoke(Control control, Action action)
        {
            if (control == null || action == null)
                return;

            try
            {
                if (control.IsDisposed || !control.IsHandleCreated)
                    return;

                if (control.InvokeRequired)
                {
                    control.Invoke(action);
                }
                else
                {
                    action();
                }
            }
            catch (ObjectDisposedException)
            {
                // 控件已释放，忽略
            }
            catch (InvalidOperationException)
            {
                // 控件句柄无效，忽略
            }
        }

        /// <summary>
        /// 安全地在 UI 线程上异步执行操作（不阻塞调用线程）
        /// </summary>
        /// <param name="control">UI 控件</param>
        /// <param name="action">要执行的操作</param>
        public static void SafeBeginInvoke(Control control, Action action)
        {
            if (control == null || action == null)
                return;

            try
            {
                if (control.IsDisposed || !control.IsHandleCreated)
                    return;

                if (control.InvokeRequired)
                {
                    control.BeginInvoke(action);
                }
                else
                {
                    action();
                }
            }
            catch (ObjectDisposedException)
            {
                // 控件已释放，忽略
            }
            catch (InvalidOperationException)
            {
                // 控件句柄无效，忽略
            }
        }

        /// <summary>
        /// 安全地在 UI 线程上异步执行操作，并在执行前再次检查控件状态
        /// </summary>
        /// <param name="control">UI 控件</param>
        /// <param name="action">要执行的操作</param>
        public static void SafeBeginInvokeWithCheck(Control control, Action action)
        {
            if (control == null || action == null)
                return;

            SafeBeginInvoke(control, () =>
            {
                // 在 UI 线程中再次检查控件状态
                if (control.IsDisposed || !control.IsHandleCreated)
                    return;

                try
                {
                    action();
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"UI 更新错误: {ex.Message}");
                }
            });
        }
    }
}

