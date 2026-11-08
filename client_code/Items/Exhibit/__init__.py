from anvil import *

from ._anvil_designer import ExhibitTemplate


class Exhibit(ExhibitTemplate):
    """One exhibit of a case's briefing; clicking the value copies it into the terminal. item = {label, value, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["label"].textContent = self.item["label"]
        self.dom_nodes["value"].textContent = self.item["value"]
        self.dom_nodes["value"].setAttribute("aria-label", "Search for %s" % self.item["value"])

    def value_click(self, event):
        self.item["host"].use_query(self.item["value"])
