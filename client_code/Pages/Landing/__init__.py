from anvil import *

from ._anvil_designer import LandingTemplate
from ... import state

# The app's video on the Addanapp YouTube channel (APP_MAKER/youtube/manifest.json), shown in the Watch section.
YT_VIDEO = "3AZprKF2iH0"


class Landing(LandingTemplate):
    """#landing (Persuade): the hero IS the detective's corkboard (the pitch is a pinned case-file card, the clues are
    pinned around it and tied with red string), the Watch section (YouTube), how it works, the curriculum, a terminal
    teaser of a case file, what's inside, the code of conduct, questions and a last call. Static copy lives in the
    template; members see "Back to the office" instead of the sign-up buttons."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        me = state.me()
        self.guest_cta.visible = self.band_guest.visible = not me
        self.member_cta.visible = self.band_member.visible = bool(me)
        self.dom_nodes["yt_cover"].addEventListener("click", self._play)

    def _play(self, event):
        """Swap the video's cover for YouTube's player (privacy-enhanced); nothing loads from YouTube before this click."""
        self.dom_nodes["yt_frame"].innerHTML = (
            '<iframe src="https://www.youtube-nocookie.com/embed/' + YT_VIDEO + '?autoplay=1&rel=0&playsinline=1" '
            'title="Osinty video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen '
            'referrerpolicy="strict-origin-when-cross-origin"></iframe>')
