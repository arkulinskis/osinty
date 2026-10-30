"""Case files: the simulated investigations (content in cases_content.py).

A run (table case_runs) remembers what the agent found, pinned, answered, which hints they took and how
many wrong answers they gave. Score = 100 - 8 per hint - 4 per wrong answer (never below 30).
XP = the case's XP x score%, awarded once (the first solve). Replays keep the best score.
"""
import re

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Agents
from . import cases_content as CC

HINT_COST = 8
WRONG_COST = 4
MIN_SCORE = 30


# ------------------------------------------------------------------------------------------- matching
def _norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _words(s):
    out = set()
    for w in re.findall(r"[a-z0-9]+", (s or "").lower()):
        out.add(w)
        if len(w) > 3 and w.endswith("s"):
            out.add(w[:-1])
    return out


def _compacts(s):
    return {_norm(chunk) for chunk in (s or "").lower().split()} | {_norm(s)}


def matches(doc, query):
    words, compacts = _words(query), _compacts(query)
    hits = 0
    for key in doc["keys"]:
        kw = _words(key)
        if (kw and kw <= words) or _norm(key) in compacts:
            hits += 1
    return hits


def check_answer(question, answer):
    a = _norm(answer)
    if not a or len(a) > 60:
        return False
    return any(_norm(x) and _norm(x) in a for x in question["accept"])


# ------------------------------------------------------------------------------------------- runs
def _run(me, case, create=False):
    r = app_tables.case_runs.get(user=me, case_id=case["id"])
    if r is None and create:
        r = app_tables.case_runs.add_row(user=me, case_id=case["id"], found=[], pinned=[], answers={}, hints={}, wrong=0, searches=0,
                                         status="open", score=0, xp=0, started=C.now(), updated=C.now(), is_demo=False)
    return r


def _score(r):
    return max(MIN_SCORE, 100 - HINT_COST * sum((r["hints"] or {}).values()) - WRONG_COST * int(r["wrong"] or 0))


def _doc(d, pinned=()):
    return {"id": d["id"], "src": d["src"], "title": d["title"], "url": d.get("url", ""), "date": d.get("date", ""),
            "body": d["body"], "meta": d.get("meta") or [], "pinned": d["id"] in pinned}


def _state(case, r):
    found = list(r["found"] or []) if r else []
    pinned = list(r["pinned"] or []) if r else []
    answers = dict(r["answers"] or {}) if r else {}
    hints = dict(r["hints"] or {}) if r else {}
    by_id = {d["id"]: d for d in case["docs"]}
    status = r["status"] if r else "new"
    solved_once = bool(r and r["xp"])
    qs = []
    for q in case["questions"]:
        used = int(hints.get(q["id"], 0))
        qs.append({"id": q["id"], "text": q["text"], "answer": answers.get(q["id"]), "hints": q["hints"][:used],
                   "hints_left": len(q["hints"]) - used})
    return {"status": status, "found": [_doc(by_id[i], pinned) for i in found if i in by_id], "pinned": pinned,
            "questions": qs, "score": _score(r) if r else 100, "best": int(r["score"] or 0) if r else 0,
            "xp": int(r["xp"] or 0) if r else 0, "searches": int(r["searches"] or 0) if r else 0,
            "wrong": int(r["wrong"] or 0) if r else 0, "solved_once": solved_once,
            "debrief": case["debrief"] if solved_once or status == "solved" else None}


def _case_or_fail(case_id):
    return CC.case_by_id(case_id) if isinstance(case_id, str) else None


# ------------------------------------------------------------------------------------------- callables
@anvil.server.callable(require_user=True)
def list_cases():
    me = C.require_user()
    runs = {r["case_id"]: r for r in app_tables.case_runs.search(user=me)}
    solvers = {}
    for r in app_tables.case_runs.search():
        if r["xp"]:
            solvers[r["case_id"]] = solvers.get(r["case_id"], 0) + 1
    out = []
    for c in CC.CASES:
        r = runs.get(c["id"])
        out.append({"id": c["id"], "num": c["num"], "title": c["title"], "codename": c["codename"], "level": c["level"],
                    "xp": c["xp"], "minutes": c["minutes"], "teaser": c["teaser"], "client": c["client"], "module": c["module"],
                    "sources": c["sources"], "questions": len(c["questions"]),
                    "status": (r["status"] if r else "new"), "solved": bool(r and r["xp"]), "best": int(r["score"] or 0) if r else 0,
                    "answered": len(r["answers"] or {}) if r else 0, "solvers": solvers.get(c["id"], 0)})
    return {"cases": out, "sources": CC.SOURCES}


