"""Reference calculator for the SOL 6.0 decision rule (R-star) and prompt examples.
Import-only module; see tests_calc.py and cases_build.py.
"""
import itertools, math
from scipy.optimize import brentq

TOL = 0.01  # price tie tolerance (EV prudente points)


def devig_power(odds):
    q = [1 / o for o in odds]
    if sum(q) <= 1:
        s = sum(q); return [x / s for x in q]
    k = brentq(lambda k: sum(x ** k for x in q) - 1, 1.0, 60.0)
    return [x ** k for x in q]


def devig_mult(odds):
    q = [1 / o for o in odds]; s = sum(q); return [x / s for x in q]


def margin(odds):
    return sum(1 / o for o in odds) - 1


class Leg:
    def __init__(self, rid, match, sport, odds, p, band=0.02, quality="A", gate=False, cond=None, label="", group=None):
        self.rid, self.match, self.sport, self.odds, self.p = rid, match, sport, odds, p
        self.band, self.quality, self.gate, self.cond, self.label = band, quality, gate, cond, label
        self.group = group  # dependence group (same player / same team): never treated as independent

    @property
    def p_low(self):
        return max(0.0, self.p - self.band)

    def ev(self):
        return self.odds * self.p - 1

    def ev_low(self):
        return self.odds * self.p_low - 1


def ticket_stats(legs, boost=0.0):
    o = math.prod(l.odds for l in legs)
    P = math.prod(l.p for l in legs)
    Pl = math.prod(l.p_low for l in legs)
    payout = 1 + (o - 1) * (1 + boost)
    return dict(odds=o, P=P, P_low=Pl, ev=payout * P - 1, ev_low=payout * Pl - 1, n=len(legs),
                sports=sorted({l.sport for l in legs}), rids=[l.rid for l in legs],
                qual=max(l.quality for l in legs), conds=sum(1 for l in legs if l.gate))


def admissible(legs, allow_conditional=False):
    if len({l.match for l in legs}) < len(legs):
        return False
    groups = [l.group for l in legs if l.group]
    if len(groups) != len(set(groups)):
        return False
    for l in legs:
        if l.quality == "C":
            return False
        if l.gate and not allow_conditional:
            return False
    return True


def rstar(candidates, target=None):
    """R-star v3: rank admissible candidates by EV prudente; the head group = within TOL of the best;
    inside the head group: fewer legs, then better worst quality, then fewer pending conditions, then higher EV prudente.
    P(ticket) is never a ranking criterion between different odds (target unused, kept for API compat)."""
    if not candidates:
        return []
    best = max(c["ev_low"] for c in candidates)
    head = [c for c in candidates if c["ev_low"] >= best - TOL - 1e-12]
    rest = [c for c in candidates if c not in head]
    head.sort(key=lambda c: (c["n"], c["qual"], c["conds"], -c["ev_low"]))
    rest.sort(key=lambda c: (-c["ev_low"], c["n"]))
    return head + rest


def enumerate_tickets(legs, kmin=1, kmax=5, lo=None, hi=None, sports=None, allow_conditional=False, boost_fn=None):
    out = []
    for k in range(kmin, kmax + 1):
        for combo in itertools.combinations(legs, k):
            if not admissible(combo, allow_conditional):
                continue
            if sports and not all(l.sport in sports for l in combo):
                continue
            b = boost_fn(k) if boost_fn else 0.0
            t = ticket_stats(combo, b)
            if lo is not None and t["odds"] < lo - 1e-9:
                continue
            if hi is not None and t["odds"] > hi + 1e-9:
                continue
            out.append(t)
    return out


def threshold_odds(x_leg_or_ticket_plow, y_ev_low):
    """minimum odds for X to keep rank vs Y: (1+EV_low(Y))/P_low(X), rounded up to 0.01"""
    v = (1 + y_ev_low) / x_leg_or_ticket_plow
    return math.ceil(v * 100 - 1e-9) / 100


def fmt(t):
    return (f"{'+'.join(t['rids']):22s} k={t['n']} cote={t['odds']:.3f} P={t['P']*100:5.1f}% "
            f"EV={t['ev']*100:+5.1f}% EVprud={t['ev_low']*100:+5.1f}% {','.join(t['sports'])}")


# ---------------- v7 extensions ----------------
def with_odds(legs, rid, o):
    out = []
    for l in legs:
        out.append(Leg(l.rid, l.match, l.sport, (o if l.rid == rid else l.odds), l.p, l.band, l.quality, l.gate, label=l.label, group=l.group))
    return out


def replay_threshold(legs, rid, lo=1.50, hi=4.00, step=0.01, stop=1.01, chooser=None):
    """Lower the odds of leg `rid` cent by cent, recomputing every ticket that contains it, and replay the full ranking.
    Returns (threshold, new_winner_rids): the lowest odds at which the current winner still wins, and who wins just below."""
    chooser = chooser or (lambda L: (rstar(enumerate_tickets(L, lo=lo, hi=hi)) or [None])[0])
    o0 = [l.odds for l in legs if l.rid == rid][0]
    w0 = chooser(legs)
    o = o0
    while o - step >= stop:
        o = round(o - step, 2)
        w = chooser(with_odds(legs, rid, o))
        if w is None or w["rids"] != w0["rids"]:
            return round(o + step, 2), (w["rids"] if w else None)
    return None, None


def shield(legs, lo=1.75, hi=2.10, cap=0.02):
    """🛡️ ticket court: two legs in the zone; among tickets whose EV prudente is within `cap` of the best one in the zone,
    pick the highest P(ticket); report the price sacrifice."""
    c = enumerate_tickets(legs, kmin=2, kmax=2, lo=lo, hi=hi)
    if not c:
        return None, None, []
    best = max(t["ev_low"] for t in c)
    allowed = [t for t in c if t["ev_low"] >= best - cap - 1e-12]
    allowed.sort(key=lambda t: (-t["P"], -t["ev_low"]))
    return allowed[0], best, sorted(c, key=lambda t: -t["ev_low"])


