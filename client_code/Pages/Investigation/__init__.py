import re

from anvil import *
import anvil.server
from anvil.js import window

from ._anvil_designer import InvestigationTemplate
from ... import os_kit, router, state

TABS = ["board", "leads", "checklist", "report"]
PHASES = ["Plan", "Plan", "Plan", "Collect", "Collect", "Process", "Analyse", "Analyse", "Analyse", "Report"]


class Investigation(InvestigationTemplate):
    """#casebook/<id>/<tab>: one private investigation. Tabs: the corkboard (Components/Corkboard: drag pins, tie red
    strings, click a pin to edit it, a string's label to cut it), leads (add with an Admiralty grade, edit, the strings),
    the checklist (intelligence cycle + ethics) and the printable report.
    Server: get_investigation, update_investigation, set_checklist, delete_investigation, add/update/move/delete_lead,
    add/delete_link (Casebook.py)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.inv_id = args[0] if args else ""
        self.tab = args[1] if len(args) > 1 and args[1] in TABS else "board"
        self.connect_mode = False
        self.connect_from = None
        self.D: dict = {}
        self._load()

    def leave(self):
        self.board.destroy()

    def _load(self):
        d = anvil.server.call("get_investigation", self.inv_id)
        ok = bool(d and d.get("ok"))
        self.missing.visible = not ok
        self.page.visible = ok
        if ok:
            self.D = d
            self.lead_form.fill(d["kinds"])
            self._draw()

    def _lead(self, lead_id):
        return ([l for l in self.D["leads"] if l["id"] == lead_id] or [None])[0]

    # ------------------------------------------------------------------ the page
    def _draw(self):
        D, n = self.D, self.dom_nodes
        I = D["investigation"]
        router.set_title(I["title"])
        n["title"].textContent = I["title"]
        sub = ""
        if I["subject"]:
            sub += "<b>Subject:</b> " + os_kit.esc(I["subject"]) + (" " if re.search(r"[.?!]$", I["subject"]) else ". ")
        sub += ("<b>Question:</b> " + os_kit.esc(I["objective"])) if I["objective"] else "<i>No question written yet. Edit the file and write one.</i>"
        n["sub"].innerHTML = sub
        for s, el in (("open", self.st_open), ("cold", self.st_cold), ("closed", self.st_closed)):
            el.classes["on"] = I["status"] == s
        done = len([c for c in D["checklist"] if I["checklist"].get(c["id"])])
        n["c_board"].textContent = n["c_leads"].textContent = str(len(D["leads"]))
        n["c_check"].textContent = "%d/%d" % (done, len(D["checklist"]))
        for t, el in (("board", self.tab_board), ("leads", self.tab_leads), ("checklist", self.tab_checklist), ("report", self.tab_report)):
            state.set_attr(el, "href", router.href("casebook", self.inv_id, t))
            el.classes["on"] = t == self.tab
        self.board_part.visible = self.tab == "board"
        self.leads_part.visible = self.tab == "leads"
        self.checklist_part.visible = self.tab == "checklist"
        self.report_part.visible = self.tab == "report"
        getattr(self, "_draw_" + self.tab)()

    # ------------------------------------------------------------------ corkboard
    def _draw_board(self):
        D = self.D
        self.connect_button.text = "Done tying" if self.connect_mode else "Tie a red string"
        self.connect_button.role = ["btn", "btn-sm", "ic-link"] + (["btn-primary"] if self.connect_mode else [])
        self.board_hint.text = (("Now click the second lead." if self.connect_from else "Click the first lead.") if self.connect_mode
                                else "Drag pins to arrange them. Click a pin to edit it, a string's label to cut it.")
        self.board_empty.visible = not D["leads"]
        leads = [dict(l, icon=os_kit.KIND_ICON.get(l["kind"], "edit"), label=os_kit.kind_label(l["kind"])) for l in D["leads"]]
        self.board.show({"w": D["board"]["w"], "h": D["board"]["h"], "leads": leads, "links": D["links"], "selected": self.connect_from},
                        self._pin_click, self._pin_moved, self._cut)

    def _pin_moved(self, lead_id, x, y):
        lead = self._lead(lead_id)
        if lead:
            lead["x"], lead["y"] = x, y
        state.call_quiet("move_lead", lead_id, x, y)

    def _pin_click(self, lead_id):
        lead = self._lead(lead_id)
        if lead is None:
            return
        if not self.connect_mode:
            self._edit_lead(lead)
            return
        if not self.connect_from or self.connect_from == lead_id:
            self.connect_from = None if self.connect_from == lead_id else lead_id
            self._draw_board()
            return
        from ...Dialogs.TieString import TieString
        r = alert(TieString(inv_id=self.inv_id, a=self._lead(self.connect_from), b=lead), buttons=[], role="app-dialog", dismissible=True)
        if r:
            self.D["links"].append(r["link"])
            self.connect_from = None
            self._draw()
            os_kit.celebrate(r)

    def _cut(self, link_id):
        if confirm("Cut this string?", buttons=[("Cancel", False), ("Cut it", True)], role="app-dialog"):
            if state.call("delete_link", link_id) is not None:
                self.D["links"] = [k for k in self.D["links"] if k["id"] != link_id]
                self._draw()

    @handle("connect_button", "click")
    def connect_button_click(self, **event_args):
        self.connect_mode, self.connect_from = not self.connect_mode, None
        if self.connect_mode and len(self.D["leads"]) < 2:
            self.connect_mode = False
            state.toast("Pin at least two leads first.", "error")
        self._draw_board()

    def _add_lead(self):
        from ...Dialogs.LeadEditor import LeadEditor
        r = alert(LeadEditor(inv_id=self.inv_id, kinds=self.D["kinds"]), buttons=[], role="app-dialog", large=True, dismissible=True)
        if r and r.get("saved"):
            self.D["leads"].append(r["saved"]["lead"])
            self._draw()
            os_kit.celebrate(r["saved"])
            state.toast("Pinned.", "ok")

    @handle("add_lead_button", "click")
    def add_lead_button_click(self, **event_args):
        self._add_lead()

    @handle("first_lead_button", "click")
    def first_lead_button_click(self, **event_args):
        self._add_lead()

    def _edit_lead(self, lead):
        from ...Dialogs.LeadEditor import LeadEditor
        r = alert(LeadEditor(inv_id=self.inv_id, kinds=self.D["kinds"], lead=lead), buttons=[], role="app-dialog", large=True,
                  dismissible=True)
        if not r:
            return
        if r.get("deleted"):
            self._load()
        elif r.get("saved"):
            new = r["saved"]["lead"]
            self.D["leads"] = [new if l["id"] == lead["id"] else l for l in self.D["leads"]]
            self._draw()

    def edit_lead(self, lead_id):
        lead = self._lead(lead_id)
        if lead:
            self._edit_lead(lead)

    # ------------------------------------------------------------------ leads
    def _draw_leads(self):
        D = self.D
        self.leads_panel.items = [dict(l, host=self) for l in D["leads"]]
        self.leads_empty.visible = not D["leads"]
        self.links_part.visible = bool(D["links"])
        names = {l["id"]: l["value"] for l in D["leads"]}
        self.links_panel.items = [{"id": k["id"], "a": names.get(k["a"], "?"), "b": names.get(k["b"], "?"), "label": k["label"],
                                   "host": self} for k in D["links"]]

    @handle("pin_button", "click")
    def pin_button_click(self, **event_args):
        self.pin_button.enabled = False
        try:
            r = state.call("add_lead", self.inv_id, self.lead_form.data())
        finally:
            self.pin_button.enabled = True
        if r:
            self.D["leads"].append(r["lead"])
            self.lead_form.fill(self.D["kinds"])
            self._draw()
            os_kit.celebrate(r)
            state.toast("Pinned.", "ok")

    def cut_link(self, link_id):
        self._cut(link_id)

    # ------------------------------------------------------------------ checklist
    def _draw_checklist(self):
        I = self.D["investigation"]
        self.check_panel.items = [{"id": c["id"], "text": c["text"], "phase": PHASES[i] if i < len(PHASES) else "",
                                   "checked": bool(I["checklist"].get(c["id"])), "host": self}
                                  for i, c in enumerate(self.D["checklist"])]

    def set_check(self, key, flag):
        r = state.call("set_checklist", self.inv_id, key, flag)
        if r:
            self.D["investigation"]["checklist"] = r["checklist"]
            done = len([c for c in self.D["checklist"] if r["checklist"].get(c["id"])])
            self.dom_nodes["c_check"].textContent = "%d/%d" % (done, len(self.D["checklist"]))
        return r

    # ------------------------------------------------------------------ report
    def _draw_report(self):
        D, n = self.D, self.dom_nodes
        I, leads, links = D["investigation"], D["leads"], D["links"]
        names = {l["id"]: l["value"] for l in leads}
        n["r_date"].textContent = os_kit.long_date(str(window.Date().toISOString()))
        n["r_title"].textContent = I["title"]
        label, cls = [(s[1], s[2]) for s in os_kit.STATUS if s[0] == I["status"]][0] if I["status"] in ("open", "cold", "closed") else ("Open", "")
        n["r_stamp"].className, n["r_stamp"].textContent = ("os-stamp " + cls).strip(), label
        n["r_bluf"].textContent = I["objective"] or "Write the question in this file, then your answer here before sending."
        n["r_subject"].textContent = I["subject"] or "—"
        n["r_opened"].textContent = os_kit.long_date(I["created"])
        n["r_leads"].textContent = "%d (%d graded)" % (len(leads), len([l for l in leads if l["grade"]]))
        n["r_links"].textContent = str(len(links))
        groups: dict = {}
        order = []
        for l in leads:
            if l["kind"] not in groups:
                groups[l["kind"]] = []
                order.append(l["kind"])
            groups[l["kind"]].append(l)
        self.findings_panel.items = [{"label": os_kit.kind_label(k), "leads": groups[k]} for k in order]
        self.no_findings.visible = not leads
        self.conn_part.visible = bool(links)
        n["conn_h"].textContent = "4. Connections"
        self.conn_panel.items = [{"a": names.get(k["a"], "?"), "mid": k["label"] or "linked to", "b": names.get(k["b"], "?")} for k in links]
        timeline = sorted([l for l in leads if l["when"]], key=lambda l: l["when"])
        self.time_part.visible = bool(timeline)
        n["time_h"].textContent = "%d. Timeline" % (5 if links else 4)
        self.time_panel.items = [{"a": l["when"], "b": l["value"]} for l in timeline]
        done = [c for c in D["checklist"] if I["checklist"].get(c["id"])]
        n["r_method"].textContent = "%d of %d checks completed%s" % (
            len(done), len(D["checklist"]), (": " + "; ".join(c["text"].lower() for c in done) + ".") if done else ".")

    @handle("print_button", "click")
    def print_button_click(self, **event_args):
        window.print()

    # ------------------------------------------------------------------ the file itself
    def status_click(self, event):
        s = event.currentTarget.getAttribute("data-status")
        r = state.call("update_investigation", self.inv_id, {"status": s})
        if r:
            self.D["investigation"]["status"] = r["investigation"]["status"]
            self._draw()
            state.toast("Marked %s." % s)

    @handle("edit_button", "click")
    def edit_button_click(self, **event_args):
        from ...Dialogs.FileEditor import FileEditor
        r = alert(FileEditor(inv=self.D["investigation"]), buttons=[], role="app-dialog", dismissible=True)
        if r:
            self.D["investigation"] = r
            self._draw()

    @handle("delete_button", "click")
    def delete_button_click(self, **event_args):
        if confirm("Every lead and string goes with it. This can't be undone.", title="Delete this investigation?",
                   buttons=[("Cancel", False), ("Delete", True)], role="app-dialog"):
            if state.call("delete_investigation", self.inv_id) is not None:
                state.toast("Deleted.")
                router.go("casebook")
