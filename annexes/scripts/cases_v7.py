"""Ground truth for the v7 validation cases C8 (single vs long combo + ticket court), C9 (refund ticket),
C10 (plan B that changes when odds move). Usage: python3 -I cases_v7.py SCRIPTS_DIR"""
import sys, math, itertools
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from calc import *

def mk(rid, match, sport, wmx, idx, ref, band=0.02, gate=False, label="", group=None):
    p = devig_power(ref)[idx]
    b = max(band, abs(devig_power(ref)[idx] - devig_mult(ref)[idx]))
    return Leg(rid, match, sport, wmx[idx], p, b, "A", gate, label=label, group=group)

def show_legs(legs):
    for l in legs:
        print(f"  {l.rid:4s} {l.label:30s} o={l.odds:.2f} p={l.p*100:5.1f}% [{l.p_low*100:4.1f}] EV={l.ev()*100:+5.1f}% EVp={l.ev_low()*100:+5.1f}%{' GATE' if l.gate else ''}")

print("===== C8 : simple contre long combiné, ticket court, bonus =====")
C8 = [
    mk("R1", "N1", "basket", [2.18, 1.72], 0, [2.02, 1.92], label="Ridge gagne (NBA, ext.)"),
    mk("R2", "T1", "tennis", [1.31, 3.40], 0, [1.29, 3.85], label="Ilic bat Moreau"),
    mk("R3", "T2", "tennis", [1.36, 3.10], 0, [1.34, 3.45], label="Costa bat Mayer"),
    mk("R4", "T3", "tennis", [1.42, 2.85], 0, [1.40, 3.10], label="Faure bat Olsen"),
    mk("R5", "F1", "football", [1.33, 5.20, 8.50], 0, [1.31, 5.60, 10.0], label="Montval gagne"),
    mk("R6", "F2", "football", [1.38, 4.80, 7.50], 0, [1.36, 5.10, 8.60], label="Aubrac gagne"),
    mk("R7", "F3", "football", [1.95, 3.40, 3.90], 0, [1.92, 3.60, 4.20], label="Laval gagne"),
    mk("R8", "T4", "tennis", [1.55, 2.40], 0, [1.49, 2.70], label="Novak bat Ruiz"),
]
show_legs(C8)
boost = lambda k: {3: 0.05, 4: 0.10, 5: 0.15}.get(k, 0.0)
main = rstar(enumerate_tickets(C8, lo=1.50, hi=4.00, boost_fn=boost))
print("  ⭐ (zone 1,50–4,00, bonus inclus) :", fmt(main[0])); [print("     ", fmt(t)) for t in main[1:4]]
long5 = [t for t in enumerate_tickets(C8, kmin=5, kmax=5, boost_fn=boost)]
long5.sort(key=lambda t: -t["ev"])
print("  meilleur 5 jambes par EV centrale (bonus +15 %) :", fmt(long5[0]))
t5 = long5[0]; legs5 = [l for l in C8 if l.rid in t5["rids"]]
nb = ticket_stats(legs5)
print(f"  même 5 jambes SANS bonus : EV {nb['ev']*100:+.1f}% / prudente {nb['ev_low']*100:+.1f}% ; produit (1+EVp) jambes = {math.prod(1+l.ev_low() for l in legs5)-1:+.4f} (factorisation valable sans bonus)")
print(f"  AVEC bonus : EVp {t5['ev_low']*100:+.1f}% ≠ produit des (1+EVp) des jambes : la factorisation ne vaut plus")
ev_best = max(main, key=lambda t: t["ev"])
print("  meilleur ticket de la zone par EV CENTRALE (piège) :", fmt(ev_best))
sh, best, ranked = shield(C8)
print(f"  🛡️ règle v7 (plafond 2 pts) : {fmt(sh)} ; meilleure EVp de la zone {best*100:+.1f}%, sacrifice {(best-sh['ev_low'])*100:.1f} pt")
print("  🛡️ ancienne règle (R★ pur) :", fmt(rstar([t for t in enumerate_tickets(C8, kmin=2, kmax=2, lo=1.75, hi=2.10)])[0]))
for t in ranked[:5]: print("       ", fmt(t))
thr = replay_threshold(C8, "R1", lo=1.50, hi=4.00, chooser=lambda L: (rstar(enumerate_tickets(L, lo=1.50, hi=4.00, boost_fn=boost)) or [None])[0])
print("  seuil ⭐ par rejeu complet (cote de Ridge) :", thr)

