from anvil import *
import anvil.server

from ._anvil_designer import CasesTemplate


class Cases(CasesTemplate):
    """#cases: the filing cabinet of case files, with your status on each. Server: list_cases."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        d = anvil.server.call("list_cases")
        solved = len([c for c in d["cases"] if c["solved"]])
        self.dom_nodes["closed"].textContent = "%d of %d closed" % (solved, len(d["cases"]))
        self.cases_panel.items = d["cases"]
