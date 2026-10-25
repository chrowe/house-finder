"""One-time backfill: adds Finished Area (SF) to every account already in
accounts.jsonl, scraped before enrich.py fetched RecordCard.asp (see #33).

Reuses enrich.py's session/search machinery (a valid Summary.asp?AccountNumber=N
call still requires the account to be in the current session's last search
resultset, same as a fresh scrape), but skips summary-bottom.asp since we
already have everything from that page — only RecordCard.asp is new.

Usage: python3 backfill_sqft.py
Resumable: accounts that already have a (possibly empty-but-tried) finishedAreaSf
are skipped; accounts.jsonl is rewritten atomically every CHECKPOINT_EVERY accounts.
A future full `enrich.py` run from scratch no longer needs this script — it fetches
RecordCard.asp itself now.
"""
import json, os, re, sys
import requests
import enrich

OUT = "accounts.jsonl"
CHECKPOINT_EVERY = 50

def load_records():
    records = []
    with open(OUT) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def save_records(records):
    tmp = OUT + ".tmp"
    with open(tmp, "w") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    os.replace(tmp, OUT)

def fetch_sqft(s, account_number):
    r1 = enrich.polite_get(s, f"{enrich.BASE}/Summary.asp", params={"AccountNumber": account_number})
    if r1 is None:
        return None
    r2 = enrich.polite_get(s, f"{enrich.BASE}/RecordCard.asp")
    if r2 is None:
        return None
    return enrich.finished_area_sf(r2.text) or "N/A"

def main():
    records = load_records()
    by_account = {r["accountNumber"]: r for r in records}
    pending_total = sum(1 for r in records if not r.get("finishedAreaSf"))
    print(f"{len(records)} accounts total, {pending_total} need sqft backfill", file=sys.stderr)

    s = requests.Session()
    s.headers.update(enrich.HEADERS)
    done = 0
    for letter in enrich.LETTERS:
        ids = enrich.search_letter(s, letter)
        if ids is None:
            print(f"letter={letter} search failed, will retry next run", file=sys.stderr)
            continue
        pending = [n for n in ids if n in by_account and not by_account[n].get("finishedAreaSf")]
        if not pending:
            continue
        print(f"letter={letter} -> {len(pending)} of {len(ids)} need backfill", file=sys.stderr)
        for n in pending:
            sqft = fetch_sqft(s, n)
            if sqft is None:
                print(f"account={n} failed, will retry next run", file=sys.stderr)
                continue
            by_account[n]["finishedAreaSf"] = sqft
            done += 1
            if done % CHECKPOINT_EVERY == 0:
                save_records(records)
                print(f"checkpoint: {done} backfilled", file=sys.stderr)
    save_records(records)
    print(f"done. backfilled {done} accounts", file=sys.stderr)

if __name__ == "__main__":
    main()
