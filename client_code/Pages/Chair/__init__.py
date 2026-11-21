import json

from anvil import *
import anvil.server
from anvil.js import window

from ._anvil_designer import ChairTemplate
from ... import os_kit, state

STORE = "chair"  # guests: {"day", "picks", "reply", "streak", "last", "best"} in this browser


def _local():
    try:
        v = json.loads(state.store_get(STORE, "") or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:
        return {}


def _save_local(v):
    state.store_set(STORE, json.dumps(v))


class Chair(ChairTemplate):
    """#chair, the client chair: three fictional clients a day (the same for everyone), each with a request and a
    fact or two. Rule on each (take / with conditions / show them the door), hand in, read HQ's rulings with the reason,
    what other agents chose and a lesson link, then copy a one-line result to share.
    Works signed out: a guest's ruling and streak stay in this browser (STORE). Members get +10 XP once a day and their
    streak from the server. Server: get_chair, submit_chair (Chair.py)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.picks: dict = {}
        self.reply = None
        self.day = 0
        self._load()

    # ------------------------------------------------------------------ loading
    def _load(self):
        try:
            d = anvil.server.call("get_chair")
        except Exception:
            self._error("We couldn't reach HQ. Check your connection and try again.")
            return
        if not d or not d.get("ok"):
            self._error((d or {}).get("error") or "Something went wrong.")
            return
        self.error_box.visible = False
        self.data, self.day = d, d["day"]
        self.member = bool(d.get("member"))
        n = self.dom_nodes
        n["num"].textContent = "No. %d · %s · %d fictional clients" % (self.day, os_kit.today_long(), len(d["clients"]))
        mine = d.get("mine")
        local = _local()
        if mine:
            self._show_result(mine, fresh=False)
        elif not self.member and local.get("day") == self.day and local.get("reply"):
            self._show_result(local["reply"], fresh=False)
        else:
            self._draw_open()
        self._draw_streak()

    def _error(self, text):
        self.error_box.visible = True
        self.dom_nodes["error_text"].textContent = text
        self.clients_panel.visible = self.hand_part.visible = self.result_part.visible = False
        self.streak_part.visible = False

    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        self._load()

    # ------------------------------------------------------------------ choosing
    def _draw_open(self):
        clients = self.data["clients"]
        self.clients_panel.visible = True
        self.clients_panel.items = [dict(c, n=i + 1, of=len(clients), pick=self.picks.get(c["id"]), ruled=False, host=self)
                                    for i, c in enumerate(clients)]
        self.result_part.visible = False
        self.hand_part.visible = True
        self._draw_progress()

    def _draw_progress(self):
        total, done = len(self.data["clients"]), len(self.picks)
        self.dom_nodes["progress"].textContent = ("All %d ruled. Ready when you are." % total) if done == total \
            else "%d of %d ruled" % (done, total)
        self.hand_in_button.enabled = done == total

    def pick(self, client_id, choice):
        """A ruling button on a client card (Items/ChairClient)."""
        self.picks[client_id] = choice
        key = state.focus_key()
        self._draw_open()
        state.refocus(self.clients_panel, key)

    @handle("hand_in_button", "click")
    def hand_in_button_click(self, **event_args):
        if len(self.picks) < len(self.data["clients"]):
            state.toast("Rule on all three clients first.", "error")
            return
        self.hand_in_button.enabled = False
        try:
            r = state.call("submit_chair", self.day, self.picks)
        finally:
            self.hand_in_button.enabled = True
        if not r:
            return
        if not self.member:
            r["streak"] = self._guest_streak(r)
        self._show_result(r, fresh=True)
        os_kit.celebrate(r)
        window.scrollTo({"top": 0, "behavior": "smooth"})

    # ------------------------------------------------------------------ the rulings
    def _guest_streak(self, r):
        local = _local()
        last = local.get("last")
        streak = int(local.get("streak") or 0)
        if last == self.day:
            pass
        elif last == self.day - 1:
            streak += 1
        else:
            streak = 1
        reply = {k: r.get(k) for k in ("rulings", "score", "of")}
        reply["streak"] = streak
        _save_local({"day": self.day, "reply": reply, "last": self.day, "streak": streak,
                     "best": max(streak, int(local.get("best") or 0))})
        return streak

    def _show_result(self, r, fresh):
        self.reply = r
        rulings = r["rulings"]
        self.clients_panel.visible = True
        self.clients_panel.items = [dict(x, n=i + 1, of=len(rulings), ruled=True, host=self) for i, x in enumerate(rulings)]
        self.hand_part.visible = False
        self.result_part.visible = True
        n = self.dom_nodes
        score, of = r["score"], r["of"]
        n["score_stamp"].textContent = "%d/%d" % (score, of)
        n["score_stamp"].className = "os-stamp ch-score" + (" good" if score == of else " warn" if score else "")
        n["result_title"].textContent = ["Back to the Academy, agent.", "Shaky judgement today.", "Good instincts.",
                                         "Sharp judgement. HQ agrees on every call."][min(score, 3)] if of == 3 else "Rulings in."
        bits = []
        streak = r.get("streak")
        if streak:
            bits.append("%s in a row in the chair." % state.plural(streak, "day"))
        if r.get("xp_gained"):
            bits.append("+%d XP for your record." % r["xp_gained"])
        elif self.member and not fresh:
            bits.append("Today's XP is already banked.")
        bits.append("Read each ruling below: the reason matters more than the score.")
        n["result_text"].textContent = " ".join(bits)
        n["share_text"].textContent = self._share()
        self.join_part.visible = not self.member
        n["next_text"].textContent = "New clients tomorrow at midnight UTC. Every client is fictional."
        self._draw_streak(streak)

    def _share(self):
        r = self.reply or {}
        return "Osinty Client Chair #%d · %d/%d · %s/#chair" % (self.day, r.get("score", 0), r.get("of", 3), window.location.host)

    @handle("copy_button", "click")
    def copy_button_click(self, **event_args):
        os_kit.copy(self._share(), "Result copied. Paste it anywhere.")

    def _draw_streak(self, streak=None):
        if streak is None:
            streak = (self.reply or {}).get("streak")
        if streak is None and not self.member:
            local = _local()
            if local.get("last") in (self.day, self.day - 1):
                streak = local.get("streak")
        self.streak_part.visible = bool(streak)
        self.dom_nodes["streak"].textContent = "%s streak" % state.plural(int(streak or 0), "day")
