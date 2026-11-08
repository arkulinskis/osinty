from anvil import *

from ._anvil_designer import DebriefTemplate
from ... import os_kit


class Debrief(DebriefTemplate):
    """HQ's debrief after a case is closed (and from "Read the debrief"). Closes with "next" to go to the cabinet."""

    def __init__(self, title="", debrief=None, result=None, **properties):
        super().__init__(**properties)
        n = self.dom_nodes
        n["title"].textContent = title
        self.score_line.visible = bool(result)
        if result:
            n["score"].textContent = "Score %s/100" % result["score"]
            n["xp"].textContent = (" · +%s XP" % result["xp_gained"]) if result.get("xp_gained") else " · replay, no new XP"
        n["body"].innerHTML = os_kit.paras(debrief or [])

    @handle("stay_button", "click")
    def stay_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="next")
