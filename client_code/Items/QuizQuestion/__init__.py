from anvil import *

from ._anvil_designer import QuizQuestionTemplate


class QuizQuestion(QuizQuestionTemplate):
    """One quiz question with its options (radio buttons in group q<i>). item = {i, q, options}.
    answer() = the chosen option's index (-1 = none); show_result() marks right and wrong after grading."""

    def __init__(self, **properties):
        super().__init__(**properties)
        q = self.item
        self.dom_nodes["num"].textContent = "Q%d" % (q["i"] + 1)
        self.dom_nodes["text"].textContent = q["q"]
        self.options_panel.items = [{"group": "q%d" % q["i"], "i": i, "text": o} for i, o in enumerate(q["options"])]
        self.why.visible = False

    def answer(self):
        for c in self.options_panel.get_components():
            if getattr(c, "selected")():
                return getattr(c, "item")["i"]
        return -1

    def show_result(self, res):
        chosen = self.answer()
        for c in self.options_panel.get_components():
            getattr(c, "mark")(right=getattr(c, "item")["i"] == res["answer"],
                               wrong=getattr(c, "item")["i"] == chosen and not res["correct"])
        self.why.visible = True
        self.why.classes["no"] = not res["correct"]
        self.dom_nodes["why_text"].textContent = ("Correct. " if res["correct"] else "Not quite. ") + res["why"]
