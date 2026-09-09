"""
Small-Cap Universe + Market-Cap Filter
═══════════════════════════════════════════════════════════════════════════════

WHAT THIS IS (plain terms):
The existing scanner only looks at ~200 big Indian companies. This strategy is
about SMALL companies, so it needs its own list. This file holds that list and a
market-cap sanity check (keep only ₹500cr–₹5000cr).

It does NOT edit scanner_engine.py. It subclasses the scanner and swaps the
stock list. Everything else (MACD, moving averages, RSI, scoring) is reused
unchanged.

⚠️ STARTER LIST: the tickers below are a hand-picked starting set, not the final
universe. Replace/expand from the Nifty Smallcap 250 constituents before the
real dry run. Ticker format is Yahoo Finance style: SYMBOL.NS
"""

import os
import sys
import time
from typing import List, Optional

# repo root on path so `scanner_engine` imports whether run as a module or directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner_engine import MACDScanner

# Rupees. ₹1 crore = 1e7. Band comes from framework.config so the universe
# filter and the fundamentals gate can never drift apart.
from strategies.framework.config import MARKET_CAP_BAND_CR

DEFAULT_MIN_CR, DEFAULT_MAX_CR = MARKET_CAP_BAND_CR
_CRORE = 1e7

# --- Curated small-cap watch list ---------------------------------------------
# ~130 NSE names that were small/lower-mid-cap when compiled (2026-09). This is a
# WATCH LIST, not a guarantee of size: the ₹500-5,000cr band check
# (apply_cap_filter=True, or scan_and_store --check-caps) is the real gate and
# drops anything that has grown out of the band. Refresh from the official Nifty
# Smallcap 250 constituents each quarter; format is SYMBOL.NS.
SMALLCAP_TICKERS: List[str] = [
    # capital markets / financials
    "CDSL.NS", "CAMS.NS", "ANGELONE.NS", "KFINTECH.NS", "IEX.NS", "MCX.NS",
    "CREDITACC.NS", "APTUS.NS", "HOMEFIRST.NS", "UGROCAP.NS", "SPANDANA.NS",
    "CSBBANK.NS", "DCBBANK.NS", "KARURVYSYA.NS", "SOUTHBANK.NS", "JMFINANCIL.NS",
    # PSU / defence / rail / infra
    "RAILTEL.NS", "IRCON.NS", "NBCC.NS", "RITES.NS", "HUDCO.NS", "RVNL.NS",
    "MAZDOCK.NS", "GRSE.NS", "COCHINSHIP.NS", "BEML.NS", "MIDHANI.NS",
    "IRCTC.NS", "IREDA.NS", "HFCL.NS", "ITI.NS", "ENGINERSIN.NS", "NCC.NS",
    "KALPATPOWR.NS", "KEC.NS", "PNCINFRA.NS", "GRINFRA.NS", "HGINFRA.NS",
    # IT mid/small
    "DATAPATTNS.NS", "IDEAFORGE.NS", "NETWEB.NS", "MASTEK.NS", "BIRLASOFT.NS",
    "ZENSAR.NS", "SONATSOFTW.NS", "HAPPSTMNDS.NS", "TANLA.NS", "ROUTE.NS",
    "INTELLECT.NS", "CYIENT.NS", "KPITTECH.NS", "NEWGEN.NS", "RATEGAIN.NS",
    "MAPMYINDIA.NS", "LATENTVIEW.NS", "TATATECH.NS", "ZAGGLE.NS",
    # pharma / healthcare
    "LAURUSLABS.NS", "GRANULES.NS", "NATCOPHARM.NS", "IPCALAB.NS", "SEQUENT.NS",
    "NEULAND.NS", "CAPLINPOINT.NS", "METROPOLIS.NS", "THYROCARE.NS", "KIMS.NS",
    "RAINBOW.NS", "MEDPLUS.NS", "AJANTPHARM.NS", "JBCHEPHARM.NS", "BLISSGVS.NS",
    "SUVENPHAR.NS", "GLAND.NS", "PPLPHARMA.NS", "MARKSANS.NS", "ERIS.NS",
    # consumer / electricals / durables
    "VGUARD.NS", "CROMPTON.NS", "ORIENTELEC.NS", "AMBER.NS", "DIXON.NS",
    "KEI.NS", "FINCABLES.NS", "APARINDS.NS", "TRIVENI.NS", "ELGIEQUIP.NS",
    "SYMPHONY.NS", "TTKPRESTIG.NS", "BAJAJELEC.NS", "CERA.NS", "KAJARIACER.NS",
    "GREENPANEL.NS", "CENTURYPLY.NS", "VIPIND.NS", "RELAXO.NS", "SAFARI.NS",
    # chemicals / industrials / materials
    "NAVINFLUOR.NS", "FINEORG.NS", "GALAXYSURF.NS", "ALKYLAMINE.NS", "BALAMINES.NS",
    "NOCIL.NS", "ROSSARI.NS", "CLEAN.NS", "TATACHEM.NS", "DEEPAKNTR.NS",
    "GRINDWELL.NS", "TIMKEN.NS", "SKFINDIA.NS", "CARBORUNIV.NS", "KSB.NS",
    "RATNAMANI.NS", "PRINCEPIPE.NS", "SUPREMEIND.NS", "FINPIPE.NS", "ASTRAL.NS",
    # auto ancillary / misc
    "ENDURANCE.NS", "SUNDRMFAST.NS", "GABRIEL.NS", "JAMNAAUTO.NS", "SUPRAJIT.NS",
    "MINDACORP.NS", "CRAFTSMAN.NS", "SANSERA.NS", "RKFORGE.NS",
    "GESHIP.NS", "COFORGE.NS", "PGHL.NS", "VSTIND.NS", "RADICO.NS",
    "CCL.NS", "HERITGFOOD.NS", "DODLA.NS", "KRBL.NS",
]


