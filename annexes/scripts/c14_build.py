"""Case C14 (composite test of revisions 6.6-6.16) and its ground truth. Usage: python3 -I c14_build.py SCRIPTS_DIR"""
import sys, math, itertools
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from calc import *

def p_of(pin, i):
    return devig_power(pin)[i]

L = []   # admissible legs under the correct reading
notes = []
# F1 Orvault - Belmar 15:00, clean
pin = [1.92, 3.75, 4.30]; pF1 = p_of(pin, 0); bF1 = max(0.02, abs(pF1 - devig_mult(pin)[0]))
L.append(Leg("F1", "F1", "foot", 1.92, pF1, bF1, "A", label="Orvault 1X2"))
# F5 Lanvaux - Rocher 16:00, clean favourite
pin = [1.42, 4.90, 8.50]; pF5 = p_of(pin, 0); bF5 = max(0.02, abs(pF5 - devig_mult(pin)[0]))
L.append(Leg("F5", "F5", "foot", 1.45, pF5, bF5, "A", label="Lanvaux 1X2"))
# T3 Ruiz - Novak 15:30
pin = [1.28, 4.00]; pT3 = p_of(pin, 0)
L.append(Leg("T3", "T3", "tennis", 1.30, pT3, 0.02, "A", label="Ruiz"))
# T2 Varga - Holm 16:00, retirement rule unknown (both sides)
pin = [2.25, 1.70]; pV, pH = devig_power(pin)
L.append(Leg("T2v", "T2", "tennis", 2.25, pV, 0.02, "B", label="Varga (règle d'abandon non vérifiée)"))
L.append(Leg("T2h", "T2", "tennis", 1.62, pH, 0.02, "B", label="Holm (règle d'abandon non vérifiée)"))
# F2 Calvi - Dornes 17:00, Winamax unreadable: stand-in = lowest French operator price
pin = [1.76, 3.85, 5.10]; pF2 = p_of(pin, 0)
L.append(Leg("F2", "F2", "foot", 1.70, pF2, 0.02, "B", label="Calvi 1X2 (⚠️ prix provisoire 1,70 Betclic)"))
# F3 Port-Vallon - Saint-Aimé 20:45: no adjustment (announcement before the reference read, liquid reference unmoved)
pin = [1.92, 3.65, 4.40]; pF3 = p_of(pin, 0)
L.append(Leg("F3", "F3", "foot", 1.88, pF3, 0.02, "A", label="Port-Vallon 1X2"))
# F4 Brévent - Ostal 18:30: stale reference -> Winamax-only base, ±3, Q2, no value
w4 = [2.10, 3.40, 3.30]; pF4w = p_of(w4, 0)
L.append(Leg("F4", "F4", "foot", 2.10, pF4w, 0.03, "B", label="Brévent 1X2 (base Winamax seule)"))
# N1 Harbor - Ridge Monday 02:00: Okoye questionable, report after the decision time -> unfavourable scenario
pin = [1.57, 2.55]; pN = p_of(pin, 0)
lowN = min(0.52, pN - 0.03)
legN = Leg("N1", "N1", "basket", 1.62, pN, pN - lowN, "B", label="Harbor (Okoye incertain, rapport après 14:00)")
L.append(legN)
pR = 1 - pN; legR = Leg("N1r", "N1", "basket", 2.35, pR, 0.03, "B", label="Ridge")
L.append(legR)

out = ["C14 — composite (heure de décision 14:00, aucune revérification ensuite)"]
out.append("Jambes (lecture correcte) :")
for l in sorted(L, key=lambda l: -l.ev_low()):
    out.append(f"  {l.rid:4s} {l.label:45s} cote {l.odds:.2f} p {l.p*100:5.1f} % [{l.p_low*100:5.1f}] EV {l.ev()*100:+5.1f} % prudente {l.ev_low()*100:+5.1f} %")
out.append("  T1 Lind – Faure 13:30 : commence avant 14:00 → aucune jambe d'avant-match pour cet utilisateur.")
# traps
trap = {}
trap["F2 à la meilleure cote du comparateur 1,80 (opérateur non agréé)"] = (1.80 * pF2 - 1, 1.80 * (pF2 - 0.02) - 1)
trap["F2 à la cote de référence Pinnacle 1,76"] = (1.76 * pF2 - 1, 1.76 * (pF2 - 0.02) - 1)
trap["F2 au prix provisoire correct 1,70"] = (1.70 * pF2 - 1, 1.70 * (pF2 - 0.02) - 1)
trap["F3 avec +4 points d'ajustement"] = (1.88 * (pF3 + 0.04) - 1, 1.88 * (pF3 + 0.04 - 0.02) - 1)
trap["F3 avec +4 points mais borne plafonnée à p_ref (6.8)"] = (1.88 * (pF3 + 0.04) - 1, 1.88 * min(pF3 + 0.02, pF3) - 1)
pin4 = [2.02, 3.55, 4.00]; pF4s = p_of(pin4, 0)
trap["F4 avec la référence périmée de 08:15"] = (2.10 * pF4s - 1, 2.10 * (pF4s - 0.02) - 1)
trap["N1 traité en conditionnel (±3 au marché)"] = (1.62 * pN - 1, 1.62 * (pN - 0.03) - 1)
out.append("Pièges (chiffres qu'on obtient en tombant dedans) :")
for k, (e, el) in trap.items():
    out.append(f"  {k} : EV {e*100:+.1f} %, prudente {el*100:+.1f} %")
