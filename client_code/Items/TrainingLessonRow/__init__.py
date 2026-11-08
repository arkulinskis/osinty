from anvil import *

from ._anvil_designer import TrainingLessonRowTemplate


class TrainingLessonRow(TrainingLessonRowTemplate):
    """Admin → Training: passes for one lesson, with a bar. item = {num, title, passes, top}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        l, n = self.item, self.dom_nodes
        n["num"].textContent = l["num"]
        n["title"].textContent = l["title"]
        n["passes"].textContent = str(l["passes"])
        n["bar"].style.width = "%dpx" % round(80.0 * l["passes"] / max(1, l["top"]))
