"""Executed checks for the SOL 6.0 calculation core and the worked examples quoted in the prompts.
Run: python3 -I tests_calc.py SCRIPTS_DIR
"""
import sys, math, random, itertools
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from calc import *

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

# ---------- worked examples of the new prompt ----------
leg = Leg("x", "m", "tennis", 1.30, 0.775, 0.02)
check("SOL6 3.9 exemple jambe 1,30 : EV prudente −1,85 %", abs(leg.ev_low() + 0.0185) < 1e-12, f"{leg.ev_low()*100:.3f}%")
check("SOL6 3.9 exemple jambe 1,30 : perte relative de chance 22,5 %", abs((1 - 0.775) - 0.225) < 1e-12)
check("SOL6 3.7 cote minimale 1/0,62 arrondie au centième supérieur = 1,62", math.ceil(1 / 0.62 * 100) / 100 == 1.62, f"{1/0.62:.4f}")
mix = 0.5 * (1 - math.exp(-0.5)); avg = 1 - math.exp(-0.25)
check("SOL6 6.2.4 mélange des minutes 19,7 % vs 22,1 %", round(mix * 100, 1) == 19.7 and round(avg * 100, 1) == 22.1, f"{mix:.4f} {avg:.4f}")
pm = devig_mult([1.25, 3.80]); evs = [o * p - 1 for o, p in zip([1.25, 3.80], pm)]
check("SOL6 2.2 base Winamax seule : EV identique pour toutes les issues (multiplicative)", abs(evs[0] - evs[1]) < 1e-12 and abs(evs[0] - (1 / (1 + margin([1.25, 3.80])) - 1)) < 1e-12, f"{evs}")
pp = devig_power([1.25, 3.80]); evp = [o * p - 1 for o, p in zip([1.25, 3.80], pp)]
check("Méthode power : le favori garde une EV moins négative que l'outsider (biais favori-outsider)", evp[0] > evp[1], f"{[round(e,4) for e in evp]}")
check("SOL6 6.1.4 abandons : 1-(0,97)^5 ≈ une chance sur sept", abs((1 - 0.97 ** 5) - 1 / 7) < 0.01, f"{1-0.97**5:.4f}")
o, b = 4.0, 0.10
check("SOL6 3.9 bonus sur gain net : retour = 1 + (cote-1)(1+b)", abs((1 + (o - 1) * (1 + b)) - 4.3) < 1e-12)

# ---------- R-star properties ----------
random.seed(3)
viol = 0
for _ in range(20000):
    base = [Leg(f"r{i}", f"m{i}", "x", random.uniform(1.1, 3.0), random.uniform(0.3, 0.9), 0.02) for i in range(3)]
    t = ticket_stats(base)
    new = Leg("n", "mn", "x", random.uniform(1.1, 3.0), random.uniform(0.3, 0.9), 0.02)
    t2 = ticket_stats(base + [new])
    if new.ev_low() < 0 and t2["ev_low"] >= t["ev_low"]:
        viol += 1
    if new.ev_low() > 0 and t["ev_low"] > -1 and t2["ev_low"] <= t["ev_low"]:
        viol += 1
check("R★ : ajouter une jambe d'EV prudente < 0 fait toujours baisser l'EV prudente du ticket (et > 0 la fait monter)", viol == 0, f"violations={viol} / 20000")
a = Leg("a", "m1", "tennis", 1.40, 0.76, 0.02); f = Leg("f", "m2", "football", 1.55, 0.686, 0.02)
t_ms = ticket_stats([a, f])
check("R★ : deux jambes d'EV prudente > 0 de sports différents forment un double meilleur que chaque simple", t_ms["ev_low"] > max(a.ev_low(), f.ev_low()), f"{t_ms['ev_low']:.4f} vs {a.ev_low():.4f},{f.ev_low():.4f}")
x = ticket_stats([Leg("s1", "m1", "x", 1.50, 0.66, 0.02)]); y = ticket_stats([Leg("s2", "m2", "x", 3.00, 0.34, 0.02)])
check("R★ : la chance de toucher ne départage pas deux cotes différentes à prix égal (ordre inchangé dans les deux sens)",
      abs(x["ev_low"] - y["ev_low"]) < 1e-12 and rstar([y, x])[0]["rids"] == ["s2"] and rstar([x, y])[0]["rids"] == ["s1"],
      f"EVp {x['ev_low']:.4f} / {y['ev_low']:.4f}, P {x['P']:.2f} / {y['P']:.2f}")
d1 = Leg("v1", "m1", "tennis", 1.40, 0.76, 0.02, group="Varga"); d2 = Leg("v2", "m4", "tennis", 1.45, 0.722, 0.02, group="Varga")
check("R★ : deux jambes d'un même groupe de dépendance ne sont jamais combinées comme indépendantes", not admissible([d1, d2]))
X = ticket_stats([Leg("c", "m5", "basket", 1.62, devig_power([1.52, 2.66])[0], 0.02)])
Y = ticket_stats([Leg("a", "m1", "tennis", 1.30, devig_power([1.27, 4.05])[0], 0.02), Leg("c", "m5", "basket", 1.62, devig_power([1.52, 2.66])[0], 0.02)])
floor = threshold_odds(X["P_low"], Y["ev_low"])
check("Seuil de bascule (3.10) : à la cote plancher, l'EV prudente de X rejoint celle de Y (C1 : 1,60)", floor == 1.60 and floor * X["P_low"] - 1 >= Y["ev_low"] - 1e-9, f"plancher={floor} EVp(X à plancher)={floor*X['P_low']-1:.4f} EVp(Y)={Y['ev_low']:.4f}")

