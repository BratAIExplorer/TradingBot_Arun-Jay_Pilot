"""Builds etfs.csv (input for etf_tradability) from IBKR's public product-listings
search — no login needed. Keeps only the venues in VENUES.

productCountry is the ETF's country (ISIN prefix), not the venue, so we pull each
country and filter by exchangeId. Venue ids are IBKR's: ARCA/NASDAQ/... = US,
LSEETF = London, EBS = SIX Swiss.

Usage:
    python -m brokers.fetch_etf_list            # writes etfs.csv
"""
import csv
import json
import urllib.request

URL = "https://www.interactivebrokers.com/webrest/search/products-by-filters"
COUNTRIES = ["US", "CH", "GB", "IE"]
VENUES = {"ARCA", "NASDAQ", "NYSE", "AMEX", "BATS", "LSEETF", "LSE", "EBS"}  # ponytail: add ISE etc. if wanted


def _page(country, n, size=500):
    body = {"pageNumber": n, "pageSize": str(size), "sortField": "symbol", "sortDirection": "ASC",
            "productCountry": [country], "productSymbol": "", "newProduct": "all",
            "productType": ["ETF"], "domain": "com"}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req, timeout=60))["products"]


def main():
    seen = {}
    for country in COUNTRIES:
        n = 1
        while True:
            rows = _page(country, n)
            if not rows:
                break
            for r in rows:
                if r["exchangeId"] in VENUES:
                    seen[r["conid"]] = r
            n += 1
        print(f"{country}: {len(seen)} kept so far")
    with open("etfs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["symbol", "exchange", "currency", "name", "isin", "country"])
        for r in sorted(seen.values(), key=lambda r: (r["exchangeId"], r["symbol"])):
            w.writerow([r["symbol"], r["exchangeId"], r["currency"], r["description"], r["isin"], r["country"]])
    print(f"wrote {len(seen)} ETFs -> etfs.csv")


if __name__ == "__main__":
    main()
