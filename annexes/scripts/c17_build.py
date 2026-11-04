"""Case C17: an ordinary day, no traps, default request, revision 6.33 zones. Usage: python3 -I c17_build.py SCRIPTS_DIR CASE_OUT GT_OUT"""
import sys, random, itertools
sys.path.insert(0, sys.argv[1])
from calc import *
rng = random.Random(1223)

def priced(ps, margin):
    lo, hi = 0.3, 1.0
    for _ in range(80):
        k = (lo + hi) / 2
        s = sum(p ** k for p in ps)
        if s > 1 + margin: lo = k
        else: hi = k
    return [round(1 / (p ** k), 2) for p in ps]

def fr(x): return f"{x:.2f}".replace(".", ",")
M = []
foot = [("F1", "Ligue de Valmorie (D1)", "18:30", "Orvault – Belmar", [0.50, 0.27, 0.23]),
        ("F2", "Ligue de Valmorie (D1)", "20:45", "Calvi – Dornes", [0.62, 0.22, 0.16]),
        ("F3", "Coupe de Valmorie, 8e de finale", "19:00", "Lanvaux – Rocher", [0.44, 0.28, 0.28]),
        ("F4", "Ligue de Valmorie (D1)", "21:00", "Port-Vallon – Saint-Aimé", [0.38, 0.29, 0.33])]
ten = [("T1", "ATP 250 de Corvel (dur intérieur), 8e", "14:00", "Lind – Faure", 0.70),
       ("T2", "ATP 250 de Corvel, 8e", "15:30", "Ruiz – Novak", 0.55),
       ("T3", "WTA 250 de Lisière (dur intérieur), 8e", "16:00", "Varga – Holm", 0.62),
       ("T4", "WTA 250 de Lisière, 8e", "18:00", "Kovac – Brandt", 0.48)]
nba = [("N1", "NBA", "jeudi 01:00", "Harbor Hawks – Ridge Rams", 0.58),
       ("N2", "NBA", "jeudi 02:00", "Bay Comets – Austin Arrows", 0.66),
       ("N3", "NBA", "jeudi 03:30", "Lake Owls – Delta Kings", 0.45)]
legs = []
lines = []
for mid, comp, h, teams, ps in foot:
    pin = priced(ps, 0.025)
    w = [round(o * rng.uniform(0.955, 0.99), 2) for o in priced(ps, 0.025)]
    w = [round(x, 2) for x in w]
    # nudge one outcome to be slightly generous sometimes
    lines.append(f"{mid} · football · {h} · {comp} · {teams} · Winamax {' / '.join(fr(x) for x in w)} · Pinnacle {' / '.join(fr(x) for x in pin)}")
    pp = devig_power(pin)
    for i, lab in enumerate(["1", "N", "2"]):
        legs.append(Leg(f"{mid}-{lab}", mid, "foot", w[i], pp[i], 0.02, label=f"{teams} : {lab}"))
for mid, comp, h, teams, p in ten + nba:
    sport = "tennis" if mid.startswith("T") else "basket"
    pin = priced([p, 1 - p], 0.03)
    w = [round(o * rng.uniform(0.955, 0.995), 2) for o in priced([p, 1 - p], 0.03)]
    lines.append(f"{mid} · {sport if sport=='tennis' else 'NBA'} · {h} · {comp} · {teams} · Winamax {fr(w[0])} / {fr(w[1])} · Pinnacle {fr(pin[0])} / {fr(pin[1])}")
    pp = devig_power(pin)
    band = 0.03 if sport == "basket" else 0.02
    for i in (0, 1):
        legs.append(Leg(f"{mid}-{i+1}", mid, sport, w[i], pp[i], band, label=f"{teams} : {teams.split(' – ')[i]}"))
case = f"""CAS DE CONTRÔLE FICTIF C17 — journée ordinaire, noms et chiffres inventés ; données figées à l'heure indiquée.

Demande de l'utilisateur : « Analyse du jour. »
Préparation : mercredi 23 décembre 2026, 13:00 (heure de Paris).
Accès : aucune recherche possible au-delà de ces données. Cotes Winamax lues dans l'application (12:50) ; Pinnacle via un comparateur qui le nomme (12:45). Statuts : aucun absent important, aucun statut incertain ; rapports NBA de la veille sans changement attendu.
Règlement Winamax (vérifié) : football, 1X2 sur le temps réglementaire (coupe : temps réglementaire aussi) ; NBA, vainqueur prolongations incluses ; tennis, vainqueur annulé en cas d'abandon.

PROGRAMME
""" + "\n".join(lines) + "\n"
open(sys.argv[2], "w", encoding="utf-8").write(case)
out = ["C17 — journée ordinaire (zones de la révision 6.33)"]
for l in sorted(legs, key=lambda l: -l.ev_low())[:10]:
    out.append(f"  {l.rid:6s} {l.label:42s} cote {l.odds:.2f} p {l.p*100:5.1f} % EV {l.ev()*100:+5.1f} % prudente {l.ev_low()*100:+5.1f} %")
star = rstar(enumerate_tickets(legs, lo=1.80, hi=3.00))
out.append("⭐ (1,80–3,00) : " + fmt(star[0]))
for t in star[1:3]: out.append("   suivant : " + fmt(t))
s1 = rstar([t for t in enumerate_tickets(legs, kmax=1) if t["odds"] >= 1.50])
out.append("🎯 (≥ 1,50) : " + fmt(s1[0]))
sh, kind = shield_v3(legs)
out.append(f"🛡️ : {fmt(sh)} ({kind})")
rk = rstar([t for t in enumerate_tickets(legs, kmin=2, kmax=2, lo=2.50, hi=3.50)])
out.append("🚀 (2 jambes, 2,50–3,50) : " + fmt(rk[0]))
tn = [l for l in legs if l.sport == "tennis"]
for k in (3, 4):
    r = rstar(enumerate_tickets(tn, kmin=k, kmax=k))
    out.append(f"🎾 meilleur à {k} : " + fmt(r[0]))
out.append("Attendu de forme : réponse courte par défaut (décision, menu, fiche finale), chances en clair (« x fois sur 10 »), coût honnête, aucune recommandation sous 1,50 hors demande.")
open(sys.argv[3], "w", encoding="utf-8").write("\n".join(out) + "\n")
print("\n".join(out))
