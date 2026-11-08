from anvil import *
from anvil.js import window

from ._anvil_designer import CaseQuestionTemplate
from ... import state


class CaseQuestion(CaseQuestionTemplate):
    """One case question: a short free-text answer, hints that cost points. item = a question from the case state
    (id, text, answer, hints, hints_left) + n + host (the CaseDesk page)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        q, n = self.item, self.dom_nodes
        n["num"].textContent = "Q%d" % q["n"]
        n["text"].textContent = q["text"]
        solved = bool(q.get("answer"))
        self.solved.visible = solved
        self.open_part.visible = not solved
        n["answer"].textContent = q.get("answer") or ""
        self.hint_button.visible = bool(q["hints_left"])
        self.hint_button.text = "Hint (%d left)" % q["hints_left"]
        self.no_hints.visible = not q["hints_left"]
        self.hints_panel.items = [{"n": i + 1, "text": h} for i, h in enumerate(q["hints"])]
        for k, v in (("aria-label", "Answer to question %d" % q["n"]), ("autocomplete", "off"), ("spellcheck", "false"), ("maxlength", "80")):
            state.set_control_attr(self.answer_box, k, v)

    @handle("answer_box", "pressed_enter")
    def answer_box_pressed_enter(self, **event_args):
        self.submit_button_click()

    @handle("submit_button", "click")
    def submit_button_click(self, **event_args):
        value = (self.answer_box.text or "").strip()
        if not value:
            return
        self.submit_button.enabled = False
        try:
            self.item["host"].answer(self.item["id"], value, self)
        finally:
            self.submit_button.enabled = True

    @handle("hint_button", "click")
    def hint_button_click(self, **event_args):
        self.item["host"].take_hint(self.item["id"])

    def shake(self):
        self.form.classes["shake"] = True
        window.setTimeout(self._unshake, 450)

    def _unshake(self):
        self.form.classes["shake"] = False