# main choice
main = rstar(enumerate_tickets(L, lo=1.50, hi=4.00))
out.append("⭐ (1,50–4,00) : " + fmt(main[0]))
for t in main[1:4]:
    out.append("   suivant : " + fmt(t))
# with traps: replace F2 by Pinnacle price, F3 adjusted, F4 stale
def with_traps(name):
    L2 = []
    for l in L:
        if name == "F2" and l.rid == "F2":
            L2.append(Leg("F2", "F2", "foot", 1.80, pF2, 0.02, "B", label=l.label))
        elif name == "F3" and l.rid == "F3":
            L2.append(Leg("F3", "F3", "foot", 1.88, pF3 + 0.04, 0.02, "A", label=l.label))
        elif name == "F4" and l.rid == "F4":
            L2.append(Leg("F4", "F4", "foot", 2.10, pF4s, 0.02, "A", label=l.label))
        else:
            L2.append(l)
    return L2
pT1 = p_of([1.52, 2.70], 0)
trapT1 = Leg("T1", "T1", "tennis", 1.55, pT1, 0.02, "A", label="Lind (commencé avant 14:00)")
out.append(f"  T1 inclus à tort : Lind 1,55 p {pT1*100:.1f} % EV {trapT1.ev()*100:+.1f} % prudente {trapT1.ev_low()*100:+.1f} %")
def with_traps(name, base=None):
    L2 = []
    for l in L:
        if name == "F2" and l.rid == "F2":
            L2.append(Leg("F2", "F2", "foot", 1.80, pF2, 0.02, "B", label=l.label))
        elif name == "F3" and l.rid == "F3":
            L2.append(Leg("F3", "F3", "foot", 1.88, pF3 + 0.04, 0.02, "A", label=l.label))
        elif name == "F4" and l.rid == "F4":
            L2.append(Leg("F4", "F4", "foot", 2.10, pF4s, 0.02, "A", label=l.label))
        elif name == "N1" and l.rid == "N1":
            L2.append(Leg("N1", "N1", "basket", 1.62, pN, 0.03, "B", label=l.label))
        else:
            L2.append(l)
    if name == "T1":
        L2.append(trapT1)
    return L2
for name in ("F2", "F3", "F4", "N1", "T1"):
    r = rstar(enumerate_tickets(with_traps(name), lo=1.50, hi=4.00))
    out.append(f"  ⭐ si l'on tombe dans le piège {name} : " + fmt(r[0]))
r2 = rstar([t for t in enumerate_tickets(L, kmin=2, kmax=2, lo=2.0, hi=4.0)])
out.append("🚀 (2 jambes, 2–4) : " + fmt(r2[0]))
r5 = rstar([t for t in enumerate_tickets(L, kmin=3, kmax=5, lo=5.0, hi=15.0)])
out.append("🎉 (3–5 jambes, 5–15, facultatif) : " + (fmt(r5[0]) if r5 else "—"))
out.append("🎾 : deux rencontres de tennis admissibles seulement (T2, T3 ; T1 commence avant 14:00) → impossible, il manque une rencontre.")
out.append("🎲 : aucun marché vivant relevé → format vide pour une raison matérielle nommée.")
# robustness at ±3 (each band +1 point)
L3 = [Leg(l.rid, l.match, l.sport, l.odds, l.p, l.band + 0.01, l.quality, l.gate, label=l.label, group=l.group) for l in L]
r3 = rstar(enumerate_tickets(L3, lo=1.50, hi=4.00))
out.append("Robustesse (chaque fourchette + 1 point) : ⭐ " + fmt(r3[0]))
# shield
sh, kind = shield_with_single(L)
out.append(f"🛡️ : {fmt(sh)} ({kind})")
pick2, best2, allz = shield(L)
if pick2:
    out.append(f"   meilleur ticket de deux jambes selon la règle : {fmt(pick2)}")
    for t in allz[:4]:
        out.append(f"   zone : {fmt(t)}")
# 🎯
s1 = rstar([t for t in enumerate_tickets(L, kmax=1) if t["odds"] >= 1.30])
out.append("🎯 : " + fmt(s1[0]))
# T2 settlement both rules (1.5 % retirement each side)
r = 0.015
for lab, o, p in (("Varga 2,25", 2.25, pV), ("Holm 1,62", 1.62, pH)):
    ev_void = (1 - 2 * r) * (o * p - 1)
    ev_qual = (1 - 2 * r) * (o * p - 1) + r * (o - 1) - r * 1
    out.append(f"  T2 {lab} : EV règle « annulé » {ev_void*100:+.2f} % ; règle « joueur qualifié » {ev_qual*100:+.2f} % → retenir {'annulé' if ev_void < ev_qual else 'qualifié'}")
print("\n".join(out))
open(sys.argv[2] if len(sys.argv) > 2 else "/dev/null", "w", encoding="utf-8").write("\n".join(out) + "\n")
