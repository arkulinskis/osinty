from anvil import *

from ._anvil_designer import StepRowTemplate
from ... import os_kit


class StepRow(StepRowTemplate):
    """One "In the field" step of a lesson. item = the step text (**bold**, *italic*, `code`)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.dom_nodes["text"].innerHTML = os_kit.md(self.item)
