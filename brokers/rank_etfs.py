"""Ranks the tradable ETFs (etf_tradable.csv) within each sector and keeps the top N per sector.

A SCREEN on liquidity, cost, size and trend — not investment advice. Rank 1 = best score.

Data: sector is tagged from the ETF name (IBKR leaves category blank); AUM, expense ratio,
volume and returns come from Yahoo (yfinance). Yahoo coverage of London/Swiss ETFs is patchy,
so every row carries `metrics` (how many of the 4 scores had data); rows with <2 are not ranked.

Usage:
    python -m brokers.rank_etfs            # -> etf_ranking.csv (all) + etf_top10.csv
"""
import csv
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import yfinance as yf

TOP_N = 10
MIN_METRICS = 2
WEIGHTS = {"liquidity": 0.30, "cost": 0.30, "size": 0.20, "trend": 0.20}
CACHE = "etf_yahoo_cache.json"
SUFFIX = {"LSEETF": ".L", "LSE": ".L", "EBS": ".SW"}  # US venues need none

# First match wins — order matters (specific before broad).
SECTORS = [
    ("Crypto", r"BITCOIN|ETHER|CRYPTO|BLOCKCHAIN"),
    ("Gold & Commodities", r"\bGOLD\b|SILVER|PLATINUM|PALLADIUM|COMMODIT|COPPER|PHYSICAL"),
    ("Bonds", r"BOND|\bBND\b|\bBD\b|TREASUR|GOVERNMENT|GOVT|\bTIPS\b|FIXED INC|HIGH YIELD|HIGH YILD|CREDIT|AGGREGATE|T-BILL|\bMUNI?\b|MUNICIPAL|DURATION|FLOATING|\bLOAN|\bNOTE\b|CORPORATE|CORE PLUS|MORTGAGE"),
    ("Technology", r"TECH|SEMICONDUCTOR|SOFTWARE|CYBER|CLOUD|\bIT\b|INFORMATION|ROBOT|\bAI\b|ARTIFICIAL|INTERNET|DIGITAL"),
    ("Health Care", r"HEALTH|HLTH|BIOTECH|PHARMA|MEDICAL|GENOM|LIFE SCI"),
    ("Financials", r"FINANCIAL|BANK|INSURANCE|FINTECH"),
    ("Energy", r"ENERGY|\bNRG\b|\bOIL\b|\bGAS\b|URANIUM|SOLAR|\bWIND\b|HYDROGEN|NUCLEAR|PIPELINE|MLP|CLEAN EDGE|CLN EDG"),
    ("Utilities", r"UTILIT|WATER"),
    ("Real Estate", r"REAL ESTATE|REIT|PROPERTY"),
    ("Materials", r"MATERIAL|MINING|MINERS|METALS|LITHIUM|BATTERY"),
    ("Industrials", r"INDUSTRIAL|AEROSPACE|DEFENSE|DEFENCE|TRANSPORT|INFRASTRUCTURE|AIRLINE|SHIPPING"),
    ("Consumer Staples", r"STAPLES|FOOD|BEVERAGE|AGRIBUS"),
    ("Consumer Discretionary", r"DISCRETIONARY|DSCRTN|RETAIL|LEISURE|HOMEBUILD|CONSUMER|LUXURY|TRAVEL"),
    ("Communication Services", r"COMMUNICATION|\bMEDIA\b|TELECOM|STREAMING|GAMING|ESPORT|VIDEO GAME"),
    ("Emerging Markets", r"EMERGING|\bEM\b|CHINA|INDIA|BRAZIL|TAIWAN|KOREA|VIETNAM|MEXICO|SAUDI|AFRICA|LATIN|FRONTIER|ASIA"),
    ("Dividend / Factor", r"DIVIDEND|VALUE|QUALITY|LOW VOL|MIN VOL|MINIMUM VOL|MOMENTUM|SIZE FACTOR|MULTIFACTOR|EQUAL WEIGHT|BUYBACK"),
    ("International Developed", r"JAPAN|EUROPE|EURO |EAFE|UK |GERMAN|FRANCE|SWISS|PACIFIC|WORLD|GLOBAL|ACWI|INTERNATIONAL|EX-US|EX US|NORDIC|CANADA|AUSTRALIA"),
    ("US Broad Equity", r"S&P|500|TOTAL MARKET|RUSSELL|NASDAQ|MSCI USA|\bUS\b|U\.S\.|DOW|LARGE CAP|MID CAP|SMALL CAP|GROWTH|EQUITY"),
]


