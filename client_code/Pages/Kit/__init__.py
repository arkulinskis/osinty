from anvil import *
import anvil.server

from ._anvil_designer import KitTemplate
from ... import os_data, os_kit, router, state


def _gadget_form(gid):
    if gid == "dorkbuilder":
        from ...Gadgets.DorkBuilder import DorkBuilder
        return DorkBuilder()
    if gid == "permutator":
        from ...Gadgets.Permutator import Permutator
        return Permutator()
    if gid == "emailperm":
        from ...Gadgets.EmailPerm import EmailPerm
        return EmailPerm()
    if gid == "exifreader":
        from ...Gadgets.ExifReader import ExifReader
        return ExifReader()
    if gid == "snowflake":
        from ...Gadgets.Decoder import Decoder
        return Decoder()
    from ...Gadgets.Grader import Grader
    return Grader()


class Kit(KitTemplate):
    """#kit: the Field Kit. Six gadgets that run in the browser (#kit/<gadget>, client_code/Gadgets) and the library of
    real OSINT tools (os_data.TOOLS) with category filters, search and "save to my kit" (stars).
    Server: get_kit, toggle_kit (Agents.py). Photos in the EXIF reader never leave the browser."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        g = os_data.tool_by_id(args[0]) if args else None
        self.gadget = None
        if g and not g.get("url"):
            self.library_part.visible = False
            router.set_title(g["name"])
            self.dom_nodes["g_name"].textContent = g["name"]
            self.dom_nodes["g_what"].textContent = g["what"]
            self.gadget = _gadget_form(g["id"])
            self.gadget_holder.add_component(self.gadget)
            return
        self.gadget_part.visible = False
        self.cat = state.store_get("kit.cat", "all")
        self.saved: list = list(anvil.server.call("get_kit")["saved"])
        state.set_control_attr(self.search_box, "aria-label", "Search tools")
        self.gadgets_panel.items = os_data.GADGETS
        self._draw_cats()
        self._draw()

    def leave(self):
        if self.gadget is not None and hasattr(self.gadget, "leave"):
            self.gadget.leave()

    def _draw_cats(self):
        cats = [("all", "All")] + list(os_data.CATS.items())
        self.cats_panel.items = [{"key": k, "text": v, "on": k == self.cat, "host": self} for k, v in cats]

    def chip(self, key):
        self.cat = key
        state.store_set("kit.cat", key)
        self._draw_cats()
        self._draw()

    def _draw(self):
        needle = (self.search_box.text or "").lower()
        mine = self.saved_box.checked
        tools = [t for t in os_data.TOOLS
                 if (self.cat == "all" or t["cat"] == self.cat) and (not mine or t["id"] in self.saved)
                 and (not needle or needle in (t["name"] + " " + t["what"] + " " + t["tip"]).lower())]
        self.tools_panel.items = [dict(t, saved=t["id"] in self.saved, host=self) for t in tools]
        self.tools_empty.visible = not tools
        self.dom_nodes["empty_text"].textContent = "Star tools to build your kit." if mine else "No tool matches that search."

    @handle("search_box", "change")
    def search_box_change(self, **event_args):
        self._draw()

    @handle("saved_box", "change")
    def saved_box_change(self, **event_args):
        self._draw()

    def star(self, tool_id):
        flag = tool_id not in self.saved
        r = state.call("toggle_kit", tool_id, flag)
        if r:
            self.saved = list(r["saved"])
            self._draw()
            os_kit.celebrate(r)
            if flag:
                state.toast("Saved to your kit.")
