"""Generate cases C11 (tennis full mode at scale), C12 (live markets), C13 (freebet + journal review) and their ground truth.
Usage: python3 -I gen_c11_c13.py SCRIPTS_DIR CASES_DIR GT_FILE"""
import sys, math, random, itertools
sys.path.insert(0, sys.argv[1])
from calc import *
CASES, GT = sys.argv[2], sys.argv[3]
rng = random.Random(20261104)
gt = []

def fr(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")

def odds_pair(p, margin):
    # split margin proportionally (power-like for realism): q_i = p_i^(1/k) with sum = 1+margin
    lo, hi = 0.3, 1.0
    for _ in range(60):
        k = (lo + hi) / 2
        s = p ** k + (1 - p) ** k
        if s > 1 + margin: lo = k   # s decreases as k grows: too much margin -> raise k
        else: hi = k
    k = (lo + hi) / 2
    return round(1 / (p ** k), 2), round(1 / ((1 - p) ** k), 2)

# ---------------- C11 : tennis full mode at scale ----------------
names = ["Arendt", "Lomé", "Saric", "Okafor", "Valente", "Hosszu", "Brandt", "Ibarra", "Morel", "Kaspar", "Laine", "Pujol",
         "Haas", "Ndiaye", "Novak", "Ruiz", "Sato", "Brennan", "Dumas", "Petrova", "Bianchi", "Rossi", "Garin", "Lopez",
         "Marchetti", "Kovac", "Weber", "Lind", "Faure", "Olsen", "Ilic", "Moreau", "Costa", "Mayer", "Ricci", "Vega",
         "Kerr", "Stein", "Pavic", "Adeyemi", "Moss", "Holm", "Varga", "Ito", "Duval", "Rinaldi", "Mertens", "Keller", "Amari"]
rng.shuffle(names)
ni = iter(names)
matches = []
def add(mid, tour, surf, time, status, elo_a, elo_b, wmx=True, ref=True, note="", doubles=False):
    a, b = next(ni), next(ni)
    if doubles:
        a, b = f"{a}/{next(ni)}", f"{b}/{next(ni)}"
    p = 1 / (1 + 10 ** (-(elo_a - elo_b) / 400))
    pin = odds_pair(p, 0.025)
    w = odds_pair(min(0.97, max(0.03, p + rng.uniform(-0.035, 0.03))), 0.065)
    matches.append(dict(mid=mid, tour=tour, surf=surf, time=time, status=status, a=a, b=b, ea=elo_a, eb=elo_b,
                        pin=pin if ref else None, wmx=w if wmx else None, note=note, doubles=doubles))

T1, T2, T3, T4 = "Valbonne Indoor (ATP 500, dur intérieur), 8es de finale", "Lisière Ladies (WTA 250, dur intérieur), 2e tour", \
    "Challenger de Valcorta (terre battue extérieure)", "ITF W50 de Brévent (terre battue intérieure), 2e tour"
add("A1", T1, "dur intérieur", "11:00", "commencé à 11:00", 1890, 1760)
add("A2", T1, "dur intérieur", "13:30 (pas avant)", "à venir", 1915, 1790)
add("A3", T1, "dur intérieur", "15:00 (pas avant)", "à venir", 1820, 1805)
add("A4", T1, "dur intérieur", "17:00 (pas avant)", "à venir", 1950, 1770, note="a joué 2 h 55 hier, fin à 23:15")
add("A5", T1, "dur intérieur", "19:00", "à venir", 1840, 1870)
matches.append(dict(mid="A6", tour=T1, surf="dur intérieur", time="20:30 (pas avant)", status="affiche non confirmée",
                    a="vainqueur de A5", b=next(ni), ea=None, eb=1905, pin=None, wmx=None, note="adversaire = vainqueur de A5", doubles=False))
add("AD1", T1 + " — double, quarts", "dur intérieur", "12:00", "à venir", 1700, 1640, doubles=True)
add("AD2", T1 + " — double, quarts", "dur intérieur", "16:00 (pas avant)", "à venir", 1660, 1685, doubles=True,
    note="un joueur de la paire favorite joue aussi A2 en simple (13:30)")
add("W1", T2, "dur intérieur", "12:30", "à venir", 1800, 1690)
add("W2", T2, "dur intérieur", "14:00 (pas avant)", "à venir", 1755, 1748)
add("W3", T2, "dur intérieur", "15:30 (pas avant)", "forfait annoncé à 10:15 (poignet) : l'adversaire passe sans jouer", 1780, 1700, wmx=False, ref=False)
add("W4", T2, "dur intérieur", "17:00 (pas avant)", "à venir", 1835, 1655, note="retour de blessure (cheville) il y a 3 semaines, 2e tournoi")
add("C1", T3 + ", 2e tour", "terre extérieure", "11:30", "à venir", 1680, 1590)
add("C2", T3 + ", 2e tour", "terre extérieure", "13:00 (pas avant)", "à venir", 1620, 1625)
add("C3", T3 + ", 2e tour", "terre extérieure", "reporté à demain 11:00 (pluie)", "reporté", 1655, 1570)
add("C4", T3 + ", qualifications, dernier tour", "terre extérieure", "10:00 → 14:30 (pas avant), retard pluie", "à venir", 1560, 1520)
add("C5", T3 + ", qualifications, dernier tour", "terre extérieure", "16:00 (pas avant)", "à venir", 1540, 1545, wmx=False)
add("I1", T4, "terre intérieure", "12:00", "à venir", 1500, 1430, ref=False)
add("I2", T4, "terre intérieure", "13:30 (pas avant)", "à venir", 1470, 1465, wmx=False, ref=False)
add("I3", T4, "terre intérieure", "15:00 (pas avant)", "à venir", 1520, 1410)

mA2 = [m for m in matches if m["mid"] == "A2"][0]; mAD2 = [m for m in matches if m["mid"] == "AD2"][0]
fav = "b" if mAD2["wmx"][1] < mAD2["wmx"][0] else "a"
mAD2[fav] = f"{mA2['a']}/{mAD2[fav].split('/')[1]}"
mAD2["note"] = f"{mA2['a']} (paire favorite) joue aussi A2 en simple (13:30)"
lines = ["CAS DE CONTRÔLE FICTIF C11 — noms, compétitions et chiffres inventés ; données figées à l'heure indiquée.", "",
         "Demande de l'utilisateur : « Tennis : tout le programme d'aujourd'hui. »",
         "Préparation : jeudi 3 décembre 2026, 11:30 (heure de Paris).",
         "Accès : aucune recherche possible au-delà de ces données. Programme recensé en croisant l'offre Winamax (captures 11:10–11:20) et les sites des tournois ; référence Pinnacle via un comparateur qui le nomme (11:05–11:15) quand elle existe. Classements Elo de surface (déjà mélangés surface/global) relevés lundi.",
         "Règlement Winamax (vérifié) : abandon après le début → pari annulé, cote ramenée à 1 dans un combiné ; forfait avant le début → pari annulé.",
         "Si un rapport TXT séparé est utile, écris-le dans le fichier indiqué par la consigne du test.", "", "PROGRAMME"]
cur = None
for m in matches:
    if m["tour"] != cur:
        cur = m["tour"]; lines.append(cur)
    who = f"{m['a']} – {m['b']}"
    elo = f"Elo {m['ea']} / {m['eb']}" if m["ea"] else f"Elo {m['b']} {m['eb']}"
    w = f"Winamax {fr(m['wmx'][0])} / {fr(m['wmx'][1])}" if m["wmx"] else "Winamax : non proposé"
    pnc = f"Pinnacle {fr(m['pin'][0])} / {fr(m['pin'][1])}" if m["pin"] else "Pinnacle : non disponible"
    st = "" if m["status"] == "à venir" else f" · statut : {m['status']}"
    note = f" · {m['note']}" if m["note"] else ""
    lines.append(f"{m['mid']} · {m['time']} · {who} · {w} · {pnc} · {elo}{st}{note}")
lines += ["", "INFORMATIONS", "- Aucune autre information que celles indiquées par match.",
          "- Les joueurs non mentionnés n'ont ni blessure ni fatigue notable connue."]
open(f"{CASES}/C11.txt", "w", encoding="utf-8").write("\n".join(lines) + "\n")

legs = []
for m in matches:
    if m["status"] != "à venir" or not m["wmx"]:
        continue
    for side in (0, 1):
        if m["pin"]:
            pp, pm = devig_power(list(m["pin"])), devig_mult(list(m["pin"]))
            p = pp[side]; band = max(0.02, abs(pp[side] - pm[side])); q = "A"
        else:
            p = devig_power(list(m["wmx"]))[side]; band = 0.03; q = "B"
        grp = "joueur partagé A2/AD2" if m["mid"] in ("A2", "AD2") else None
        name = m["a"] if side == 0 else m["b"]
        legs.append(Leg(m["mid"] + ("" if side == 0 else "b"), m["mid"], "tennis", m["wmx"][side], p, band, q, False,
                        label=f"{name} ({m['mid']})", group=grp))
m_by = {m['mid']: m for m in matches}
gt.append("C11 — tennis complet à grande échelle")
gt.append(f"Recensés : {len(matches)} ; hors avant-match ou hors journée : A1 (commencé), W3 (forfait), C3 (reporté à demain) ; affiche non confirmée : A6 ; analysables : {len(matches)-4} (dont C5 et I2 sans cote Winamax, I1 et I2 sans référence).")
for l in sorted(legs, key=lambda l: -l.ev_low()):
    gt.append(f"  {l.rid} {l.label} : cote {fr(l.odds)}, p {l.p*100:.1f} %, EV {l.ev()*100:+.1f} %, prudente {l.ev_low()*100:+.1f} %{' (retour de blessure : information, pas une porte)' if 'retour de blessure' in m_by[l.match]['note'] else ''}{' (base Winamax seule)' if l.quality=='B' else ''}")
main = rstar(enumerate_tickets(legs, lo=1.50, hi=4.00))
gt.append("  Choix principal selon la règle : " + fmt(main[0]))
for k in (3, 4, 5):
    r = rstar(enumerate_tickets(legs, kmin=k, kmax=k))
    gt.append(f"  🎾 meilleur à {k} : " + (fmt(r[0]) if r else "—"))
r = rstar(enumerate_tickets(legs, kmin=3, kmax=5)); gt.append("  🎾 retenu : " + fmt(r[0]))
gt.append("  Pièges : compter A1, W3, C3 ou A6 parmi les analysés ; inventer une cote pour C5 ou I2 ; associer A2 et AD2 (même joueur) sans le dire ; compteurs incohérents (recensés = analysés + limités + en attente, plus les exclus à part).")

# ---------------- C12 : live markets ----------------
pin1x2 = [1.58, 4.20, 6.00]; pH, pD, pA = devig_power(pin1x2)
p_over = devig_power([1.72, 2.18])[0]
best = None
for a in [x / 100 for x in range(80, 320)]:
    for b in [x / 100 for x in range(20, 180)]:
        g = [[math.exp(-a - b) * a ** i * b ** j / math.factorial(i) / math.factorial(j) for j in range(12)] for i in range(12)]
        ph = sum(g[i][j] for i in range(12) for j in range(12) if i > j)
        po = sum(g[i][j] for i in range(12) for j in range(12) if i + j > 2)
        e = (ph - pH) ** 2 + (po - p_over) ** 2
        if best is None or e < best[0]: best = (e, a, b, g)
_, la, lb, g = best
P = lambda f: sum(g[i][j] for i in range(12) for j in range(12) if f(i, j))
w2 = P(lambda i, j: i - j >= 2); w1 = P(lambda i, j: i - j == 1); rest = 1 - w2 - w1
btts = P(lambda i, j: i > 0 and j > 0); hw_btts = P(lambda i, j: i > j and j > 0)
fair_ah_h = (1 - w1 / 2) / (w2 + w1 / 2); fair_ah_a = (1 - w1 / 2) / rest
pin_ah = (round(fair_ah_h / 1.025, 2), round(fair_ah_a / 1.025, 2))
lam_start = 0.52 * 85 / 90 + 0.06; lam_sub = 0.52 * 25 / 90
p_sc = 0.75 * (1 - math.exp(-lam_start)) + 0.25 * (1 - math.exp(-lam_sub))
p_sc_avg_minutes = 1 - math.exp(-(0.52 * (0.75 * 85 + 0.25 * 25) / 90 + 0.75 * 0.06))
pI = devig_power([1.42, 2.98])[0]; pDoe = devig_power([1.90, 1.92])[0]
# candidate legs: (MLeg, quoted odds, quality, kind, combinable)
C = []
def cb(rid, match, o, p, band, lab, q="Q1", kind="prix", comb=True):
    C.append((binary(rid, match, o, p, band, lab), o, q, kind, comb))
def cm(rid, match, o, states, band, lab, q="Q1", kind="prix", comb=True):
    C.append((MLeg(rid, match, states, band, lab), o, q, kind, comb))
cb("F-1", "F1", 1.62, pH, 0.02, "Montval 1X2")
cb("F-N", "F1", 4.00, pD, 0.02, "nul")
cb("F-2", "F1", 5.40, pA, 0.02, "Saint-Brice 1X2")
cm("F-DNB1", "F1", 1.20, [("gain", pH, 1.20), ("nul", pD, 1.0), ("perte", pA, 0.0)], 0.02, "Montval remboursé si nul")
cm("F-DNB2", "F1", 3.90, [("gain", pA, 3.90), ("nul", pD, 1.0), ("perte", pH, 0.0)], 0.02, "Saint-Brice remboursé si nul")
cb("F-DC", "F1", 1.12, pH + pD, 0.02, "double chance 1X")
cm("F-AH1", "F1", 1.83, [("gain", w2, 1.83), ("demi-gain", w1, (1.83 + 1) / 2), ("perte", rest, 0.0)], 0.02, "Montval −0,75", kind="vivant")
cm("F-AH2", "F1", 1.97, [("gain", rest, 1.97), ("demi-perte", w1, 0.5), ("perte", w2, 0.0)], 0.02, "Saint-Brice +0,75", kind="vivant")
cb("F-O", "F1", 1.75, p_over, 0.02, "plus de 2,5 buts", kind="vivant")
cb("F-U", "F1", 2.05, 1 - p_over, 0.02, "moins de 2,5 buts", kind="vivant")
cb("F-BY", "F1", 1.80, btts, 0.03, "les deux marquent : oui (modèle)", q="Q2", kind="vivant")
cb("F-BN", "F1", 2.00, 1 - btts, 0.03, "les deux marquent : non (modèle)", q="Q2", kind="vivant")
cb("F-MM", "F1", 3.60, hw_btts, 0.03, "MyMatch Montval gagne + les deux marquent (modèle)", q="Q2", kind="vivant", comb=False)
cb("F-SC", "F1", 2.40, p_sc, 0.03, "Durand buteur (modèle de minutes)", q="Q2", kind="vivant")
cb("T-I", "T1", 1.45, pI, 0.02, "Ilic vainqueur")
cb("T-M", "T1", 2.75, 1 - pI, 0.02, "Moreau vainqueur")
cb("N-O", "N1", 1.87, pDoe, 0.03, "Doe plus de 24,5 points", kind="vivant")
cb("N-U", "N1", 1.93, 1 - pDoe, 0.03, "Doe moins de 24,5 points", kind="vivant")
QR = {"Q1": 1, "Q2": 2, "Q3": 3}
def tick(combo):
    c = ticket_states([x[0] for x in combo]); cp = ticket_states([x[0] for x in combo], prudent=True)
    return dict(rids=[x[0].rid for x in combo], labs=[x[0].label for x in combo], n=len(combo), odds=math.prod(x[1] for x in combo),
                P=c["p_full"], Pprofit=c["p_profit"], ev=c["ev"], ev_low=cp["ev"], qual=max(QR[x[2]] for x in combo),
                kinds={x[3] for x in combo})
T = []
for k in (1, 2, 3):
    for combo in itertools.combinations(C, k):
        if len({x[0].match for x in combo}) < k: continue
        if k > 1 and not all(x[4] for x in combo): continue
        T.append(tick(combo))
def rank(ts):
    if not ts: return []
    b = max(t["ev_low"] for t in ts)
    head = sorted([t for t in ts if t["ev_low"] >= b - 0.01 - 1e-12], key=lambda t: (t["n"], t["qual"], -t["ev_low"]))
    return head + sorted([t for t in ts if t not in head], key=lambda t: -t["ev_low"])
def f12(t):
    return (f"{' + '.join(t['labs'])} : cote {t['odds']:.3f}, P(gain plein) {t['P']*100:.1f} %, P(profit) {t['Pprofit']*100:.1f} %, "
            f"EV {t['ev']*100:+.1f} %, prudente {t['ev_low']*100:+.1f} %")
gt.append("")
gt.append("C12 — marchés vivants")
gt.append(f"  1X2 Pinnacle 1,58/4,20/6,00 → p {pH*100:.1f} / {pD*100:.1f} / {pA*100:.1f} % ; plus de 2,5 {p_over*100:.1f} % ; grille de Poisson calée λ {la:.2f} / {lb:.2f}")
gt.append(f"  Handicap asiatique Montval −0,75 à 1,83 : gagne de 2+ {w2*100:.1f} % (retour 1,83), gagne de 1 {w1*100:.1f} % (demi-gain, retour 1,415), sinon perte ; prix juste {fair_ah_h:.3f} (Pinnacle affiché {fr(pin_ah[0])}) ; EV {[t for t in T if t['rids']==['F-AH1']][0]['ev']*100:+.1f} %, prudente {[t for t in T if t['rids']==['F-AH1']][0]['ev_low']*100:+.1f} % (2 points déplacés de « gagne de 2+ » vers « perte »)")
for rid in ("F-1", "F-DNB1", "F-DC", "F-O", "F-BY", "F-MM", "F-SC", "T-I", "N-O"):
    t = [t for t in T if t["rids"] == [rid]][0]; gt.append("  " + f12(t))
gt.append(f"  MyMatch : p jointe {hw_btts*100:.1f} % contre produit naïf {pH*btts*100:.1f} % (EV naïve {(3.60*pH*btts-1)*100:+.1f} %) ; buteur : mélange {p_sc*100:.1f} % contre « minutes moyennes » {p_sc_avg_minutes*100:.1f} %.")
gt.append("  Tennis Ilic : handicap et total de jeux sans référence → probabilité non estimée (🎲 sur lecture seulement, sans EV) ; un modèle de jeux est acceptable s'il est annoncé comme tel avec une fourchette large.")
zone = lambda lo, hi: [t for t in T if lo - 1e-9 <= t["odds"] <= hi + 1e-9]
r = rank(zone(1.50, 4.00)); gt.append("  ⭐ (1,50–4,00) : " + f12(r[0]) + " ; suivants : " + " | ".join(f"{' + '.join(t['labs'])} {t['ev_low']*100:+.1f} %" for t in r[1:4]))
r = rank([t for t in T if t["n"] == 1 and t["odds"] >= 1.30]); gt.append("  🎯 : " + f12(r[0]))
sh = [t for t in zone(1.75, 2.10) if t["n"] == 2]
if sh:
    b = max(t["ev_low"] for t in sh); ok = sorted([t for t in sh if t["ev_low"] >= b - 0.02 - 1e-12], key=lambda t: -t["Pprofit"])
    gt.append(f"  🛡️ (2 jambes, 1,75–2,10) : {len(sh)} ticket(s) ; mieux payé {b*100:+.1f} % ; retenu : " + f12(ok[0]))
else:
    gt.append("  🛡️ : aucun ticket de deux jambes dans 1,75–2,10")
viv = rank([t for t in T if t["n"] == 1 and t["kinds"] == {"vivant"}]); gt.append("  🎲 (marchés vivants chiffrables) : " + " | ".join(f"{t['labs'][0]} {t['ev_low']*100:+.1f} %" for t in viv[:4]))
r = rank([t for t in zone(2.0, 4.0) if t["n"] == 2]); gt.append("  🚀 (2 jambes, 2–4) : " + (f12(r[0]) if r else "—"))
r = rank([t for t in zone(5.0, 15.0) if t["n"] >= 3]); gt.append("  🎉 (3–5 jambes, 5–15) : " + (f12(r[0]) if r else "—"))
gt.append("  🎾 : une seule rencontre de tennis → impossible (il manque deux rencontres).")
gt.append("  Pièges : demi-gain compté o/2 (EV de l'AH ≈ −8,7 %, AH écarté à tort) ; buteur aux minutes moyennes ; MyMatch au produit des probabilités ; probabilité inventée pour les jeux de tennis ; MyMatch combiné avec une autre jambe (ticket à part).")
case12 = f"""CAS DE CONTRÔLE FICTIF C12 — noms, compétitions et chiffres inventés ; données figées à l'heure indiquée.

Demande de l'utilisateur : « Analyse du jour, surtout les marchés plaisir. »
Préparation : samedi 5 décembre 2026, 13:00 (heure de Paris).
Accès : aucune recherche possible au-delà de ces données. Cotes Winamax lues dans l'application (12:40) ; Pinnacle via un comparateur qui le nomme (12:35).
Règlement Winamax (vérifié) : handicaps asiatiques réglés en demi-mises sur les lignes voisines ; buteur : pari remboursé si le joueur n'entre pas en jeu ; MyMatch : ticket à part, non combinable.

Football — Ligue de Valmorie (D1), F1 · 17:30 · Montval – Saint-Brice
- Winamax 1X2 : 1,62 / 4,00 / 5,40 ; remboursé si nul : Montval 1,20 / Saint-Brice 3,90 ; double chance 1X : 1,12
- Winamax plus/moins de 2,5 buts : 1,75 / 2,05 ; les deux équipes marquent : oui 1,80 / non 2,00
- Winamax handicap asiatique : Montval −0,75 à 1,83 / Saint-Brice +0,75 à 1,97
- Winamax MyMatch « Montval gagne + les deux équipes marquent » : 3,60
- Winamax « N. Durand buteur » : 2,40
- Pinnacle 1X2 : 1,58 / 4,20 / 6,00 ; plus/moins de 2,5 : 1,72 / 2,18 ; handicap asiatique Montval −0,75 : {fr(pin_ah[0])} / Saint-Brice +0,75 : {fr(pin_ah[1])}
- Durand : 0,52 but attendu hors penalty par 90 minutes (saison, 1 650 minutes), tireur de penalty (environ 0,06 but par match de plus quand il est titulaire) ; titulaire probable à 75 % (presse locale), sinon entrée vers la 65e ; composition vers 16:30.
Tennis — T1 · 15:00 · M. Ilic – S. Moreau (dur intérieur)
- Winamax vainqueur 1,45 / 2,75 ; handicap de jeux Ilic −3,5 : 1,85 / +3,5 : 1,90 ; total de jeux plus/moins de 21,5 : 1,85 / 1,90
- Pinnacle vainqueur 1,42 / 2,98 ; aucun handicap ni total lisible chez Pinnacle.
Basket — NBA, N1 · dimanche 01:30 · Harbor Hawks – Ridge Rams
- Winamax « J. Doe plus de 24,5 points » 1,87 / moins 1,93 ; Pinnacle 1,90 / 1,92
- Doe : 25,9 points de moyenne sur 20 matchs (35 minutes), aucun problème physique signalé ; rapport du jour attendu vers 19:00.
"""
open(f"{CASES}/C12.txt", "w", encoding="utf-8").write(case12)

# ---------------- C13 : freebet + journal review ----------------
fb_legs = [("A", "Bréda gagne", 1.85, [1.80, 3.80, 4.80], 0), ("B", "Ridge gagne (NBA)", 2.60, [2.50, 1.56], 0),
           ("C", "Rodez gagne (ext.)", 3.40, [3.25, 3.50, 2.25], 0), ("D", "Weber bat Lind", 1.36, [1.33, 3.60], 0),
           ("E", "Novak bat Ruiz", 1.55, [1.52, 2.62], 0)]
gt.append("")
gt.append("C13 — freebet de 10 € (mise non rendue, cote minimale 1,80) et bilan d'un journal")
vals = []
for rid, lab, o, ref, idx in fb_legs:
    p = devig_power(ref)[idx]
    vals.append((rid, lab, o, p, p * (o - 1), (p - 0.02) * (o - 1)))
    gt.append(f"  {rid} {lab} {fr(o)} : p {p*100:.1f} %, valeur du freebet {p*(o-1)*10:.2f} € (prudente {(p-0.02)*(o-1)*10:.2f} €){'' if o >= 1.80 else ' — sous la cote minimale seul'}")
pD = devig_power([1.33, 3.60])[0]; pE = devig_power([1.52, 2.62])[0]
de_o = 1.36 * 1.55; de_p = pD * pE
gt.append(f"  Combiné D+E {fr(de_o)} : p {de_p*100:.1f} %, valeur {de_p*(de_o-1)*10:.2f} € (prudente {(pD-0.02)*(pE-0.02)*(de_o-1)*10:.2f} €)")
best_fb = max(vals, key=lambda v: v[5])
gt.append(f"  Meilleur usage par valeur prudente : {best_fb[0]} ({best_fb[1]}), {best_fb[5]*10:.2f} € ; la valeur augmente avec la cote à prix égal, mais ne justifie pas d'allonger un ticket sans avantage.")
# journal of 60 legs
rows = []
for k in range(60):
    p_ret = rng.uniform(0.45, 0.80)
    o_take = round(1 / p_ret * rng.uniform(0.93, 1.03), 2)
    p_close = min(0.95, max(0.05, p_ret + rng.gauss(0.005, 0.025)))
    o_close = round(1 / p_close * 1.035, 2)
    y = 1 if rng.random() < p_close else 0
    rows.append((k + 1, p_ret, o_take, o_close, p_close, y))
jl = ["date;ticket;R-id;cote prise;p_ret;cote de clôture;p de clôture;résultat"]
for k, p_ret, o, oc, pc, y in rows:
    jl.append(f"J{k:02d};T{k:02d};R1;{fr(o)};{fr(p_ret,3)};{fr(oc)};{fr(pc,3)};{y}")
clv = [o / oc - 1 for _, _, o, oc, _, _ in rows]
br_ret = sum((p - y) ** 2 for _, p, _, _, _, y in rows) / 60
br_cl = sum((pc - y) ** 2 for _, _, _, _, pc, y in rows) / 60
roi = sum((o * y - 1) for _, _, o, _, _, y in rows) / 60
sd = (sum(((o * y - 1) - roi) ** 2 for _, _, o, _, _, y in rows) / 59) ** 0.5
mclv = sum(clv) / 60; sclv = (sum((c - mclv) ** 2 for c in clv) / 59) ** 0.5
gt.append(f"  Journal (60 jambes simples) : CLV moyenne {mclv*100:+.1f} % (±{1.96*sclv/60**0.5*100:.1f}), part au-dessus de la clôture {sum(1 for c in clv if c > 0)/60*100:.0f} % ; Brier p_ret {br_ret:.4f} contre clôture {br_cl:.4f} ; rendement {roi*100:+.1f} % (±{1.96*sd/60**0.5*100:.1f}) ; 60 < 200 jambes → aucune convention à modifier.")
case13 = """CAS DE CONTRÔLE FICTIF C13 — noms, compétitions et chiffres inventés ; données figées à l'heure indiquée.

Demande de l'utilisateur : « J'ai un freebet de 10 € à utiliser ce soir. Dis-moi où le placer. Et fais le bilan de mon journal ci-dessous. »
Préparation : mardi 8 décembre 2026, 16:00 (heure de Paris).
Conditions du freebet (vérifiées dans l'application) : mise non rendue (seul le gain net est versé), cote minimale 1,80 (sur le ticket), simple ou combiné, avant-match, expire ce soir à 23:59.
Accès : aucune recherche possible au-delà de ces données. Cotes Winamax (15:40) et Pinnacle via un comparateur qui le nomme (15:35). Aucun statut incertain.

PROGRAMME ET COTES
A · 20:45 · football · Bréda – Hautval · Winamax 1,85 / 3,60 / 4,40 · Pinnacle 1,80 / 3,80 / 4,80
B · mercredi 01:00 · NBA · Ridge Rams – Harbor Hawks · Winamax 2,60 / 1,50 · Pinnacle 2,50 / 1,56
C · 21:00 · football · Laval – Rodez (Rodez à l'extérieur) · Winamax 2,15 / 3,40 / 3,40 · Pinnacle 2,25 / 3,50 / 3,25 · (la sélection étudiée est Rodez gagne à 3,40)
D · 18:00 · tennis · Weber – Lind · Winamax 1,36 / 3,05 · Pinnacle 1,33 / 3,60
E · 19:30 · tennis · Novak – Ruiz · Winamax 1,55 / 2,45 · Pinnacle 1,52 / 2,62

JOURNAL FOURNI (60 jambes simples déjà réglées, une par ticket ; colonnes séparées par « ; »)
""" + "\n".join(jl) + "\n"
open(f"{CASES}/C13.txt", "w", encoding="utf-8").write(case13)
open(GT, "a", encoding="utf-8").write("\n\n═══ CAS DE STRESS C11 À C13 (fixés avant exécution) ═══\n" + "\n".join(gt) + "\n")
print("\n".join(gt))