@anvil.server.callable(require_user=True)
def get_case(case_id):
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    r = _run(me, case)
    info = {k: case[k] for k in ("id", "num", "title", "codename", "level", "xp", "minutes", "teaser", "client", "brief", "exhibits", "sources", "module")}
    return C.ok(case=info, sources=CC.SOURCES, state=_state(case, r))


@anvil.server.callable(require_user=True)
def case_search(case_id, source, query):
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    if source not in case["sources"]:
        return C.fail("That source isn't available in this case.")
    query = C.text(query, 120)
    if len(_norm(query)) < 2:
        return C.fail("Type something to search for.")
    if C.rate_limited("case_search", 300, 3600):
        return C.fail("The terminal is overheating. Take a short break and try again.")
    r = _run(me, case, create=True)
    scored = [(matches(d, query), i, d) for i, d in enumerate(case["docs"]) if d["src"] == source]
    hits = [d for s, _i, d in sorted([x for x in scored if x[0] > 0], key=lambda x: (-x[0], x[1]))]
    found = list(r["found"] or [])
    new = [d["id"] for d in hits if d["id"] not in found]
    r.update(found=found + new, searches=int(r["searches"] or 0) + 1, updated=C.now())
    Agents.touch(me)
    pinned = list(r["pinned"] or [])
    return C.ok(results=[_doc(d, pinned) for d in hits], new=new, query=query, source=source)


@anvil.server.callable(require_user=True)
def case_pin(case_id, doc_id, flag):
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    r = _run(me, case)
    if r is None or doc_id not in (r["found"] or []):
        return C.fail("Find that document before you pin it.")
    pinned = [p for p in (r["pinned"] or []) if p != doc_id]
    if flag:
        pinned.append(doc_id)
    r.update(pinned=pinned, updated=C.now())
    return C.ok(pinned=pinned)


@anvil.server.callable(require_user=True)
def case_hint(case_id, question_id):
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    q = next((x for x in case["questions"] if x["id"] == question_id), None)
    if q is None:
        return C.fail("That question doesn't exist.")
    r = _run(me, case, create=True)
    if (r["answers"] or {}).get(q["id"]):
        return C.fail("You've already cracked that one.")
    hints = dict(r["hints"] or {})
    used = int(hints.get(q["id"], 0))
    if used >= len(q["hints"]):
        return C.fail("No more hints for this question. Trust your instincts.")
    hints[q["id"]] = used + 1
    r.update(hints=hints, updated=C.now())
    return C.ok(hint=q["hints"][used], hints=q["hints"][:used + 1], hints_left=len(q["hints"]) - used - 1, score=_score(r))


@anvil.server.callable(require_user=True)
def case_answer(case_id, question_id, answer):
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    q = next((x for x in case["questions"] if x["id"] == question_id), None)
    if q is None:
        return C.fail("That question doesn't exist.")
    answer = C.text(answer, 80)
    if not _norm(answer):
        return C.fail("Type your answer first.")
    r = _run(me, case, create=True)
    answers = dict(r["answers"] or {})
    if answers.get(q["id"]):
        return C.ok(correct=True, already=True, state=_state(case, r))
    if not check_answer(q, answer):
        r.update(wrong=int(r["wrong"] or 0) + 1, updated=C.now())
        Agents.touch(me)
        return C.ok(correct=False, score=_score(r), state=_state(case, r))
    answers[q["id"]] = answer
    r.update(answers=answers, updated=C.now())
    before = Agents.snapshot(me)
    gained = 0
    solved_now = len(answers) == len(case["questions"])
    if solved_now:
        score = _score(r)
        if not r["xp"]:
            gained = int(round(case["xp"] * score / 100.0))
            r.update(xp=gained)
        r.update(status="solved", score=max(score, int(r["score"] or 0)), finished=C.now())
    Agents.award(me, gained)
    out = C.ok(correct=True, solved=solved_now, xp_gained=gained, score=_score(r), state=_state(case, r))
    out.update(Agents.changes(me, before))
    return out


@anvil.server.callable(require_user=True)
def case_reset(case_id):
    """Start the case again. A solved case keeps its XP and best score (a replay earns no new XP)."""
    me = C.require_user()
    case = _case_or_fail(case_id)
    if case is None:
        return C.fail("That case file doesn't exist.")
    r = _run(me, case)
    if r is None:
        return C.ok(state=_state(case, None))
    r.update(found=[], pinned=[], answers={}, hints={}, wrong=0, searches=0, updated=C.now(),
             status="replay" if r["xp"] else "open")
    return C.ok(state=_state(case, r))
