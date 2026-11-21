from anvil import *

from ._anvil_designer import DebriefTemplate
from ... import os_kit


class Debrief(DebriefTemplate):
    """HQ's debrief after a case is closed (and from "Read the debrief"). Closes with "next" to go to the cabinet.
    guest_xp (a guest's training run of case #1): the XP waiting for them; the main button becomes "Join the Bureau"
    and closes with "join"."""

    def __init__(self, title="", debrief=None, result=None, guest_xp=None, **properties):
        super().__init__(**properties)
        n = self.dom_nodes
        n["title"].textContent = title
        guest = guest_xp is not None
        self.score_line.visible = bool(result)
        if result:
            n["score"].textContent = "Score %s/100" % result["score"]
            if guest:
                n["xp"].textContent = " · training run, not saved"
            else:
                n["xp"].textContent = (" · +%s XP" % result["xp_gained"]) if result.get("xp_gained") else " · replay, no new XP"
        n["body"].innerHTML = os_kit.paras(debrief or [])
        self.join_box.visible = guest
        if guest:
            n["join_text"].textContent = ("Join the Bureau to bank +%s XP. Sign up now and this run is saved to your record, "
                                          "with five more case files waiting." % guest_xp)
            self.next_button.text = "Join the Bureau"
            self.next_button.role = ["btn", "btn-primary", "ic-arrow"]

    @handle("stay_button", "click")
    def stay_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        self.raise_event("x-close-alert", value="join" if self.join_box.visible else "next")
