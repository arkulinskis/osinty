"""Server tests against the strict mock of Anvil (tools/testing/mock).

    python tools/testing/test_server.py          -> prints ALL OK, or the first failure   (no -I: reads anvil.yaml)

call(name, ...) runs a server function the way the browser does: by name, with require_user enforced,
and the reply must be JSON (a datetime or a row in a reply fails here, like it would break the page).
Add tests for every new server function: the happy path, bad input, and someone who isn't allowed.
"""
import datetime as dt
import importlib
import json
import os
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
_tmp = pathlib.Path(tempfile.mkdtemp())
shutil.copytree(PROJECT / "server_code", _tmp / "app")
(_tmp / "app" / "__init__.py").write_text("")
os.environ["ANVIL_APP_YAML"] = str(PROJECT / "anvil.yaml")  # the mock's tables follow the app's own schema
sys.path[:0] = [str(HERE / "mock"), str(_tmp)]
import anvil.server  # noqa: E402
import anvil.users  # noqa: E402
from anvil.tables import app_tables as T  # noqa: E402
M = {p.stem: importlib.import_module("app." + p.stem) for p in sorted((PROJECT / "server_code").glob("*.py"))}
now = dt.datetime.now(dt.timezone.utc)


def call(name, *args):
    r = anvil.server.call(name, *args)
    json.dumps(r)  # strict: must be JSON-able
    return r


def as_user(row):
    anvil.users.CURRENT[0] = row
    anvil.server.session.use(row.get_id() if row is not None else None)


def denied(name, *args):
    try:
        call(name, *args)
    except anvil.server.PermissionDenied:
        return True
    return False


def ok(r, msg=""):
    assert isinstance(r, dict) and r.get("ok"), (msg, r)
    return r


def bad(r, msg=""):
    assert isinstance(r, dict) and r.get("ok") is False and r.get("error"), (msg, r)
    return r


def person(email, name=None, **kw):
    return T.users.add_row(email=email, enabled=True, signed_up=now, display_name=name, **kw)


# ---------------------------------------------------------------------------------- accounts
admin = person("arkulinskis@gmail.com", "The Admin")
ana = person("ana@example.com", "Ana")
bob = person("bob@example.com")

as_user(None)
assert call("get_me") is None
assert denied("update_profile", "X")
as_user(admin)
assert call("get_me")["is_admin"] is True, "ADMIN_EMAILS become admins on first sign-in"
as_user(ana)
me = call("get_me")
assert me["name"] == "Ana" and me["is_admin"] is False
assert ana["last_seen"] is not None
as_user(bob)
assert call("get_me")["name"] == "Bob", "a name comes from the email when none is set"
bad(call("update_profile", " x "))
assert ok(call("update_profile", "  Bob   Stone "))["me"]["name"] == "Bob Stone"

# ---------------------------------------------------------------------------------- feedback
as_user(None)
bad(call("submit_feedback", "bug", "hi"))
ok(call("submit_feedback", "bug", "The button is broken", "guest@example.com", {"page": "#home", "evil": "x" * 9999}))
fb = T.feedback.search()[0]
assert fb["name"] == "Guest" and fb["email"] == "guest@example.com" and "evil" not in fb["context"] and fb["status"] == "new"
for i in range(4):
    ok(call("submit_feedback", "idea", "Idea number %d" % i))
bad(call("submit_feedback", "idea", "One too many this hour"), "rate limit")
as_user(ana)
ok(call("submit_feedback", "nonsense-kind", "Signed-in feedback"))
assert T.feedback.get(message="Signed-in feedback")["kind"] == "other"
assert denied("list_feedback")
as_user(admin)
lst = call("list_feedback")
assert lst["counts"]["new"] == 6 and len(lst["items"]) == 6
fid = lst["items"][0]["id"]
ok(call("set_feedback_status", fid, "done", "Fixed it"))
assert call("list_feedback", "done")["items"][0]["note"] == "Fixed it"
bad(call("set_feedback_status", fid, "weird"))
bad(call("set_feedback_status", "nope", "done"))
ok(call("delete_feedback", fid))
assert len(call("list_feedback")["items"]) == 5

