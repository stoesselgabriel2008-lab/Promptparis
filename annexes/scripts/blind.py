"""Copy test outputs to the judge folder under blind X/Y names (mapping fixed before outputs were read).
Usage: python3 -I blind.py SCRATCHPAD_DIR
"""
import sys, os, re, json
S = sys.argv[1]
MAPPING = {  # fixed on 2026-11-04 before any output existed
    "C1": {"X": "M", "Y": "R"}, "C2": {"X": "R", "Y": "M"}, "C3": {"X": "M", "Y": "R"},
    "C4": {"X": "R", "Y": "M"}, "C5": {"X": "R", "Y": "M"}, "C6": {"X": "M", "Y": "R"},
}
pat = re.compile(r"SOL\s*(6\.0|5\.17|5\.16)", re.I)
pat2 = re.compile(r"R★|R\*")
os.makedirs(os.path.join(S, "judge", "blind"), exist_ok=True)
for c, m in MAPPING.items():
    for lab, var in m.items():
        src = os.path.join(S, "outputs", f"{c}_{var}.txt")
        if not os.path.exists(src):
            print("missing", src); continue
        t = open(src, encoding="utf-8").read()
        t = pat2.sub("[règle]", pat.sub("SOL", t))
        open(os.path.join(S, "judge", "blind", f"{c}_{lab}.txt"), "w", encoding="utf-8").write(t)
json.dump(MAPPING, open(os.path.join(S, "judge", "mapping.json"), "w"))
print("ok")
