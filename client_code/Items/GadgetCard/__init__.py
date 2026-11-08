from anvil import *

from ._anvil_designer import GadgetCardTemplate
from ... import router, state


class GadgetCard(GadgetCardTemplate):
    """A gadget on the kit page (opens #kit/<id>). item = {id, name, icon, what}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        g = self.item
        state.set_attr(self.link, "href", router.href("kit", g["id"]))
        self.dom_nodes["icon"].className = "ic ic-" + g["icon"]
        self.dom_nodes["name"].textContent = g["name"]
        self.dom_nodes["what"].textContent = g["what"]