# ---------------------------------------------------------------------------------- admin
as_user(ana)
for fn, args in [("admin_overview", ()), ("list_users", ()), ("set_admin", (bob.get_id(), True)), ("demo_load", ()), ("demo_remove", ())]:
    assert denied(fn, *args), fn
as_user(admin)
ov = call("admin_overview")
assert ov["users"] == 3 and ov["admins"] == 1 and ov["feedback_new"] == 5 and ov["demo"]["state"] == "never"
assert len(call("list_users")["users"]) == 3 and len(call("list_users", "bob")["users"]) == 1
ok(call("set_admin", bob.get_id(), True))
assert bob["is_admin"] is True
bad(call("set_admin", admin.get_id(), False), "can't remove your own admin")
ok(call("set_enabled", bob.get_id(), False))
assert bob["enabled"] is False
bad(call("set_enabled", admin.get_id(), False))
ok(call("set_enabled", bob.get_id(), True))
ok(call("set_admin", bob.get_id(), False))
assert bob["is_admin"] is False

# ---------------------------------------------------------------------------------- demo data
as_user(ana)
office = call("get_office")
assert M["DemoData"].state() == "loaded", "demo loads on first visit"
assert office["board"]["rows"][0]["name"] == "Maya Chen" and office["board"]["rows"][0]["demo"]
assert len(office["bulletins"]) == 3 and office["me"]["rank"] == "Rookie" and office["next_lesson"]["id"] == "m1l1"
assert office["next_case"]["id"] == "c1" and office["lessons_total"] == 24
assert len(office["badges"]) == len(M["Agents"].BADGES) and not any(b["earned"] for b in office["badges"])
as_user(admin)
ok(call("demo_remove"))
assert M["DemoData"].state() == "removed" and not T.users.search(is_demo=True) and not T.progress.search()
as_user(ana)
call("get_office")
assert M["DemoData"].state() == "removed", "removed demo data doesn't come back by itself"
as_user(admin)
ok(call("demo_load"))
ok(call("demo_load"))
assert len(T.users.search(is_demo=True)) == len(M["DemoData"].DEMO_AGENTS), "reloading replaces the demo instead of doubling it"
assert len(T.bulletins.search()) == 3

# ---------------------------------------------------------------------------------- ranks
A = M["Agents"]
assert A.rank_info(0)["rank"] == "Rookie" and A.rank_info(119)["next"] == "Gumshoe"
assert A.rank_info(120)["rank"] == "Gumshoe" and A.rank_info(5000)["next"] is None and A.rank_info(5000)["pct"] == 100
LCm, CCm = M["lessons_content"], M["cases_content"]
max_xp = sum(40 for _ in LCm.all_lessons()) + sum(c["xp"] for c in CCm.CASES)
assert max_xp >= A.RANKS[-1][0], "the top rank must be reachable (%d XP available)" % max_xp

# ---------------------------------------------------------------------------------- daily briefing + streak
as_user(None)
assert denied("claim_briefing") and denied("get_office") and denied("get_dossier")
as_user(ana)
r = ok(call("claim_briefing"))
assert r["xp_gained"] == 5 and ana["xp"] == 5 and r["streak"] == 1
bad(call("claim_briefing"), "only once a day")
assert call("get_office")["briefing_done"] is True
ana["active_day"] = A.today() - dt.timedelta(days=1)
ana["streak"] = 2
A.touch(ana)
assert ana["streak"] == 3, "a day after yesterday continues the streak"
ana["active_day"] = A.today() - dt.timedelta(days=3)
A.touch(ana)
assert ana["streak"] == 1, "a gap resets the streak"

