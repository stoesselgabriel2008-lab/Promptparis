"""Collect regular-season NBA/NHL results + pre-game odds (open/close) from ESPN public APIs.
Usage: python3 -I espn_collect.py OUT_DIR
Polite: 4 workers, small sleeps, retries with backoff.
"""
import csv, json, sys, time, datetime as dt, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

OUT = sys.argv[1]
SEASONS = {
    ("basketball", "nba"): [("2024-25", "2024-10-15", "2025-04-20"), ("2025-26", "2025-10-15", "2026-04-20")],
    ("hockey", "nhl"): [("2024-25", "2024-10-01", "2025-04-20"), ("2025-26", "2025-10-01", "2026-04-20")],
}


def get(url, tries=5):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa
            time.sleep(1.5 * (k + 1))
    return None


def dates(a, b):
    d = dt.date.fromisoformat(a)
    e = dt.date.fromisoformat(b)
    while d <= e:
        yield d
        d += dt.timedelta(days=1)


def scoreboard(sport, league, day):
    time.sleep(0.15)
    u = f"https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/scoreboard?dates={day:%Y%m%d}&limit=50"
    d = get(u)
    rows = []
    if not d:
        return rows
    for e in d.get("events", []):
        if e.get("season", {}).get("type") != 2:
            continue
        st = e.get("status", {})
        if st.get("type", {}).get("name") != "STATUS_FINAL":
            continue
        c = e["competitions"][0]
        h = next(t for t in c["competitors"] if t["homeAway"] == "home")
        a = next(t for t in c["competitors"] if t["homeAway"] == "away")
        rows.append({
            "id": e["id"], "date": e["date"], "home": h["team"]["abbreviation"], "away": a["team"]["abbreviation"],
            "hs": int(h.get("score", 0)), "as": int(a.get("score", 0)), "period": st.get("period"),
            "detail": st.get("type", {}).get("detail"), "neutral": c.get("neutralSite"),
        })
    return rows


def dec(o, *path):
    for p in path:
        if not isinstance(o, dict):
            return None
        o = o.get(p)
    try:
        return float(o) if o is not None else None
    except (TypeError, ValueError):
        return None


def strv(o, *path):
    for p in path:
        if not isinstance(o, dict):
            return None
        o = o.get(p)
    return o


def odds(sport, league, gid):
    time.sleep(0.15)
    u = f"https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{gid}/competitions/{gid}/odds"
    d = get(u)
    if not d:
        return {}
    items = [it for it in d.get("items", []) if "live" not in (strv(it, "provider", "name") or "").lower()]
    if not items:
        return {}
    it = sorted(items, key=lambda x: strv(x, "provider", "priority") or 9)[0]
    H, A = it.get("homeTeamOdds", {}), it.get("awayTeamOdds", {})
    r = {"provider": strv(it, "provider", "name")}
    for tag in ("open", "close"):
        r[f"ml_h_{tag}"] = dec(H, tag, "moneyLine", "decimal")
        r[f"ml_a_{tag}"] = dec(A, tag, "moneyLine", "decimal")
        r[f"sp_h_line_{tag}"] = strv(H, tag, "pointSpread", "american")
        r[f"sp_h_{tag}"] = dec(H, tag, "spread", "decimal")
        r[f"sp_a_{tag}"] = dec(A, tag, "spread", "decimal")
        r[f"tot_line_{tag}"] = strv(it, tag, "total", "american")
        r[f"over_{tag}"] = dec(it, tag, "over", "decimal")
        r[f"under_{tag}"] = dec(it, tag, "under", "decimal")
    return r


def main():
    for (sport, league), seasons in SEASONS.items():
        for label, a, b in seasons:
            with ThreadPoolExecutor(4) as ex:
                games = [g for rows in ex.map(lambda d: scoreboard(sport, league, d), list(dates(a, b))) for g in rows]
            seen, uniq = set(), []
            for g in games:
                if g["id"] not in seen:
                    seen.add(g["id"]); uniq.append(g)
            print(league, label, "games", len(uniq), flush=True)
            with ThreadPoolExecutor(4) as ex:
                ods = list(ex.map(lambda g: odds(sport, league, g["id"]), uniq))
            fn = f"{OUT}/{league}_{label}.csv"
            keys = list(uniq[0].keys()) + sorted({k for o in ods for k in o})
            with open(fn, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=keys)
                w.writeheader()
                for g, o in zip(uniq, ods):
                    w.writerow({**g, **o})
            print(league, label, "written", fn, "with odds", sum(1 for o in ods if o.get("ml_h_close")), flush=True)


if __name__ == "__main__":
    main()
