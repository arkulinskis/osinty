from anvil import *

from ._anvil_designer import CheckRowTemplate


class CheckRow(CheckRowTemplate):
    """One checklist step. item = {id, text, phase, checked, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["phase"].textContent = self.item["phase"]
        self.box.text = self.item["text"]
        self.box.checked = self.item["checked"]

    @handle("box", "change")
    def box_change(self, **event_args):
        if not self.item["host"].set_check(self.item["id"], self.box.checked):
            self.box.checked = not self.box.checked