# ---------------------------------------------------------------------------------- academy
as_user(None)
assert denied("get_academy") and denied("get_lesson", "m1l1") and denied("submit_quiz", "m1l1", [0, 0, 0])
as_user(ana)
ac = call("get_academy")
assert len(ac["modules"]) == 8 and ac["total"] == 24 and ac["done"] == 0
le = ok(call("get_lesson", "m1l1"))
assert le["next"] == "m1l2" and le["prev"] is None and le["best"] is None
assert all("answer" not in q and "why" not in q for q in le["lesson"]["quiz"]), "answers never reach the browser before grading"
bad(call("get_lesson", "nope"))
bad(call("submit_quiz", "m1l1", [1]), "every question needs an answer")
bad(call("submit_quiz", "nope", [0, 0, 0]))
L1 = LCm.lesson_by_id("m1l1")[2]
right = [q["answer"] for q in L1["quiz"]]
wrong = [(a + 1) % len(q["options"]) for a, q in zip(right, L1["quiz"])]
r = ok(call("submit_quiz", "m1l1", wrong))
assert r["passed"] is False and r["xp_gained"] == 0 and r["score"] == 0 and not T.progress.search(user=ana)
two = right[:2] + wrong[2:]
r = ok(call("submit_quiz", "m1l1", two))
assert r["passed"] and r["xp_gained"] == 30 and r["score"] == 2
assert [b["id"] for b in r["badges"]] == ["first_lesson"], r["badges"]
r = ok(call("submit_quiz", "m1l1", right))
assert r["xp_gained"] == 10, "a better retake earns the difference"
r = ok(call("submit_quiz", "m1l1", right))
assert r["xp_gained"] == 0, "no XP twice"
ok(call("submit_quiz", "m1l1", [True, "x", None]))  # junk answers are just wrong
assert ana["xp"] == 45 and call("get_academy")["done"] == 1
for m, i, lesson in LCm.all_lessons():
    for q in lesson["quiz"]:
        assert 0 <= q["answer"] < len(q["options"]) and q["why"], lesson["id"]
    assert len(lesson["quiz"]) == 3 and lesson["body"] and lesson["steps"], lesson["id"]

# every tool id a lesson mentions exists in the Field Kit library (client_code/os_data.py: TOOLS + GADGETS)
import re  # noqa: E402
kit_src = (PROJECT / "client_code" / "os_data.py").read_text(encoding="utf-8")
kit_ids = set(re.findall(r'"id": "([a-z0-9]+)"', kit_src))
missing = {t for _m, _i, lesson in LCm.all_lessons() for t in lesson["tools"] if t not in kit_ids}
assert not missing, "lesson tools missing from os_data.TOOLS / GADGETS: %s" % sorted(missing)

# ---------------------------------------------------------------------------------- case files
CS = M["Cases"]
for c in CCm.CASES:
    ids = [d["id"] for d in c["docs"]]
    assert len(ids) == len(set(ids)), c["id"]
    assert all(d["src"] in c["sources"] for d in c["docs"]), c["id"]
    assert all(len(q["hints"]) == 2 and q["accept"] for q in c["questions"]), c["id"]
    for q in c["questions"]:
        for acc in q["accept"]:
            assert CS.check_answer(q, acc), (c["id"], acc)
as_user(None)
assert denied("list_cases") and denied("get_case", "c1") and denied("case_search", "c1", "web", "cat")
as_user(ana)
lc = call("list_cases")
assert len(lc["cases"]) == 6 and lc["cases"][0]["status"] == "new" and lc["cases"][0]["solvers"] >= 1
g = ok(call("get_case", "c1"))
assert g["state"]["status"] == "new" and g["state"]["found"] == [] and '"accept"' not in json.dumps(g)
bad(call("get_case", "zzz"))
bad(call("case_search", "c1", "whois", "maple"), "source not in this case")
bad(call("case_search", "c1", "web", " "))
s1 = ok(call("case_search", "c1", "web", "found orange cat maple street"))
assert s1["results"][0]["id"] == "c1w1" and "c1w1" in s1["new"]
assert ok(call("case_search", "c1", "social", "joe"))["results"] == [], "a pivot doc needs its exact key"
s2 = ok(call("case_search", "c1", "social", "@lantern_joe"))
assert [d["id"] for d in s2["results"]] == ["c1s1"]
assert ok(call("case_search", "c1", "image", "IMG_4471.jpg"))["results"][0]["meta"]
assert len(ok(call("get_case", "c1"))["state"]["found"]) >= 3
ok(call("case_pin", "c1", "c1w1", True))
bad(call("case_pin", "c1", "c1i9", True), "can't pin what you haven't found")
assert ok(call("get_case", "c1"))["state"]["pinned"] == ["c1w1"]
ok(call("case_pin", "c1", "c1w1", False))
h = ok(call("case_hint", "c1", "q2"))
assert h["hint"] and h["hints_left"] == 1 and h["score"] == 92
ok(call("case_hint", "c1", "q2"))
bad(call("case_hint", "c1", "q2"), "only two hints")
bad(call("case_hint", "c1", "q9"))
r = ok(call("case_answer", "c1", "q1", "joe"))
assert r["correct"] is False and r["score"] == 80
bad(call("case_answer", "c1", "q1", "   "))
r = ok(call("case_answer", "c1", "q1", "@Lantern_Joe"))
assert r["correct"] and not r["solved"]
ok(call("case_answer", "c1", "q2", "Birch Lane"))
bad(call("case_hint", "c1", "q2"), "no hints for a cracked question")
before_xp = ana["xp"]
r = ok(call("case_answer", "c1", "q3", "his name is Joe"))
assert r["solved"] and r["xp_gained"] == 80 and ana["xp"] == before_xp + 80 and r["state"]["debrief"]
assert "first_case" in [b["id"] for b in r["badges"]]
run = T.case_runs.get(user=ana, case_id="c1")
assert run["status"] == "solved" and run["score"] == 80
ok(call("case_reset", "c1"))
assert run["status"] == "replay" and run["found"] == [] and run["xp"] == 80
for q in CCm.CASES[0]["questions"]:
    r = ok(call("case_answer", "c1", q["id"], q["accept"][0]))
