from anvil import *

from ._anvil_designer import LeadFormTemplate
from ... import os_data, os_kit, state


class LeadForm(LeadFormTemplate):
    """The lead fields (Leads tab and the add/edit lead dialog). fill(kinds, lead=None), data() -> dict for the server."""

    def __init__(self, **properties):
        super().__init__(**properties)
        for box, n in ((self.value_box, 160), (self.note_box, 1500), (self.source_box, 400), (self.when_box, 40)):
            state.set_control_attr(box, "maxlength", n)

    def fill(self, kinds, lead=None):
        lead = lead or {}
        g = lead.get("grade") or ""
        self.kind_box.items = [(os_kit.kind_label(k), k) for k in kinds]
        self.kind_box.selected_value = lead.get("kind") or kinds[0]
        self.rel_box.items = [("Source reliability: ungraded", "")] + [("%s: %s" % (k, v), k) for k, v in os_data.REL.items()]
        self.cred_box.items = [("Information credibility: ungraded", "")] + [("%s: %s" % (k, v), k) for k, v in os_data.CRED.items()]
        self.rel_box.selected_value = g[:1] if g else ""
        self.cred_box.selected_value = g[1:2] if g else ""
        state.set_control_attr(self.rel_box, "aria-label", "Source reliability")
        state.set_control_attr(self.cred_box, "aria-label", "Information credibility")
        self.value_box.text = lead.get("value") or ""
        self.note_box.text = lead.get("note") or ""
        self.source_box.text = lead.get("source") or ""
        self.when_box.text = lead.get("when") or ""

    def data(self):
        rel, cred = self.rel_box.selected_value or "", self.cred_box.selected_value or ""
        return {"kind": self.kind_box.selected_value, "value": self.value_box.text or "", "note": self.note_box.text or "",
                "source": self.source_box.text or "", "when": self.when_box.text or "",
                "grade": (rel + cred) if rel and cred else ""}

    def focus(self):
        self.value_box.focus()
