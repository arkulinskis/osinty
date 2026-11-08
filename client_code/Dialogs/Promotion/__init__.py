from anvil import *

from ._anvil_designer import PromotionTemplate


class Promotion(PromotionTemplate):
    """The promotion card shown by os_kit.celebrate when a reply says rank_up."""

    def __init__(self, reply=None, **properties):
        super().__init__(**properties)
        reply = reply or {}
        me = reply.get("me") or {}
        self.shield.level = me.get("level") or 1
        self.dom_nodes["title"].textContent = "You're now a %s" % reply.get("rank_up")
        nxt = (" Next rank: %s at %s XP." % (me["next"], me["next_xp"])) if me.get("next") else " The top of the Bureau. Respect."
        self.dom_nodes["line"].textContent = "%s XP on file.%s" % (me.get("xp", 0), nxt)

    @handle("ok_button", "click")
    def ok_button_click(self, **event_args):
        self.raise_event("x-close-alert", value=True)
