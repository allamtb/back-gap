/**
 * 交易所币种规则配置
 * 
 * 定义不同交易所对于不同市场类型的交易对规则
 * 可以在前端界面进行配置和修改
 */

// 默认规则配置
export const DEFAULT_EXCHANGE_RULES = {
  backpack: {
    spot: {
      quote: 'USDC',      // 计价货币
      separator: '/',     // 分隔符
      suffix: '',         // 后缀
    },
    future: {
      quote: 'USDC',
      separator: '/',
      suffix: '',
    },
  },
  binance: {
    spot: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
    future: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
  },
  okx: {
    spot: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
    future: {
      quote: 'USD',
      separator: '/',
      suffix: '',
    },
  },
  bybit: {
    spot: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
    future: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
  },
  gateio: {
    spot: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
    future: {
      quote: 'USDT',
      separator: '/',
      suffix: '',
    },
  },
  kraken: {
    spot: {
      quote: 'USD',
      separator: '/',
      suffix: '',
    },
    future: {
      quote: 'USD',
      separator: '/',
      suffix: '',
    },
  },
};

// LocalStorage 键名
const STORAGE_KEY = 'gap-dash-exchange-rules';

/**
 * 从 LocalStorage 加载规则
 * 如果没有保存的规则，返回默认规则
 */
export function loadExchangeRules() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      // 合并默认规则和保存的规则（保证新增交易所有默认值）
      return {
        ...DEFAULT_EXCHANGE_RULES,
        ...parsed,
      };
    }
  } catch (error) {
    console.error('加载交易所规则失败:', error);
  }
  return { ...DEFAULT_EXCHANGE_RULES };
}

/**
 * 保存规则到 LocalStorage
 */
export function saveExchangeRules(rules) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(rules));
    return true;
  } catch (error) {
    console.error('保存交易所规则失败:', error);
    return false;
  }
}

/**
 * 重置为默认规则
 */
export function resetExchangeRules() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return { ...DEFAULT_EXCHANGE_RULES };
  } catch (error) {
    console.error('重置交易所规则失败:', error);
    return null;
  }
}

/**
 * 根据币种代码、交易所和市场类型生成完整交易对
 * 
 * @param {string} coin - 币种代码（如 'BTC'）
 * @param {string} exchange - 交易所ID（如 'backpack'）
 * @param {string} marketType - 市场类型（'spot' 或 'future'）
 * @param {object} rules - 规则配置（可选，默认使用加载的规则）
 * @returns {string} 完整交易对（如 'BTC/USDC'）
 * 
 * @example
 * generateSymbol('BTC', 'backpack', 'spot') // => 'BTC/USDC'
 * generateSymbol('ETH', 'binance', 'spot')  // => 'ETH/USDT'
 * generateSymbol('SOL', 'okx', 'future')    // => 'SOL/USD'
 */
export function generateSymbol(coin, exchange, marketType = 'spot', rules = null) {
  const exchangeRules = rules || loadExchangeRules();
  
  const exchangeId = exchange.toLowerCase();
  const marketTypeKey = marketType.toLowerCase();
  const coinUpper = coin.toUpperCase();
  
  // 获取对应的规则
  const rule = exchangeRules[exchangeId]?.[marketTypeKey];
  
  if (!rule) {
    console.warn(`未找到规则: ${exchangeId}.${marketTypeKey}，使用默认 USDT`);
    return `${coinUpper}/USDT`;
  }
  
  const { quote, separator, suffix } = rule;
  
  // 如果分隔符为空，则不添加分隔符（如 btcusdt）
  // 拼接完整交易对: BTC + / + USDC + (空) = BTC/USDC 或 BTC + USDC = BTCUSDC
  const sep = separator || '';
  return `${coinUpper}${sep}${quote}${suffix}`;
}

/**
 * 获取指定交易所和市场类型的规则
 */
export function getExchangeRule(exchange, marketType = 'spot', rules = null) {
  const exchangeRules = rules || loadExchangeRules();
  const exchangeId = exchange.toLowerCase();
  const marketTypeKey = marketType.toLowerCase();
  
  return exchangeRules[exchangeId]?.[marketTypeKey] || null;
}

/**
 * 更新指定交易所的规则
 */
export function updateExchangeRule(exchange, marketType, newRule) {
  const rules = loadExchangeRules();
  const exchangeId = exchange.toLowerCase();
  const marketTypeKey = marketType.toLowerCase();
  
  if (!rules[exchangeId]) {
    rules[exchangeId] = {};
  }
  
  rules[exchangeId][marketTypeKey] = {
    ...rules[exchangeId][marketTypeKey],
    ...newRule,
  };
  
  return saveExchangeRules(rules) ? rules : null;
}

/**
 * 获取所有支持的交易所列表
 */
export function getSupportedExchanges() {
  const rules = loadExchangeRules();
  return Object.keys(rules);
}

/**
 * 验证规则是否完整
 */
export function validateRule(rule) {
  if (!rule || typeof rule !== 'object') {
    return false;
  }
  
  const { quote, separator } = rule;
  
  // quote 是必需的，separator 可以为空字符串（允许无分隔符的交易所）
  if (!quote || typeof quote !== 'string' || quote.trim() === '') {
    return false;
  }
  
  // separator 可以为空字符串，但不能是 undefined 或 null（必须明确指定）
  if (separator === undefined || separator === null) {
    return false;
  }
  
  // separator 必须是字符串类型（可以是空字符串）
  if (typeof separator !== 'string') {
    return false;
  }
  
  // 如果 separator 只包含空格，应该转换为空字符串（但这里只验证，不修改）
  // 实际转换在保存时进行
  
  return true;
}

