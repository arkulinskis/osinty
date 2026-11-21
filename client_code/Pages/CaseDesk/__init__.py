import json

from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import CaseDeskTemplate
from ... import os_kit, router, state

TRIAL_KEY = "os-trial"  # a guest's training run of case file #1, in this browser (router.after_sign_in banks it)


def trial_get():
    try:
        t = json.loads(state.store_get(TRIAL_KEY, "") or "{}")
        return t if isinstance(t, dict) else {}
    except Exception:
        return {}


def trial_set(t):
    state.store_set(TRIAL_KEY, json.dumps(t) if t else "")


class CaseDesk(CaseDeskTemplate):
    """#cases/<caseId>: the case desk. Briefing + exhibits, the terminal (search the case's fictional sources), results
    you can pin, the notebook of everything found, and the questions (free-text answers, hints cost points). Clicking
    an exhibit or `code` in a document copies it into the search box (the pivot).
    Server: get_case, case_search, case_pin, case_hint, case_answer, case_reset (Cases.py).
    Items reach the page through item["host"] (DocCard pin, Exhibit/code pivot, CaseQuestion answer/hint).

    Guest mode (signed out, case c1 only): the training run. The run lives in this browser (TRIAL_KEY) and goes to
    the stateless try_case / try_search / try_hint / try_answer, which check it again and send it back; pins stay in
    the browser. "Join the Bureau" remembers #cases/c1, and router.after_sign_in banks the run (claim_trial)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.case_id = args[0] if args else ""
        self.results: list = []
        self.new_ids: list = []
        self.log_html = ""
        self.guest = not state.me() and self.case_id == "c1"
        self.trial: dict = trial_get() if self.guest else {}
        self.guest_bar.visible = self.guest
        state.set_control_attr(self.query_box, "aria-label", "Search query")
        state.set_control_attr(self.query_box, "autocomplete", "off")
        state.set_control_attr(self.query_box, "spellcheck", "false")
        state.set_control_attr(self.query_box, "maxlength", "120")
        d = anvil.server.call("try_case", self.trial) if self.guest else anvil.server.call("get_case", self.case_id)
        ok = bool(d and d.get("ok"))
        self.missing.visible = not ok
        self.desk.visible = ok
        if ok:
            self.info, self.sources, self.st = d["case"], d["sources"], d["state"]
            self.src = self.info["sources"][0]
            self._keep_trial(d)
            router.set_title(self.info["title"])
            self._draw_all()

    # ------------------------------------------------------------------ guest helpers
    def _keep_trial(self, reply):
        """Guests: keep the run the server checked and sent back."""
        if self.guest and reply and reply.get("trial") is not None:
            self.trial = reply["trial"]
            trial_set(self.trial)

    def _call(self, member_fn, guest_fn, *args):
        """state.call for members, the try_* twin (+ the run) for guests."""
        if self.guest:
            r = state.call(guest_fn, *(args + (self.trial,)))
            self._keep_trial(r)
            return r
        return state.call(member_fn, self.info["id"], *args)

    @handle("join_button", "click")
    def join_button_click(self, **event_args):
        router.remember_after(router.href("cases", "c1"))
        router.go("auth", "signup")

    # ------------------------------------------------------------------ drawing
    def _draw_all(self):
        i, n = self.info, self.dom_nodes
        n["title"].textContent = i["title"]
        n["file"].textContent = "File #%s · Operation %s · %s" % (i["num"], i["codename"], i["level"])
        n["client"].textContent = "Client: " + i["client"]
        n["brief"].innerHTML = os_kit.paras(i["brief"])
        self.exhibits_panel.items = [{"label": e[0], "value": e[1], "host": self} for e in i["exhibits"]]
        self._draw_sources()
        self._draw_score()
        self._draw_questions()
        self._draw_results()
        self._draw_notes()
        self._log(self.log_html or "Ready. Pick a source, type a query, press Run.")

    def _draw_sources(self):
        self.sources_panel.items = [{"id": s, "label": self.sources[s]["label"], "on": s == self.src, "host": self}
                                    for s in self.info["sources"]]
        self.query_box.placeholder = self.sources[self.src]["hint"]

    def _draw_score(self):
        st, n = self.st, self.dom_nodes
        solved = st["status"] == "solved"
        self.closed_stamp.visible = solved
        n["score_label"].textContent = "Best score" if solved else "Score if you crack it now"
        n["score"].textContent = str(st["best"] if solved else st["score"])
        self.reset_button.visible = st["status"] != "new"
        if self.guest:
            n["score_label"].textContent = "Training score" if solved else "Score if you crack it now"

    def _draw_questions(self):
        qs = self.st["questions"]
        done = len([q for q in qs if q.get("answer")])
        self.dom_nodes["q_count"].textContent = "%d/%d" % (done, len(qs))
        self.dom_nodes["q_count"].className = "ui-badge" + (" good" if done == len(qs) else "")
        self.questions_panel.items = [dict(q, n=k + 1, host=self) for k, q in enumerate(qs)]
        self.debrief_button.visible = bool(self.st.get("debrief"))

    def _draw_results(self):
        self.results_panel.items = [{"doc": d, "new": d["id"] in self.new_ids, "host": self} for d in self.results]

    def _draw_notes(self):
        found = self.st["found"]
        pinned = [d for d in found if d.get("pinned")]
        self.dom_nodes["notes_count"].textContent = "%s · %d pinned" % (state.plural(len(found), "document"), len(pinned))
        ordered = sorted(found, key=lambda d: 0 if d.get("pinned") else 1)
        self.notes_panel.items = [{"doc": d, "host": self} for d in ordered]
        self.notes_empty.visible = not found

    def _log(self, html):
        self.log_html = html
        self.dom_nodes["log"].innerHTML = html

    def source_label(self, src):
        return self.sources.get(src, {}).get("label", src)

    # ------------------------------------------------------------------ the terminal
    def pick_source(self, src):
        self.src = src
        self._draw_sources()
        self.query_box.focus()

    def use_query(self, text):
        """The pivot: an exhibit or a `code` value goes into the search box."""
        self.query_box.text = text
        self.query_box.focus()
        anvil.js.get_dom_node(self.term).scrollIntoView({"behavior": "smooth", "block": "center"})
        state.toast("Copied into the search box. Pick a source and Run.")

    @handle("query_box", "pressed_enter")
    def query_box_pressed_enter(self, **event_args):
        self.run_button_click()

    @handle("run_button", "click")
    def run_button_click(self, **event_args):
        q = (self.query_box.text or "").strip()
        if not q:
            return
        self.run_button.enabled = False
        try:
            if self.guest:
                r = anvil.server.call("try_search", self.src, q, self.trial)
                self._keep_trial(r)
            else:
                r = anvil.server.call("case_search", self.info["id"], self.src, q)
        finally:
            self.run_button.enabled = True
        if not r.get("ok"):
            self._log("&gt; <b>error</b>: " + os_kit.esc(r.get("error")))
            return
        self.results, self.new_ids = r["results"], r["new"]
        known = [d["id"] for d in self.st["found"]]
        self.st["found"] = self.st["found"] + [d for d in r["results"] if d["id"] not in known]
        if self.st["status"] == "new":
            self.st["status"] = "open"
            self._draw_score()
        label = os_kit.esc(self.source_label(self.src))
        if r["results"]:
            what = state.plural(len(r["results"]), "result") + ((", %d new" % len(r["new"])) if r["new"] else "")
        else:
            what = "no results. Try other keywords, a different source, or something you found earlier."
        self._log('&gt; <b>%s</b>: "%s": %s' % (label, os_kit.esc(r["query"]), what))
        self._draw_results()
        self._draw_notes()
        if r["results"] and window.innerWidth < 900:
            anvil.js.get_dom_node(self.results_panel).scrollIntoView({"behavior": "smooth", "block": "start"})

    def toggle_pin(self, doc_id):
        doc = ([d for d in self.st["found"] if d["id"] == doc_id] or [None])[0]
        flag = not (doc and doc.get("pinned"))
        if self.guest:  # a guest's pins stay in this browser
            pins = [p for p in self.trial.get("pinned", []) if p != doc_id] + ([doc_id] if flag else [])
            self.trial["pinned"] = pins
            trial_set(self.trial)
            r = {"pinned": pins}
        else:
            r = state.call("case_pin", self.info["id"], doc_id, flag)
        if not r:
            return
        for d in self.st["found"] + self.results:
            d["pinned"] = d["id"] in r["pinned"]
        self._draw_results()
        self._draw_notes()
        state.toast("Pinned to the evidence board." if flag else "Unpinned.")

    # ------------------------------------------------------------------ questions
    def take_hint(self, qid):
        if not confirm("It costs 8 points off this case's score.", title="Take a hint?",
                       buttons=[("Cancel", False), ("Show the hint", True)], role="app-dialog"):
            return
        r = self._call("case_hint", "try_hint", qid)
        if not r:
            return
        for q in self.st["questions"]:
            if q["id"] == qid:
                q["hints"], q["hints_left"] = r["hints"], r["hints_left"]
        self.st["score"] = r["score"]
        if self.st["status"] == "new":
            self.st["status"] = "open"
        self._draw_questions()
        self._draw_score()

    def answer(self, qid, value, row):
        r = self._call("case_answer", "try_answer", qid, value)
        if not r:
            return
        keep = self.st["found"]
        self.st = r["state"]
        if len(keep) >= len(r["state"]["found"]):
            self.st["found"] = keep
        if not r["correct"]:
            row.shake()
            state.toast("That doesn't match the evidence. -4 points.", "error")
            self.st["score"] = r["score"]
            self._draw_score()
            return
        self._draw_questions()
        self._draw_score()
        if r.get("solved") and self.guest:
            window.setTimeout(anvil.js.report_exceptions(lambda: self._debrief(r)), 500)
        elif r.get("solved"):
            os_kit.celebrate(r)
            window.setTimeout(anvil.js.report_exceptions(lambda: self._debrief(r)), 2600 if r.get("rank_up") else 700)
        else:
            state.toast("Correct. Keep digging.", "ok")

    def _debrief(self, res=None):
        from ...Dialogs.Debrief import Debrief
        waiting = (res or {}).get("xp_waiting") or int(round(self.info["xp"] * (self.st.get("best") or 100) / 100.0))
        choice = alert(Debrief(title=self.info["title"], debrief=self.st.get("debrief") or [], result=res,
                               guest_xp=waiting if self.guest else None),
                       buttons=[], role="app-dialog", large=True, dismissible=True)
        if choice == "join":
            self.join_button_click()
        elif choice == "next":
            router.go("cases")

    @handle("debrief_button", "click")
    def debrief_button_click(self, **event_args):
        self._debrief(None)

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        if self.guest:
            text = "Your training run (notebook, answers and hints) is cleared."
        elif self.st.get("solved_once"):
            text = "Your XP and best score stay. Your notebook and answers are cleared so you can try for a better score."
        else:
            text = "Your notebook, answers and hints are cleared."
        if not confirm(text, title="Restart this case?", buttons=[("Cancel", False), ("Restart", True)], role="app-dialog"):
            return
        if self.guest:
            trial_set({})
            self.trial = {}
            r = state.call("try_case", {})
            self._keep_trial(r)
        else:
            r = state.call("case_reset", self.info["id"])
        if r:
            self.st, self.results, self.new_ids, self.log_html = r["state"], [], [], ""
            self._draw_all()
