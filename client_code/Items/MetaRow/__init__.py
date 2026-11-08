from anvil import *

from ._anvil_designer import MetaRowTemplate
from ... import os_kit


class MetaRow(MetaRowTemplate):
    """One metadata line of a case document (e.g. Registrant: REDACTED). item = {k, v}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["k"].textContent = self.item["k"]
        self.dom_nodes["v"].innerHTML = os_kit.md(self.item["v"])
