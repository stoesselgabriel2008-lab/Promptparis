"""Design + ground truth for the fictional control cases (C1..C6). Prints R-star results per format."""
import sys, math
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from calc import *


def mk(rid, match, sport, wmx, idx, ref=None, quality="A", gate=False, label="", group=None):
    if ref is not None:
        p = devig_power(ref)[idx]; band = max(0.02, abs(devig_power(ref)[idx] - devig_mult(ref)[idx]))
    else:
        p = devig_power(wmx)[idx]; band = 0.03; quality = "B" if quality == "A" else quality
    return Leg(rid, match, sport, wmx[idx], p, band, quality, gate, label=label, group=group)


def show(title, legs, extra=None):
    print(f"\n===== {title} =====")
    for l in legs:
        print(f"  {l.rid:4s} {l.match:4s} {l.sport:8s} {l.label:34s} o={l.odds:.2f} p={l.p*100:5.1f}% [{l.p_low*100:4.1f}] "
              f"EV={l.ev()*100:+5.1f}% EVp={l.ev_low()*100:+5.1f}% q={l.quality}{' GATE' if l.gate else ''}")
    def best(name, target=None, **kw):
        r = rstar(enumerate_tickets(legs, **kw), target)
        print(f"  {name:28s}", fmt(r[0]) if r else "—")
        for t in r[1:3]:
            print(f"  {'':28s}", fmt(t))
        return r
    main = best("MAIN 1.50-4.00 (t=1.90)", lo=1.50, hi=4.00, target=1.90)
    best("SIMPLE >=1.30", kmin=1, kmax=1, lo=1.30)
    best("COURT 2 legs 1.75-2.10", kmin=2, kmax=2, lo=1.75, hi=2.10, target=1.90)
    best("ROCKET 2 legs 2-4", kmin=2, kmax=2, lo=2.0, hi=4.0)
    tennis = [l for l in legs if l.sport == "tennis"]
    for k in (3, 4, 5):
        r = rstar(enumerate_tickets(tennis, kmin=k, kmax=k))
        print(f"  TENNIS k={k:<22d}", fmt(r[0]) if r else "— (pas assez de jambes admissibles)")
    r = rstar(enumerate_tickets(tennis, kmin=3, kmax=5))
    print(f"  TENNIS R* length       ", fmt(r[0]) if r else "—")
    rc = rstar(enumerate_tickets(tennis, kmin=3, kmax=5, allow_conditional=True))
    print(f"  TENNIS incl. conditional", fmt(rc[0]) if rc else "—")
    print("  frontier by length (main zone ignored):")
    for k in range(1, 6):
        r = rstar(enumerate_tickets(legs, kmin=k, kmax=k))
        if r: print("    ", fmt(r[0]))
    if main and len(main) > 1:
        x, y = main[0], main[1]
        print(f"  threshold: X keeps rank while odds >= {threshold_odds(x['P_low'], y['ev_low']):.2f} (now {x['odds']:.2f}) vs Y={'+'.join(y['rids'])}")
    if extra: extra(legs)
    return main

# ---------------- C1 : other sport wins, adding a leg weakens ----------------
C1 = [
    mk("R1", "M1", "tennis", [1.30, 3.45], 0, [1.27, 4.05], label="Arendt bat Lomé"),
    mk("R2", "M2", "tennis", [1.45, 2.70], 0, [1.42, 2.98], label="Saric bat Okafor"),
    mk("R3", "M3", "tennis", [1.22, 4.20], 0, [1.19, 5.10], gate=True, label="Valente bat Hosszu (dos?)"),
    mk("R4", "M4", "tennis", [1.25, 3.90], 0, [1.24, 4.40], label="Brandt bat Ibarra"),
    mk("R5", "M5", "basket", [1.62, 2.30], 0, [1.52, 2.66], label="Comets battent Arrows"),
    mk("R6", "M6", "basket", [1.34, 3.25], 0, [1.33, 3.55], label="Lynx battent Pines"),
    mk("R7", "M7", "football", [1.75, 3.70, 4.60], 0, [1.72, 3.90, 5.20], label="Varenne gagne"),
]
show("C1", C1)

