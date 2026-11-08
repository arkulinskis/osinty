from anvil import *

from ._anvil_designer import BulletinRowTemplate
from ... import os_kit


class BulletinRow(BulletinRowTemplate):
    """A bulletin from HQ in the office. item = {title, body, kind (note|new|alert), created}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b, n = self.item, self.dom_nodes
        n["when"].textContent = os_kit.long_date(b["created"])
        n["title"].textContent = b["title"]
        n["body"].textContent = b["body"]
        self.card.classes[b.get("kind") or "note"] = True
