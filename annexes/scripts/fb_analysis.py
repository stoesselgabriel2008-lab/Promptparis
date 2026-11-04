"""Football market study on football-data.co.uk files.
Usage: python3 -I fb_analysis.py DATA_DIR
Train (mapping Elo->probabilities, base rates): seasons 1718, 1819, 2122 (ghost-game seasons 1920/2021 excluded from fit).
Elo warm-up from 1516. Test (out-of-sample): 2223, 2324, 2425, 2526.
"""
import glob, os, sys, math
import numpy as np, pandas as pd
from scipy.optimize import brentq, minimize

D = sys.argv[1]
TRAIN = {"1718", "1819", "2122"}
TEST = {"2223", "2324", "2425", "2526"}
rng = np.random.default_rng(7)

frames = []
for f in sorted(glob.glob(os.path.join(D, "*_*.csv"))):
    lg, se = os.path.basename(f)[:-4].split("_")
    try:
        x = pd.read_csv(f, encoding="latin-1", on_bad_lines="skip")
    except Exception as e:
        print("skip", f, e); continue
    x["League"], x["Season"] = lg, se
    frames.append(x)
df = pd.concat(frames, ignore_index=True)
df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"])
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
df = df.dropna(subset=["Date"]).sort_values(["Date", "League"]).reset_index(drop=True)
df["y"] = df["FTR"].map({"H": 0, "D": 1, "A": 2})
print("matches", len(df), "| test", df.Season.isin(TEST).sum(), "| train", df.Season.isin(TRAIN).sum())

# ---------------- de-vig ----------------
def q_of(odds):
    o = np.asarray(odds, float)
    return 1.0 / o

def devig_mult(odds):
    q = q_of(odds); return q / q.sum()

def devig_power(odds):
    q = q_of(odds)
    if not np.all(np.isfinite(q)) or q.sum() <= 1.0:
        return q / q.sum()
    k = brentq(lambda k: np.sum(q ** k) - 1.0, 1.0, 50.0)
    return q ** k

def devig_shin(odds):
    q = q_of(odds); S = q.sum()
    if S <= 1.0:
        return q / S
    def p_of(z):
        return (np.sqrt(z * z + 4 * (1 - z) * q * q / S) - z) / (2 * (1 - z))
    z = brentq(lambda z: p_of(z).sum() - 1.0, 0.0, 0.999)
    p = p_of(z); return p / p.sum()

METHODS = {"mult": devig_mult, "power": devig_power, "shin": devig_shin}

