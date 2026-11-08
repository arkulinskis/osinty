from anvil import *

from ._anvil_designer import LeadEditorTemplate
from ... import state


class LeadEditor(LeadEditorTemplate):
    """Add a lead (lead=None) or edit one. Closes with {"saved": reply} or {"deleted": True} or None."""

    def __init__(self, inv_id=None, kinds=(), lead=None, **properties):
        super().__init__(**properties)
        self.inv_id = inv_id
        self.lead: dict = lead or {}  # empty = a new lead
        self.form.fill(list(kinds), self.lead)
        self.delete_button.visible = bool(self.lead)
        if self.lead:
            self.dom_nodes["heading"].textContent = "Edit lead"
            self.save_button.text = "Save lead"
            self.save_button.role = ["btn", "btn-primary", "ic-check"]

    @handle("", "show")
    def form_show(self, **event_args):
        self.form.focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        self.save_button.enabled = False
        try:
            if self.lead:
                r = state.call("update_lead", self.lead["id"], self.form.data())
            else:
                r = state.call("add_lead", self.inv_id, self.form.data())
        finally:
            self.save_button.enabled = True
        if r:
            self.raise_event("x-close-alert", value={"saved": r})

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("Its red strings are cut too.", title="Remove this lead?", buttons=[("Cancel", False), ("Remove", True)],
                   role="app-dialog"):
            if state.call("delete_lead", self.lead["id"]) is not None:
                self.raise_event("x-close-alert", value={"deleted": True})
