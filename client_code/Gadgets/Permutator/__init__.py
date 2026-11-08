from anvil import *

from ._anvil_designer import PermutatorTemplate
from ... import gadget_kit, os_kit


class Permutator(PermutatorTemplate):
    """Turn a name (and a number) into the usernames people actually pick."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.names: list = []
        for box in (self.first_box, self.last_box, self.extra_box):
            box.add_event_handler("change", self._run)
        self._run()

    def _run(self, **event_args):
        self.names = gadget_kit.usernames(self.first_box.text, self.last_box.text, self.extra_box.text)
        self.dom_nodes["count"].textContent = str(len(self.names))
        self.dom_nodes["list"].textContent = "\n".join(self.names) or "Type a name."

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        os_kit.copy("\n".join(self.names))
