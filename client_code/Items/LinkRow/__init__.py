from anvil import *

from ._anvil_designer import LinkRowTemplate


class LinkRow(LinkRowTemplate):
    """One red string in the Leads tab. item = {id, a, b, label, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["a"].textContent = self.item["a"]
        self.dom_nodes["label"].textContent = "— %s —" % (self.item["label"] or "linked")
        self.dom_nodes["b"].textContent = self.item["b"]

    @handle("cut_button", "click")
    def cut_button_click(self, **event_args):
        self.item["host"].cut_link(self.item["id"])
