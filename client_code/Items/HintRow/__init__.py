from anvil import *

from ._anvil_designer import HintRowTemplate


class HintRow(HintRowTemplate):
    """A hint you've paid for. item = {n, text}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["n"].textContent = "HINT %d" % self.item["n"]
        self.dom_nodes["text"].textContent = self.item["text"]
