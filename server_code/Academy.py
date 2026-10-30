"""Academy: the curriculum (lessons_content.py), lesson pages and quiz grading.

XP per lesson: 30 for passing (2 of 3 or better), +10 for a perfect score. A retake that does better
earns the difference, never more than once.
"""
import anvil.server
from anvil.tables import app_tables

from . import common as C
from . import Agents
from . import lessons_content as LC

PASS_XP = 30
PERFECT_XP = 10


def _xp_for(score, total):
    if score * 3 < total * 2:  # below 2/3: not passed
        return 0
    return PASS_XP + (PERFECT_XP if score == total else 0)


def _public_lesson(lesson):
    out = {k: lesson[k] for k in ("id", "title", "minutes", "summary", "body", "steps", "tools", "field_note")}
    out["quiz"] = [{"q": q["q"], "options": q["options"]} for q in lesson["quiz"]]
    return out


@anvil.server.callable(require_user=True)
def get_academy():
    me = C.require_user()
    done = {p["lesson_id"]: p for p in app_tables.progress.search(user=me)}
    modules = []
    for m in LC.MODULES:
        lessons = []
        for i, lesson in enumerate(m["lessons"]):
            p = done.get(lesson["id"])
            lessons.append({"id": lesson["id"], "num": "%d.%d" % (m["num"], i + 1), "title": lesson["title"], "minutes": lesson["minutes"],
                            "summary": lesson["summary"], "done": p is not None,
                            "score": int(p["score"]) if p else None, "total": int(p["total"]) if p else len(lesson["quiz"])})
        modules.append({"id": m["id"], "num": m["num"], "title": m["title"], "tag": m["tag"], "icon": m["icon"], "blurb": m["blurb"],
                        "lessons": lessons, "done": len([x for x in lessons if x["done"]])})
    return {"modules": modules, "done": len(done), "total": Agents.TOTAL_LESSONS, "me": Agents.rank_info(me["xp"])}


@anvil.server.callable(require_user=True)
def get_lesson(lesson_id):
    me = C.require_user()
    m, i, lesson = LC.lesson_by_id(lesson_id)
    if lesson is None:
        return C.fail("That lesson doesn't exist.")
    flat = [x[2]["id"] for x in LC.all_lessons()]
    pos = flat.index(lesson["id"])
    p = app_tables.progress.get(user=me, lesson_id=lesson["id"])
    return C.ok(lesson=_public_lesson(lesson), num="%d.%d" % (m["num"], i + 1),
                module={"id": m["id"], "num": m["num"], "title": m["title"], "tag": m["tag"]},
                prev=flat[pos - 1] if pos > 0 else None, next=flat[pos + 1] if pos + 1 < len(flat) else None,
                best={"score": int(p["score"]), "total": int(p["total"])} if p else None)


@anvil.server.callable(require_user=True)
def submit_quiz(lesson_id, answers):
    me = C.require_user()
    m, _i, lesson = LC.lesson_by_id(lesson_id)
    if lesson is None:
        return C.fail("That lesson doesn't exist.")
    quiz = lesson["quiz"]
    if not isinstance(answers, list) or len(answers) != len(quiz):
        return C.fail("Answer every question first.")
    results, score = [], 0
    for q, a in zip(quiz, answers):
        good = isinstance(a, int) and not isinstance(a, bool) and a == q["answer"]
        score += 1 if good else 0
        results.append({"correct": bool(good), "answer": q["answer"], "why": q["why"]})
    total = len(quiz)
    before = Agents.snapshot(me)
    p = app_tables.progress.get(user=me, lesson_id=lesson["id"])
    gained = 0
    earned = _xp_for(score, total)
    if earned:
        if p is None:
            app_tables.progress.add_row(user=me, lesson_id=lesson["id"], module_id=m["id"], score=score, total=total,
                                        xp=earned, completed=C.now(), is_demo=False)
            gained = earned
        elif score > (p["score"] or 0):
            gained = max(0, earned - int(p["xp"] or 0))
            p.update(score=score, xp=max(earned, int(p["xp"] or 0)), completed=C.now())
    Agents.award(me, gained)
    passed = earned > 0
    return C.ok(score=score, total=total, passed=passed, results=results, xp_gained=gained, **Agents.changes(me, before))