assert r["solved"] and r["xp_gained"] == 0 and run["score"] == 100 and run["status"] == "solved", "replays keep the best score, no new XP"
as_user(bob)
assert ok(call("get_case", "c1"))["state"]["status"] == "new", "runs are per person"
assert ok(call("case_answer", "c2", "q1", "Marco Vidal"))["correct"]
bad(call("case_answer", "c2", "q9", "x"))
bad(call("case_reset", "zzz"))

# ---------------------------------------------------------------------------------- casebook
as_user(None)
assert denied("list_investigations") and denied("create_investigation", "X")
as_user(ana)
assert call("list_investigations")["items"] == []
bad(call("create_investigation", " "))
inv = ok(call("create_investigation", "Who runs the shop?", "lumenhaus", "Find the owner"))["investigation"]
iid = inv["id"]
bad(call("add_lead", iid, {"kind": "person", "value": ""}))
l1 = ok(call("add_lead", iid, {"kind": "domain", "value": "shop.example", "grade": "b2", "source": "WHOIS"}))["lead"]
assert l1["grade"] == "B2" and l1["kind"] == "domain"
l2 = ok(call("add_lead", iid, {"kind": "hacker", "value": "Someone", "grade": "Z9"}))["lead"]
assert l2["kind"] == "note" and l2["grade"] == "", "unknown kinds and grades are cleaned"
assert (l1["x"], l1["y"]) != (l2["x"], l2["y"]), "new pins don't stack"
ok(call("update_lead", l2["id"], {"kind": "person", "value": "V. K.", "note": "director"}))
ok(call("move_lead", l2["id"], 99999, -5))
lead2 = T.leads.get_by_id(l2["id"])
assert lead2["x"] == 1400 - 180 and lead2["y"] == 0, "positions stay on the board"
bad(call("move_lead", l2["id"], "a", "b"))
link = ok(call("add_link", iid, l1["id"], l2["id"], "registrant"))["link"]
bad(call("add_link", iid, l2["id"], l1["id"]), "no duplicate strings")
bad(call("add_link", iid, l1["id"], l1["id"]))
ok(call("set_checklist", iid, "purpose", True))
bad(call("set_checklist", iid, "nope", True))
ok(call("update_investigation", iid, {"status": "closed", "title": "Renamed"}))
bad(call("update_investigation", iid, {"status": "weird"}))
got = ok(call("get_investigation", iid))
assert got["investigation"]["title"] == "Renamed" and got["investigation"]["checklist"] == {"purpose": True}
assert len(got["leads"]) == 2 and got["links"][0]["label"] == "registrant"
sample = ok(call("create_sample_investigation"))["investigation"]
sg = ok(call("get_investigation", sample["id"]))
assert len(sg["leads"]) == 6 and len(sg["links"]) == 5
earned = A.earned_badges(ana)
assert "casebook" in earned and "strings" in earned
as_user(bob)
bad(call("get_investigation", iid), "someone else's investigation is invisible")
bad(call("add_lead", iid, {"kind": "note", "value": "x"}))
bad(call("update_lead", l1["id"], {"value": "x"}))
bad(call("move_lead", l1["id"], 1, 1))
bad(call("delete_link", link["id"]))
bad(call("update_investigation", iid, {"title": "Mine now"}))
bad(call("set_checklist", iid, "purpose", False))
ok(call("delete_investigation", iid))
assert T.investigations.get_by_id(iid) is not None, "deleting someone else's investigation does nothing"
ok(call("delete_lead", l1["id"]))
assert T.leads.get_by_id(l1["id"]) is not None, "deleting someone else's lead does nothing"
bob_inv = ok(call("create_investigation", "Bob's file"))["investigation"]
bob_lead = ok(call("add_lead", bob_inv["id"], {"kind": "note", "value": "x"}))["lead"]
as_user(ana)
bad(call("add_link", iid, l1["id"], bob_lead["id"]), "can't string to someone else's lead")
ok(call("delete_lead", l2["id"]))
assert not T.links.search(investigation=T.investigations.get_by_id(iid)), "deleting a lead removes its strings"
ok(call("delete_investigation", iid))
assert T.investigations.get_by_id(iid) is None and not [x for x in T.leads.search() if x["investigation"] is None]

