"""Decision-relevant checks:
(1) sensitivity of the main choice (⭐) to R-star conventions on the six control cases;
(2) empirical size of reference-probability moves (pre-match -> close) to calibrate the ±2 point band.
Usage: python3 -I sensitivity.py SCRIPTS_DIR SCRATCHPAD_DIR
"""
import sys, io, contextlib, glob, os, math
sys.path.insert(0, sys.argv[1])
import calc
import numpy as np, pandas as pd

S = sys.argv[2]
with contextlib.redirect_stdout(io.StringIO()):
    import cases_build as cb  # builds legs (prints suppressed)

CASES = {"C1": cb.C1, "C2": cb.C2, "C3": cb.C3, "C4": cb.C4, "C5": cb.C5, "C6 avant": cb.C6_before, "C6 après": cb.C6_after}

def rebuild(legs, band_ind, band_wmx, method):
    out = []
    for l in legs:
        # recompute p with chosen de-vig if reference known in cases_build (approximation: keep p, adjust band)
        b = band_wmx if l.quality == "B" and l.band >= 0.03 else band_ind
        out.append(calc.Leg(l.rid, l.match, l.sport, l.odds, l.p, b, l.quality, l.gate, label=l.label, group=l.group))
    return out

def main_choice(legs, lo, hi, tol):
    calc.TOL = tol
    r = calc.rstar(calc.enumerate_tickets(legs, lo=lo, hi=hi))
    return "+".join(r[0]["rids"]) if r else "—"

print("(1) Sensibilité du choix principal ⭐ aux conventions (zone, tolérance, fourchette)")
grid = []
for tol in (0.005, 0.01, 0.02):
    for band in (0.015, 0.02, 0.03):
        for lo, hi in ((1.40, 4.0), (1.50, 4.0), (1.60, 3.5)):
            grid.append((tol, band, lo, hi))
base = (0.01, 0.02, 1.50, 4.0)
summary = {}
for name, legs in CASES.items():
    picks = {}
    for tol, band, lo, hi in grid:
        L = rebuild(legs, band, max(band, 0.03), "power")
        picks[(tol, band, lo, hi)] = main_choice(L, lo, hi, tol)
    b = picks[base]
    same = sum(1 for v in picks.values() if v == b)
    alts = sorted({v for v in picks.values() if v != b})
    summary[name] = (b, same, len(picks), alts)
    print(f"  {name:9s} défaut={b:10s} identique dans {same}/{len(picks)} réglages ; autres choix : {', '.join(alts) if alts else 'aucun'}")
calc.TOL = 0.01

print("\n(2) Méthode de retrait de marge : le choix change-t-il (power vs multiplicative) ?")
def legs_with_method(legs_spec, method):
    pass
# recompute C1..C6 with multiplicative de-vig using the raw odds stored in cases_build via mk() calls is not kept;
# instead evaluate the effect per leg: difference between power and multiplicative p for each reference market used.
refs = {
    "C1": [[1.27, 4.05], [1.42, 2.98], [1.19, 5.10], [1.24, 4.40], [1.52, 2.66], [1.33, 3.55], [1.72, 3.90, 5.20]],
    "C2": [[1.30, 3.90], [1.50, 2.70], [1.26, 4.10], [1.36, 3.35], [1.44, 4.80, 8.00], [1.68, 4.00, 5.40], [1.60, 4.10, 6.00]],
    "C6 après": [[1.42, 3.00], [1.17, 5.30], [1.25, 4.30], [1.53, 2.62], [1.60, 4.20, 5.80]],
}
for name, mk_refs in refs.items():
    legs = CASES[name]
    alt = []
    for l, ref in zip(legs, mk_refs):
        pm = calc.devig_mult(ref)[0]
        alt.append(calc.Leg(l.rid, l.match, l.sport, l.odds, pm, l.band, l.quality, l.gate, label=l.label, group=l.group))
    pick_p = main_choice(legs, 1.5, 4.0, 0.01); pick_m = main_choice(alt, 1.5, 4.0, 0.01)
    dmax = max(abs(a.p - l.p) for a, l in zip(alt, legs))
    print(f"  {name:9s} power -> {pick_p:10s} | multiplicative -> {pick_m:10s} | écart max de probabilité entre méthodes {dmax*100:.1f} pts")

print("\n(3) Taille réelle des mouvements de la probabilité de référence (avant-match -> clôture)")
frames = []
for f in sorted(glob.glob(os.path.join(S, "data_fb", "*_*.csv"))):
    lg, se = os.path.basename(f)[:-4].split("_")
    if se not in ("2223", "2324", "2425", "2526"): continue
    x = pd.read_csv(f, encoding="latin-1", on_bad_lines="skip"); frames.append(x)
fb = pd.concat(frames, ignore_index=True)
cols_pre, cols_close = ["PSH", "PSD", "PSA"], ["PSCH", "PSCD", "PSCA"]
O1 = fb[cols_pre].apply(pd.to_numeric, errors="coerce").to_numpy(float)
O2 = fb[cols_close].apply(pd.to_numeric, errors="coerce").to_numpy(float)
ok = np.all(np.isfinite(O1), 1) & np.all(np.isfinite(O2), 1) & np.all(O1 > 1, 1) & np.all(O2 > 1, 1)
d = []
for a, b in zip(O1[ok], O2[ok]):
    pa, pb = calc.devig_power(list(a)), calc.devig_power(list(b))
    fav = int(np.argmin(a[[0, 2]]) * 2)
    d.append(pb[fav] - pa[fav])
d = np.array(d)
print(f"  Football (Pinnacle avant-match -> clôture, favori, n={len(d)}) : écart absolu médian {np.median(abs(d))*100:.1f} pts ; 75e centile {np.percentile(abs(d),75)*100:.1f} ; 90e centile {np.percentile(abs(d),90)*100:.1f} ; part > 2 pts {np.mean(abs(d)>0.02):.0%}")
for lg in ("nba", "nhl"):
    fs = sorted(glob.glob(os.path.join(S, "data_us", f"{lg}_*.csv")))
    x = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
    dd = []
    for _, r in x.iterrows():
        try:
            if min(r.ml_h_open, r.ml_a_open, r.ml_h_close, r.ml_a_close) > 1:
                po = calc.devig_power([r.ml_h_open, r.ml_a_open])[0]; pc = calc.devig_power([r.ml_h_close, r.ml_a_close])[0]
                dd.append(pc - po)
        except Exception:
            pass
    dd = np.array(dd)
    print(f"  {lg.upper()} (ESPN BET ouverture -> clôture, n={len(dd)}) : écart absolu médian {np.median(abs(dd))*100:.1f} pts ; 75e centile {np.percentile(abs(dd),75)*100:.1f} ; 90e centile {np.percentile(abs(dd),90)*100:.1f} ; part > 2 pts {np.mean(abs(dd)>0.02):.0%}")
