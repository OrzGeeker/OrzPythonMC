"""OrzMC application: Textual TUI + typer CLI, built on the orzmc library.

The app layer only calls the library's public API (``orzmc/__init__.py``) and
injects its own ``Reporter`` / ``ProgressSink`` implementations for the TUI.
"""

from __future__ import annotations

__version__ = "2.0.0"

__all__ = ["__version__"]
