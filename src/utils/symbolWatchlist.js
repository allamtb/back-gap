// Symbol watchlist localStorage helper
// 新数据结构（v2）：
// {
//   updatedAt: number,
//   all: string[],        // 所有币种列表（从持仓中提取）
//   enabled: string[]     // 用户选中的币种列表
// }

const STORAGE_KEY = 'gd.symbols.v2';

function nowTs() {
  return Date.now();
}

function uniqueSorted(list) {
  return Array.from(new Set((list || []).filter(Boolean))).sort();
}

function safeParse(value) {
  try {
    return value ? JSON.parse(value) : null;
  } catch (e) {
    return null;
  }
}

function normalizeShape(raw) {
  const empty = { updatedAt: nowTs(), all: [], enabled: [] };
  if (!raw || typeof raw !== 'object') return empty;
  
  return {
    updatedAt: raw.updatedAt || nowTs(),
    all: uniqueSorted(raw.all || []),
    enabled: uniqueSorted(raw.enabled || raw.all || []),
  };
}

export function readWatchlist() {
  const raw = safeParse(localStorage.getItem(STORAGE_KEY));
  return normalizeShape(raw);
}

export function writeWatchlist(data) {
  const normalized = normalizeShape(data);
  normalized.updatedAt = nowTs();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
  return normalized;
}

// 设置所有币种列表（从持仓数据中提取）
export function setAllSymbols(baseSymbols) {
  const current = readWatchlist();
  const nextAll = uniqueSorted(baseSymbols);
  const nextEnabled = current.enabled.length > 0 ? current.enabled : nextAll;
  
  return writeWatchlist({
    all: nextAll,
    enabled: uniqueSorted(nextEnabled),
  });
}

// 合并币种到 all 列表
export function mergeAllSymbols(baseSymbols) {
  const current = readWatchlist();
  const nextAll = uniqueSorted([...current.all, ...(baseSymbols || [])]);
  const nextEnabled = current.enabled.length > 0 ? current.enabled : nextAll;
  
  return writeWatchlist({
    all: nextAll,
    enabled: uniqueSorted(nextEnabled),
  });
}

// 获取所有币种
export function getAllSymbols() {
  const wl = readWatchlist();
  return wl.all || [];
}

// 获取已启用的币种
export function getEnabledSymbols(fallbackToAll = true) {
  const wl = readWatchlist();
  const enabled = wl.enabled || [];
  return enabled.length > 0 ? enabled : (fallbackToAll ? wl.all : []);
}

// 设置已启用的币种
export function setEnabledSymbols(enabledBaseSymbols) {
  const wl = readWatchlist();
  return writeWatchlist({
    all: wl.all,
    enabled: uniqueSorted(enabledBaseSymbols || []),
  });
}

// 生成查询参数（返回币种列表）
export function getSymbolsForQuery() {
  return getEnabledSymbols(true);
}

// ========== 兼容旧版本的函数（保留以防其他地方使用） ==========

// 兼容旧版本：按交易所设置（实际只保存币种）
export function setAllForExchange(exchangeId, baseSymbols) {
  return mergeAllSymbols(baseSymbols);
}

// 兼容旧版本：按交易所合并（实际只保存币种）
export function mergeAllForExchange(exchangeId, baseSymbols) {
  return mergeAllSymbols(baseSymbols);
}

// 兼容旧版本：获取所有币种（按交易所分组，但实际返回统一列表）
export function getAllByExchange() {
  // 返回空对象，表示不再按交易所分组
  return {};
}

// 兼容旧版本：获取已启用币种（按交易所分组，但实际返回统一列表）
export function getEnabledByExchange(fallbackToAll = true) {
  // 返回空对象，表示不再按交易所分组
  return {};
}

// 兼容旧版本：按交易所设置已启用币种（实际只保存币种）
export function setEnabledForExchange(exchangeId, enabledBaseSymbols) {
  return setEnabledSymbols(enabledBaseSymbols);
}

// 兼容旧版本：生成查询参数（返回简单的币种列表）
export function getQueriesFromEnabled(options = {}) {
  // 旧版本返回 [{ exchange, baseSymbols }]
  // 新版本返回币种列表
  return getEnabledSymbols(true);
}
