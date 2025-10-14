// Symbol watchlist localStorage helper
// Key structure:
// {
//   updatedAt: number,
//   byExchange: {
//     [exchangeId]: { all: string[], enabled?: string[] }
//   }
// }

const STORAGE_KEY = 'gd.symbols.v1';

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
  const empty = { updatedAt: nowTs(), byExchange: {} };
  if (!raw || typeof raw !== 'object') return empty;
  const byExchange = raw.byExchange && typeof raw.byExchange === 'object' ? raw.byExchange : {};
  const normalized = { updatedAt: raw.updatedAt || nowTs(), byExchange: {} };
  Object.keys(byExchange).forEach((exId) => {
    const entry = byExchange[exId] || {};
    const all = uniqueSorted(entry.all || []);
    const enabled = entry.enabled ? uniqueSorted(entry.enabled) : undefined;
    normalized.byExchange[exId] = { all, ...(enabled ? { enabled } : {}) };
  });
  return normalized;
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

export function setAllForExchange(exchangeId, baseSymbols) {
  const current = readWatchlist();
  const existing = current.byExchange[exchangeId] || { all: [], enabled: undefined };
  const nextAll = uniqueSorted(baseSymbols);
  const nextEnabled = Array.isArray(existing.enabled) ? existing.enabled : nextAll;
  current.byExchange[exchangeId] = { all: nextAll, enabled: uniqueSorted(nextEnabled) };
  return writeWatchlist(current);
}

export function mergeAllForExchange(exchangeId, baseSymbols) {
  const current = readWatchlist();
  const existing = current.byExchange[exchangeId] || { all: [], enabled: undefined };
  const nextAll = uniqueSorted([...(existing.all || []), ...(baseSymbols || [])]);
  current.byExchange[exchangeId] = {
    all: nextAll,
    enabled: Array.isArray(existing.enabled) ? uniqueSorted(existing.enabled) : nextAll,
  };
  return writeWatchlist(current);
}

export function getAllByExchange() {
  const wl = readWatchlist();
  const out = {};
  Object.keys(wl.byExchange).forEach((ex) => {
    out[ex] = wl.byExchange[ex].all || [];
  });
  return out;
}

export function getEnabledByExchange(fallbackToAll = true) {
  const wl = readWatchlist();
  const out = {};
  Object.keys(wl.byExchange).forEach((ex) => {
    const entry = wl.byExchange[ex] || {};
    const enabled = entry.enabled;
    out[ex] = Array.isArray(enabled) ? enabled : (fallbackToAll ? (entry.all || []) : []);
  });
  return out;
}

export function setEnabledForExchange(exchangeId, enabledBaseSymbols) {
  const wl = readWatchlist();
  const existing = wl.byExchange[exchangeId] || { all: [], enabled: undefined };
  wl.byExchange[exchangeId] = {
    all: uniqueSorted(existing.all || []),
    enabled: uniqueSorted(enabledBaseSymbols || []),
  };
  return writeWatchlist(wl);
}

export function getQueriesFromEnabled(options = {}) {
  const { exchangesFilter } = options; // optional Set of exchange ids
  const enabledMap = getEnabledByExchange(true);
  const queries = Object.keys(enabledMap)
    .filter((ex) => !exchangesFilter || exchangesFilter.has(ex))
    .map((exchange) => ({ exchange, baseSymbols: uniqueSorted(enabledMap[exchange]) }))
    .filter((q) => q.baseSymbols.length > 0);
  return queries;
}