def _in_band(mcap_inr: Optional[float], min_cr: float, max_cr: float) -> bool:
    """Pure check: is a market cap (in rupees) inside the crore band?"""
    if mcap_inr is None or mcap_inr <= 0:
        return False
    return (min_cr * _CRORE) <= mcap_inr <= (max_cr * _CRORE)


def get_market_cap(ticker: str) -> Optional[float]:
    """
    Market cap in rupees, or None if unavailable.
    Uses yfinance .info — one web call per ticker, sometimes rate-limited or
    partial, so failures are swallowed and return None (same defensive style as
    scanner_engine.py).
    """
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        mc = info.get("marketCap")
        return float(mc) if mc else None
    except Exception:
        return None


def filter_by_market_cap(tickers: List[str],
                         min_cr: float = DEFAULT_MIN_CR,
                         max_cr: float = DEFAULT_MAX_CR,
                         verbose: bool = False) -> List[str]:
    """
    Keep only tickers whose market cap sits in the band.
    Tickers with unknown market cap are DROPPED (can't verify -> don't trade).
    """
    kept: List[str] = []
    for t in tickers:
        mc = get_market_cap(t)
        if _in_band(mc, min_cr, max_cr):
            kept.append(t)
            if verbose:
                print(f"  keep {t:<16} ₹{mc / _CRORE:,.0f}cr")
        elif verbose:
            shown = f"₹{mc / _CRORE:,.0f}cr" if mc else "unknown"
            print(f"  drop {t:<16} {shown}")
        time.sleep(0.1)  # be nice to Yahoo
    return kept


def _yf_history(ticker: str, period: str = "60d"):
    """Default candle provider: yfinance daily OHLC, or None on any failure."""
    try:
        import yfinance as yf
        df = yf.Ticker(ticker).history(period=period)
        return df if df is not None and not df.empty else None
    except Exception:
        return None


