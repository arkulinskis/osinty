from anvil import *

from ._anvil_designer import ChipButtonTemplate


class ChipButton(ChipButtonTemplate):
    """A small toggle chip (kit categories, dork recipes). item = {key, text, on, host}; a click calls host.chip(key)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b = self.dom_nodes["btn"]
        b.textContent = self.item["text"]
        b.className = "chip" + (" on" if self.item.get("on") else "")
        if self.item.get("on") is not None:
            b.setAttribute("aria-pressed", "true" if self.item.get("on") else "false")

    def btn_click(self, event):
        self.item["host"].chip(self.item["key"])
