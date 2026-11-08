from anvil import *

from ._anvil_designer import ReportGroupTemplate


class ReportGroup(ReportGroupTemplate):
    """The report's findings of one kind (people, domains ...). item = {label, leads}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["label"].textContent = self.item["label"]
        self.dom_nodes["table"].setAttribute("aria-label", self.item["label"])
        self.rows_panel.items = self.item["leads"]