class SmallCapScanner(MACDScanner):
    """
    Same scoring engine as MACDScanner, but scans the small-cap list.

    apply_cap_filter=True runs the (slow) market-cap check first. Leave it False
    for quick iteration and rely on the curated list.

    fetch: candle provider seam — `fetch(ticker) -> DataFrame(Close/High/Low) | None`.
    Defaults to yfinance; pass a stub to run the scan fully offline. This override
    also uses the framework's own MACD-crossover detector instead of the broken
    scanner_engine.detect_macd_crossover.
    """

    def __init__(self, progress_callback=None,
                 tickers: Optional[List[str]] = None,
                 apply_cap_filter: bool = False,
                 min_cr: float = DEFAULT_MIN_CR,
                 max_cr: float = DEFAULT_MAX_CR,
                 fetch=None):
        super().__init__(progress_callback=progress_callback)
        self._tickers = list(tickers) if tickers else list(SMALLCAP_TICKERS)
        self._apply_cap_filter = apply_cap_filter
        self._min_cr = min_cr
        self._max_cr = max_cr
        self._fetch = fetch or _yf_history

    def get_stock_list(self, mode: str = "SMALLCAP") -> List[str]:
        if self._apply_cap_filter:
            return filter_by_market_cap(self._tickers, self._min_cr, self._max_cr)
        return list(self._tickers)

    def scan_single_stock(self, ticker: str, progress: int, total: int) -> Optional[dict]:
        """Offline-capable copy of the parent: candles via self._fetch, crossover
        via the framework detector. Same output dict shape and score >= 60 gate."""
        from datetime import datetime
        from strategies.small_cap_dryrun import fresh_macd_cross

        if self.stop_requested:
            return None
        df = self._fetch(ticker)
        if df is None or len(df) < 30:
            return None

        prices = df["Close"]
        current_price = prices.iloc[-1]
        macd_line, signal_line, _ = self.calculate_macd(prices)
        if macd_line is None:
            return None

        is_fresh, cross_date = fresh_macd_cross(df, within_bars=30)
        if not is_fresh:
            return None
        try:
            days_ago = (datetime.now() - datetime.strptime(cross_date, "%d-%b-%Y")).days
        except (ValueError, TypeError):
            days_ago = 0

        ma_data = self.check_moving_averages(prices, current_price)
        rsi = self.get_rsi(prices)
        score = self.calculate_confluence_score(
            ma_data["above_20"], ma_data["above_50"], rsi, days_ago
        )
        if score < 60:
            return None
        signal = "STRONG BUY" if score >= 75 else "BUY"
        return {
            "ticker": ticker,
            "company": ticker,
            "price": round(float(current_price), 2),
            "signal": signal,
            "confluence_score": score,
            "macd_cross_date": cross_date,
            "days_ago": days_ago,
            "above_20ma": ma_data["above_20"],
            "above_50ma": ma_data["above_50"],
            "ma_20": ma_data["ma_20"],
            "ma_50": ma_data["ma_50"],
            "rsi": rsi if rsi else "N/A",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


if __name__ == "__main__":
    # Self-check: band math only (no network).
    assert _in_band(1_000 * _CRORE, 500, 5000) is True
    assert _in_band(300 * _CRORE, 500, 5000) is False      # too small
    assert _in_band(9_000 * _CRORE, 500, 5000) is False     # too big
    assert _in_band(None, 500, 5000) is False
    assert _in_band(0, 500, 5000) is False
    assert _in_band(500 * _CRORE, 500, 5000) is True        # inclusive lower
    assert _in_band(5000 * _CRORE, 500, 5000) is True       # inclusive upper

    s = SmallCapScanner()
    assert s.get_stock_list() == SMALLCAP_TICKERS
    assert len(SMALLCAP_TICKERS) == len(set(SMALLCAP_TICKERS)), "duplicate ticker in list"
    print("✅ small_cap_universe self-check passed "
          f"({len(SMALLCAP_TICKERS)} starter tickers)")
