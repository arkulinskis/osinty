from anvil import *

from ._anvil_designer import KVRowTemplate


class KVRow(KVRowTemplate):
    """A label and a value as plain text (EXIF fields). item = {k, v}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["k"].textContent = self.item["k"]
        self.dom_nodes["v"].textContent = self.item["v"]
