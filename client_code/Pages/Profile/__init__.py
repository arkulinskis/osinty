from anvil import *
import anvil.server

from ._anvil_designer import ProfileTemplate
from ... import auth, router, state


class Profile(ProfileTemplate):
    """#profile, "Your dossier": rank card and ladder, service record, commendations, the Bureau privacy switch, then
    the account: agent name, light/dark, a password reset link, Privacy & Terms, feedback, sign out.
    Server: get_dossier, set_board_hidden (Agents.py), update_profile."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        state.heading(self.name_title, 1)
        self._show_me()
        self._show_theme()
        self._dossier(anvil.server.call("get_dossier"))

    def _show_me(self):
        me = state.me()
        self.initials.text = state.initials(me.get("name"))
        self.name_title.text = me.get("name") or ""
        joined = state.month_year(me.get("joined"))
        self.email_line.text = (me.get("email") or "") + (" · member since " + joined if joined else "")
        self.name_box.text = me.get("name") or ""
        self.admin_link.visible = bool(me.get("is_admin"))
        state.set_control_attr(self.name_box, "maxlength", 60)

    def _dossier(self, d):
        me, n = d["me"], self.dom_nodes
        self.shield.level = me["level"]
        n["rank"].textContent = me["rank"]
        n["xp"].textContent = "%d XP%s" % (me["xp"], (" · %d to %s" % (me["to_next"], me["next"])) if me.get("next") else "")
        n["bar"].setAttribute("aria-valuenow", str(me["pct"]))
        n["bar_fill"].style.width = "%d%%" % me["pct"]
        place = d["board"].get("my_place")
        n["duty"].textContent = state.plural(d["streak"], "day") + " on duty" + ((" · #%s in the Bureau" % place) if place else "")
        self.ranks_panel.items = [{"name": r["name"], "xp": r["xp"], "now": r["name"] == me["rank"], "got": me["xp"] >= r["xp"]}
                                  for r in d["ranks"]]
        n["s_lessons"].textContent = "%d/%d" % (d["lessons_done"], d["lessons_total"])
        n["s_perfect"].textContent = str(d["perfect"])
        n["s_cases"].textContent = "%d/%d" % (d["cases_solved"], d["cases_total"])
        n["s_best"].textContent = str(d["best_case"] or "–")
        n["s_invs"].textContent = str(d["investigations"])
        self.hide_box.checked = bool(d["board_hidden"])
        self.badges_panel.items = d["badges"]

    @handle("hide_box", "change")
    def hide_box_change(self, **event_args):
        r = state.call("set_board_hidden", self.hide_box.checked)
        if r:
            state.toast("You're off the leaderboard." if r["board_hidden"] else "You're back on the leaderboard.", "ok")
        else:
            self.hide_box.checked = not self.hide_box.checked

    def _show_theme(self):
        t = state.theme()
        for name, el in (("auto", self.theme_auto), ("light", self.theme_light), ("dark", self.theme_dark)):
            el.classes["on"] = name == t

    def theme_click(self, event):
        state.set_theme(event.currentTarget.getAttribute("data-theme-pick"))
        self._show_theme()
        shell = getattr(self, "layout", None)
        if shell is not None:
            shell.refresh("profile")

    @handle("name_box", "pressed_enter")
    def name_box_pressed_enter(self, **event_args):
        self.save_button_click()

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if len(name) < 2:
            state.toast("Please tell us your name.", "error")
            return
        r = state.call("update_profile", name)
        if r:
            state.set_me(r["me"])
            self._show_me()
            shell = getattr(self, "layout", None)
            if shell is not None:
                shell.refresh("profile")
            state.toast("Saved", "ok")

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        r = auth.reset(state.me()["email"])
        state.toast(r["message"], "ok")

    def feedback_click(self, event):
        state.feedback()

    def sign_out_click(self, event):
        auth.sign_out()
        state.toast("Signed out. See you soon!")
        router.go("landing")
