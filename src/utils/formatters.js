/**
 * 格式化工具函数
 * 直接展示后端返回的原始数据，不做任何精度处理
 */

/**
 * 直接返回原始价格（不做任何格式化，后端给什么就展示什么）
 * @param {number|string} price - 价格值
 * @returns {string|number} 原始价格
 */
export function formatPrice(price) {
  if (price === null || price === undefined || price === '' || price === '-') {
    return '-';
  }
  // 直接返回原始值，不做任何处理
  return price;
}

/**
 * 直接返回原始数量（不做任何格式化）
 * @param {number|string} amount - 数量值
 * @returns {string|number} 原始数量
 */
export function formatAmount(amount) {
  if (amount === null || amount === undefined || amount === '' || amount === '-') {
    return '-';
  }
  // 直接返回原始值，不做任何处理
  return amount;
}

/**
 * 格式化百分比（只添加%符号和正负号，不改变精度）
 * @param {number} value - 百分比值
 * @returns {string} 带%符号的百分比
 */
export function formatPercent(value) {
  if (value === null || value === undefined || isNaN(value)) {
    return '-';
  }
  
  const sign = value > 0 ? '+' : '';
  return `${sign}${value}%`; // 只添加符号，保持后端返回的原始精度
}

/**
 * 格式化货币（USDT） - 直接显示原始值
 * @param {number} value - 金额
 * @returns {string} 格式化后的货币字符串
 */
export function formatCurrency(value) {
  if (value === null || value === undefined || value === '' || isNaN(value)) {
    return '-';
  }

  const sign = value < 0 ? '-' : '';
  const absValue = Math.abs(value);
  
  return `${sign}$${absValue}`; // 直接展示原始金额
}

/**
 * 格式化大数字（带千分位）- 保持原始精度
 * @param {number} value - 数值
 * @returns {string} 格式化后的字符串
 */
export function formatLargeNumber(value) {
  if (value === null || value === undefined || value === '' || isNaN(value)) {
    return '-';
  }

  // 使用浏览器原生的格式化，保持原始精度
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 20, // 支持最多20位小数
  }).format(value);
}

/**
 * 精确计算两个数字的差值（避免浮点数精度问题）
 * 使用字符串运算来保证精度
 * @param {number|string} num1 - 被减数
 * @param {number|string} num2 - 减数
 * @returns {string|number} 精确的差值
 */
export function preciseSubtract(num1, num2) {
  if (num1 == null || num2 == null) return '-';
  
  try {
    // 转换为字符串
    const str1 = String(num1);
    const str2 = String(num2);
    
    // 转换为整数运算（避免浮点数问题）
    const parts1 = str1.split('.');
    const parts2 = str2.split('.');
    
    // 获取最大小数位数
    const decimals1 = parts1[1]?.length || 0;
    const decimals2 = parts2[1]?.length || 0;
    const maxDecimals = Math.max(decimals1, decimals2);
    
    // 转换为整数
    const multiplier = Math.pow(10, maxDecimals);
    const int1 = Math.round(parseFloat(str1) * multiplier);
    const int2 = Math.round(parseFloat(str2) * multiplier);
    
    // 整数相减
    const result = int1 - int2;
    
    // 转换回小数
    const finalResult = result / multiplier;
    
    // 返回原始精度的结果
    return finalResult;
  } catch (error) {
    console.error('精确减法计算失败:', error);
    return '-';
  }
}

/**
 * 精确计算数组求和（避免浮点数精度问题）
 * 使用整数运算来保证精度
 * @param {Array<number|string>} numbers - 数字数组
 * @returns {string|number} 精确的总和
 */
export function preciseSum(numbers) {
  if (!Array.isArray(numbers) || numbers.length === 0) return 0;
  
  try {
    // 过滤掉无效值
    const validNumbers = numbers.filter(n => n != null && n !== '');
    if (validNumbers.length === 0) return 0;
    
    // 找出所有数字的最大小数位数
    let maxDecimals = 0;
    const strings = validNumbers.map(num => {
      const str = String(num);
      const parts = str.split('.');
      const decimals = parts[1]?.length || 0;
      maxDecimals = Math.max(maxDecimals, decimals);
      return str;
    });
    
    // 转换为整数并累加
    const multiplier = Math.pow(10, maxDecimals);
    const sum = strings.reduce((total, str) => {
      const intValue = Math.round(parseFloat(str) * multiplier);
      return total + intValue;
    }, 0);
    
    // 转换回小数
    const finalResult = sum / multiplier;
    
    return finalResult;
  } catch (error) {
    console.error('精确求和计算失败:', error);
    return 0;
  }
}