# ---------- old prompt (SOL 5.16) worked examples, kept or quoted in the audit ----------
check("SOL5.16 ex. A : 0,75×1,25−1 = −6,25 % ; 0,55×1,90−1 = +4,5 %", abs(0.75 * 1.25 - 1 + 0.0625) < 1e-12 and abs(0.55 * 1.90 - 1 - 0.045) < 1e-12)
check("SOL5.16 ex. B : 0,7×0,7=49 % ; ×0,75 = 36,75 %", abs(0.7 * 0.7 * 0.75 - 0.3675) < 1e-12)
ev_c = 0.36 * 2.10 + 0.18 * 1.40 - 1
check("SOL5.16 ex. C (DNB dans un ticket) : EV = +0,80 %, profit 54 %, gain plein 36 %", abs(ev_c - 0.008) < 1e-12 and abs(0.50 * 0.72 + 0.25 * 0.72 - 0.54) < 1e-12)
check("SOL5.16 ex. D : 60 min 28,35 % ; 90 min 39,35 %", round((1 - math.exp(-0.5 * 60 / 90)) * 100, 2) == 28.35 and round((1 - math.exp(-0.5)) * 100, 2) == 39.35)
check("SOL5.16 ex. E : médianes 80 % ; moyennes 100 %", abs(sum([0.40, 0.30, 0.10]) - 0.80) < 1e-12 and abs(sum([(0.6 + 0.4 + 0.3) / 3, (0.3 + 0.2 + 0.6) / 3, (0.1 + 0.4 + 0.1) / 3]) - 1) < 1e-12)
check("SOL5.16 ex. G : demi-gain 1,40 ; ×1,50 = 2,10 ; demi-perte ×1,50 = 0,75", abs((1.80 + 1) / 2 - 1.40) < 1e-12 and abs(1.40 * 1.50 - 2.10) < 1e-12 and abs(0.5 * 1.5 - 0.75) < 1e-12)
check("SOL5.16 ex. H : 1,40×1,35 = 1,89 ; 50,4 % ; EV −4,744 % ; 3,42 ; 26 % ; −11,08 %", abs(1.4 * 1.35 - 1.89) < 1e-12 and abs(1.89 * 0.504 - 1 + 0.04744) < 1e-9 and abs(1.8 * 1.9 * 0.26 - 1 + 0.1108) < 1e-9)
check("SOL5.16 9.6 : 80 %^3/^4/^5 = 51,2 / 40,96 / 32,768 %", abs(0.8 ** 3 - 0.512) < 1e-12 and abs(0.8 ** 4 - 0.4096) < 1e-12 and abs(0.8 ** 5 - 0.32768) < 1e-12)
lam = 2.6
p_over = 1 - math.exp(-lam) * (1 + lam + lam ** 2 / 2)
grid = sum(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(3, 40))
check("Formule Poisson P(plus de 2,5) conforme à la somme de la grille", abs(p_over - grid) < 1e-12, f"{p_over:.6f}")


# ---------- examples added in the final version (v5) ----------
pr = devig_power([1.38, 3.20])[0]
check("SOL6 fiche : exemple de registre (p_ref 71,0 % ; EV +0,8 % ; prudente −2,0 % ; marge Winamax 6,8 %)",
      round(pr*100,1) == 71.0 and round((1.42*pr-1)*100,1) == 0.8 and round((1.42*(pr-0.02)-1)*100,1) == -2.0 and round(margin([1.42, 2.75])*100,1) == 6.8,
      f"{pr:.4f} {1.42*pr-1:+.4f} {1.42*(pr-0.02)-1:+.4f} {margin([1.42,2.75]):.4f}")
check("SOL6 3.10 exemple : (1 − 0,025 − 0,01) / 0,613 = 1,574 → plancher 1,58", math.ceil((1-0.025-0.01)/0.613*100)/100 == 1.58)
pc = devig_power([1.52, 2.66])[0]; pa = devig_power([1.27, 4.05])[0]
evx = 1.62*(pc-0.03)-1; evy = 1.30*(pa-0.02)*1.62*(pc-0.03)-1
fl = math.ceil((1+evy-0.01)/(pc-0.03)*100-1e-9)/100
ok_t = (1.58*(pc-0.03)-1 >= evy-0.01) and (1.57*(pc-0.03)-1 < evy-0.01)
check("SOL6 carte d'exemple : Comets EV +4,2 %, prudente −0,6 % (±3 avant rapport), plancher 1,58 avec t = −1 point exact au centime",
      round((1.62*pc-1)*100,1) == 4.2 and round(evx*100,1) == -0.6 and fl == 1.58 and ok_t, f"EVp {evx:+.5f} Y {evy:+.5f} plancher {fl}")

w = max(len(n) for n, _, _ in results)
ok = sum(1 for _, c, _ in results if c)
for n, c, d in results:
    print(f"{'OK ' if c else 'ÉCHEC'} {n}{'  — ' + d if d else ''}")
print(f"\n{ok}/{len(results)} contrôles réussis")