# ---------------------------------------------------------------------------------- dossier, leaderboard, kit
as_user(ana)
d = call("get_dossier")
assert d["cases_solved"] == 1 and d["lessons_done"] == 1 and len(d["ranks"]) == 7
assert d["board"]["my_place"] is not None
ok(call("set_board_hidden", True))
assert call("get_dossier")["board"]["my_place"] is None and all(not r["me"] for r in call("get_office")["board"]["rows"])
ok(call("set_board_hidden", False))
assert call("get_kit")["saved"] == []
bad(call("toggle_kit", "../evil", True))
bad(call("toggle_kit", 5, True))
for t in ["wayback", "tineye", "crtsh", "suncalc"]:
    ok(call("toggle_kit", t, True))
r = ok(call("toggle_kit", "yandex", True))
assert len(r["saved"]) == 5 and "kit5" in [b["id"] for b in r["badges"]]
assert ok(call("toggle_kit", "yandex", False))["saved"] == ["wayback", "tineye", "crtsh", "suncalc"]
as_user(None)
assert denied("get_kit") and denied("toggle_kit", "wayback", True) and denied("set_board_hidden", True)

# ---------------------------------------------------------------------------------- admin: training stats + bulletins
as_user(ana)
for fn, args in [("admin_training", ()), ("admin_bulletins", ()), ("post_bulletin", ("T", "B")), ("delete_bulletin", ("x",))]:
    assert denied(fn, *args), fn
as_user(admin)
tr = call("admin_training")
assert len(tr["lessons"]) == 24 and tr["cases"][0]["solved"] >= 2
bad(call("post_bulletin", "", "body"))
b = ok(call("post_bulletin", "New lesson!", "Module 9 is coming.", "weird"))["bulletin"]
assert b["kind"] == "note" and b["author"] == "The Admin"
assert call("admin_bulletins")["items"][0]["id"] == b["id"]
as_user(ana)
assert call("get_office")["bulletins"][0]["title"] == "New lesson!"
as_user(admin)
ok(call("delete_bulletin", b["id"]))
ok(call("delete_bulletin", "nope"))
ov = call("admin_overview")
assert ov["lessons_passed"] >= 1 and ov["cases_solved"] >= 1

# ---------------------------------------------------------------------------------- Privacy & Terms
if "legal_server" in M:
    as_user(ana)
    st = call("legal_state")
    assert st["signedIn"] and st["accepted_version"] is None
    ok(call("legal_accept", st["version"], "signup"))
    assert ana["legal_source"] == "signup" and call("legal_state")["accepted_version"] == st["version"]

# ---------------------------------------------------------------------------------- every callable is covered by a permission check
# A callable that changes data without require_user / a C.require_* check is a security hole. List the public ones here.
PUBLIC = {"get_me", "submit_feedback", "legal_state", "legal_accept"}
for name, (f, need) in sorted(anvil.server.CALLABLES.items()):
    if name in PUBLIC:
        continue
    assert need, "%s is callable by anyone: add require_user=True (or list it in PUBLIC in test_server.py)" % name

print("ALL OK (%d server functions)" % len(anvil.server.CALLABLES))