class MLeg:
    """Multi-state leg: states = [(name, prob, gross_return)], probabilities sum to 1."""
    def __init__(self, rid, match, states, band=0.02, label=""):
        self.rid, self.match, self.states, self.band, self.label = rid, match, states, band, label
        assert abs(sum(p for _, p, _ in states) - 1) < 1e-9

    def prudent(self):
        """Move `band` of probability from the best-return state to the worst-return state (total stays 100 %)."""
        st = [list(s) for s in self.states]
        ib = max(range(len(st)), key=lambda i: st[i][2]); iw = min(range(len(st)), key=lambda i: st[i][2])
        d = min(self.band, st[ib][1])
        st[ib][1] -= d; st[iw][1] += d
        return [tuple(s) for s in st]


def ticket_states(mlegs, prudent=False, boost=0.0):
    """Joint distribution of gross return for independent multi-state legs. Boost (on net winnings) only if every leg is a full win."""
    import itertools as it
    dists = [(l.prudent() if prudent else l.states) for l in mlegs]
    out = {}
    for combo in it.product(*dists):
        p = math.prod(s[1] for s in combo)
        r = math.prod(s[2] for s in combo)
        full = all(s[0] == "gain" for s in combo)
        if full and boost:
            r = 1 + (r - 1) * (1 + boost)
        out[r] = out.get(r, 0) + p
    ev = sum(p * r for r, p in out.items()) - 1
    p_full = sum(p for r, p in out.items() if r >= max(out) - 1e-12)
    p_profit = sum(p for r, p in out.items() if r > 1 + 1e-12)
    p_refund = sum(p for r, p in out.items() if abs(r - 1) < 1e-12)
    return dict(ev=ev, p_full=p_full, p_profit=p_profit, p_refund=p_refund, dist=sorted(out.items()), total=sum(out.values()))


def binary(rid, match, o, p, band=0.02, label=""):
    return MLeg(rid, match, [("gain", p, o), ("perte", 1 - p, 0.0)], band, label)


# ---------------- 6.3 : freebet (stake not returned) ----------------
def freebet_rank(legs, amount=10.0, min_odds=1.0, kmax=5, tol=0.01):
    """Value of a stake-not-returned freebet ticket = amount * P * (odds - 1); prudent value uses P_low.
    R-star logic: head group within tol*amount of the best prudent value, then fewer legs, worse-quality last, more value."""
    out = []
    for k in range(1, kmax + 1):
        for combo in itertools.combinations(legs, k):
            if not admissible(combo):
                continue
            t = ticket_stats(combo)
            if t["odds"] < min_odds - 1e-9:
                continue
            t["value"] = amount * t["P"] * (t["odds"] - 1)
            t["value_low"] = amount * t["P_low"] * (t["odds"] - 1)
            out.append(t)
    if not out:
        return []
    b = max(t["value_low"] for t in out)
    head = sorted([t for t in out if t["value_low"] >= b - tol * amount - 1e-12], key=lambda t: (t["n"], t["qual"], t["conds"], -t["value_low"]))
    return head + sorted([t for t in out if t not in head], key=lambda t: -t["value_low"])


# ---------------- 6.16 : 🛡️ with a dominating single ----------------
def shield_with_single(legs, lo=1.75, hi=2.10, cap=0.02):
    """Two-leg short ticket as in shield(); a single in the zone replaces it when it dominates it
    (chance and EV prudente at least equal). Returns (ticket, kind) with kind in {'deux jambes', 'simple dominant'}."""
    pick, best, _ = shield(legs, lo, hi, cap)
    singles = [ticket_stats([l]) for l in legs if lo - 1e-9 <= l.odds <= hi + 1e-9 and admissible([l])]
    if pick is None:
        return (max(singles, key=lambda t: (t["P"], t["ev_low"])) if singles else None), "simple (aucun ticket de deux jambes)"
    dom = [t for t in singles if t["P"] >= pick["P"] - 1e-12 and t["ev_low"] >= pick["ev_low"] - 1e-12]
    if dom:
        return max(dom, key=lambda t: (t["P"], t["ev_low"])), "simple dominant"
    return pick, "deux jambes"


# ---------------- 6.26 : 🛡️ full rule ----------------
def shield_v3(legs, lo=1.75, hi=2.10, cap=0.02):
    """🛡️ ticket court (6.26): reference = best EV prudente among zone tickets of 1 or 2 legs; allowed = within `cap`;
    pick the most probable allowed two-leg ticket; a single in the zone replaces it if it dominates it (P and EVp at least equal);
    if no two-leg ticket is allowed, pick the most probable allowed ticket (single included)."""
    z = [t for t in enumerate_tickets(legs, kmin=1, kmax=2, lo=lo, hi=hi)]
    if not z:
        return None, "aucun ticket dans la zone"
    best = max(t["ev_low"] for t in z)
    allowed = [t for t in z if t["ev_low"] >= best - cap - 1e-12]
    doubles = [t for t in allowed if t["n"] == 2]
    if doubles:
        pick = max(doubles, key=lambda t: (t["P"], t["ev_low"]))
        dom = [t for t in allowed if t["n"] == 1 and t["P"] >= pick["P"] - 1e-12 and t["ev_low"] >= pick["ev_low"] - 1e-12]
        return (max(dom, key=lambda t: (t["P"], t["ev_low"])), "simple dominant") if dom else (pick, "deux jambes")
    return max(allowed, key=lambda t: (t["P"], t["ev_low"])), "simple (aucune paire dans la limite)"
