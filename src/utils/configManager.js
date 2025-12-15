/**
 * 交易所配置管理工具
 * 统一管理 localStorage 中的交易所配置
 */

// 本地存储键名
const STORAGE_KEY = "exchangeConfig";

// 统一账户交易所列表（现货和合约共用同一个账户）
const UNIFIED_ACCOUNT_EXCHANGES = ["backpack"];

/**
 * 获取所有交易所配置
 * @returns {Array} 交易所配置数组
 */
export const getExchangeConfig = () => {
  try {
    const configStr = localStorage.getItem(STORAGE_KEY);
    if (!configStr) {
      return [];
    }

    const config = JSON.parse(configStr);
    const exchanges = config.exchanges || [];
    
    // 🔄 向后兼容：为旧配置添加 unifiedAccount 字段
    return exchanges.map((ex) => ({
      ...ex,
      unifiedAccount: ex.unifiedAccount ?? isUnifiedAccountExchange(ex.exchange),
    }));
  } catch (error) {
    console.error("读取交易所配置失败:", error);
    return [];
  }
};

/**
 * 保存交易所配置
 * @param {Array} exchanges - 交易所配置数组
 * @returns {boolean} 是否保存成功
 */
export const saveExchangeConfig = (exchanges) => {
  try {
    const config = { exchanges };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    return true;
  } catch (error) {
    console.error("保存交易所配置失败:", error);
    return false;
  }
};

/**
 * 获取特定交易所的配置
 * @param {string} exchangeName - 交易所名称
 * @returns {Object|null} 交易所配置对象，未找到返回 null
 */
export const getExchangeByName = (exchangeName) => {
  const exchanges = getExchangeConfig();
  return exchanges.find((ex) => ex.exchange === exchangeName) || null;
};

/**
 * 添加新的交易所配置
 * @param {Object} exchangeConfig - 交易所配置对象
 * @returns {boolean} 是否添加成功
 */
export const addExchange = (exchangeConfig) => {
  try {
    const exchanges = getExchangeConfig();
    
    // 检查是否已存在相同的交易所
    const exists = exchanges.some(
      (ex) => ex.exchange === exchangeConfig.exchange
    );
    
    if (exists) {
      console.warn(`交易所 ${exchangeConfig.exchange} 已存在`);
      return false;
    }
    
    exchanges.push(exchangeConfig);
    return saveExchangeConfig(exchanges);
  } catch (error) {
    console.error("添加交易所配置失败:", error);
    return false;
  }
};

/**
 * 更新交易所配置
 * @param {string} exchangeName - 要更新的交易所名称
 * @param {Object} updatedConfig - 更新后的配置对象
 * @returns {boolean} 是否更新成功
 */
export const updateExchange = (exchangeName, updatedConfig) => {
  try {
    const exchanges = getExchangeConfig();
    const index = exchanges.findIndex((ex) => ex.exchange === exchangeName);
    
    if (index === -1) {
      console.warn(`未找到交易所 ${exchangeName}`);
      return false;
    }
    
    exchanges[index] = { ...exchanges[index], ...updatedConfig };
    return saveExchangeConfig(exchanges);
  } catch (error) {
    console.error("更新交易所配置失败:", error);
    return false;
  }
};

/**
 * 删除交易所配置
 * @param {string} exchangeName - 要删除的交易所名称
 * @returns {boolean} 是否删除成功
 */
export const deleteExchange = (exchangeName) => {
  try {
    const exchanges = getExchangeConfig();
    const filtered = exchanges.filter((ex) => ex.exchange !== exchangeName);
    
    if (filtered.length === exchanges.length) {
      console.warn(`未找到交易所 ${exchangeName}`);
      return false;
    }
    
    return saveExchangeConfig(filtered);
  } catch (error) {
    console.error("删除交易所配置失败:", error);
    return false;
  }
};

/**
 * 获取交易所凭证（用于 API 调用）
 * @param {boolean} includeUnifiedAccount - 是否包含 unifiedAccount 字段
 * @returns {Array} 交易所凭证数组
 */
export const getExchangeCredentials = (includeUnifiedAccount = false) => {
  const exchanges = getExchangeConfig();
  return exchanges.map((exchange) => {
    const credentials = {
      exchange: exchange.exchange,
      apiKey: exchange.apiKey,
      apiSecret: exchange.apiSecret,
      password: exchange.password || undefined,
    };
    
    // 如果需要，包含 unifiedAccount 字段
    if (includeUnifiedAccount) {
      credentials.unifiedAccount = exchange.unifiedAccount || false;
    }
    
    return credentials;
  });
};

/**
 * 清除所有配置
 * @returns {boolean} 是否清除成功
 */
export const clearAllConfig = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return true;
  } catch (error) {
    console.error("清除配置失败:", error);
    return false;
  }
};

/**
 * 检查是否有配置
 * @returns {boolean} 是否有配置
 */
export const hasConfig = () => {
  const exchanges = getExchangeConfig();
  return exchanges.length > 0;
};

/**
 * 获取配置的交易所数量
 * @returns {number} 交易所数量
 */
export const getExchangeCount = () => {
  return getExchangeConfig().length;
};

/**
 * 检查交易所是否已配置
 * @param {string} exchangeName - 交易所名称
 * @returns {boolean} 是否已配置
 */
export const isExchangeConfigured = (exchangeName) => {
  if (!exchangeName) return false;
  const exchanges = getExchangeConfig();
  return exchanges.some((ex) => ex.exchange === exchangeName);
};

/**
 * 判断交易所是否为统一账户模式（现货和合约共用账户）
 * @param {string} exchangeName - 交易所名称
 * @returns {boolean} 是否为统一账户
 */
export const isUnifiedAccountExchange = (exchangeName) => {
  if (!exchangeName) return false;
  return UNIFIED_ACCOUNT_EXCHANGES.includes(exchangeName.toLowerCase());
};

/**
 * 获取统一账户交易所列表
 * @returns {Array} 统一账户交易所名称数组
 */
export const getUnifiedAccountExchanges = () => {
  return [...UNIFIED_ACCOUNT_EXCHANGES];
};

