from anvil import *

from ._anvil_designer import ShieldTemplate
from ... import os_kit


class Shield(ShieldTemplate):
    """The rank badge (level 1-7). Size it with CSS on the page (.of-rank .shield ...)."""

    def __init__(self, **properties):
        self._level = 1
        super().__init__(**properties)
        self._draw()

    def _draw(self):
        self.dom_nodes["box"].innerHTML = os_kit.shield(self._level)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = int(value or 1)
        self._draw()
