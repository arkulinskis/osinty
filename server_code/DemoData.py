"""Demo content, so the app never looks empty. Loaded automatically the first time anyone opens the app
(ensure_loaded), removed or reloaded from Admin -> Demo data. Removing it is remembered: it doesn't come back.

Demo agents have is_demo=True and @example.com emails; they can't sign in (no password). They fill the
Bureau leaderboard and the case-file solve counts. Every demo row is flagged is_demo=True, so remove()
deletes exactly what load() added.
"""
import datetime as dt

from anvil.tables import app_tables

from . import common as C
from . import cases_content as CC
from . import lessons_content as LC

# name, lessons passed (in order), cases solved (in order), average case score, streak
DEMO_AGENTS = [
    ("Maya Chen", 24, 6, 88, 9),
    ("Theo Martin", 21, 5, 80, 4),
    ("Ines Ozola", 18, 4, 92, 2),
    ("Kofi Mensah", 13, 3, 76, 1),
    ("Sofia Rossi", 9, 2, 84, 3),
    ("Liam O'Connor", 6, 1, 68, 0),
    ("Aiko Tanaka", 4, 1, 96, 1),
    ("Noor Haddad", 2, 0, 0, 0),
]
DEMO_BULLETINS = [
    ("new", "Welcome to the Bureau, agent",
     "Start with Module 1 in the Academy, then open Case File #1. Sign the daily briefing on your desk for a little XP and a streak."),
    ("alert", "Field reminder: observe, don't touch",
     "Never like, follow, message or call anyone during an investigation. Every lead goes in your casebook, not in someone's inbox."),
    ("note", "New case file: Operation Nightjar",
     "A missing-person search-party exercise with decoy namesakes. Senior Investigators, it's yours."),
]
# Tables that hold demo rows (each has an is_demo column). Children before parents.
DEMO_TABLES = ["progress", "case_runs", "bulletins"]


def state():
    return C.get_setting("demo", "never")  # "never" | "loaded" | "removed"


def ensure_loaded():
    """Call from the app's main data callables: loads the demo once, unless an admin removed it."""
    if state() == "never":
        load()


def load():
    remove(remember=False)
    now = C.now()
    lessons = [(m, lesson) for m, _i, lesson in LC.all_lessons()]
    for n, (name, n_lessons, n_cases, avg, streak) in enumerate(DEMO_AGENTS):
        email = "%s.demo@example.com" % name.split()[0].lower()
        u = app_tables.users.get(email=email) or app_tables.users.add_row(email=email, enabled=False)
        xp = 0
        for k, (m, lesson) in enumerate(lessons[:n_lessons]):
            total = len(lesson["quiz"])
            score = total if (k + n) % 3 else total - 1
            gained = 30 + (10 if score == total else 0)
            xp += gained
            app_tables.progress.add_row(user=u, lesson_id=lesson["id"], module_id=m["id"], score=score, total=total, xp=gained,
                                        completed=now - dt.timedelta(days=40 - k), is_demo=True)
        for k, c in enumerate(CC.CASES[:n_cases]):
            score = max(30, min(100, avg + (k * 7 % 15) - 7))
            gained = int(round(c["xp"] * score / 100.0))
            xp += gained
            hints = {} if score >= 92 else {"q1": 1}
            app_tables.case_runs.add_row(user=u, case_id=c["id"], found=[d["id"] for d in c["docs"][:5]], pinned=[], hints=hints,
                                         answers={q["id"]: q["accept"][0] for q in c["questions"]}, wrong=1 if score < 85 else 0,
                                         searches=8 + k, status="solved", score=score, xp=gained, started=now - dt.timedelta(days=20 - k),
                                         updated=now - dt.timedelta(days=19 - k), finished=now - dt.timedelta(days=19 - k), is_demo=True)
        u.update(display_name=name, is_demo=True, signed_up=now - dt.timedelta(days=60 - n), xp=xp, streak=streak,
                 active_day=(now.date() - dt.timedelta(days=1)) if streak else None, board_hidden=False)
    for i, (kind, title, body) in enumerate(DEMO_BULLETINS):
        app_tables.bulletins.add_row(title=title, body=body, kind=kind, author=None, created=now - dt.timedelta(days=i * 3 + 1), is_demo=True)
    C.set_setting("demo", "loaded")
    return counts()


def remove(remember=True):
    for name in DEMO_TABLES:
        for r in getattr(app_tables, name).search(is_demo=True):
            r.delete()
    for u in app_tables.users.search(is_demo=True):
        u.delete()
    if remember:
        C.set_setting("demo", "removed")
    return counts()


def counts():
    out = {"agents": len(app_tables.users.search(is_demo=True))}
    for name in DEMO_TABLES:
        out[name.replace("_", " ")] = len(getattr(app_tables, name).search(is_demo=True))
    return out
