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
