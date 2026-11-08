from anvil import *

from ._anvil_designer import OutBlockTemplate


class OutBlock(OutBlockTemplate):
    """One labelled result in a gadget's dark output box. item = {label, big: [main, sub]?, text?}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        i, n = self.item, self.dom_nodes
        big = i.get("big") or []
        n["label"].textContent = i["label"]
        n["big"].textContent = big[0] if big else ""
        n["sub"].textContent = big[1] if len(big) > 1 else ""
        n["text"].textContent = i.get("text") or ""
        for k in ("big", "sub", "text"):
            n[k].style.display = "" if n[k].textContent else "none"
