from anvil import *
import anvil.server
from anvil.js import window

from ._anvil_designer import HomeTemplate
from ... import os_kit, router, state


def _greeting():
    h = window.Date().getHours()
    return "Working late" if h < 5 else "Morning" if h < 12 else "Afternoon" if h < 18 else "Evening"


class Home(HomeTemplate):
    """#home, "The Office": the agent's desk. Rank + XP, streak, the daily briefing (+5 XP once a day), next lesson,
    case files in progress, the casebook, commendations, the Bureau leaderboard and bulletins from HQ.
    Server: get_office, claim_briefing (Agents.py)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self._load()

    def _load(self):
        self._draw(anvil.server.call("get_office"))

    def _draw(self, d):
        n, me = self.dom_nodes, d["me"]
        first = ((state.me() or {}).get("name") or "Agent").split(" ")[0]
        n["date"].textContent = os_kit.today_long()
        n["greet"].textContent = _greeting()
        n["first"].textContent = first
        self.shield.level = me["level"]
        n["rank"].textContent = me["rank"]
        n["rank_sub"].textContent = "%d XP%s" % (me["xp"], (" · %d to %s" % (me["to_next"], me["next"])) if me.get("next") else " · top rank")
        n["bar"].setAttribute("aria-valuenow", str(me["pct"]))
        n["bar_fill"].style.width = "%d%%" % me["pct"]
        n["streak_chip"].className = "of-chip" + (" hot" if d["streak"] >= 3 else "")
        n["streak"].textContent = state.plural(d["streak"], "day") + " on duty"
        n["lessons"].textContent = "%d/%d lessons" % (d["lessons_done"], d["lessons_total"])
        n["cases"].textContent = "%d/%d cases closed" % (d["cases_solved"], d["cases_total"])
        place = d["board"].get("my_place")
        self.place_chip.visible = bool(place)
        n["place"].textContent = "#%s in the Bureau" % place
        n["tip_title"].textContent = d["tip"]["title"]
        n["tip_body"].textContent = d["tip"]["body"]
        self.sign_button.visible = not d["briefing_done"]
        self.signed_part.visible = bool(d["briefing_done"])

        nl = d.get("next_lesson")
        self.nl_link.visible = bool(nl)
        self.nl_all.visible = not nl
        if nl:
            n["nl_title"].textContent = nl["num"] + " " + nl["title"]
            n["nl_text"].textContent = nl["summary"]
            n["nl_go"].textContent = "Start · %s min" % nl["minutes"]
            n["nl_mod"].textContent = "Module %s" % nl["module_num"]
            state.set_attr(self.nl_link, "href", router.href("academy", nl["id"]))
        else:
            n["nl_title"].textContent = "Academy complete"
            n["nl_text"].textContent = "Every lesson passed. Retake any quiz for a perfect score."
            n["nl_mod"].textContent = ""

        ac = d["active_cases"][0] if d["active_cases"] else None
        nc = d.get("next_case")
        self.nc_link.visible = bool(ac or nc)
        self.nc_all.visible = not (ac or nc)
        self.nc_badge.visible = bool(nc) and not ac
        if ac:
            n["nc_title"].textContent = ac["title"]
            n["nc_text"].textContent = "Operation %s is open on your desk: %d/%d questions cracked, %s found." % (
                ac["codename"], ac["answered"], ac["total"], state.plural(ac["found"], "document"))
            n["nc_go"].textContent = "Resume"
            state.set_attr(self.nc_link, "href", router.href("cases", ac["id"]))
        elif nc:
            n["nc_title"].textContent = nc["title"]
            n["nc_text"].textContent = nc["teaser"]
            n["nc_go"].textContent = "Open the file"
            n["nc_badge_text"].textContent = "%s · %s XP" % (nc["level"], nc["xp"])
            state.set_attr(self.nc_link, "href", router.href("cases", nc["id"]))
        else:
            n["nc_title"].textContent = "All cases closed"
            n["nc_text"].textContent = "Replay any file to beat your best score."

        inv = d["investigations"]
        n["inv_open"].textContent = str(inv["open"])
        n["inv_text"].textContent = ("%s out of %d. Pin leads, tie red strings, print the report." % (state.plural(inv["open"], "open investigation"), inv["total"])
                                     if inv["total"] else "Your own investigations live here: leads, a corkboard, a checklist and a printable report.")

        earned = len([b for b in d["badges"] if b["earned"]])
        n["badges_count"].textContent = "%d of %d earned" % (earned, len(d["badges"]))
        self.badges_panel.items = d["badges"]

        board = d["board"]
        n["board_total"].textContent = state.plural(board["total"], "agent") + " ranked"
        self.board_panel.items = board["rows"]
        self.board_empty.visible = not board["rows"]
        self.board_me.visible = bool(place and place > len(board["rows"]))
        n["board_me_text"].textContent = "You're #%s. Keep going." % place
        self.bulletin_panel.items = d["bulletins"]
        self.bull_empty.visible = not d["bulletins"]

    @handle("sign_button", "click")
    def sign_button_click(self, **event_args):
        self.sign_button.enabled = False
        try:
            r = state.call("claim_briefing")
        finally:
            self.sign_button.enabled = True
        if r:
            os_kit.celebrate(r)
            state.toast("Briefing signed. %s on duty." % state.plural(r["streak"], "day"), "ok")
            self._load()
