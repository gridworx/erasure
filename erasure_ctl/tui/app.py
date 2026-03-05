"""Main Textual TUI application."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Button, Footer, Header, Label, Static

from erasure_ctl.core.asset_matcher import AssetMatcher
from erasure_ctl.core.config import ErasureConfig, load_config
from erasure_ctl.core.runtime import Runtime


class ModeButton(Button):
    """A styled button for mode selection."""


class ErasureApp(App):
    """Erasure — Secure disk erasure with branded certificates."""

    TITLE = "Erasure"
    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: thick $primary;
        padding: 1 2;
    }

    #app-title {
        text-align: center;
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    #company-name {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    #mode-label {
        text-align: center;
        color: $warning;
        text-style: italic;
        margin-bottom: 1;
    }

    .mode-section {
        margin: 1 0;
    }

    ModeButton {
        width: 100%;
        margin: 0 0 1 0;
    }

    ModeButton.disabled-mode {
        opacity: 0.4;
    }

    #operator-line {
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }

    .mode-desc {
        color: $text-muted;
        text-align: center;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, runtime: Runtime, mock: bool = False) -> None:
        super().__init__()
        self.runtime = runtime
        self.mock = mock
        self.config: ErasureConfig | None = None
        self.matcher: AssetMatcher | None = None

    def compose(self) -> ComposeResult:
        self.config = load_config(self.runtime.data_dir)
        self.matcher = AssetMatcher(self.runtime.data_dir)

        company_name = self.config.company.name or "No company.csv found"
        mode_text = f"[{self.runtime.mode.upper()} MODE]"
        if self.mock:
            mode_text += " [MOCK]"

        yield Header()
        with Container(id="main-container"):
            yield Label(f"ERASURE v{_version()}", id="app-title")
            yield Label(company_name, id="company-name")
            yield Label(mode_text, id="mode-label")

            if self.config.operators:
                yield Label(
                    f"Operator: {self.config.operators[0].name}",
                    id="operator-line",
                )
            else:
                yield Label("No operators.csv found", id="operator-line")

            with Vertical(classes="mode-section"):
                can_internal = self.runtime.can_wipe_internal
                btn1 = ModeButton(
                    "1. Wipe This System (Internal)",
                    id="btn-internal",
                    variant="primary" if can_internal else "default",
                    disabled=not can_internal,
                )
                if not can_internal:
                    btn1.add_class("disabled-mode")
                yield btn1
                if not can_internal:
                    yield Label(
                        "Boot from the Erasure USB to wipe internal drives",
                        classes="mode-desc",
                    )

                can_external = self.runtime.can_wipe_external or self.mock
                btn2 = ModeButton(
                    "2. Wipe External Drive",
                    id="btn-external",
                    variant="primary" if can_external else "default",
                    disabled=not can_external,
                )
                if not can_external:
                    btn2.add_class("disabled-mode")
                yield btn2
                if not can_external:
                    yield Label(
                        "Run with sudo to wipe external drives",
                        classes="mode-desc",
                    )

                yield ModeButton(
                    "3. Manual Attestation",
                    id="btn-attestation",
                    variant="success",
                )

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-internal":
            self.notify("Internal wipe mode — not yet implemented", severity="information")
        elif event.button.id == "btn-external":
            self.notify("External drive wipe — not yet implemented", severity="information")
        elif event.button.id == "btn-attestation":
            self.notify("Manual attestation — not yet implemented", severity="information")


def _version() -> str:
    from erasure_ctl import __version__
    return __version__
