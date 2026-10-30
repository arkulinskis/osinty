"""Admin page callables: overview, users (make admin, disable), demo data, training stats, bulletins.
Admins only. Feedback admin calls live in Feedback.py."""
import anvil.server
from anvil.tables import app_tables
import anvil.tables as tables

from . import common as C
from . import DemoData, Feedback
from . import cases_content as CC
from . import lessons_content as LC


@anvil.server.callable(require_user=True)
def admin_overview():
    C.require_admin()
    return {"users": len([u for u in app_tables.users.search() if not u["is_demo"]]),
            "admins": len(app_tables.users.search(is_admin=True)),
            "feedback_new": Feedback.new_count(),
            "lessons_passed": len(app_tables.progress.search()),
            "cases_solved": len([r for r in app_tables.case_runs.search() if r["xp"]]),
            "investigations": len(app_tables.investigations.search()),
            "demo": {"state": DemoData.state(), "counts": DemoData.counts()}}


def _user(u):
    return {"id": u.get_id(), "email": u["email"], "name": C.name_of(u), "is_admin": C.is_admin(u),
            "enabled": u["enabled"] is not False, "joined": C.iso(u["signed_up"]), "last_seen": C.iso(u["last_seen"])}


@anvil.server.callable(require_user=True)
def list_users(query=None):
    C.require_admin()
    query = C.text(query, 80).lower()
    rows = [u for u in app_tables.users.search(tables.order_by("signed_up", ascending=False)) if not u["is_demo"]]
    if query:
        rows = [u for u in rows if query in (u["email"] or "").lower() or query in (u["display_name"] or "").lower()]
    return {"users": [_user(u) for u in rows[:200]], "total": len(rows)}


@anvil.server.callable(require_user=True)
def set_admin(user_id, flag):
    me = C.require_admin()
    u = C.row_by_id(app_tables.users, user_id)
    if u is None:
        return C.fail("That account no longer exists.")
    if u == me and not flag:
        return C.fail("You can't remove your own admin rights.")
    u["is_admin"] = bool(flag)
    return C.ok(user=_user(u))


@anvil.server.callable(require_user=True)
def set_enabled(user_id, flag):
    me = C.require_admin()
    u = C.row_by_id(app_tables.users, user_id)
    if u is None:
        return C.fail("That account no longer exists.")
    if u == me:
        return C.fail("You can't disable your own account.")
    u["enabled"] = bool(flag)
    return C.ok(user=_user(u))


@anvil.server.callable(require_user=True)
def demo_load():
    C.require_admin()
    DemoData.load()
    return C.ok(demo={"state": DemoData.state(), "counts": DemoData.counts()})


@anvil.server.callable(require_user=True)
def demo_remove():
    C.require_admin()
    DemoData.remove()
    return C.ok(demo={"state": DemoData.state(), "counts": DemoData.counts()})


@anvil.server.callable(require_user=True)
def admin_training():
    """How the curriculum and the case files are doing: passes per lesson, solves and average scores per case."""
    C.require_admin()
    passes = {}
    for p in app_tables.progress.search():
        passes[p["lesson_id"]] = passes.get(p["lesson_id"], 0) + 1
    lessons = [{"id": lesson["id"], "num": "%d.%d" % (m["num"], i + 1), "title": lesson["title"], "module": m["title"],
                "passes": passes.get(lesson["id"], 0)} for m, i, lesson in LC.all_lessons()]
    cases = []
    for c in CC.CASES:
        runs = list(app_tables.case_runs.search(case_id=c["id"]))
        solved = [r for r in runs if r["xp"]]
        cases.append({"id": c["id"], "title": c["title"], "started": len(runs), "solved": len(solved),
                      "avg_score": int(round(sum(r["score"] or 0 for r in solved) / len(solved))) if solved else None,
                      "avg_hints": round(sum(sum((r["hints"] or {}).values()) for r in solved) / float(len(solved)), 1) if solved else None})
    return {"lessons": lessons, "cases": cases}


def _bulletin(b):
    return {"id": b.get_id(), "title": b["title"], "body": b["body"], "kind": b["kind"] or "note", "created": C.iso(b["created"]),
            "demo": bool(b["is_demo"]), "author": C.name_of(b["author"]) if b["author"] else "HQ"}


BULLETIN_KINDS = ("note", "new", "alert")


@anvil.server.callable(require_user=True)
def admin_bulletins():
    C.require_admin()
    rows = sorted(app_tables.bulletins.search(), key=lambda b: b["created"], reverse=True)
    return {"items": [_bulletin(b) for b in rows]}


@anvil.server.callable(require_user=True)
def post_bulletin(title, body, kind="note"):
    me = C.require_admin()
    title, body = C.text(title, 100), C.text(body, 1000, multiline=True)
    if len(title) < 3 or len(body) < 3:
        return C.fail("A bulletin needs a title and a message.")
    b = app_tables.bulletins.add_row(title=title, body=body, kind=kind if kind in BULLETIN_KINDS else "note", author=me,
                                     created=C.now(), is_demo=False)
    return C.ok(bulletin=_bulletin(b))


@anvil.server.callable(require_user=True)
def delete_bulletin(bulletin_id):
    C.require_admin()
    b = C.row_by_id(app_tables.bulletins, bulletin_id)
    if b is not None:
        b.delete()
    return C.ok()