def market(cols, method="power"):
    """returns (N,k) array of fair probabilities or NaN rows, and overround array"""
    if not all(c in df.columns for c in cols):
        return None, None
    O = df[cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    P = np.full(O.shape, np.nan); OR = np.full(len(O), np.nan)
    ok = np.all(np.isfinite(O), axis=1) & np.all(O > 1.0, axis=1)
    f = METHODS[method]
    for i in np.where(ok)[0]:
        P[i] = f(O[i]); OR[i] = np.sum(1 / O[i]) - 1
    return P, OR

# ---------------- Elo (per league, simple, a priori parameters) ----------------
K, HA, REG = 20.0, 60.0, 0.2
elo_diff = np.full(len(df), np.nan)
ratings = {}
last_season = {}
for lg, g in df.groupby("League", sort=False):
    R = {}
    prev = None
    for i in g.index:
        se = df.at[i, "Season"]
        if se != prev:
            if R:
                vals = sorted(R.values())
                m = np.mean(vals)
                for t in R: R[t] = R[t] + REG * (m - R[t])
                newbie = np.mean(vals[:3])
            else:
                newbie = 1500.0
            prev = se
        h, a = df.at[i, "HomeTeam"], df.at[i, "AwayTeam"]
        rh, ra = R.get(h, newbie), R.get(a, newbie)
        elo_diff[i] = rh - ra
        e = 1 / (1 + 10 ** (-(rh + HA - ra) / 400))
        s = {0: 1.0, 1: 0.5, 2: 0.0}[df.at[i, "y"]]
        gd = abs(df.at[i, "FTHG"] - df.at[i, "FTAG"])
        G = 1 if gd <= 1 else (1.5 if gd == 2 else (11 + gd) / 8)
        R[h] = rh + K * G * (s - e); R[a] = ra - K * G * (s - e)
df["elo_diff"] = elo_diff

# ordered logit on elo diff, fitted on TRAIN
def ol_probs(theta, x):
    b, t1, t2 = theta
    pa = 1 / (1 + np.exp(-(t1 - b * x)))          # P(away)
    pad = 1 / (1 + np.exp(-(t2 - b * x)))         # P(away or draw)
    pa = np.clip(pa, 1e-6, 1); pad = np.clip(pad, pa + 1e-6, 1 - 1e-6)
    return np.column_stack([1 - pad, pad - pa, pa])

tr = df.Season.isin(TRAIN).to_numpy()
te = df.Season.isin(TEST).to_numpy()
xtr, ytr = df.elo_diff.to_numpy()[tr] / 100, df.y.to_numpy()[tr]
nll = lambda th: -np.mean(np.log(ol_probs(th, xtr)[np.arange(len(ytr)), ytr]))
th = minimize(nll, [0.3, -0.6, 0.5], method="Nelder-Mead", options={"maxiter": 4000}).x
P_elo = ol_probs(th, df.elo_diff.to_numpy() / 100)
clim = np.bincount(ytr, minlength=3) / len(ytr)
print("ordered-logit theta", np.round(th, 3), "| train base rates H/D/A", np.round(clim, 3))

# ---------------- scoring ----------------
def scores(P, y):
    ok = np.all(np.isfinite(P), axis=1)
    P, y = P[ok], y[ok]
    Y = np.eye(P.shape[1])[y]
    brier = np.mean(np.sum((P - Y) ** 2, axis=1))
    ll = -np.mean(np.log(np.clip(P[np.arange(len(y)), y], 1e-12, 1)))
    cP, cY = np.cumsum(P, 1)[:, :-1], np.cumsum(Y, 1)[:, :-1]
    rps = np.mean(np.sum((cP - cY) ** 2, axis=1) / (P.shape[1] - 1))
    return ok.sum(), brier, rps, ll, ok

yte = df.y.to_numpy()[te]
print("\n=== 1X2, test seasons 2022/23-2025/26 (out-of-sample) ===")
print(f"{'forecast':38s} {'n':>6s} {'Brier':>7s} {'RPS':>7s} {'LogLoss':>8s} {'BSS':>7s} {'RPSS':>7s} {'LLSS':>7s}")
Pc = np.tile(clim, (te.sum(), 1))
n0, b0, r0, l0, _ = scores(Pc, yte)
res = {}
cands = [("Climatology (train H/D/A freq)", Pc), ("Elo + ordered logit (a priori K)", P_elo[te])]
for name, cols in [("Bet365 pre-match", ["B365H", "B365D", "B365A"]), ("Pinnacle pre-match", ["PSH", "PSD", "PSA"]),
                   ("Bet365 closing", ["B365CH", "B365CD", "B365CA"]), ("Pinnacle closing", ["PSCH", "PSCD", "PSCA"]),
                   ("Market avg closing", ["AvgCH", "AvgCD", "AvgCA"])]:
    for m in (["mult", "power", "shin"] if name == "Pinnacle closing" else ["power"]):
        P, OR = market(cols, m)
        if P is None: continue
        res[(name, m)] = (P, OR)
        cands.append((f"{name} [{m}]", P[te]))
# common sample: rows where all market forecasts exist
common = np.ones(te.sum(), bool)
for _, P in cands: common &= np.all(np.isfinite(P), axis=1)
for name, P in cands:
    n, b, r, l, _ = scores(P[common], yte[common])
    _, b0c, r0c, l0c, _ = scores(Pc[common], yte[common])
    print(f"{name:38s} {n:6d} {b:7.4f} {r:7.4f} {l:8.4f} {1-b/b0c:7.3f} {1-r/r0c:7.3f} {1-l/l0c:7.3f}")

# bootstrap CI of logloss difference Elo vs Pinnacle closing power and B365 pre vs Pinn closing
def boot_diff(P1, P2, y, B=1000):
    l1 = -np.log(np.clip(P1[np.arange(len(y)), y], 1e-12, 1)); l2 = -np.log(np.clip(P2[np.arange(len(y)), y], 1e-12, 1))
    d = l1 - l2; idx = rng.integers(0, len(d), (B, len(d)))
    bs = d[idx].mean(1); return d.mean(), np.percentile(bs, [2.5, 97.5])
Ppin = res[("Pinnacle closing", "power")][0][te][common]
for nm, P in [("Elo - PinnacleClose", P_elo[te][common]), ("Pinn mult - power", res[("Pinnacle closing", "mult")][0][te][common]),
              ("Pinn shin - power", res[("Pinnacle closing", "shin")][0][te][common]), ("B365 pre - PinnClose", res[("Bet365 pre-match", "power")][0][te][common])]:
    m, ci = boot_diff(P, Ppin, yte[common]); print(f"logloss diff {nm:22s} {m:+.4f}  95%CI [{ci[0]:+.4f},{ci[1]:+.4f}]")

# ---------------- margins ----------------
print("\n=== Average overround (sum 1/odds - 1), test seasons ===")
def ovr(cols):
    if not all(c in df.columns for c in cols): return np.nan, 0
    O = df.loc[te, cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    ok = np.all(np.isfinite(O), 1) & np.all(O > 1, 1)
    return np.mean(np.sum(1 / O[ok], 1) - 1), ok.sum()
for nm, cols in [("1X2 Bet365 closing", ["B365CH", "B365CD", "B365CA"]), ("1X2 Pinnacle closing", ["PSCH", "PSCD", "PSCA"]),
                 ("1X2 market avg closing", ["AvgCH", "AvgCD", "AvgCA"]), ("1X2 market MAX closing", ["MaxCH", "MaxCD", "MaxCA"]),
                 ("O/U2.5 Bet365 closing", ["B365C>2.5", "B365C<2.5"]), ("O/U2.5 Pinnacle closing", ["PC>2.5", "PC<2.5"]),
                 ("O/U2.5 avg closing", ["AvgC>2.5", "AvgC<2.5"]), ("AH Bet365 closing", ["B365CAHH", "B365CAHA"]),
                 ("AH Pinnacle closing", ["PCAHH", "PCAHA"])]:
    m, n = ovr(cols); print(f"{nm:26s} {m*100:6.2f}%  (n={n})")

# ---------------- calibration of Pinnacle closing (power) ----------------
print("\n=== Calibration, Pinnacle closing power de-vig, test seasons (favourite side H or A) ===")
P = res[("Pinnacle closing", "power")][0][te]
ok = np.all(np.isfinite(P), 1)
Pt, yt = P[ok], yte[ok]
fav = np.where(Pt[:, 0] >= Pt[:, 2], 0, 2)
pf = Pt[np.arange(len(Pt)), fav]; wf = (yt == fav).astype(float)
bins = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
for lo, hi in zip(bins[:-1], bins[1:]):
    s = (pf >= lo) & (pf < hi)
    if s.sum() >= 30:
        se = math.sqrt(wf[s].mean() * (1 - wf[s].mean()) / s.sum())
        print(f"fav p in [{lo:.1f},{hi:.1f}): n={s.sum():5d} mean_p={pf[s].mean():.3f} observed={wf[s].mean():.3f} (+/-{1.96*se:.3f})")
pdraw = Pt[:, 1]; wd = (yt == 1).astype(float)
for lo, hi in [(0.0, 0.22), (0.22, 0.26), (0.26, 0.30), (0.30, 1)]:
    s = (pdraw >= lo) & (pdraw < hi)
    if s.sum() >= 30:
        print(f"draw p in [{lo:.2f},{hi:.2f}): n={s.sum():5d} mean_p={pdraw[s].mean():.3f} observed={wd[s].mean():.3f}")

# ---------------- favourite-longshot: ROI by odds bucket ----------------
print("\n=== Flat-stake ROI by odds bucket, all 1X2 outcomes, test seasons ===")
def roi_bucket(cols, label):
    O = df.loc[te, cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    ok = np.all(np.isfinite(O), 1) & np.all(O > 1, 1)
    O, yy = O[ok], yte[ok]
    R = np.where(np.eye(3)[yy] == 1, O, 0.0) - 1
    o, r = O.ravel(), R.ravel()
    out = []
    for lo, hi in [(1, 1.5), (1.5, 2), (2, 3), (3, 5), (5, 10), (10, 1e9)]:
        s = (o >= lo) & (o < hi)
        if s.sum():
            out.append(f"[{lo:g},{hi if hi<1e8 else 'inf'}) n={s.sum()} ROI={r[s].mean()*100:+.1f}%±{1.96*r[s].std()/math.sqrt(s.sum())*100:.1f}")
    print(label + ": " + " | ".join(out))
roi_bucket(["B365CH", "B365CD", "B365CA"], "Bet365 closing")
roi_bucket(["PSCH", "PSCD", "PSCA"], "Pinnacle closing")

# ---------------- price vs sharp reference ----------------
print("\n=== Does a price above the de-vigged sharp reference pay? (test seasons, flat stakes) ===")
def ev_test(odds_cols, ref_P, thr, label):
    O = df.loc[te, odds_cols].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    Pref = ref_P[te]
    ok = np.all(np.isfinite(O), 1) & np.all(np.isfinite(Pref), 1)
    O, Pr, yy = O[ok], Pref[ok], yte[ok]
    ev = O * Pr - 1
    sel = ev > thr
    R = (np.where(np.eye(3)[yy] == 1, O, 0.0) - 1)[sel]
    if sel.sum() == 0:
        print(f"{label}: no bets"); return
    se = R.std() / math.sqrt(len(R))
    print(f"{label:62s} bets={sel.sum():6d} ({sel.sum()/ok.sum():.1%} of matches) ROI={R.mean()*100:+.2f}% (95% ±{1.96*se*100:.2f}) mean est. EV={ev[sel].mean()*100:+.2f}%")
Ppc = res[("Pinnacle closing", "power")][0]
Ppp = res[("Pinnacle pre-match", "power")][0]
for thr in (0.0, 0.03):
    ev_test(["B365CH", "B365CD", "B365CA"], Ppc, thr, f"Bet365 closing vs Pinnacle closing fair, EV>{thr:.0%}")
    ev_test(["B365H", "B365D", "B365A"], Ppp, thr, f"Bet365 pre-match vs Pinnacle pre-match fair, EV>{thr:.0%}")
    ev_test(["MaxCH", "MaxCD", "MaxCA"], Ppc, thr, f"Best price closing vs Pinnacle closing fair, EV>{thr:.0%}")
for thr in (0.03, 0.08):
    ev_test(["B365CH", "B365CD", "B365CA"], P_elo, thr, f"Bet365 closing vs Elo model, EV>{thr:.0%}")

# ---------------- totals and AH ----------------
print("\n=== Over/Under 2.5 and Asian handicap (half lines), test seasons ===")
tot = (df.FTHG + df.FTAG).to_numpy()
yo = (tot > 2.5).astype(int)
base_over = yo[tr].mean()
Pou, _ = market(["PC>2.5", "PC<2.5"], "power")
if Pou is not None:
    ok = te & np.all(np.isfinite(Pou), 1)
    p = Pou[ok, 0]; yy = yo[ok]
    b = np.mean((p - yy) ** 2); bb = np.mean((base_over - yy) ** 2)
    l = -np.mean(yy * np.log(p) + (1 - yy) * np.log(1 - p)); lb = -np.mean(yy * np.log(base_over) + (1 - yy) * np.log(1 - base_over))
    print(f"O/U 2.5 Pinnacle closing: n={ok.sum()} base over rate(train)={base_over:.3f} test over rate={yy.mean():.3f} Brier={b:.4f} vs base {bb:.4f} BSS={1-b/bb:.3f} LLSS={1-l/lb:.3f}")
    for lo, hi in [(0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 1)]:
        s = (p >= lo) & (p < hi)
        if s.sum() >= 30: print(f"   p_over in [{lo:.1f},{hi:.1f}): n={s.sum()} mean_p={p[s].mean():.3f} observed={yy[s].mean():.3f}")
if all(c in df.columns for c in ["AHCh", "PCAHH", "PCAHA"]):
    line = pd.to_numeric(df["AHCh"], errors="coerce").to_numpy()
    half = np.isfinite(line) & (np.abs(np.abs(line) % 1 - 0.5) < 1e-9)
    Pah, _ = market(["PCAHH", "PCAHA"], "power")
    gd = (df.FTHG - df.FTAG).to_numpy()
    ok = te & half & np.all(np.isfinite(Pah), 1)
    p = Pah[ok, 0]; yy = ((gd[ok] + line[ok]) > 0).astype(int)
    b = np.mean((p - yy) ** 2); bb = np.mean((0.5 - yy) ** 2)
    print(f"AH half-lines Pinnacle closing: n={ok.sum()} home-cover rate={yy.mean():.3f} Brier={b:.4f} vs coin {bb:.4f} BSS={1-b/bb:.3f}")

# ---------------- combos: compounding the margin ----------------
print("\n=== Combos of favourites (Bet365 closing, odds<=2.0, distinct matches same day), test seasons ===")
O3 = df[["B365CH", "B365CD", "B365CA"]].apply(pd.to_numeric, errors="coerce").to_numpy(float)
Pp = res[("Pinnacle closing", "power")][0]
cand = []
for i in np.where(te)[0]:
    if not (np.all(np.isfinite(O3[i])) and np.all(np.isfinite(Pp[i]))): continue
    j = 0 if O3[i, 0] <= O3[i, 2] else 2
    if O3[i, j] <= 2.0:
        cand.append((df.at[i, "Date"], O3[i, j], Pp[i, j], int(df.at[i, "y"] == j)))
cd = pd.DataFrame(cand, columns=["Date", "o", "p", "w"])
for k in (1, 2, 3, 4, 5):
    rets, exps = [], []
    for d, g in cd.groupby("Date"):
        if len(g) < k: continue
        for _ in range(min(10, math.comb(len(g), k))):
            s = g.sample(k, random_state=int(rng.integers(1e9)))
            rets.append(np.prod(s.o) * s.w.prod() - 1); exps.append(np.prod(s.o * s.p) - 1)
    rets = np.array(rets)
    print(f"k={k}: combos={len(rets):6d} realized ROI={rets.mean()*100:+.1f}% (±{1.96*rets.std()/math.sqrt(len(rets))*100:.1f}, legs reused) | expected vs Pinnacle fair={np.mean(exps)*100:+.1f}% | hit rate={np.mean(rets>-1):.3f}")
print("done")
