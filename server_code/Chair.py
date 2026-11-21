"""The Client Chair (#chair): three fictional clients a day (chair_content.py). Take the job, take it with
conditions, or show them the door; HQ rules on each one with the reason and what other agents chose.

Everyone gets the same three clients on the same UTC day: a seeded shuffle of all clients, ten days per shuffle,
so nobody sees a repeat for ten days. Works signed out (the guest's streak lives in their browser); members get
+10 XP once a day and the day counts on their duty streak.
Tables (client: none; read with try/except so the page works before the user accepts the schema):
  chair_stats (day, client, take, cond, decline)   anonymous vote counts per day and client
  chair_runs (user, day, score, picks, created, is_demo)   one row per member per day
"""
import datetime as dt
import random

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Agents
from . import chair_content as CH
from . import lessons_content as LC

EPOCH = dt.date(2026, 11, 19)  # day #1 = 2026-11-20, the day the chair opened
PER_DAY = 3
CHAIR_XP = 10
CROWD_MIN = 5  # crowd percentages show from this many votes on a client
CHOICES = ("take", "cond", "decline")


def day_num(day=None):
    return ((day or Agents.today()) - EPOCH).days


def deal(num):
    """The ids of day `num`'s clients: distinct, the same for everyone, a fresh shuffle every ten days."""
    per_cycle = len(CH.CLIENTS) // PER_DAY
    cycle, idx = divmod(max(0, num - 1), per_cycle)
    order = sorted(c["id"] for c in CH.CLIENTS)
    random.Random("osinty-chair-%d" % cycle).shuffle(order)
    return order[idx * PER_DAY:(idx + 1) * PER_DAY]


def _public(c):
    return {"id": c["id"], "who": c["who"], "ask": c["ask"], "facts": list(c["facts"])}


def _lesson(lesson_id):
    m, i, lesson = LC.lesson_by_id(lesson_id)
    if lesson is None:
        return None
    return {"id": lesson_id, "num": "%d.%d" % (m["num"], i + 1), "title": lesson["title"]}


def _crowd(num, client_id):
    try:
        row = app_tables.chair_stats.get(day=num, client=client_id)
    except Exception:
        return None
    if row is None:
        return None
    counts = {k: int(row[k] or 0) for k in CHOICES}
    total = sum(counts.values())
    if total < CROWD_MIN:
        return None
    return {"total": total, "pct": {k: int(round(100.0 * v / total)) for k, v in counts.items()}}


def _vote(num, picks):
    try:
        for cid, choice in picks.items():
            row = app_tables.chair_stats.get(day=num, client=cid)
            if row is None:
                row = app_tables.chair_stats.add_row(day=num, client=cid, take=0, cond=0, decline=0)
            row[choice] = int(row[choice] or 0) + 1
    except Exception:
        pass  # the table doesn't exist yet (schema not accepted): rulings still work, without crowd numbers


def _rulings(num, picks):
    out, score = [], 0
    for cid in deal(num):
        c = CH.client_by_id(cid)
        pick = picks.get(cid)
        right = pick == c["verdict"]
        score += 1 if right else 0
        out.append(dict(_public(c), pick=pick, pick_label=CH.VERDICTS.get(pick, ""), verdict=c["verdict"],
                        verdict_label=CH.VERDICTS[c["verdict"]], right=right, condition=c["condition"], why=c["why"],
                        lesson=_lesson(c["lesson"]), crowd=_crowd(num, cid)))
    return out, score


def _my_run(me, num):
    if me is None:
        return None
    try:
        return app_tables.chair_runs.get(user=me, day=num)
    except Exception:
        return None


def _streak(me, num):
    """Days in a row (ending today or yesterday) this member sat in the chair."""
    try:
        days = {int(r["day"]) for r in app_tables.chair_runs.search(user=me)}
    except Exception:
        return 0
    d = num if num in days else num - 1
    n = 0
    while d in days:
        n += 1
        d -= 1
    return n


def _clean_picks(num, picks):
    today = deal(num)
    if not isinstance(picks, dict) or sorted(picks.keys()) != sorted(today):
        return None
    if any(picks[k] not in CHOICES for k in today):
        return None
    return {k: picks[k] for k in today}


def office_card(me):
    """For the home page: today's number and whether this member has ruled yet."""
    num = day_num()
    r = _my_run(me, num)
    return {"day": num, "done": r is not None, "score": int(r["score"] or 0) if r is not None else None, "of": PER_DAY}


# ------------------------------------------------------------------------------------------- callables
@anvil.server.callable
def get_chair():
    """Today's three clients, without HQ's verdicts. A member who already ruled today gets the rulings back."""
    me = C.me()
    num = day_num()
    out = {"ok": True, "day": num, "date": Agents.today().isoformat(), "xp": CHAIR_XP, "member": me is not None,
           "clients": [_public(CH.client_by_id(cid)) for cid in deal(num)], "mine": None}
    r = _my_run(me, num)
    if r is not None:
        picks = _clean_picks(num, r["picks"]) or {}
        rulings, score = _rulings(num, picks)
        out["mine"] = {"rulings": rulings, "score": score, "of": PER_DAY, "streak": _streak(me, num), "xp_gained": 0}
    return out


@anvil.server.callable
def submit_chair(num, picks):
    """Hand in today's rulings: {client_id: take|cond|decline} for exactly today's three clients."""
    today = day_num()
    if num != today:
        return C.fail("A new day, new clients: reload the page to see today's.")
    clean = _clean_picks(today, picks)
    if clean is None:
        return C.fail("Rule on all three clients first.")
    if C.rate_limited("submit_chair", 20, 3600):
        return C.fail("Easy, agent. Try again in a little while.")
    me = C.me()
    gained, streak, before = 0, None, None
    if me is not None:
        r = _my_run(me, today)
        if r is not None:  # one ruling per member per day: show the first one again
            clean = _clean_picks(today, r["picks"]) or clean
        else:
            _vote(today, clean)
            score = _rulings(today, clean)[1]
            try:
                app_tables.chair_runs.add_row(user=me, day=today, score=score, picks=clean, created=C.now(), is_demo=False)
                before = Agents.snapshot(me)
                gained = Agents.award(me, CHAIR_XP)
            except Exception:
                pass  # no table yet: no XP until the schema is accepted
        streak = _streak(me, today)
    else:
        voted = anvil.server.session.get("chair_voted") or []
        if today not in voted:
            _vote(today, clean)
            getattr(anvil.server, "session")["chair_voted"] = (voted + [today])[-5:]
    rulings, score = _rulings(today, clean)
    out = C.ok(day=today, rulings=rulings, score=score, of=PER_DAY, xp_gained=gained, streak=streak)
    if before is not None:
        out.update(Agents.changes(me, before))
    return out
