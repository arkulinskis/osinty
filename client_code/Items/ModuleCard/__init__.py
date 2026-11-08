from anvil import *

from ._anvil_designer import ModuleCardTemplate


class ModuleCard(ModuleCardTemplate):
    """One module folder on the Academy page. item = a module from get_academy (num, tag, icon, title, blurb,
    lessons, done)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        m, n = self.item, self.dom_nodes
        total = len(m["lessons"])
        n["folder"].setAttribute("data-tab", "Module %s · %s" % (m["num"], m["tag"]))
        n["icon"].className = "ic ic-" + m["icon"]
        n["title"].textContent = m["title"]
        n["blurb"].textContent = m["blurb"]
        if m["done"] == total:
            n["stamp"].className, n["stamp"].textContent = "os-stamp good", "Passed"
        elif m["done"]:
            n["stamp"].className, n["stamp"].textContent = "os-stamp warn", "%d/%d" % (m["done"], total)
        else:
            n["stamp"].style.display = "none"
        self.lessons_panel.items = m["lessons"]
