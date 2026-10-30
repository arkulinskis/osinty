"""Agents: XP, ranks, streaks, badges, the leaderboard ("the Bureau"), the office (home page), the daily
briefing, the dossier (profile stats) and the saved Field Kit tools.

Other modules award XP through award(user, amount) and report rank-ups and new badges with
snapshot(user) before and after (see changes()).
"""
import datetime as dt
import re

import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import DemoData
from . import cases_content as CC
from . import lessons_content as LC

RANKS = [(0, "Rookie"), (120, "Gumshoe"), (320, "Operative"), (600, "Field Agent"), (950, "Detective"),
         (1400, "Senior Investigator"), (1850, "Master Sleuth")]
BRIEFING_XP = 5

BADGES = [
    ("first_lesson", "First Day on the Job", "Pass your first lesson.", "book"),
    ("ethics", "Clean Hands", "Pass 'The law, ethics and the line you don't cross'.", "shield"),
    ("module", "Graduate", "Pass every lesson in one module.", "award"),
    ("perfect5", "Sharp Mind", "Score 100% on five quizzes.", "bolt"),
    ("academy", "Valedictorian", "Pass all 24 lessons.", "star"),
    ("first_case", "Case Closed", "Solve your first case file.", "folder"),
    ("no_hints", "Lone Wolf", "Solve a case without a single hint.", "eye"),
    ("all_cases", "Legend of the Bureau", "Solve all six case files.", "crown"),
    ("casebook", "Gumshoe's Notebook", "Put five leads in one investigation.", "edit"),
    ("strings", "Red String", "Connect three pairs of leads on a corkboard.", "link"),
    ("streak3", "Night Shift", "Be on duty three days in a row.", "moon"),
    ("streak7", "Relentless", "Be on duty seven days in a row.", "flame"),
    ("kit5", "Well Equipped", "Save five tools to your Field Kit.", "tool"),
]
TOTAL_LESSONS = sum(len(m["lessons"]) for m in LC.MODULES)


# ------------------------------------------------------------------------------------------- ranks and XP
def rank_info(xp):
    xp = int(xp or 0)
    idx = 0
    for i, (need, _name) in enumerate(RANKS):
        if xp >= need:
            idx = i
    floor, name = RANKS[idx]
    nxt = RANKS[idx + 1] if idx + 1 < len(RANKS) else None
    pct = 100 if nxt is None else int(round(100.0 * (xp - floor) / (nxt[0] - floor)))
    return {"xp": xp, "rank": name, "level": idx + 1, "of": len(RANKS), "next": nxt[1] if nxt else None,
            "next_xp": nxt[0] if nxt else None, "to_next": (nxt[0] - xp) if nxt else 0, "pct": max(0, min(100, pct))}


def today():
    return C.now().date()


def touch(user):
    """Count today as a day on duty (the streak)."""
    t = today()
    last = user["active_day"]
    if last == t:
        return
    if last == t - dt.timedelta(days=1):
        user["streak"] = int(user["streak"] or 0) + 1
    else:
        user["streak"] = 1
    user["active_day"] = t


def live_streak(user):
    last = user["active_day"]
    if last is None or last < today() - dt.timedelta(days=1):
        return 0
    return int(user["streak"] or 0)


def award(user, amount):
    amount = int(amount or 0)
    if amount > 0:
        user["xp"] = int(user["xp"] or 0) + amount
    touch(user)
    return amount


# ------------------------------------------------------------------------------------------- badges
def earned_badges(user):
    progress = list(app_tables.progress.search(user=user))
    done = {p["lesson_id"] for p in progress}
    runs = [r for r in app_tables.case_runs.search(user=user) if r["xp"]]
    invs = list(app_tables.investigations.search(owner=user))
    got = set()
    if done:
        got.add("first_lesson")
    if "m1l2" in done:
        got.add("ethics")
    if any(all(lesson["id"] in done for lesson in m["lessons"]) for m in LC.MODULES):
        got.add("module")
    if len([p for p in progress if p["score"] == p["total"]]) >= 5:
        got.add("perfect5")
    if len(done) >= TOTAL_LESSONS:
        got.add("academy")
    if runs:
        got.add("first_case")
    if any(not sum((r["hints"] or {}).values()) for r in runs):
        got.add("no_hints")
    if len({r["case_id"] for r in runs}) >= len(CC.CASES):
        got.add("all_cases")
    links = 0
    for inv in invs:
        if len(app_tables.leads.search(investigation=inv)) >= 5:
            got.add("casebook")
        links += len(app_tables.links.search(investigation=inv))
    if links >= 3:
        got.add("strings")
    streak = live_streak(user)
    if streak >= 3:
        got.add("streak3")
    if streak >= 7:
        got.add("streak7")
    if len(user["kit"] or []) >= 5:
        got.add("kit5")
    return got


def badge_list(got):
    return [{"id": b[0], "name": b[1], "how": b[2], "icon": b[3], "earned": b[0] in got} for b in BADGES]


def snapshot(user):
    return {"rank": rank_info(user["xp"])["rank"], "badges": earned_badges(user)}


def changes(user, before):
    """What changed since snapshot(): {rank_up: name|None, badges: [{id, name, icon}], me: rank_info}."""
    after = snapshot(user)
    new = [b for b in BADGES if b[0] in after["badges"] - before["badges"]]
    return {"rank_up": after["rank"] if after["rank"] != before["rank"] else None,
            "badges": [{"id": b[0], "name": b[1], "icon": b[3]} for b in new],
            "me": rank_info(user["xp"])}


