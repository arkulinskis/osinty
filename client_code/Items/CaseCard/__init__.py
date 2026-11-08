from anvil import *

from ._anvil_designer import CaseCardTemplate
from ... import os_kit, router, state


class CaseCard(CaseCardTemplate):
    """One case file in the cabinet. item = a case from list_cases."""

    def __init__(self, **properties):
        super().__init__(**properties)
        c, n = self.item, self.dom_nodes
        n["folder"].setAttribute("data-tab", "File #%s · %s" % (c["num"], c["level"]))
        if c["solved"]:
            n["stamp"].className, n["stamp"].textContent = "os-stamp good", "Closed · %s" % c["best"]
        elif c["status"] in ("open", "replay"):
            n["stamp"].className, n["stamp"].textContent = "os-stamp warn", "Open"
        else:
            n["stamp"].style.display = "none"
        n["code"].textContent = "OPERATION " + c["codename"]
        n["title"].textContent = c["title"]
        n["client"].textContent = c["client"]
        n["teaser"].textContent = c["teaser"]
        n["go"].textContent = "Review" if c["solved"] else "Open the file" if c["status"] == "new" else "Resume"
        state.set_attr(self.open_link, "href", router.href("cases", c["id"]))
        n["xp"].textContent = "%s XP" % c["xp"]
        n["minutes"].textContent = "%s min" % c["minutes"]
        n["srcs"].setAttribute("aria-label", "Sources: " + ", ".join(c["sources"]))
        n["srcs"].innerHTML = "".join('<i class="ic ic-%s" aria-hidden="true"></i>' % os_kit.SRC_ICON.get(s, "search") for s in c["sources"])
        n["solvers"].textContent = ("Closed by " + state.plural(c["solvers"], "agent")) if c["solvers"] else "Nobody has closed this one yet"
