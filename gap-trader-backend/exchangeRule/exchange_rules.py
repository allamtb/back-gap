#!/usr/bin/env python3
"""
交易所符号格式规则（自动生成）

此文件由 generate_exchange_rules.py 自动生成
不要手动编辑此文件

规则结构:
{
    "exchange_id": {
        "spot": {"quote": "USDT", "separator": "/", "suffix": ""},
        "future": {"quote": "USDT", "separator": "/", "suffix": ":USDT"}
    }
}
"""

# 交易所符号格式规则
EXCHANGE_RULES = {
    "binance": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "okx": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bybit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "gate": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "huobi": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "TUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "kucoin": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinbase": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "kraken": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitfinex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDQ",
            "separator": "/",
            "suffix": ""
        }
    },
    "cryptocom": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "PYUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "apex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        }
    },
    "ascendex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "backpack": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "bequant": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bigone": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "binancecoinm": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ":BTC"
        }
    },
    "binanceus": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD4",
            "separator": "/",
            "suffix": ""
        }
    },
    "binanceusdm": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        }
    },
    "bingx": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bit2c": {},
    "bitbank": {},
    "bitbns": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitflyer": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitget": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "WUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bithumb": {
        "future": {
            "quote": "BTC",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitmart": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitmex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitopro": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitrue": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitso": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "BTC",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitstamp": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bitteam": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "BUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "bittrade": {},
    "bitvavo": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "blockchaincom": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "btcalpha": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "btcbox": {},
    "btcmarkets": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "btcturk": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "cex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinbaseadvanced": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinbaseexchange": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinbaseinternational": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "coincatch": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "coincheck": {},
    "coinex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinmetro": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinone": {},
    "coinsph": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "coinspot": {},
    "cryptomus": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "defx": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ":USDC"
        }
    },
    "delta": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "deribit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "derive": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "digifinex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "exmo": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "fmfwio": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "foxbit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "gateio": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "gemini": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "GUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "hashkey": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "hibachi": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        }
    },
    "hitbtc": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "hollaex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "htx": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "TUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "hyperliquid": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "independentreserve": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "indodax": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "krakenfutures": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ":BTC"
        }
    },
    "kucoinfutures": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ":USDT"
        }
    },
    "latoken": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "lbank": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "luno": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "mercado": {},
    "mexc": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "modetrade": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ":USDC"
        }
    },
    "myokx": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "ndax": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "novadax": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "oceanex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "okxus": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "onetrading": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    },
    "oxfun": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ":OX"
        }
    },
    "p2b": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "BTC",
            "separator": "/",
            "suffix": ""
        }
    },
    "paradex": {
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ":USDC-105000-P"
        }
    },
    "paymium": {},
    "phemex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "poloniex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "probit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "timex": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "tokocrypto": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "TUSD",
            "separator": "/",
            "suffix": ""
        }
    },
    "toobit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "upbit": {
        "spot": {
            "quote": "BTC",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "BTC",
            "separator": "/",
            "suffix": ""
        }
    },
    "wavesexchange": {},
    "whitebit": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USD",
            "separator": "/",
            "suffix": ""
        }
    },
    "woo": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "woofipro": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ":USDC"
        }
    },
    "xt": {
        "spot": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        },
        "future": {
            "quote": "USDT",
            "separator": "/",
            "suffix": ""
        }
    },
    "zaif": {},
    "zonda": {
        "future": {
            "quote": "USDC",
            "separator": "/",
            "suffix": ""
        }
    }
}


def get_all_exchanges():
    """获取所有支持的交易所列表"""
    return list(EXCHANGE_RULES.keys())


def get_exchange_rule(exchange: str, market_type: str = 'spot'):
    """
    获取交易所规则
    
    Args:
        exchange: 交易所ID
        market_type: 市场类型（spot 或 future）
        
    Returns:
        规则字典或 None
    """
    exchange = exchange.lower()
    market_type = market_type.lower()
    
    if exchange in EXCHANGE_RULES:
        return EXCHANGE_RULES[exchange].get(market_type)
    return None
