from anvil import *
import anvil.server

from ._anvil_designer import CasebookTemplate
from ... import router, state


class Casebook(CasebookTemplate):
    """#casebook: your own private investigations, a new file, or the filled-in training file.
    Server: list_investigations, create_investigation (Dialogs/FileEditor), create_sample_investigation."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        d = anvil.server.call("list_investigations")
        self.files_panel.items = d["items"]
        self.empty.visible = not d["items"]
        self.head_actions.visible = bool(d["items"])

    def _new(self):
        from ...Dialogs.FileEditor import FileEditor
        r = alert(FileEditor(), buttons=[], role="app-dialog", dismissible=True)
        if r:
            router.go("casebook", r["id"])

    def _sample(self, button):
        button.enabled = False
        try:
            r = state.call("create_sample_investigation")
        finally:
            button.enabled = True
        if r:
            state.toast("Training file added.", "ok")
            router.go("casebook", r["investigation"]["id"])

    @handle("new_button", "click")
    def new_button_click(self, **event_args):
        self._new()

    @handle("new_button2", "click")
    def new_button2_click(self, **event_args):
        self._new()

    @handle("sample_button", "click")
    def sample_button_click(self, **event_args):
        self._sample(self.sample_button)

    @handle("sample_button2", "click")
    def sample_button2_click(self, **event_args):
        self._sample(self.sample_button2)
