from anvil import *

from ._anvil_designer import ReportRowTemplate


class ReportRow(ReportRowTemplate):
    """One finding in the report. item = a lead."""

    def __init__(self, **properties):
        super().__init__(**properties)
        l, n = self.item, self.dom_nodes
        n["value"].textContent = l["value"]
        n["when"].textContent = l["when"]
        n["note"].textContent = l["note"]
        n["grade"].textContent = l["grade"] or "—"
        n["source"].textContent = l["source"] or "—"
