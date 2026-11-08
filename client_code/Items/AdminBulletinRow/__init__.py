from anvil import *

from ._anvil_designer import AdminBulletinRowTemplate
from ... import os_kit, state


class AdminBulletinRow(AdminBulletinRowTemplate):
    """Admin → Bulletins: one bulletin with Delete (raises x-changed on the panel)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        b, n = self.item, self.dom_nodes
        n["kind"].className = "ui-badge" + {"alert": " bad", "new": " good"}.get(b.get("kind"), "")
        n["kind"].textContent = b.get("kind") or "note"
        n["title"].textContent = b["title"]
        n["when"].textContent = "%s · %s" % (os_kit.long_date(b["created"]), b.get("author") or "")
        n["body"].textContent = b["body"]
        self.demo.visible = bool(b.get("demo"))

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("Delete this bulletin?", buttons=[("Cancel", False), ("Delete", True)], role="app-dialog"):
            if state.call("delete_bulletin", self.item["id"]) is not None:
                self.parent.raise_event("x-changed")
