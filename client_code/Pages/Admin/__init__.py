from anvil import *

from ._anvil_designer import AdminTemplate
from ... import state

TABS = ["overview", "feedback", "users", "training", "bulletins", "demo"]


class Admin(AdminTemplate):
    """#admin/<tab>: overview numbers, the old feedback inbox, users (admin / active switches), training stats (passes
    per lesson, solves and scores per case), bulletins from HQ (shown in every agent's office) and the demo data.
    Each tab is its own address, so the browser's back button works."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.tab = args[0] if args and args[0] in TABS else "overview"
        self._filter = "new"
        for name in TABS:
            getattr(self, name + "_part").visible = name == self.tab
            getattr(self, "tab_" + name).classes["on"] = name == self.tab
        self.feedback_panel.add_event_handler("x-changed", self._feedback_changed)
        self.bulletins_panel.add_event_handler("x-changed", self._bulletins_changed)
        state.set_control_attr(self.search_box, "aria-label", "Search people")
        getattr(self, "_" + self.tab)()

    # ---- overview
    def _overview(self):
        d = state.call("admin_overview")
        n = self.dom_nodes
        n["s_users"].textContent = str(d["users"])
        n["s_admins"].textContent = str(d["admins"])
        n["s_admins_label"].textContent = "admin" if d["admins"] == 1 else "admins"
        n["s_feedback"].textContent = str(d["feedback_new"])
        n["s_lessons"].textContent = str(d["lessons_passed"])
        n["s_cases"].textContent = str(d["cases_solved"])
        n["s_invs"].textContent = str(d["investigations"])
        n["demo_line"].textContent = "Demo data is %s (%d demo agents). Manage it in the Demo data tab." % (
            d["demo"]["state"], d["demo"]["counts"].get("agents", 0))

    # ---- feedback
    def _feedback(self):
        d = state.call("list_feedback", None)
        items = [i for i in d["items"] if self._filter == "all" or i["status"] == self._filter]
        self.feedback_panel.items = items
        self.no_feedback.visible = not items
        labels = {"new": "New", "read": "Read", "done": "Done", "all": "All"}
        for key, el in (("new", self.f_new), ("read", self.f_read), ("done", self.f_done), ("all", self.f_all)):
            n = len(d["items"]) if key == "all" else d["counts"].get(key, 0)
            el.text = "%s (%d)" % (labels[key], n)
            el.role = ["seg", "on"] if key == self._filter else ["seg"]
            state.set_control_attr(el, "aria-pressed", "true" if key == self._filter else "false")

    def _set_filter(self, value):
        self._filter = value
        self._feedback()

    @handle("f_new", "click")
    def f_new_click(self, **event_args):
        self._set_filter("new")

    @handle("f_read", "click")
    def f_read_click(self, **event_args):
        self._set_filter("read")

    @handle("f_done", "click")
    def f_done_click(self, **event_args):
        self._set_filter("done")

    @handle("f_all", "click")
    def f_all_click(self, **event_args):
        self._set_filter("all")

    def _feedback_changed(self, **event_args):
        self._feedback()

    # ---- users
    def _users(self, query=None):
        d = state.call("list_users", query or None)
        self.users_panel.items = d["users"]
        self.users_count.text = state.plural(d["total"], "person", "people")

    @handle("search_box", "pressed_enter")
    def search_box_pressed_enter(self, **event_args):
        self._users(self.search_box.text)

    @handle("search_button", "click")
    def search_button_click(self, **event_args):
        self._users(self.search_box.text)

    # ---- training
    def _training(self):
        d = state.call("admin_training")
        top = max([l["passes"] for l in d["lessons"]] + [1])
        self.tr_cases_panel.items = d["cases"]
        self.tr_lessons_panel.items = [dict(l, top=top) for l in d["lessons"]]

    # ---- bulletins
    def _bulletins(self):
        self.b_kind.items = [("Note", "note"), ("New", "new"), ("Alert", "alert")]
        state.set_control_attr(self.b_title, "maxlength", 100)
        state.set_control_attr(self.b_body, "maxlength", 1000)
        d = state.call("admin_bulletins")
        self.bulletins_panel.items = d["items"]
        self.no_bulletins.visible = not d["items"]

    def _bulletins_changed(self, **event_args):
        self._bulletins()

    @handle("post_button", "click")
    def post_button_click(self, **event_args):
        self.post_button.enabled = False
        try:
            r = state.call("post_bulletin", self.b_title.text or "", self.b_body.text or "", self.b_kind.selected_value)
        finally:
            self.post_button.enabled = True
        if r:
            state.toast("Posted", "ok")
            self.b_title.text = self.b_body.text = ""
            self._bulletins()

    # ---- demo data
    def _demo(self):
        d = state.call("admin_overview")["demo"]
        counts = ", ".join("%s %s" % (v, k) for k, v in d["counts"].items())
        self.dom_nodes["demo_status"].textContent = "Status: %s · %s" % (d["state"], counts)
        self.demo_load_button.text = "Reload demo data" if d["state"] == "loaded" else "Load demo data"

    @handle("demo_load_button", "click")
    def demo_load_button_click(self, **event_args):
        if confirm("Demo people and content are added (any old demo rows are replaced).", title="Load the demo data?",
                   buttons=[("Cancel", False), ("Load", True)], role="app-dialog"):
            if state.call("demo_load"):
                state.toast("Done", "ok")
                self._demo()

    @handle("demo_remove_button", "click")
    def demo_remove_button_click(self, **event_args):
        if confirm("Every demo row is deleted. Real data stays.", title="Remove the demo data?",
                   buttons=[("Cancel", False), ("Remove", True)], role="app-dialog"):
            if state.call("demo_remove"):
                state.toast("Done", "ok")
                self._demo()
