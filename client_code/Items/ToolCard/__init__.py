from anvil import *

from ._anvil_designer import ToolCardTemplate
from ... import os_data, state


class ToolCard(ToolCardTemplate):
    """One real tool in the library, with its tip and a star (save to my kit). item = a tool + saved + host."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t, n = self.item, self.dom_nodes
        n["cat"].textContent = os_data.CATS.get(t["cat"], "")
        n["name"].textContent = t["name"]
        n["what"].textContent = t["what"]
        n["tip"].textContent = t["tip"]
        n["open_sr"].textContent = " " + t["name"] + " (opens a new tab)"
        state.set_attr(self.open_link, "href", t["url"])
        n["cost"].className = "ui-badge" + (" good" if t["cost"] == "Free" else " warn" if t["cost"] == "Paid" else "")
        n["cost"].textContent = t["cost"]
        on = bool(t.get("saved"))
        self.star_button.text = ("Remove %s from my kit" if on else "Save %s to my kit") % t["name"]
        self.star_button.role = ["btn", "btn-ghost", "btn-icon", "ic-star", "kt-star"] + (["on"] if on else [])
        state.set_control_attr(self.star_button, "aria-pressed", "true" if on else "false")

    @handle("star_button", "click")
    def star_button_click(self, **event_args):
        self.item["host"].star(self.item["id"])
