from anvil import *

from ._anvil_designer import NoteDocTemplate
from ... import os_kit


class NoteDoc(NoteDocTemplate):
    """A document in the case notebook: a one-line summary that opens to the whole document. item = {doc, host}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        doc = self.item["doc"]
        self.dom_nodes["icon"].className = "ic ic-" + ("pushpin" if doc.get("pinned") else os_kit.SRC_ICON.get(doc["src"], "search"))
        self.dom_nodes["title"].textContent = doc["title"]
        self.doc_card.draw({"doc": doc, "host": self.item["host"]})
