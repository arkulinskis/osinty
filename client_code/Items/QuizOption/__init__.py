from anvil import *

from ._anvil_designer import QuizOptionTemplate


class QuizOption(QuizOptionTemplate):
    """One answer option of a quiz question. item = {group, i, text}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.radio.text = self.item["text"]
        self.radio.group_name = self.item["group"]
        self.radio.value = str(self.item["i"])

    def selected(self):
        return bool(self.radio.selected)

    @handle("radio", "clicked")
    def radio_clicked(self, **event_args):
        if self.parent is not None:
            for c in self.parent.get_components():
                getattr(c, "box").classes["on"] = getattr(c, "selected")()

    def mark(self, right=False, wrong=False):
        self.box.classes["right"] = right
        self.box.classes["wrong"] = wrong
        self.radio.enabled = False
