from anvil import *

from ._anvil_designer import RankRowTemplate


class RankRow(RankRowTemplate):
    """One rung of the rank ladder in the dossier. item = {name, xp, now, got}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["name"].textContent = self.item["name"] + (" (you)" if self.item["now"] else "")
        self.dom_nodes["xp"].textContent = "%s XP" % self.item["xp"]
        self.row.classes["now"] = bool(self.item["now"])
        self.row.classes["got"] = bool(self.item["got"]) and not self.item["now"]
