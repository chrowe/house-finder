"""Scrape Montpelier VT property record cards (beds/baths/year built/sale history/etc)
from the town assessor's public Patriot Properties database and save as JSONL,
keyed by SPAN (= "Property Account Number", the same ID used in VCGI parcel data).

How the site actually works (reverse-engineered):
  Summary.asp?AccountNumber=N only returns real data if N is a member of the
  CURRENT session's last search resultset (ASP session state). So we must first
  run a SearchResults.asp search (one per street-name initial letter/digit,
  which in a small town like Montpelier returns every account on those streets)
  to populate a valid resultset, then fetch each AccountNumber in it.

Usage: python3 enrich.py
Resumable: already-scraped AccountNumbers (by presence in accounts.jsonl) are skipped;
fully-scraped search letters are recorded in letters_done.txt and skipped on resume.
Slow and polite: the site blocks (403) after a few hundred requests in a short window.
"""
import re, time, json, os, sys, random, string
import requests

BASE = "https://montpeliervt.patriotproperties.com"
OUT = "accounts.jsonl"
LETTERS_DONE = "letters_done.txt"
LETTERS = list(string.ascii_uppercase) + list(string.digits)
DELAY = 3.0              # seconds between requests (deliberately slow/polite)
BACKOFF_403 = 600        # seconds to wait after a 403
MAX_RETRIES = 4          # give up on a single request after this many failures (resumable later)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MontpelierHouseFinder/1.0; local research tool)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://montpeliervt.patriotproperties.com/default.asp",
}

def field(html, label):
    label_pat = r'\s+'.join(re.escape(w) for w in label.split())
    m = re.search(label_pat + r'.*?color="#0000FF"[^>]*>(?:<b>)?&nbsp;?\s*([^<]*)', html, re.S)
    return (m.group(1) or "").strip() if m else ""

def narrative_fields(html):
    m = re.search(r'Narrative Description.*?Legal Description', html, re.S)
    if not m:
        return {}
    blues = re.findall(r'color="blue">([^<]*)</font>', m.group(0))
    keys = ["narr_acres", "land_class", "style", "year_built", "exterior",
            "roof", "units", "rooms", "bedrooms", "baths", "half_baths", "three_qtr_baths"]
    vals = [v.strip() for v in blues]
    vals += [""] * (len(keys) - len(vals))
    return dict(zip(keys, vals[:len(keys)]))

def parse_record(html, account_number):
    span = field(html, "Property Account Number")
    if not span:
        return None
    rec = {
        "accountNumber": account_number,
        "span": span,
        "parcelId": field(html, "Parcel ID"),
        "location": field(html, "Location"),
        "owner": field(html, "Owner"),
        "ownerCity": field(html, "City"),
        "ownerState": field(html, "State"),
        "saleDate": field(html, "Sale Date"),
        "salePrice": field(html, "Sale Price"),
        "grantor": field(html, "Grantor(Seller)"),
        "assessYear": field(html, "Year"),
        "buildingValue": field(html, "Building Value"),
        "xtraFeaturesValue": field(html, "Xtra Features Value"),
        "landArea": field(html, "Land Area"),
        "landValue": field(html, "Land Value"),
        "totalValue": field(html, "Total Value"),
    }
    rec.update(narrative_fields(html))
    return rec

def load_set(path, key=str):
    s = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line:
                    s.add(key(line))
    return s

def already_done_accounts():
    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for line in f:
                try:
                    done.add(json.loads(line)["accountNumber"])
                except Exception:
                    pass
    return done

def polite_get(s, url, **kw):
    """Returns the response, or None after MAX_RETRIES transient failures
    (403s retry forever since they're a known recoverable block, not counted)."""
    attempt = 0
    while True:
        try:
            r = s.get(url, timeout=25, **kw)
        except requests.RequestException as e:
            attempt += 1
            print(f"network error {e} (attempt {attempt}/{MAX_RETRIES})", file=sys.stderr)
            if attempt >= MAX_RETRIES:
                return None
            time.sleep(15 * attempt)
            continue
        if r.status_code == 403:
            print(f"403 on {url}, backing off {BACKOFF_403}s", file=sys.stderr)
            time.sleep(BACKOFF_403)
            continue
        time.sleep(DELAY + random.uniform(0, 1.0))
        return r

def search_letter(s, letter):
    r = polite_get(s, f"{BASE}/SearchResults.asp", params={"SearchSubmitted": "yes", "SearchStreetName": letter})
    if r is None:
        return None
    ids = set(int(n) for n in re.findall(r"AccountNumber=(\d+)", r.text))
    m = re.search(r"page\s+1\s+of\s+(\d+)", r.text, re.I)
    total_pages = int(m.group(1)) if m else 1
    for page in range(2, total_pages + 1):
        r = polite_get(s, f"{BASE}/SearchResults.asp", params={"page": page})
        if r is None:
            return None  # partial result set isn't safe to treat as complete
        ids |= set(int(n) for n in re.findall(r"AccountNumber=(\d+)", r.text))
    return sorted(ids)

def fetch_account(s, n):
    r1 = polite_get(s, f"{BASE}/Summary.asp", params={"AccountNumber": n})
    if r1 is None:
        return None
    r2 = polite_get(s, f"{BASE}/summary-bottom.asp")
    if r2 is None:
        return None
    return parse_record(r2.text, n)

def main():
    done_accounts = already_done_accounts()
    done_letters = load_set(LETTERS_DONE)
    print(f"{len(done_accounts)} accounts already scraped, {len(done_letters)} letters already done", file=sys.stderr)
    s = requests.Session()
    s.headers.update(HEADERS)
    found = 0
    with open(OUT, "a") as out, open(LETTERS_DONE, "a") as ldone:
        for letter in LETTERS:
            if letter in done_letters:
                continue
            ids = search_letter(s, letter)
            if ids is None:
                print(f"letter={letter} search failed, will retry next run", file=sys.stderr)
                continue
            print(f"letter={letter} -> {len(ids)} accounts", file=sys.stderr)
            letter_complete = True
            for n in ids:
                if n in done_accounts:
                    continue
                rec = fetch_account(s, n)
                if rec:
                    out.write(json.dumps(rec) + "\n")
                    out.flush()
                    done_accounts.add(n)
                    found += 1
                else:
                    print(f"account={n} failed, will retry next run", file=sys.stderr)
                    letter_complete = False
            if letter_complete:
                ldone.write(letter + "\n")
                ldone.flush()
    print(f"done. found={found}", file=sys.stderr)

if __name__ == "__main__":
    main()