print("\n===== C9 : ticket avec remboursement, condition invérifiable avant la 1re jambe =====")
pG, pR, pP = devig_power([1.80, 3.80, 4.80])
print(f"  Bréda 1X2 réf. -> pG {pG:.3f} pR {pR:.3f} pP {pP:.3f}")
dnb = MLeg("R1", "F1", [("gain", pG, 1.40), ("rembourse", pR, 1.0), ("perte", pP, 0.0)], 0.02, "Bréda remboursé si nul 1,40")
s1 = ticket_states([dnb]); s1p = ticket_states([dnb], prudent=True)
print(f"  DNB seul : EV {s1['ev']*100:+.1f}% (formule pG(o-1)-pP = {(pG*0.40-pP)*100:+.1f}%) prudente {s1p['ev']*100:+.1f}% ; gain plein {pG*100:.1f}% remboursé {pR*100:.1f}% perte {pP*100:.1f}% ; cote d'équilibre {1+pP/pG:.3f}")
p_play = devig_power([1.45, 2.85])[0]
p_abs = devig_power([1.75, 2.15])[0]
print(f"  Harbor : p si star présente (réf. actuelle) {p_play:.3f} ; repère si star absente {p_abs:.3f}")
nba = binary("R2", "N1", 1.48, p_play, 0.03, "Harbor 1,48 (avant rapport, ±3)")
nba_abs = binary("R2", "N1", 1.48, p_abs, 0.02, "Harbor 1,48 scénario star absente")
for name, L in [("DNB + Harbor (statut supposé connu)", [dnb, nba]), ("DNB + Harbor, scénario prudent star absente (pari placé avant 18:30)", [dnb, nba_abs])]:
    t = ticket_states(L); tp = ticket_states(L, prudent=True)
    print(f"  {name}: cote pleine {1.40*1.48:.3f} ; EV {t['ev']*100:+.1f}% prudente {tp['ev']*100:+.1f}% ; gain plein {t['p_full']*100:.1f}% ; profit {t['p_profit']*100:.1f}% ; remboursé {t['p_refund']*100:.1f}% ; total {tp['total']:.3f}")
    print("     distribution (retour: prob) :", [(round(r, 3), round(p, 3)) for r, p in t['dist']])
nb1 = ticket_states([nba]); nb1p = ticket_states([nba], prudent=True)
print(f"  Harbor seul (après le rapport) : EV {nb1['ev']*100:+.1f}% prudente(±3) {nb1p['ev']*100:+.1f}%")
w1 = mk("R3", "T1", "tennis", [1.55, 2.45], 0, [1.52, 2.62], label="Novak bat Ruiz")
print(f"  Novak 1,55 : p {w1.p:.3f} EV {w1.ev()*100:+.1f}% EVp {w1.ev_low()*100:+.1f}%")
ticket = ticket_states([dnb, binary('R3','T1',1.55,w1.p,0.02)]); ticketp = ticket_states([dnb, binary('R3','T1',1.55,w1.p,0.02)], prudent=True)
print(f"  DNB + Novak 2,17 : EV {ticket['ev']*100:+.1f}% prudente {ticketp['ev']*100:+.1f}% ; gain plein {ticket['p_full']*100:.1f}% ; profit {ticket['p_profit']*100:.1f}% ; remboursé (1,55 seul) {ticket['p_refund']*100:.1f}%")

print("\n===== C10 : plan B qui change quand la cote bouge =====")
def c10(a_odds, c_ref, g_gate):
    return [
        mk("R1", "M1", "tennis", [a_odds, 2.30], 0, [1.62, 2.50], label=f"Kerr bat Lopez @{a_odds}"),
        mk("R2", "M2", "tennis", [1.28, 3.80], 0, [1.26, 4.30], label="Stein bat Pavic"),
        mk("R3", "M3", "football", [1.70, 3.80, 5.00], 0, c_ref, label="Aubrac gagne"),
        mk("R4", "M4", "basket", [1.40, 3.05], 0, [1.38, 3.30], label="Harbor gagne"),
        mk("R5", "M5", "tennis", [1.42, 2.90], 0, [1.40, 3.15], label="Novak bat Ruiz"),
        mk("R6", "M6", "football", [1.66, 4.10, 5.00], 0, [1.58, 4.40, 6.00], gate=g_gate, label="Laval gagne (meneur ?)"),
    ]
before = c10(1.75, [1.62, 4.20, 6.00], True)
show_legs(before)
r0 = rstar(enumerate_tickets(before, lo=1.50, hi=4.00))
print("  ⭐ 17:00 :", fmt(r0[0])); [print("     ", fmt(t)) for t in r0[1:4]]
print("  seuil par rejeu complet (cote de Kerr) :", replay_threshold(before, "R1"))
x = r0[0]; ys = [t for t in r0[1:] if "R1" in t["rids"]]
if ys:
    y = ys[0]; xl = [l for l in before if l.rid == "R1"][0]
    print(f"  formule contre le meilleur concurrent qui partage la jambe ({'+'.join(y['rids'])}) : {math.ceil((1+y['ev_low']-0.01)/xl.p_low*100-1e-9)/100}")
plan_b_17 = r0[1]
print("  plan B 17:00 (meilleur ticket sans la jambe de Kerr) :", fmt([t for t in r0 if 'R1' not in t['rids']][0]))
after = c10(1.66, [1.75, 4.00, 5.20], False)
print("  --- 19:30 : Kerr Winamax 1,75 -> 1,66 (référence inchangée) ; Aubrac référence 1,62 -> 1,75 (Winamax inchangé 1,70) ; meneur de Laval confirmé")
show_legs(after)
r1 = rstar(enumerate_tickets(after, lo=1.50, hi=4.00))
print("  ⭐ 19:30 :", fmt(r1[0])); [print("     ", fmt(t)) for t in r1[1:4]]
print("  plan B 19:30 (meilleur sans les jambes du ⭐) :", fmt([t for t in r1 if not set(t['rids']) & set(r1[0]['rids'])][0]))
trap = Leg("R3x", "M3", "football", 1.70, devig_power([1.62, 4.20, 6.00])[0], 0.02)
print(f"  piège : garder l'ancienne p d'Aubrac ({trap.p:.3f}) -> EV {trap.ev()*100:+.1f}% au lieu de {after[2].ev()*100:+.1f}%")
trap2 = Leg("R1x", "M1", "tennis", 1.66, devig_power([1.66, 2.30])[0], 0.03)
print(f"  piège inverse : recalculer Kerr sur Winamax seul après sa baisse -> p {trap2.p:.3f} au lieu de {after[0].p:.3f} (référence inchangée)")
