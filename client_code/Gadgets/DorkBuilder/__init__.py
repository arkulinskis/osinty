from anvil import *
from anvil.js import window

from ._anvil_designer import DorkBuilderTemplate
from ... import gadget_kit, os_kit, state

FIELDS = ["exact", "all", "any", "not", "site", "type", "intitle", "inurl", "after", "before"]
RECIPES = [
    ("Exact name, one site", {"exact": "Martin Kessler", "site": "linkedin.com"}),
    ("Company documents", {"exact": "VK Media Solutions", "type": "pdf", "all": "annual report"}),
    ("Mentions not on their own site", {"exact": "Lumenhaus", "not": "site:lumenhaus-deals.example", "all": "scam OR review"}),
    ("Username anywhere", {"exact": "mkess84"}),
    ("News in a date range", {"exact": "Nightjar Collective", "any": "residency exhibition", "after": "2026-01-01", "before": "2026-12-31"}),
]


class DorkBuilder(DorkBuilderTemplate):
    """Build precise search-engine queries with operators; ready-made recipes; copy or open in Google/Bing/DuckDuckGo."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.type_box.items = [("any", "")] + [(t, t) for t in ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "csv", "txt"]]
        for name in ("after", "before"):
            state.set_control_attr(self._box(name), "type", "date")
        for name in FIELDS:
            self._box(name).add_event_handler("change", self._changed)
        self.recipes_panel.items = [{"key": i, "text": r[0], "host": self} for i, r in enumerate(RECIPES)]
        self._build()

    def _box(self, name):
        return getattr(self, name + "_box")

    def _values(self):
        return {name: (self._box(name).selected_value if name == "type" else self._box(name).text) or "" for name in FIELDS}

    def _changed(self, **event_args):
        self._build()

    def chip(self, key):
        vals = RECIPES[key][1]
        for name in FIELDS:
            box = self._box(name)
            if name == "type":
                box.selected_value = vals.get(name, "")
            else:
                box.text = vals.get(name, "")
        self._build()

    def _build(self):
        q = gadget_kit.dork(self._values())
        self.dom_nodes["q"].textContent = q or "Fill in a field to start."
        enc = window.encodeURIComponent(q)
        state.set_attr(self.g_link, "href", "https://www.google.com/search?q=" + enc)
        state.set_attr(self.b_link, "href", "https://www.bing.com/search?q=" + enc)
        state.set_attr(self.d_link, "href", "https://duckduckgo.com/?q=" + enc)
        return q

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        os_kit.copy(self._build())
