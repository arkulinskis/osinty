from anvil import *

from ._anvil_designer import InvestigationCardTemplate
from ... import os_kit, router, state


class InvestigationCard(InvestigationCardTemplate):
    """One investigation in the casebook: a manila folder that opens it. item = from list_investigations."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, n = self.item, self.dom_nodes
        state.set_attr(self.card, "href", router.href("casebook", i["id"]))
        state.set_attr(self.card, "data-tab", os_kit.long_date(i["created"]))
        label, cls = [(s[1], s[2]) for s in os_kit.STATUS if s[0] == i["status"]][0] if i["status"] in ("open", "cold", "closed") else ("Open", "")
        n["stamp"].className = ("os-stamp " + cls).strip()
        n["stamp"].textContent = label
        n["title"].textContent = i["title"]
        n["subject"].textContent = i.get("subject") or i.get("objective") or "No subject yet."
        n["leads"].textContent = state.plural(i["leads"], "lead")
        n["links"].textContent = state.plural(i["links"], "string")
        n["updated"].textContent = "updated " + state.ago(i["updated"])
