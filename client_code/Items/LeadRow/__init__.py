from anvil import *

from ._anvil_designer import LeadRowTemplate
from ... import os_kit, state


class LeadRow(LeadRowTemplate):
    """One lead in the Leads tab. item = a lead + host (the Investigation page)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        l, n = self.item, self.dom_nodes
        n["icon"].className = "ic ic-" + os_kit.KIND_ICON.get(l["kind"], "edit")
        n["value"].textContent = l["value"]
        n["grade"].className = "ui-badge" + (" brand" if l["grade"] else "")
        n["grade"].textContent = l["grade"] or "ungraded"
        n["note"].textContent = l["note"]
        n["note"].style.display = "" if l["note"] else "none"
        meta = os_kit.kind_label(l["kind"]) + ((" · " + l["when"]) if l["when"] else "") + ((" · source: " + l["source"]) if l["source"] else "")
        n["meta"].textContent = meta
        state.set_control_attr(self.edit_button, "aria-label", "Edit " + l["value"])

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        self.item["host"].edit_lead(self.item["id"])
