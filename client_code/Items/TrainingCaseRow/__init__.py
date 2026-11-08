from anvil import *

from ._anvil_designer import TrainingCaseRowTemplate


class TrainingCaseRow(TrainingCaseRowTemplate):
    """Admin → Training: one case file's numbers. item = {title, started, solved, avg_score, avg_hints}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, n = self.item, self.dom_nodes
        n["title"].textContent = c["title"]
        n["started"].textContent = str(c["started"])
        n["solved"].textContent = str(c["solved"])
        n["score"].textContent = "–" if c.get("avg_score") is None else str(c["avg_score"])
        n["hints"].textContent = "–" if c.get("avg_hints") is None else str(c["avg_hints"])
