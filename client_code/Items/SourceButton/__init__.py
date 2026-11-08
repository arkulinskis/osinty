from anvil import *

from ._anvil_designer import SourceButtonTemplate
from ... import os_kit


class SourceButton(SourceButtonTemplate):
    """A source tab in the case terminal (web, social, records, whois, archive, image). item = {id, label, on, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s, n = self.item, self.dom_nodes
        n["icon"].className = "ic ic-" + os_kit.SRC_ICON.get(s["id"], "search")
        n["label"].textContent = s["label"]
        n["btn"].className = "cd-src" + (" on" if s["on"] else "")
        n["btn"].setAttribute("aria-pressed", "true" if s["on"] else "false")

    def btn_click(self, event):
        self.item["host"].pick_source(self.item["id"])
