from anvil import *

from ._anvil_designer import TieStringTemplate
from ... import state


class TieString(TieStringTemplate):
    """Name the red string between two leads. Closes with the add_link reply (or None)."""

    def __init__(self, inv_id=None, a=None, b=None, **properties):
        super().__init__(**properties)
        self.inv_id = inv_id
        self.a: dict = a or {}
        self.b: dict = b or {}
        self.dom_nodes["a"].textContent = self.a.get("value", "")
        self.dom_nodes["b"].textContent = self.b.get("value", "")
        state.set_control_attr(self.label_box, "maxlength", 40)

    @handle("", "show")
    def form_show(self, **event_args):
        self.label_box.focus()

    @handle("label_box", "pressed_enter")
    def label_box_pressed_enter(self, **event_args):
        self.tie_button_click()

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=None)

    @handle("tie_button", "click")
    def tie_button_click(self, **event_args):
        r = state.call("add_link", self.inv_id, self.a["id"], self.b["id"], self.label_box.text or "")
        if r:
            self.raise_event("x-close-alert", value=r)
