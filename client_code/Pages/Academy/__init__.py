from anvil import *
import anvil.server

from ._anvil_designer import AcademyTemplate


class Academy(AcademyTemplate):
    """#academy: the curriculum, 8 module folders x 3 lessons, with what you've passed. Server: get_academy."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        d = anvil.server.call("get_academy")
        pct = int(round(100.0 * d["done"] / max(1, d["total"])))
        self.dom_nodes["count"].textContent = "%d/%d" % (d["done"], d["total"])
        self.dom_nodes["bar"].setAttribute("aria-valuenow", str(pct))
        self.dom_nodes["bar_fill"].style.width = "%d%%" % pct
        self.modules_panel.items = d["modules"]
