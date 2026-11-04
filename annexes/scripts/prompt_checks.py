"""Static checks for the SOL prompt before any save. Usage: python3 -I prompt_checks.py PROMPT_FILE
Exit code 0 = all checks passed."""
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
errors, notes = [], []

# 1. cross-references resolve to existing section headings
heads = set(re.findall(r"^(\d+\.\d+(?:\.\d+)?) ", s, flags=re.M))
cited = set()
s_refs = re.sub(r"Révision \d+\.\d+", "", s)  # the revision number in the header is not a section reference
for a, b in re.findall(r"\((?:voir |repères en |sinon applique )?(\d+\.\d+(?:\.\d+)?)\)|\b(\d\.\d{1,2}(?:\.\d)?)\b", s_refs):
    x = a or b
    if x and not re.match(r"^\d\.\d{2,}$", x):
        cited.add(x)
missing = sorted(c for c in cited if c not in heads and not re.match(r"^[01]\.\d+$", c))
if missing:
    errors.append(f"renvois sans section : {missing}")

# 2. required structure
for must in ["PARTIE 1 — PRIORITÉS ET ORDRE DE TRAVAIL", "2.2 La règle de décision R★", "2.5 Contrat récréatif",
             "PARTIE 9 — FICHE DE SORTIE", "PHRASE DE LANCEMENT"]:
    if must not in s:
        errors.append(f"bloc obligatoire absent : {must}")
if s.rfind("PHRASE DE LANCEMENT") < s.rfind("PARTIE 9 — FICHE DE SORTIE"):
    errors.append("la phrase de lancement doit venir après la fiche de sortie")

# 3. forbidden legacy wording (fixed in earlier passes)
for bad in ["qualité A ", "qualité B ", "qualité C ", "qualité A,", "qualité A.", "ses deux premiers concurrents",
            "B au mieux", "son EV prudente par (1", "Quand le prix change, recalcule p_ref"]:
    if bad in s:
        errors.append(f"formulation obsolète présente : « {bad} »")

# 4. headings numbered in order inside each part
nums = [tuple(int(x) for x in h.split(".")) for h in re.findall(r"^(\d+\.\d+(?:\.\d+)?) ", s, flags=re.M)]
for a, b in zip(nums, nums[1:]):
    if b < a:
        errors.append(f"numérotation non croissante : {a} puis {b}")

# 5. emoji formats all defined in 2.3
for e in ["⭐", "🎯", "🛡️", "🎾", "🎲", "🚀", "🎉"]:
    if e + " " not in s[s.find("2.3 Le menu"):s.find("2.4 Labels")]:
        errors.append(f"format {e} non défini en 2.3")

words = len(s.split())
notes.append(f"mots : {words}")
if words > 12000:
    errors.append(f"prompt trop long ({words} mots > 12 000)")

for n in notes: print("INFO", n)
for e in errors: print("ÉCHEC", e)
print("CONTRÔLES STATIQUES :", "OK" if not errors else f"{len(errors)} échec(s)")
sys.exit(1 if errors else 0)
