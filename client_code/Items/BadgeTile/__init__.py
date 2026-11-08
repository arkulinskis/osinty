from anvil import *

from ._anvil_designer import BadgeTileTemplate


class BadgeTile(BadgeTileTemplate):
    """One commendation (Home and the dossier). item = {id, name, how, icon, earned}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b, n = self.item, self.dom_nodes
        n["icon"].className = "ic ic-" + b["icon"]
        n["ring"].className = "os-badge-ic" + (" on" if b["earned"] else "")
        n["name"].textContent = b["name"]
        n["how"].textContent = b["how"] + ("" if b["earned"] else " (not earned yet)")
        self.tile.classes["off"] = not b["earned"]
