from anvil import *

from ._anvil_designer import LessonRowTemplate
from ... import router, state


class LessonRow(LessonRowTemplate):
    """A lesson link inside a module folder. item = {id, num, title, minutes, done, score, total}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        l, n = self.item, self.dom_nodes
        state.set_attr(self.link, "href", router.href("academy", l["id"]))
        self.link.classes["done"] = bool(l["done"])
        if l["done"]:
            n["num"].innerHTML = '<i class="ic ic-check" aria-hidden="true"></i><span class="ui-sr">Passed</span>'
            n["meta"].textContent = "%s/%s" % (l["score"], l["total"])
        else:
            n["num"].textContent = l["num"]
            n["meta"].textContent = "%s min" % l["minutes"]
        n["title"].textContent = l["title"]
