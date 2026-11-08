import json

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import CorkboardTemplate


class Corkboard(CorkboardTemplate):
    """Wraps the corkboard engine. data = {w, h, leads (with icon + label), links, selected}; the callbacks get a lead
    id (click), a lead id + x + y (move, after a drag) or a link id (cut)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self._board = None

    def show(self, data, click, move, cut):
        js = window.JSON.parse(json.dumps(data))  # a plain JS object: the engine moves pins in place
        if self._board is None:
            hooks = {"click": anvil.js.report_exceptions(click), "move": anvil.js.report_exceptions(move),
                     "cut": anvil.js.report_exceptions(cut)}
            self._board = window.OS.board(self.dom_nodes["board"], js, hooks)
        else:
            self._board.update(js)

    def destroy(self):
        if self._board is not None:
            self._board.destroy()
            self._board = None
