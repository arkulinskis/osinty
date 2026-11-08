from anvil import *

from ._anvil_designer import FileEditorTemplate
from ... import state


class FileEditor(FileEditorTemplate):
    """Open a new investigation, or edit one (inv = the investigation dict). Closes with the saved investigation."""

    def __init__(self, inv=None, **properties):
        super().__init__(**properties)
        self.inv = inv
        for box, n in ((self.title_box, 100), (self.subject_box, 160), (self.objective_box, 600)):
            state.set_control_attr(box, "maxlength", n)
        if inv:
            self.dom_nodes["heading"].textContent = "Edit the file"
            self.intro.visible = False
            self.save_button.text = "Save"
            self.title_box.text, self.subject_box.text, self.objective_box.text = inv["title"], inv["subject"], inv["objective"]

    @handle("", "show")
    def form_show(self, **event_args):
        self.title_box.focus()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        title = (self.title_box.text or "").strip()
        if not title:
            self.message.text, self.message.visible = "Give the file a title.", True
            return
        self.save_button.enabled = False
        try:
            if self.inv:
                r = state.call("update_investigation", self.inv["id"],
                               {"title": title, "subject": self.subject_box.text or "", "objective": self.objective_box.text or ""})
            else:
                r = state.call("create_investigation", title, self.subject_box.text or "", self.objective_box.text or "")
        finally:
            self.save_button.enabled = True
        if r:
            self.raise_event("x-close-alert", value=r["investigation"])
