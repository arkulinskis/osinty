import json

from anvil import *
import anvil.js
from anvil.js import window

from ._anvil_designer import ExifReaderTemplate
from ... import state


class ExifReader(ExifReaderTemplate):
    """Read a photo's hidden metadata (EXIF) in the browser: OS.exif in os-kit.js parses the JPEG; nothing is uploaded."""

    def __init__(self, **properties):
        super().__init__(**properties)
        self.url = None
        self.result.visible = False
        n = self.dom_nodes
        n["file"].addEventListener("change", anvil.js.report_exceptions(self._picked))
        n["drop"].addEventListener("dragover", anvil.js.report_exceptions(self._over))
        n["drop"].addEventListener("dragleave", anvil.js.report_exceptions(self._leave_drop))
        n["drop"].addEventListener("drop", anvil.js.report_exceptions(self._dropped))

    def leave(self):
        if self.url:
            getattr(window.URL, "revokeObjectURL")(self.url)

    def _picked(self, event):
        files = event.target.files
        if files.length:
            self._read(files.item(0))

    def _over(self, event):
        event.preventDefault()
        self.dom_nodes["drop"].classList.add("over")

    def _leave_drop(self, event):
        self.dom_nodes["drop"].classList.remove("over")

    def _dropped(self, event):
        event.preventDefault()
        self.dom_nodes["drop"].classList.remove("over")
        files = event.dataTransfer.files
        if files.length:
            self._read(files.item(0))

    def _read(self, file):
        self.leave()
        self.url = window.OS.exif(file, anvil.js.report_exceptions(self._show))

    def _show(self, text):
        out = json.loads(text)
        n = self.dom_nodes
        n["img"].src = out["url"]
        self.error.visible = bool(out.get("error"))
        n["error_text"].textContent = out.get("error") or ""
        rows = [{"k": "File", "v": "%s · %s KB" % (out["name"], out["kb"])}] + [{"k": r[0], "v": r[1]} for r in out["rows"]]
        gps = out.get("gps")
        self.nothing.visible = not out.get("error") and not out["rows"] and not gps
        self.rows_panel.items = rows
        self.gps.visible = bool(gps)
        if gps:
            lat, lon = gps["lat"], gps["lon"]
            n["gps_text"].textContent = "%s, %s%s" % (lat, lon, (" · %s m" % gps["alt"]) if gps.get("alt") is not None else "")
            state.set_attr(self.osm_link, "href", "https://www.openstreetmap.org/?mlat=%s&mlon=%s#map=18/%s/%s" % (lat, lon, lat, lon))
            state.set_attr(self.gmaps_link, "href", "https://www.google.com/maps?q=%s,%s" % (lat, lon))
        self.result.visible = True
