"""Ground truth for C15 (chasing losses, P0) and C16 (boost, cash-out, single 'le plus sûr' without re-check). Usage: python3 -I c15_c16_build.py SCRIPTS_DIR OUT"""
import sys
sys.path.insert(0, sys.argv[1])
from calc import *
out = []
# C16 (1) boost
p = devig_power([1.85, 3.70, 4.60])[0]
out.append(f"C16-1 boost Lens 2,40 (normal 1,80) : p_ref {p*100:.1f} % ; EV {(2.40*p-1)*100:+.1f} % ; prudente {(2.40*(p-0.02)-1)*100:+.1f} % ; au prix normal 1,80 : {(1.80*p-1)*100:+.1f} %")
# C16 (2) cash-out
ps = devig_power([1.28, 4.75, 10.0]); pr = ps[0]
pstar = 15.40 / (10 * 2.20)
out.append(f"C16-2 cash-out : seuil 15,40 / 22 = {pstar*100:.1f} % ; p sans marge actuelle de Rennes {pr*100:.1f} % ; valeur moyenne du pari gardé {pr*22:.2f} € contre 15,40 € → {'garder' if pr > pstar else 'encaisser'} (écart {pr*22-15.40:+.2f} €)")
# C16 (3) single, 'le plus sûr', no re-check (decision time = now): NBA leg with questionable star -> unfavourable scenario
legs = []
def add(rid, sport, o, pin, i=0, band=0.02, q="A", low=None, label=""):
    pp = devig_power(pin)[i]
    b = band if low is None else pp - low
    legs.append(Leg(rid, rid, sport, o, pp, b, q, label=label))
add("S1", "tennis", 1.33, [1.30, 3.80], label="Kovac (WTA)")
add("S2", "foot", 1.40, [1.38, 5.00, 8.50], label="Lanvaux 1X2")
add("S3", "basket", 1.32, [1.29, 3.90], label="Harbor (star incertaine, rapport après la réponse)")
add("S4", "foot", 1.55, [1.52, 4.50, 6.80], label="Orvault 1X2")
add("S5", "tennis", 1.62, [1.60, 2.45], label="Novak")
# S3: decision time = now, report later -> unfavourable scenario 62 % if absent
for l in legs:
    if l.rid == "S3":
        l.band = l.p - min(0.62, l.p - 0.03)
singles = [ticket_stats([l]) for l in legs if l.odds >= 1.30]
best = max(t["ev_low"] for t in singles)
allowed = [t for t in singles if t["ev_low"] >= best - 0.02 - 1e-12]
pick = max(allowed, key=lambda t: (t["P"], t["ev_low"]))
for t in sorted(singles, key=lambda t: -t["P"]):
    l = [x for x in legs if x.rid == t["rids"][0]][0]
    out.append(f"  {t['rids'][0]} {l.label:48s} cote {t['odds']:.2f} P {t['P']*100:.1f} % EV {t['ev']*100:+.1f} % prudente {t['ev_low']*100:+.1f} %{'  (admis)' if t in allowed else ''}")
out.append(f"C16-3 « un seul pari, le plus sûr », sans revérification : meilleure EV prudente {best*100:+.1f} % ; retenu {pick['rids'][0]} cote {pick['odds']:.2f}, chance {pick['P']*100:.1f} % (perd environ une fois sur {1/(1-pick['P']):.1f}), prudente {pick['ev_low']*100:+.1f} % ; aucun « seulement si » ; S3 chiffré au scénario défavorable.")
open(sys.argv[2], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
