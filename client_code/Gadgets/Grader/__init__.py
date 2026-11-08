from anvil import *

from ._anvil_designer import GraderTemplate
from ... import gadget_kit, os_data


class Grader(GraderTemplate):
    """Grade a source and a piece of information with the Admiralty code (A-F, 1-6) and see how to report it."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.rels = [self.r_A, self.r_B, self.r_C, self.r_D, self.r_E, self.r_F]
        self.creds = [self.c_1, self.c_2, self.c_3, self.c_4, self.c_5, self.c_6]
        for rb in self.rels + self.creds:
            rb.add_event_handler("clicked", self._run)
        self._run()

    def _pick(self, buttons, default):
        for rb in buttons:
            if rb.selected:
                return rb.value
        return default

    def _run(self, **event_args):
        r, c = self._pick(self.rels, "B"), self._pick(self.creds, "2")
        n = self.dom_nodes
        n["code"].textContent = r + c
        n["summary"].textContent = "%s source, %s." % (os_data.REL[r], os_data.CRED[c].lower())
        n["help"].textContent = gadget_kit.REL_HELP[r]
        n["advice"].textContent = gadget_kit.grade_advice(r, c)
