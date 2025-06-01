"""
Controllers package for business logic and UI coordination.

This package contains controllers that manage the interaction between
the UI layer and the engine layer, implementing the application's
business logic and state management.
"""

from .playback_controller import PlaybackController

__all__ = ['PlaybackController']
