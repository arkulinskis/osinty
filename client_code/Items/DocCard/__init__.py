from anvil import *

from ._anvil_designer import DocCardTemplate
from ... import os_kit


class DocCard(DocCardTemplate):
    """A document found in the terminal (results and the notebook). item = {doc, new, host}. `code` in the body is
    a pivot: click it to search for it."""

    def __init__(self, **properties):
        super().__init__(**properties)
        if self.item:
            self.draw(self.item)

    def draw(self, item):
        self.item = item
        doc, host, n = item["doc"], item["host"], self.dom_nodes
        bits = [os_kit.esc(host.source_label(doc["src"]))]
        if doc.get("date"):
            bits.append(os_kit.esc(doc["date"]))
        if item.get("new"):
            bits.append('<span class="new">new</span>')
        if doc.get("pinned"):
            bits.append('<span class="cd-pinmark">pinned</span>')
        n["icon"].className = "ic ic-" + os_kit.SRC_ICON.get(doc["src"], "search")
        n["src"].innerHTML = " · ".join(bits)
        n["title"].textContent = doc["title"]
        n["url"].textContent = doc.get("url") or ""
        n["url"].style.display = "" if doc.get("url") else "none"
        self.meta_panel.items = [{"k": m[0], "v": m[1]} for m in (doc.get("meta") or [])]
        self.meta_panel.visible = bool(doc.get("meta"))
        n["body"].innerHTML = os_kit.md(doc["body"])
        n["body"].onclick = self._body_click
        self.card.classes["pinned"] = bool(doc.get("pinned"))
        self.pin_button.text = "Unpin" if doc.get("pinned") else "Pin as evidence"

    def _body_click(self, event):
        code = event.target.closest("code")
        if code:
            self.item["host"].use_query(code.textContent)

    @handle("pin_button", "click")
    def pin_button_click(self, **event_args):
        self.item["host"].toggle_pin(self.item["doc"]["id"])
