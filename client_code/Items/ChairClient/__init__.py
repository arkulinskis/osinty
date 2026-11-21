from anvil import *

from ._anvil_designer import ChairClientTemplate

SHORT = {"take": "take the job", "cond": "take it with conditions", "decline": "show them the door"}


class ChairClient(ChairClientTemplate):
    """One client in the client chair. item = {id, who, ask, facts, n, of, host} plus, while choosing, `pick`
    (take | cond | decline | None) and ruled=False; after handing in, ruled=True with HQ's ruling: verdict,
    verdict_label, pick, right, condition, why, lesson {id, num, title} and crowd {total, pct} (or None)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, n = self.item, self.dom_nodes
        n["n"].textContent = "Client %d of %d" % (c["n"], c["of"])
        n["who"].textContent = c["who"]
        n["ask"].textContent = "“" + c["ask"] + "”"
        self.facts_panel.items = c.get("facts") or []
        n["picks"].setAttribute("aria-label", "Your ruling on client %d" % c["n"])
        ruled = bool(c.get("ruled"))
        n["picks"].style.display = "none" if ruled else ""
        n["ruling"].style.display = "" if ruled else "none"
        n["verdict_stamp"].style.display = "" if ruled else "none"
        for k in ("take", "cond", "decline"):
            on = c.get("pick") == k
            n[k].className = "ch-pick " + k + (" on" if on else "")
            n[k].setAttribute("aria-pressed", "true" if on else "false")
            n[k].setAttribute("data-key", c["id"] + "-" + k)
        n["card"].className = "ch-card" + ((" right" if c.get("right") else " wrong") if ruled else (" picked" if c.get("pick") else ""))
        if ruled:
            self._ruling(c, n)

    def _ruling(self, c, n):
        n["verdict_stamp"].textContent = "HQ: " + c["verdict_label"]
        n["verdict_stamp"].className = "os-stamp ch-vstamp" + (" good" if c["verdict"] == "take" else " warn" if c["verdict"] == "cond" else "")
        n["verdict"].textContent = ("You called it. " if c.get("right") else "HQ disagrees. ")
        n["yours"].textContent = ("You chose to %s." % SHORT.get(c.get("pick"), "pass")) if c.get("pick") else ""
        n["condition"].textContent = ("Conditions: " + c["condition"]) if c.get("condition") else ""
        n["condition"].style.display = "" if c.get("condition") else "none"
        n["why"].textContent = c["why"]
        crowd = c.get("crowd")
        n["crowd"].style.display = "" if crowd else "none"
        if crowd:
            pct = crowd["pct"]
            for k in ("take", "cond", "decline"):
                n["bar_" + k].style.width = "%d%%" % pct.get(k, 0)
            same = pct.get(c.get("pick"), 0)
            n["crowd_text"].textContent = "%d%% of %d agents chose the same as you (take %d%% · conditions %d%% · door %d%%)." % (
                same, crowd["total"], pct.get("take", 0), pct.get("cond", 0), pct.get("decline", 0))
        lesson = c.get("lesson")
        n["lesson"].style.display = "" if lesson else "none"
        if lesson:
            n["lesson"].setAttribute("href", "#academy/" + lesson["id"])
            n["lesson_text"].textContent = "Lesson %s: %s" % (lesson["num"], lesson["title"])

    def _pick(self, choice):
        if not self.item.get("ruled"):
            self.item["host"].pick(self.item["id"], choice)

    def take_click(self, event):
        self._pick("take")

    def cond_click(self, event):
        self._pick("cond")

    def decline_click(self, event):
        self._pick("decline")