# ------------------------------------------------------------------------------------------- leaderboard
def leaderboard(me, limit=10):
    people = [u for u in app_tables.users.search() if (u["xp"] or 0) > 0 and not u["board_hidden"] and (u["is_demo"] or u["enabled"] is not False)]
    people.sort(key=lambda u: (-(u["xp"] or 0), C.name_of(u)))
    rows = []
    my_place = None
    for i, u in enumerate(people):
        if me is not None and u == me:
            my_place = i + 1
        if i < limit:
            rows.append({"place": i + 1, "name": C.name_of(u), "xp": int(u["xp"] or 0), "rank": rank_info(u["xp"])["rank"],
                         "me": me is not None and u == me, "demo": bool(u["is_demo"])})
    return {"rows": rows, "my_place": my_place, "total": len(people)}


def _tip_of_day():
    t = today()
    i = t.timetuple().tm_yday % len(LC.TIPS)
    return {"title": LC.TIPS[i][0], "body": LC.TIPS[i][1], "day": t.isoformat()}


# ------------------------------------------------------------------------------------------- callables
@anvil.server.callable(require_user=True)
def get_office():
    """Everything the home page (the office) needs, in one call."""
    DemoData.ensure_loaded()
    me = C.require_user()
    done = {p["lesson_id"]: p for p in app_tables.progress.search(user=me)}
    next_lesson = None
    for m, i, lesson in LC.all_lessons():
        if lesson["id"] not in done:
            next_lesson = {"id": lesson["id"], "title": lesson["title"], "module": m["title"], "module_num": m["num"],
                           "num": "%d.%d" % (m["num"], i + 1), "minutes": lesson["minutes"], "summary": lesson["summary"]}
            break
    runs = {r["case_id"]: r for r in app_tables.case_runs.search(user=me)}
    active, next_case = [], None
    for c in CC.CASES:
        r = runs.get(c["id"])
        if r is not None and r["status"] in ("open", "replay"):
            active.append({"id": c["id"], "title": c["title"], "codename": c["codename"], "answered": len(r["answers"] or {}),
                           "total": len(c["questions"]), "found": len(r["found"] or [])})
        if next_case is None and (r is None or (r["status"] != "solved" and not r["xp"])):
            next_case = {"id": c["id"], "title": c["title"], "codename": c["codename"], "level": c["level"], "teaser": c["teaser"], "xp": c["xp"]}
    solved = len([r for r in runs.values() if r["xp"]])
    invs = list(app_tables.investigations.search(owner=me))
    bulletins = sorted(app_tables.bulletins.search(), key=lambda b: b["created"], reverse=True)[:4]
    got = earned_badges(me)
    return {
        "me": rank_info(me["xp"]), "streak": live_streak(me), "briefing_done": me["briefing_day"] == today(),
        "tip": _tip_of_day(), "next_lesson": next_lesson, "lessons_done": len(done), "lessons_total": TOTAL_LESSONS,
        "active_cases": active, "next_case": next_case, "cases_solved": solved, "cases_total": len(CC.CASES),
        "investigations": {"open": len([i for i in invs if i["status"] == "open"]), "total": len(invs)},
        "badges": badge_list(got), "board": leaderboard(me),
        "bulletins": [{"id": b.get_id(), "title": b["title"], "body": b["body"], "kind": b["kind"] or "note", "created": C.iso(b["created"])}
                      for b in bulletins],
    }


@anvil.server.callable(require_user=True)
def claim_briefing():
    """Read today's briefing: +5 XP once a day, and it counts as a day on duty."""
    me = C.require_user()
    if me["briefing_day"] == today():
        return C.fail("You've already signed today's briefing. Come back tomorrow.")
    before = snapshot(me)
    me["briefing_day"] = today()
    award(me, BRIEFING_XP)
    return C.ok(xp_gained=BRIEFING_XP, streak=live_streak(me), **changes(me, before))


@anvil.server.callable(require_user=True)
def get_dossier():
    """The profile page: rank ladder, stats, badges, privacy setting."""
    me = C.require_user()
    progress = list(app_tables.progress.search(user=me))
    runs = [r for r in app_tables.case_runs.search(user=me) if r["xp"]]
    got = earned_badges(me)
    return {"me": rank_info(me["xp"]), "streak": live_streak(me), "ranks": [{"xp": r[0], "name": r[1]} for r in RANKS],
            "lessons_done": len(progress), "lessons_total": TOTAL_LESSONS,
            "perfect": len([p for p in progress if p["score"] == p["total"]]),
            "cases_solved": len(runs), "cases_total": len(CC.CASES),
            "best_case": max([r["score"] or 0 for r in runs] or [0]),
            "investigations": len(app_tables.investigations.search(owner=me)),
            "badges": badge_list(got), "board_hidden": bool(me["board_hidden"]),
            "board": leaderboard(me, limit=0)}


@anvil.server.callable(require_user=True)
def set_board_hidden(flag):
    me = C.require_user()
    me["board_hidden"] = bool(flag)
    return C.ok(board_hidden=bool(flag))


TOOL_ID = re.compile(r"^[a-z0-9]{2,24}$")


@anvil.server.callable(require_user=True)
def get_kit():
    me = C.require_user()
    return {"saved": list(me["kit"] or [])}


@anvil.server.callable(require_user=True)
def toggle_kit(tool_id, flag):
    me = C.require_user()
    if not isinstance(tool_id, str) or not TOOL_ID.match(tool_id):
        return C.fail("Unknown tool.")
    before = snapshot(me)
    kit = [t for t in (me["kit"] or []) if t != tool_id]
    if flag:
        if len(kit) >= 100:
            return C.fail("Your kit is full (100 tools). Remove a few first.")
        kit.append(tool_id)
    me["kit"] = kit
    return C.ok(saved=kit, **changes(me, before))
