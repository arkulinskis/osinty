from anvil import *
import anvil.js
import anvil.server
from anvil.js import window

from ._anvil_designer import CaseDeskTemplate
from ... import os_kit, router, state


class CaseDesk(CaseDeskTemplate):
    """#cases/<caseId>: the case desk. Briefing + exhibits, the terminal (search the case's fictional sources), results
    you can pin, the notebook of everything found, and the questions (free-text answers, hints cost points). Clicking
    an exhibit or `code` in a document copies it into the search box (the pivot).
    Server: get_case, case_search, case_pin, case_hint, case_answer, case_reset (Cases.py).
    Items reach the page through item["host"] (DocCard pin, Exhibit/code pivot, CaseQuestion answer/hint)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.case_id = args[0] if args else ""
        self.results: list = []
        self.new_ids: list = []
        self.log_html = ""
        state.set_control_attr(self.query_box, "aria-label", "Search query")
        state.set_control_attr(self.query_box, "autocomplete", "off")
        state.set_control_attr(self.query_box, "spellcheck", "false")
        state.set_control_attr(self.query_box, "maxlength", "120")
        d = anvil.server.call("get_case", self.case_id)
        ok = bool(d and d.get("ok"))
        self.missing.visible = not ok
        self.desk.visible = ok
        if ok:
            self.info, self.sources, self.st = d["case"], d["sources"], d["state"]
            self.src = self.info["sources"][0]
            router.set_title(self.info["title"])
            self._draw_all()

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
        r = state.call("case_hint", self.info["id"], qid)
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
        r = state.call("case_answer", self.info["id"], qid, value)
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
        if r.get("solved"):
            os_kit.celebrate(r)
            window.setTimeout(anvil.js.report_exceptions(lambda: self._debrief(r)), 2600 if r.get("rank_up") else 700)
        else:
            state.toast("Correct. Keep digging.", "ok")

    def _debrief(self, res=None):
        from ...Dialogs.Debrief import Debrief
        if alert(Debrief(title=self.info["title"], debrief=self.st.get("debrief") or [], result=res), buttons=[],
                 role="app-dialog", large=True, dismissible=True) == "next":
            router.go("cases")

    @handle("debrief_button", "click")
    def debrief_button_click(self, **event_args):
        self._debrief(None)

    @handle("reset_button", "click")
    def reset_button_click(self, **event_args):
        text = ("Your XP and best score stay. Your notebook and answers are cleared so you can try for a better score."
                if self.st.get("solved_once") else "Your notebook, answers and hints are cleared.")
        if not confirm(text, title="Restart this case?", buttons=[("Cancel", False), ("Restart", True)], role="app-dialog"):
            return
        r = state.call("case_reset", self.info["id"])
        if r:
            self.st, self.results, self.new_ids, self.log_html = r["state"], [], [], ""
            self._draw_all()