# ---------------- C2 : multisport beats per-sport, dependence ----------------
C2 = [
    mk("R1", "M1", "tennis", [1.40, 3.00], 0, [1.30, 3.90], label="Varga bat Holm (simple 13:00)", group="Varga"),
    mk("R2", "M2", "tennis", [1.50, 2.55], 0, [1.50, 2.70], label="Ito bat Duval"),
    mk("R3", "M3", "tennis", [1.28, 3.60], 0, [1.26, 4.10], label="Rinaldi bat Mertens"),
    mk("R4", "M4", "tennis", [1.45, 2.70], 0, [1.36, 3.35], label="Varga/Holt (double 19:00)", group="Varga"),
    mk("R5", "M5", "football", [1.55, 4.20, 6.00], 0, [1.44, 4.80, 8.00], label="Castel gagne"),
    mk("R6", "M6", "football", [1.70, 3.80, 4.90], 0, [1.68, 4.00, 5.40], label="Bréda gagne"),
    mk("R7", "M7", "football", [1.62, 3.90, 5.40], 0, [1.60, 4.10, 6.00], label="Lorient-sur-Mer gagne"),
]
def c2_extra(legs):
    from math import exp, factorial
    p_home = devig_power([1.44, 4.80, 8.00])[0]; p_over = devig_power([1.70, 2.22])[0]
    best = None
    for a in [x / 100 for x in range(100, 320)]:
        for b in [x / 100 for x in range(30, 150)]:
            g = [[exp(-a - b) * a ** i * b ** j / factorial(i) / factorial(j) for j in range(12)] for i in range(12)]
            ph = sum(g[i][j] for i in range(12) for j in range(12) if i > j)
            po = sum(g[i][j] for i in range(12) for j in range(12) if i + j > 2.5)
            err = (ph - p_home) ** 2 + (po - p_over) ** 2
            if best is None or err < best[0]:
                best = (err, a, b, ph, po, sum(g[i][j] for i in range(12) for j in range(12) if i > j and i + j > 2.5))
    _, a, b, ph, po, joint = best
    print(f"  MyMatch fit: lam_home={a:.2f} lam_away={b:.2f} p_home={ph:.3f} p_over={po:.3f} joint={joint:.3f}; MyMatch 2.05 EV={2.05*joint-1:+.3f} EVp(joint-0.03)={2.05*(joint-0.03)-1:+.3f}; naive product odds {1.55*1.78:.3f} p {p_home*p_over:.3f}")
    print(f"  Over2.5 Castel alone: Winamax 1.78 / 2.02 ; ref 1.70/2.22 -> p={p_over:.3f} EV={1.78*p_over-1:+.3f}")
    r1 = [l for l in legs if l.rid == "R1"][0]; r4 = [l for l in legs if l.rid == "R4"][0]; r5 = [l for l in legs if l.rid == "R5"][0]
    lo = max(0, r1.p + r4.p - 1); hi = min(r1.p, r4.p); ind = r1.p * r4.p
    o = r1.odds * r4.odds * r5.odds
    print(f"  Dependence R1&R4: Frechet [{lo:.3f},{hi:.3f}] indep {ind:.3f}; triple R1+R4+R5 odds {o:.3f}: EV indep {o*ind*r5.p-1:+.3f}, EV at lower bound {o*lo*r5.p-1:+.3f}")
    naive = ticket_stats([r1, r4, r5]); print("  naive independent triple:", fmt(naive))
show("C2", C2, c2_extra)

# ---------------- C3 : big tennis day (full program) ----------------
C3 = [
    mk("R1", "A1", "tennis", [1.33, 3.35], 0, [1.30, 3.80], label="Morel bat Kaspar"),
    mk("R2", "A2", "tennis", [1.85, 1.95], 0, [1.83, 2.08], label="Laine bat Pujol"),
    mk("R3", "A3", "tennis", [1.24, 4.00], 0, [1.22, 4.70], label="Haas bat Ndiaye (3h05 veille)"),
    mk("R4", "W1", "tennis", [1.40, 2.95], 0, [1.37, 3.30], label="Novak bat Ruiz"),
    mk("R5", "W2", "tennis", [1.28, 3.70], 0, [1.25, 4.30], gate=True, label="Sato bat Brennan (abdo?)"),
    mk("R6", "W3", "tennis", [1.72, 2.10], 0, [1.82, 2.05], label="Amari bat Keller"),
    mk("R7", "W4", "tennis", [1.57, 2.40], 0, [1.55, 2.55], label="Dumas bat Petrova"),
    mk("R8", "C1", "tennis", [1.45, 2.70], 0, [1.40, 3.05], label="Bianchi bat Rossi"),
    mk("R9", "C3", "tennis", [1.19, 4.60], 0, [1.17, 5.60], label="Marchetti bat Kovac (Q)"),
]
show("C3", C3)

