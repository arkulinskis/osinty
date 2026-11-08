from anvil import *

from ._anvil_designer import ReportPairTemplate


class ReportPair(ReportPairTemplate):
    """A connection (a, mid = the string's label, b) or a timeline line (a = when, b = what) in the report."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, n = self.item, self.dom_nodes
        n["a"].textContent = i["a"]
        n["b"].textContent = i["b"]
        if i.get("mid") is None:
            n["mid"].style.display = "none"
            n["row"].className = "iv-r-tr iv-r-pair two"
        else:
            n["mid"].textContent = i["mid"]