CATEGORY_MAP = [
    ("Crypto", r"CRYPTO|DIGITAL ASSET"),
    ("Gold & Commodities", r"COMMODIT|PRECIOUS|GOLD"),
    ("Bonds", r"BOND|MUNI|TREASURY|INFLATION-PROT|FLOATING|CREDIT|MORTGAGE|LONG GOVERNMENT|SHORT GOVERNMENT|MONEY MARKET"),
    ("Technology", r"TECHNOLOGY"),
    ("Health Care", r"HEALTH|BIOTECH"),
    ("Financials", r"FINANCIAL"),
    ("Energy", r"ENERGY"),
    ("Utilities", r"UTILIT"),
    ("Real Estate", r"REAL ESTATE|GLOBAL REAL"),
    ("Materials", r"NATURAL RESOURCES|BASIC MATERIALS"),
    ("Industrials", r"INDUSTRIAL"),
    ("Consumer Staples", r"CONSUMER DEFENSIVE|STAPLES"),
    ("Consumer Discretionary", r"CONSUMER CYCLICAL|DISCRETIONARY"),
    ("Communication Services", r"COMMUNICATION"),
    ("Emerging Markets", r"EMERGING|CHINA|INDIA|LATIN|PACIFIC|ASIA"),
    ("International Developed", r"WORLD|GLOBAL|JAPAN|EUROPE|DIVERSIFIED PACIFIC|FOREIGN"),
    ("Dividend / Factor", r"VALUE|DIVIDEND|EQUITY INCOME"),
    ("US Broad Equity", r"LARGE|MID-CAP|SMALL|BLEND|GROWTH"),
]


def tag_sector(name: str, category: str | None = None) -> str:
    if isinstance(category, str) and category:
        cat = category.upper()
        hit = next((s for s, pat in CATEGORY_MAP if re.search(pat, cat)), None)
        if hit:
            return hit
    return _tag_by_name(name)


def _tag_by_name(name: str) -> str:
    n = f" {name.upper()} "
    return next((s for s, pat in SECTORS if re.search(pat, n)), "Other")


def yahoo_ticker(symbol: str, exchange: str) -> str:
    return symbol + SUFFIX.get(exchange, "")


def fetch_one(tk: str) -> dict:
    """AUM, expense ratio, avg $ volume (3m) and 1y/3y return; missing values stay None."""
    out = {"category": None, "aum": None, "expense_pct": None, "dollar_vol": None, "ret_1y": None, "ret_3y": None}
    try:
        t = yf.Ticker(tk)
        info = t.info or {}
        out["category"] = info.get("category")
        out["aum"] = info.get("totalAssets")
        out["expense_pct"] = info.get("netExpenseRatio") or info.get("annualReportExpenseRatio")
        h = t.history(period="3y", auto_adjust=True)
        if len(h) > 60:
            close, vol = h["Close"], h["Volume"]
            out["dollar_vol"] = float((close.tail(63) * vol.tail(63)).mean())  # ponytail: local currency, no FX
            if len(h) > 250:
                out["ret_1y"] = float(close.iloc[-1] / close.iloc[-252] - 1)
            if (close.index[-1] - close.index[0]).days > 3 * 365 - 30:
                out["ret_3y"] = float(close.iloc[-1] / close.iloc[0] - 1)
    except Exception as e:  # network/parse: leave metrics empty, row gets flagged by low `metrics`
        out["err"] = str(e)[:80]
    return out