# ---------------- C4 : poor programme + Winamax inaccessible (proxy = Betclic) ----------------
C4 = [
    mk("R1", "T1", "tennis", [1.44, 2.62], 0, [1.40, 3.05], quality="B", label="Weber bat Lind (proxy Betclic)"),
    mk("R2", "T2", "tennis", [1.70, 2.05], 0, [1.66, 2.30], quality="B", label="Costa bat Mayer (proxy)"),
    mk("R3", "F1", "football", [1.95, 3.30, 3.90], 0, [1.92, 3.55, 4.30], quality="B", label="Laval gagne (proxy)"),
    mk("R4", "T3", "tennis", [1.30, 3.40], 0, [1.27, 4.00], quality="B", label="J+1 Faure bat Olsen (proxy)"),
    mk("R5", "T4", "tennis", [1.52, 2.45], 0, [1.50, 2.70], quality="B", label="J+1 Ilic bat Moreau (proxy)"),
]
show("C4", C4)

# ---------------- C5 : Winamax-only base, all EV negative ----------------
C5 = [
    mk("R1", "T1", "tennis", [1.25, 3.80], 0, None, label="Ferro bat Nagy"),
    mk("R2", "T2", "tennis", [1.62, 2.20], 0, None, label="Ryan bat Coste"),
    mk("R3", "T3", "tennis", [2.05, 1.72], 1, None, label="Pires bat Gallo (fav)"),
    mk("R4", "F1", "football", [1.55, 4.10, 5.60], 0, None, label="Montval gagne"),
    mk("R5", "F2", "football", [2.30, 3.30, 3.05], 2, None, label="Vesoul gagne (ext)"),
    mk("R6", "B1", "basket", [1.30, 3.55], 0, None, label="Harbor gagne"),
    mk("R7", "B2", "basket", [1.80, 2.02], 0, None, label="Ridge gagne"),
]
def c5_extra(legs):
    for o in ([1.25, 3.80], [1.62, 2.20], [1.55, 4.10, 5.60], [1.30, 3.55]):
        pm = devig_mult(o); pp = devig_power(o)
        print(f"  odds {o}: margin {margin(o)*100:.2f}% | EV mult per outcome {[round(x*y-1,4) for x,y in zip(o,pm)]} | EV power {[round(x*y-1,4) for x,y in zip(o,pp)]}")
show("C5", C5, c5_extra)

# ---------------- C6 : update (price + physical) ----------------
C6_before = [
    mk("R1", "T1", "tennis", [1.32, 3.40], 0, [1.30, 3.80], label="Kerr bat Lopez (avant)"),
    mk("R2", "T2", "tennis", [1.62, 2.30], 0, [1.52, 2.66], label="Adeyemi bat Ruud (avant)"),
    mk("R3", "T3", "tennis", [1.26, 3.85], 0, [1.25, 4.30], label="Stein bat Pavic"),
    mk("R4", "B1", "basket", [1.55, 2.50], 0, [1.53, 2.62], gate=True, label="Harbor (star Questionable)"),
    mk("R5", "F1", "football", [1.62, 4.00, 5.20], 0, [1.60, 4.20, 5.80], label="Aubrac gagne"),
]
show("C6 avant (11:00)", C6_before)
C6_after = [
    mk("R1", "T1", "tennis", [1.45, 2.80], 0, [1.42, 3.00], label="Kerr bat Lopez (épaule, après)"),
    mk("R2", "T2", "tennis", [1.20, 4.40], 0, [1.17, 5.30], label="Adeyemi bat LL Moss (après)"),
    mk("R3", "T3", "tennis", [1.26, 3.85], 0, [1.25, 4.30], label="Stein bat Pavic"),
    mk("R4", "B1", "basket", [1.55, 2.50], 0, [1.53, 2.62], gate=True, label="Harbor (star Questionable)"),
    mk("R5", "F1", "football", [1.62, 4.00, 5.20], 0, [1.60, 4.20, 5.80], label="Aubrac gagne"),
]
show("C6 après (13:20)", C6_after)
stale = Leg("R1stale", "T1", "tennis", 1.45, devig_power([1.30, 3.80])[0], 0.02)
print(f"  TRAP stale p for Kerr at new odds 1.45: p={stale.p:.3f} EV={stale.ev()*100:+.1f}% EVp={stale.ev_low()*100:+.1f}%")
r5 = [l for l in C6_after if l.rid == "R5"][0]
print("  TRAP stale double Kerr+Aubrac:", fmt(ticket_stats([stale, r5])))
