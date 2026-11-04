"""NBA / NHL market study on ESPN-collected data (ESPN BET / main provider open & close lines).
Usage: python3 -I us_analysis.py DATA_DIR
Train = 2024-25 regular season (Elo warm-up + logistic mapping + base rate). Test = 2025-26 regular season.
"""
import sys, math, os
import numpy as np, pandas as pd
from scipy.optimize import brentq, minimize

D = sys.argv[1]
rng = np.random.default_rng(11)

def devig_power(q):
    q = np.asarray(q, float)
    if q.sum() <= 1: return q / q.sum()
    k = brentq(lambda k: np.sum(q ** k) - 1, 1.0, 60.0)
    return q ** k

def load(league):
    fs = [os.path.join(D, f"{league}_{s}.csv") for s in ("2024-25", "2025-26")]
    xs = []
    for f, s in zip(fs, ("2024-25", "2025-26")):
        if os.path.exists(f):
            x = pd.read_csv(f); x["season"] = s; xs.append(x)
    df = pd.concat(xs, ignore_index=True)
    cnt = pd.concat([df.home, df.away]).value_counts()
    real = set(cnt[cnt >= 30].index)  # drops All-Star / 4 Nations exhibition teams
    n0 = len(df); df = df[df.home.isin(real) & df.away.isin(real)].copy()
    print(league, "exhibition rows dropped:", n0 - len(df))
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)
    df["y"] = (df["hs"] > df["as"]).astype(int)
    return df

def fair(df, tag):
    P = np.full(len(df), np.nan); OR = np.full(len(df), np.nan)
    h, a = df[f"ml_h_{tag}"].to_numpy(float), df[f"ml_a_{tag}"].to_numpy(float)
    for i in range(len(df)):
        if np.isfinite(h[i]) and np.isfinite(a[i]) and h[i] > 1 and a[i] > 1:
            q = np.array([1 / h[i], 1 / a[i]]); OR[i] = q.sum() - 1
            P[i] = devig_power(q)[0]
    return P, OR

def binscores(p, y):
    b = np.mean((p - y) ** 2)
    l = -np.mean(y * np.log(np.clip(p, 1e-9, 1)) + (1 - y) * np.log(np.clip(1 - p, 1e-9, 1)))
    return b, l

