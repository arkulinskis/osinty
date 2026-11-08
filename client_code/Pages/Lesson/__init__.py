from anvil import *
import anvil.js
import anvil.server

from ._anvil_designer import LessonTemplate
from ... import os_kit, router, state


class Lesson(LessonTemplate):
    """#academy/<lessonId>: one lesson sheet (briefing, field steps, tools, field note) and its 3-question pop quiz,
    graded on the server (the answers never reach the browser before you hand in). Server: get_lesson, submit_quiz."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.lesson_id = args[0] if args else ""
        d = anvil.server.call("get_lesson", self.lesson_id)
        ok = bool(d and d.get("ok"))
        self.missing.visible = not ok
        self.sheet.visible = self.nav.visible = ok
        if ok:
            self._draw(d)

    def _draw(self, d):
        L, n = d["lesson"], self.dom_nodes
        self.lesson = L
        router.set_title(L["title"])
        n["crumb"].textContent = "Module %s: %s" % (d["module"]["num"], d["module"]["title"])
        n["title"].textContent = L["title"]
        n["minutes"].textContent = "%s min read" % L["minutes"]
        n["mod_badge"].textContent = "Lesson %s · %s" % (d["num"], d["module"]["tag"])
        self.best_badge.visible = bool(d.get("best"))
        self.xp_badge.visible = not d.get("best")
        if d.get("best"):
            n["best"].textContent = "Passed · best %s/%s" % (d["best"]["score"], d["best"]["total"])
        n["body"].innerHTML = os_kit.paras(L["body"])
        self.steps_panel.items = L["steps"]
        self.tools_box.visible = bool(L["tools"])
        self.tools_panel.items = [t for t in L["tools"]]
        n["note"].innerHTML = os_kit.md(L["field_note"])
        self.result.visible = False
        self.quiz_panel.items = [{"i": i, "q": q["q"], "options": q["options"]} for i, q in enumerate(L["quiz"])]
        self.prev_link.visible = bool(d.get("prev"))
        self.prev_gap.visible = not d.get("prev")
        self.next_link.visible = bool(d.get("next"))
        self.cases_link.visible = not d.get("next")
        if d.get("prev"):
            state.set_attr(self.prev_link, "href", router.href("academy", d["prev"]))
        if d.get("next"):
            state.set_attr(self.next_link, "href", router.href("academy", d["next"]))

    @handle("hand_in_button", "click")
    def hand_in_button_click(self, **event_args):
        qs = self.quiz_panel.get_components()
        answers = [getattr(q, "answer")() for q in qs]
        if -1 in answers:
            state.toast("Answer every question first.", "error")
            return
        self.hand_in_button.enabled = False
        try:
            r = state.call("submit_quiz", self.lesson["id"], answers)
        finally:
            self.hand_in_button.enabled = True
        if not r:
            return
        for q, res in zip(qs, r["results"]):
            getattr(q, "show_result")(res)
        n = self.dom_nodes
        perfect = r["score"] == r["total"]
        n["stamp"].className = "os-stamp" + (" good" if r["passed"] else "")
        n["stamp"].textContent = ("Perfect" if perfect else "Passed") if r["passed"] else "Failed"
        n["score"].textContent = "%d of %d correct." % (r["score"], r["total"])
        n["score_note"].textContent = ("+%d XP added to your file." % r["xp_gained"] if r.get("xp_gained")
                                       else "No new XP: you already banked this score." if r["passed"]
                                       else "Read the briefing again and retry: there's no penalty.")
        self.result.visible = True
        self.hand_in_button.visible = False
        self.retry_button.visible = True
        anvil.js.get_dom_node(self.result).scrollIntoView({"behavior": "smooth", "block": "center"})
        os_kit.celebrate(r)

    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        router.go("academy", self.lesson_id)
