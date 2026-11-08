from anvil import *

from ._anvil_designer import EmailPermTemplate
from ... import gadget_kit, os_kit


class EmailPerm(EmailPermTemplate):
    """List the likely work-email formats for a person and a domain."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.found: list = []
        for box in (self.first_box, self.last_box, self.domain_box):
            box.add_event_handler("change", self._run)
        self._run()

    def _run(self, **event_args):
        self.found = gadget_kit.emails(self.first_box.text, self.last_box.text, self.domain_box.text)
        self.dom_nodes["list"].textContent = "\n".join(self.found) or "Type a first name and a domain."

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        os_kit.copy("\n".join(self.found))