def analyse(league, K, regress):
    df = load(league)
    print(f"\n################ {league.upper()} ################")
    print("games by season:", df.season.value_counts().sort_index().to_dict())
    tr, te = (df.season == "2024-25").to_numpy(), (df.season == "2025-26").to_numpy()
    if league == "nhl":
        ot = (df.period > 3)
        print(f"share of games tied after 60 min (OT/SO): 2024-25 {ot[tr].mean():.3f}  2025-26 {ot[te].mean():.3f}")
    # Elo (home advantage learned by logistic mapping)
    R, prev, diff = {}, None, np.zeros(len(df))
    for i in range(len(df)):
        if df.at[i, "season"] != prev and R:
            m = np.mean(list(R.values()))
            for t in R: R[t] += regress * (m - R[t])
        prev = df.at[i, "season"]
        h, a = df.at[i, "home"], df.at[i, "away"]
        rh, ra = R.get(h, 1500.0), R.get(a, 1500.0)
        diff[i] = rh - ra
        e = 1 / (1 + 10 ** (-(rh - ra) / 400)); s = df.at[i, "y"]
        R[h] = rh + K * (s - e); R[a] = ra - K * (s - e)
    df["elo_diff"] = diff
    # logistic mapping fitted on 2024-25 games after 300-game warm-up
    fit = tr.copy(); fit[:300] = False
    x, y = df.elo_diff.to_numpy() / 100, df.y.to_numpy()
    nll = lambda th: -np.mean(y[fit] * np.log(1 / (1 + np.exp(-(th[0] + th[1] * x[fit])))) + (1 - y[fit]) * np.log(1 - 1 / (1 + np.exp(-(th[0] + th[1] * x[fit])))))
    th = minimize(nll, [0.1, 0.3], method="Nelder-Mead").x
    p_elo = 1 / (1 + np.exp(-(th[0] + th[1] * x)))
    base = y[tr].mean()
    pc, orc = fair(df, "close"); po, oro = fair(df, "open")
    ok = te & np.isfinite(pc) & np.isfinite(po)
    yt = y[ok]
    print(f"home-win base rate 2024-25 = {base:.3f}; 2025-26 = {y[te].mean():.3f}; logistic(elo) theta={np.round(th,3)}")
    print(f"{'forecast (test 2025-26)':34s} {'n':>5s} {'Brier':>7s} {'LogLoss':>8s} {'BSS':>7s} {'LLSS':>7s}")
    b0, l0 = binscores(np.full(ok.sum(), base), yt)
    for nm, p in [("Base rate (home win %, 2024-25)", np.full(len(df), base)), ("Elo + logistic (fit 2024-25)", p_elo),
                  ("Market OPEN, power de-vig", po), ("Market CLOSE, power de-vig", pc)]:
        b, l = binscores(p[ok], yt)
        print(f"{nm:34s} {ok.sum():5d} {b:7.4f} {l:8.4f} {1-b/b0:7.3f} {1-l/l0:7.3f}")
    def ll(p): return -(yt * np.log(p) + (1 - yt) * np.log(1 - p))
    for nm, p1, p2 in [("Elo - Close", p_elo[ok], pc[ok]), ("Open - Close", po[ok], pc[ok])]:
        d = ll(p1) - ll(p2); bs = d[rng.integers(0, len(d), (2000, len(d)))].mean(1)
        print(f"logloss diff {nm:12s} {d.mean():+.4f} 95%CI [{np.percentile(bs,2.5):+.4f},{np.percentile(bs,97.5):+.4f}]")
    allok = np.isfinite(pc)
    print(f"avg overround moneyline close: {np.nanmean(orc)*100:.2f}% ; open: {np.nanmean(oro)*100:.2f}%")
    # calibration of favourite, both seasons pooled
    pf = np.where(pc >= 0.5, pc, 1 - pc); wf = np.where(pc >= 0.5, y, 1 - y)
    s0 = allok
    print(f"favourite win rate (close, both seasons): {wf[s0].mean():.3f} (n={s0.sum()}), mean fav prob {pf[s0].mean():.3f}")
    for lo, hi in [(0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]:
        s = s0 & (pf >= lo) & (pf < hi)
        if s.sum() >= 30:
            se = math.sqrt(wf[s].mean() * (1 - wf[s].mean()) / s.sum())
            print(f"   fav p in [{lo:.1f},{hi:.1f}): n={s.sum():4d} mean_p={pf[s].mean():.3f} observed={wf[s].mean():.3f} (±{1.96*se:.3f})")
    if league == "nhl":
        reg_win = wf[s0 & ~ot.to_numpy()].sum() / s0.sum()
        print(f"   NHL favourite wins IN REGULATION: {reg_win:.3f}; games tied after 60': {ot[s0].mean():.3f}")
        for lo, hi in [(0.5, 0.6), (0.6, 0.7), (0.7, 1.0)]:
            s = s0 & (pf >= lo) & (pf < hi)
            if s.sum() >= 30:
                print(f"   fav p(2-way) in [{lo:.1f},{hi:.1f}): win incl OT={wf[s].mean():.3f}  win in 60'={(wf[s] * ~ot.to_numpy()[s]).mean():.3f}  tie after 60'={ot.to_numpy()[s].mean():.3f}")
    # ROI by odds bucket (both sides, close)
    oh, oa = df.ml_h_close.to_numpy(float), df.ml_a_close.to_numpy(float)
    o = np.concatenate([oh[allok], oa[allok]]); w = np.concatenate([y[allok], 1 - y[allok]])
    r = np.where(w == 1, o, 0) - 1
    out = []
    for lo, hi in [(1, 1.3), (1.3, 1.6), (1.6, 2.0), (2.0, 2.6), (2.6, 4), (4, 1e9)]:
        s = (o >= lo) & (o < hi)
        if s.sum(): out.append(f"[{lo:g},{hi if hi<1e8 else 'inf'}) n={s.sum()} ROI={r[s].mean()*100:+.1f}%±{1.96*r[s].std()/math.sqrt(s.sum())*100:.1f}")
    print("ROI by odds bucket (close ML): " + " | ".join(out))
    # spreads & totals at close
    sp = df.sp_h_line_close.astype(str).str.replace("+", "", regex=False)
    line = pd.to_numeric(sp, errors="coerce").to_numpy()
    margin = (df.hs - df["as"]).to_numpy()
    okl = np.isfinite(line) & (np.abs(line % 1 - 0.5) < 1e-9)
    hc = (margin + line > 0)[okl]
    favhome = (line < 0)[okl]
    favcover = np.where(favhome, hc, ~hc)
    print(f"spread (close, half-point lines n={okl.sum()}): home cover {hc.mean():.3f}, favourite cover {favcover.mean():.3f}; avg spread overround {np.nanmean(1/df.sp_h_close+1/df.sp_a_close-1)*100:.2f}%")
    tl = pd.to_numeric(df.tot_line_close, errors="coerce").to_numpy(); tot = (df.hs + df["as"]).to_numpy()
    okt = np.isfinite(tl) & (np.abs(tl % 1 - 0.5) < 1e-9)
    ov = (tot > tl)[okt]
    po_ = np.array([devig_power([1 / a, 1 / b])[0] if (a > 1 and b > 1) else np.nan for a, b in zip(df.over_close.fillna(0), df.under_close.fillna(0))])
    sel = okt & np.isfinite(po_)
    bt = np.mean((po_[sel] - (tot > tl)[sel]) ** 2)
    print(f"totals (close, half-point lines n={okt.sum()}): over rate {ov.mean():.3f}; Brier de-vigged {bt:.4f} vs coin 0.2500; avg total overround {np.nanmean(1/df.over_close+1/df.under_close-1)*100:.2f}%")
    # combos of favourites, same date, distinct games
    df["day"] = df.date.dt.tz_convert("America/New_York").dt.date
    cand = []
    for i in np.where(te & allok)[0]:
        if oh[i] <= oa[i]: cand.append((df.at[i, "day"], oh[i], pc[i], y[i]))
        else: cand.append((df.at[i, "day"], oa[i], 1 - pc[i], 1 - y[i]))
    cd = pd.DataFrame(cand, columns=["day", "o", "p", "w"])
    for k in (1, 2, 3, 4, 5):
        rets, exps = [], []
        for d, g in cd.groupby("day"):
            if len(g) < k: continue
            for _ in range(min(10, math.comb(len(g), k))):
                s = g.sample(k, random_state=int(rng.integers(1e9)))
                rets.append(np.prod(s.o) * s.w.prod() - 1); exps.append(np.prod(s.o * s.p) - 1)
        rets = np.array(rets)
        print(f"   favourites combo k={k}: n={len(rets):5d} realized ROI={rets.mean()*100:+.1f}% (±{1.96*rets.std()/math.sqrt(len(rets))*100:.1f}) expected vs close fair={np.mean(exps)*100:+.1f}% hit={np.mean(rets>-1):.3f}")

analyse("nba", K=20, regress=0.25)
if os.path.exists(os.path.join(D, "nhl_2025-26.csv")):
    analyse("nhl", K=8, regress=0.35)
else:
    print("NHL 2025-26 not collected yet")