def fetch_with_retry(tk: str) -> dict:
    """Yahoo rate-limits bursts: back off and retry instead of caching an empty result."""
    for wait in (0, 60, 180, 300):
        time.sleep(wait)
        res = fetch_one(tk)
        if "Too Many Requests" not in res.get("err", "") and "Rate limited" not in res.get("err", ""):
            return res
    return res


def load_cache() -> dict:
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def fetch_all(tickers: list[str]) -> dict:
    cache = load_cache()
    limited = lambda v: "Rate limited" in v.get("err", "") or "Too Many" in v.get("err", "")
    todo = [t for t in tickers if t not in cache or limited(cache[t])]
    print(f"Yahoo: {len(cache)} cached, {len(todo)} to fetch")
    with ThreadPoolExecutor(max_workers=3) as ex:
        for i, (tk, res) in enumerate(zip(todo, ex.map(fetch_with_retry, todo)), 1):
            cache[tk] = res
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}")
                with open(CACHE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    return cache


def score(df: pd.DataFrame) -> pd.DataFrame:
    """Percentile rank within sector per metric, weighted mean over the metrics that exist."""
    g = df.groupby("sector")
    pct = pd.DataFrame(index=df.index)
    pct["liquidity"] = g["dollar_vol"].rank(pct=True)
    pct["cost"] = 1 - g["expense_pct"].rank(pct=True) + (1 / g["expense_pct"].transform("count"))  # cheapest -> 1.0
    pct["size"] = g["aum"].rank(pct=True)
    pct["trend"] = pd.concat([g["ret_1y"].rank(pct=True), g["ret_3y"].rank(pct=True)], axis=1).mean(axis=1)
    w = pd.Series(WEIGHTS)
    have = pct.notna()
    df["metrics"] = have.sum(axis=1)
    df["score"] = (pct.fillna(0) * w).sum(axis=1) / (have * w).sum(axis=1).where(df["metrics"] > 0)
    return df


def main():
    with open("etf_tradable.csv", newline="", encoding="utf-8") as f:
        tradable = list(csv.DictReader(f))
    with open("etfs.csv", newline="", encoding="utf-8") as f:
        meta = {(r["symbol"], r["exchange"], r["currency"]): r for r in csv.DictReader(f)}

    rows = []
    for r in tradable:
        m = meta.get((r["symbol"], r["exchange"], r["currency"]), {})
        name = r.get("name") or m.get("description") or m.get("name", "")
        rows.append({"symbol": r["symbol"], "exchange": r["exchange"], "currency": r["currency"],
                     "name": name, "isin": m.get("isin", ""),
                     "yahoo": yahoo_ticker(r["symbol"], r["exchange"])})
    df = pd.DataFrame(rows).drop_duplicates("isin", keep="first")  # one listing per fund

    cache = fetch_all(df["yahoo"].tolist())
    for col in ("aum", "expense_pct", "dollar_vol", "ret_1y", "ret_3y"):
        df[col] = pd.to_numeric(df["yahoo"].map(lambda t: cache.get(t, {}).get(col)), errors="coerce")

    df["yahoo_category"] = df["yahoo"].map(lambda t: cache.get(t, {}).get("category"))
    df["sector"] = [tag_sector(n, c) for n, c in zip(df["name"], df["yahoo_category"])]
    df = score(df)
    ranked = df[df["metrics"] >= MIN_METRICS].copy()
    ranked["rank"] = ranked.groupby("sector")["score"].rank(ascending=False, method="first").astype(int)
    ranked = ranked.sort_values(["sector", "rank"])
    ranked.to_csv("etf_ranking.csv", index=False)
    ranked[ranked["rank"] <= TOP_N].to_csv("etf_top10.csv", index=False)

    print(f"\n{len(df)} funds, {len(ranked)} ranked (>= {MIN_METRICS} metrics), {len(df) - len(ranked)} unranked (no data)")
    print(df.groupby("sector").size().rename("tradable").to_frame()
          .join(ranked.groupby("sector").size().rename("ranked")).fillna(0).astype(int).to_string())


if __name__ == "__main__":
    main()
