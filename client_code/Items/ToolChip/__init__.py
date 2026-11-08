from anvil import *

from ._anvil_designer import ToolChipTemplate
from ... import os_data, router, state


class ToolChip(ToolChipTemplate):
    """A tool named by a lesson: a real tool opens its website, a gadget opens #kit/<id>. item = the tool id."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = os_data.tool_by_id(self.item) or {"id": self.item, "name": self.item, "icon": "tool"}
        self.dom_nodes["name"].textContent = t["name"]
        if t.get("url"):
            state.set_attr(self.link, "href", t["url"])
            state.set_attr(self.link, "target", "_blank")
            state.set_attr(self.link, "rel", "noopener")
            self.dom_nodes["icon"].className = "ic ic-external"
        else:
            state.set_attr(self.link, "href", router.href("kit", t["id"]))
            self.link.classes["brand"] = True
            self.dom_nodes["icon"].className = "ic ic-" + (t.get("icon") or "tool")
