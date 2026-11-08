from anvil import *

from ._anvil_designer import BoardRowTemplate


class BoardRow(BoardRowTemplate):
    """One agent on the Bureau leaderboard. item = {place, name, rank, xp, me}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        r, n = self.item, self.dom_nodes
        n["place"].textContent = str(r["place"])
        n["name"].textContent = r["name"] + (" (you)" if r.get("me") else "")
        n["rank"].textContent = r["rank"]
        n["xp"].textContent = "%s XP" % r["xp"]
        self.row.classes["me"] = bool(r.get("me"))
        self.row.classes["p%d" % r["place"]] = r["place"] <= 3
