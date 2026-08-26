"""Keyboard-navigable full-screen picker over the Mojang version catalog.

The pure selection state machine (:class:`PickerState`), the responsive layout
(:func:`_layout`) and the fragment renderers (``*_fragments``) have no I/O and
are unit tested; :func:`run_picker` wires them to a prompt_toolkit full-screen
app whose ``input``/``output`` are injectable so tests can drive it with a pipe
and a dummy output.

The layout adapts to the terminal: a status title, the item list, an up/down
``还有 N 个`` scroll indicator pair, a search box and a multi-line help block
are stacked, and slots that have no content collapse (``dont_extend_height``).
The viewport row count and the number of help lines are recomputed on every
render/keypress, so a mid-session resize is followed automatically
(prompt_toolkit re-renders on SIGWINCH).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from prompt_toolkit.application import Application, get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.data_structures import Size
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.input.base import Input
from prompt_toolkit.key_binding import KeyBindings, KeyBindingsBase, merge_key_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.layout import HSplit, Layout, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.output.base import Output
from prompt_toolkit.styles import Style
from prompt_toolkit.utils import get_cwidth

from orzmc import VersionEntry

_DEFAULT_VIEW_ROWS = 10
_FALLBACK_TERM_ROWS = 24
_FALLBACK_TERM_COLUMNS = 80

_FIXED_ROWS = 4  # title + up indicator + down indicator + search box
_MIN_VIEW_ROWS = 3  # the list keeps at least this many rows when help is shown

# Bottom help. Each line is short enough for narrow terminals, ordered by
# non-decreasing display width (so a leading slice always fits the column
# budget), and explains what the keys DO rather than just listing them.
_HELP_LINES = (
    "↑↓ 选择版本 · ←→ 前后翻页",  # 25
    "输入过滤 · t 切正式版/测试版 · x 清空",  # 37
    "Enter 选中 · Esc 用最新 · Ctrl-C 取消",  # 37
)
_MAX_HELP_LINES = len(_HELP_LINES)

_STYLES = {
    "picker.title": "bold fg:ansicyan",
    "picker.selected": "reverse bold",
    "picker.match": "fg:ansiyellow bold",
    "picker.muted": "fg:ansibrightblack",
    "picker.hint": "fg:ansibrightblack",
    "picker.scroll": "fg:ansibrightblack",
    "picker.empty": "fg:ansiyellow",
}


def _channel_label(channel: str) -> str:
    return "正式版" if channel == "release" else "测试版"


@dataclass(frozen=True)
class LayoutSpec:
    """Responsive layout derived from the terminal size."""

    view_rows: int  # item rows the list region can hold
    help_lines: int  # how many of the bottom help lines fit


def _layout(term_rows: int, term_columns: int) -> LayoutSpec:
    """Pick a layout for the given terminal size.

    Help lines (see :data:`_HELP_LINES`) are shown from the top until either
    the column or the row budget runs out. Lines are ordered by non-decreasing
    display width, so the leading slice ``_HELP_LINES[:help_lines]`` always
    fits the column budget. The row budget stops adding help once the list
    viewport would drop below :data:`_MIN_VIEW_ROWS`. The title, the two scroll
    indicator slots and the search box are statically reserved
    (:data:`_FIXED_ROWS`), so the scroll math never shifts as indicators
    appear/disappear.
    """
    col_help = sum(1 for line in _HELP_LINES if get_cwidth(line) <= term_columns)
    row_help = 0
    for n in range(_MAX_HELP_LINES, 0, -1):
        if term_rows - _FIXED_ROWS - n >= _MIN_VIEW_ROWS:
            row_help = n
            break
    help_lines = min(col_help, row_help)
    view_rows = max(1, min(_DEFAULT_VIEW_ROWS, term_rows - _FIXED_ROWS - help_lines))
    return LayoutSpec(view_rows=view_rows, help_lines=help_lines)


def _fit(text: str, width: int) -> str:
    """Truncate ``text`` to display ``width`` columns, appending ``…`` when cut."""
    if get_cwidth(text) <= width:
        return text
    used = 0
    kept: list[str] = []
    for ch in text:
        w = max(get_cwidth(ch), 1)
        if used + w > width - 1:  # reserve one column for the ellipsis
            break
        kept.append(ch)
        used += w
    return "".join(kept) + "…"


@dataclass
class PickerState:
    """Pure selection state for the version picker (no I/O, unit-testable)."""

    catalog: tuple[VersionEntry, ...]
    channel: str = "release"
    query: str = ""
    index: int = 0  # absolute index of the highlighted item
    start: int = 0  # index of the first visible row (scroll window)
    rows: int = _DEFAULT_VIEW_ROWS

    @property
    def items(self) -> list[VersionEntry]:
        """Filtered list: the current channel, narrowed by an active query.

        Search is scoped to the list the user is currently looking at: a query
        never reaches across channels, so switch channels (``t``) first to find
        snapshot ids.
        """
        channel_items = [e for e in self.catalog if e.channel == self.channel]
        if not self.query:
            return channel_items
        q = self.query.lower()
        return [e for e in channel_items if q in e.id.lower()]

    @property
    def selected(self) -> str | None:
        """Id of the highlighted item, or ``None`` for an empty list."""
        items = self.items
        return items[self.index].id if items else None

    def move(self, delta: int) -> None:
        """Move the highlight by ``delta``, clamped, keeping the cursor on screen."""
        items = self.items
        if not items:
            self.index = 0
            self.start = 0
            return
        self.index = min(max(self.index + delta, 0), len(items) - 1)
        self._ensure_cursor_visible()

    def jump(self, index: int) -> None:
        """Jump to an absolute item index, clamped, keeping the cursor on screen."""
        items = self.items
        if not items:
            self.index = 0
            self.start = 0
            return
        self.index = min(max(index, 0), len(items) - 1)
        self._ensure_cursor_visible()

    def toggle(self) -> None:
        """Switch release/snapshot, clearing the query and resetting the cursor."""
        self.channel = "snapshot" if self.channel == "release" else "release"
        self.query = ""
        self.index = 0
        self.start = 0

    def set_query(self, query: str) -> None:
        """Update the filter; reset the cursor so the first hit is highlighted."""
        self.query = query
        self.index = 0
        self.start = 0

    def clear_query(self) -> None:
        """Drop the filter (keeps the channel)."""
        self.set_query("")

    def set_rows(self, rows: int) -> None:
        """Resize the viewport, clamping cursor and scroll window to fit."""
        self.rows = max(1, rows)
        items = self.items
        if not items:
            self.index = 0
            self.start = 0
            return
        self.index = min(self.index, len(items) - 1)
        self._ensure_cursor_visible()

    def visible_items(self) -> list[VersionEntry]:
        """The slice of items currently on screen (the scroll window)."""
        return self.items[self.start : self.start + self.rows]

    def _ensure_cursor_visible(self) -> None:
        if self.index < self.start:
            self.start = self.index
        elif self.index >= self.start + self.rows:
            self.start = self.index - self.rows + 1


def title_fragments(state: PickerState, columns: int) -> StyleAndTextTuples:
    """One-line status title: channel/count, or the active in-channel search."""
    if state.query:
        title = f"搜索 “{state.query}” · {_channel_label(state.channel)} · {len(state.items)} 个"
    else:
        title = f"{_channel_label(state.channel)} · {len(state.items)} 个"
    return [("class:picker.title", _fit(title, columns))]


def list_fragments(state: PickerState, columns: int) -> StyleAndTextTuples:
    """Item rows only (the up/down scroll indicators live in their own windows)."""
    items = state.items
    if not items:
        msg = "无匹配版本 — 按 x 清空过滤" if state.query else "无匹配版本"
        return [("class:picker.empty", msg)]
    fragments: StyleAndTextTuples = []
    for offset, entry in enumerate(state.visible_items()):
        if fragments:
            fragments.append(("", "\n"))
        fragments.extend(_row_fragments(state, entry, state.start + offset == state.index, columns))
    return fragments


def up_fragments(state: PickerState) -> StyleAndTextTuples:
    """'↑ 还有 N 个' shown when content is hidden above the viewport."""
    if state.start == 0 or not state.items:
        return []
    return [("class:picker.scroll", f"↑ 还有 {state.start} 个")]


def down_fragments(state: PickerState) -> StyleAndTextTuples:
    """'↓ 还有 N 个' shown when content is hidden below the viewport."""
    below = len(state.items) - (state.start + state.rows)
    if below <= 0:
        return []
    return [("class:picker.scroll", f"↓ 还有 {below} 个")]


def help_fragments(spec: LayoutSpec) -> StyleAndTextTuples:
    """The keybinding help block: up to ``spec.help_lines`` rows, one per line."""
    lines = _HELP_LINES[: spec.help_lines]
    if not lines:
        return []
    fragments: StyleAndTextTuples = []
    for i, line in enumerate(lines):
        if i:
            fragments.append(("", "\n"))
        fragments.append(("class:picker.hint", line))
    return fragments


def _row_base(selected: bool) -> str:
    return "picker.selected" if selected else "picker.item"


def _highlight(text: str, query: str, base: str) -> StyleAndTextTuples:
    """Split ``text`` and tag the case-insensitive matches with ``picker.match``."""
    if not query:
        return [(f"class:{base}", text)]
    q = query.lower()
    lower = text.lower()
    fragments: StyleAndTextTuples = []
    pos = 0
    while True:
        hit = lower.find(q, pos)
        if hit < 0:
            if pos < len(text):
                fragments.append((f"class:{base}", text[pos:]))
            break
        if hit > pos:
            fragments.append((f"class:{base}", text[pos:hit]))
        fragments.append((f"class:{base} class:picker.match", text[hit : hit + len(q)]))
        pos = hit + len(q)
    return fragments


def _row_fragments(state: PickerState, entry: VersionEntry, selected: bool, columns: int) -> StyleAndTextTuples:
    """One list row: id (match-highlighted), muted type suffix; selection is
    conveyed purely by the row's reverse-video style."""
    base = _row_base(selected)
    suffix = f" ({entry.type})" if not entry.is_release else ""
    if get_cwidth(entry.id) + get_cwidth(suffix) > columns:
        # Ultra-narrow fallback: drop the highlight, truncate a plain row.
        return [(f"class:{base}", _fit(entry.id + suffix, columns))]
    fragments = _highlight(entry.id, state.query, base)
    if suffix:
        fragments.append(("class:picker.muted", suffix))
    return fragments


def run_picker(
    catalog: Sequence[VersionEntry],
    *,
    input: Input | None = None,
    output: Output | None = None,
) -> str | None:
    """Full-screen keyboard picker over ``catalog``.

    ↑↓ move the highlight one version at a time, ←→/PgUp/PgDn page through the
    list, and Home/End jump to the ends (the default viewport shows the most
    recent releases; scrolling reveals more, with ``↑/↓ 还有 N 个``
    indicators). Like ``t``, the ←/→ page bindings only apply while the search
    box is empty, so the arrows still move the text cursor inside a query.
    Typing filters within the current channel's list and highlights the
    matches, ``t`` toggles release/snapshot while the search box is empty,
    ``x`` clears the filter, Enter returns the highlighted version, Escape
    returns ``None`` so the caller falls back to the latest release, and
    Ctrl-C raises ``KeyboardInterrupt``. The layout adapts to the terminal
    size on every render and on resize.
    """
    initial = output.get_size() if output is not None else Size(_FALLBACK_TERM_ROWS, _FALLBACK_TERM_COLUMNS)
    spec = _layout(initial.rows, initial.columns)
    state = PickerState(catalog=tuple(catalog), rows=spec.view_rows)

    def _sync_layout_with_columns() -> tuple[LayoutSpec, int]:
        """Recompute the layout from the live terminal size and apply it."""
        size = get_app().output.get_size()
        spec = _layout(size.rows, size.columns)
        state.set_rows(spec.view_rows)
        return spec, size.columns

    def _sync_layout() -> LayoutSpec:
        return _sync_layout_with_columns()[0]

    def _header_fragments() -> StyleAndTextTuples:
        _, columns = _sync_layout_with_columns()
        return title_fragments(state, columns)

    def _up_fragments() -> StyleAndTextTuples:
        _sync_layout()
        return up_fragments(state)

    def _list_fragments() -> StyleAndTextTuples:
        _, columns = _sync_layout_with_columns()
        return list_fragments(state, columns)

    def _down_fragments() -> StyleAndTextTuples:
        _sync_layout()
        return down_fragments(state)

    def _help_fragments() -> StyleAndTextTuples:
        return help_fragments(_sync_layout())

    search_buffer = Buffer(
        multiline=False,
        on_text_changed=lambda buf: state.set_query(buf.text),
        accept_handler=lambda _buf: _accept(state),
    )
    bindings = _build_bindings(state, search_buffer, _sync_layout)

    root = HSplit(
        [
            Window(
                FormattedTextControl(_header_fragments),
                height=1,
                wrap_lines=False,
                always_hide_cursor=True,
            ),
            Window(
                FormattedTextControl(_up_fragments),
                wrap_lines=False,
                dont_extend_height=True,
                always_hide_cursor=True,
            ),
            Window(
                FormattedTextControl(_list_fragments),
                wrap_lines=False,
                dont_extend_height=True,
                always_hide_cursor=True,
            ),
            Window(
                FormattedTextControl(_down_fragments),
                wrap_lines=False,
                dont_extend_height=True,
                always_hide_cursor=True,
            ),
            VSplit(
                [
                    Window(
                        FormattedTextControl("搜索: "),
                        height=1,
                        dont_extend_width=True,
                        always_hide_cursor=True,
                    ),
                    Window(BufferControl(search_buffer), height=1),
                ]
            ),
            Window(
                FormattedTextControl(_help_fragments),
                wrap_lines=False,
                dont_extend_height=True,
                always_hide_cursor=True,
            ),
        ]
    )

    app: Application[str | None] = Application(
        layout=Layout(root),
        key_bindings=bindings,
        style=Style.from_dict(_STYLES),
        full_screen=True,
        enable_page_navigation_bindings=False,
        input=input,
        output=output,
    )
    return app.run()


def _accept(state: PickerState) -> bool:
    """Buffer accept handler: return the highlighted version and quit."""
    get_app().exit(result=state.selected)
    return True


def _build_bindings(
    state: PickerState,
    search_buffer: Buffer,
    sync_layout: Callable[[], LayoutSpec],
) -> KeyBindingsBase:
    """Key bindings for the picker; merged with the defaults for buffer editing."""
    kb = KeyBindings()

    @kb.add("up", eager=True)
    def _up(_event) -> None:
        sync_layout()
        state.move(-1)

    @kb.add("down", eager=True)
    def _down(_event) -> None:
        sync_layout()
        state.move(1)

    @kb.add("pageup", eager=True)
    def _page_up(_event) -> None:
        sync_layout()
        state.move(-state.rows)

    @kb.add("pagedown", eager=True)
    def _page_down(_event) -> None:
        sync_layout()
        state.move(state.rows)

    # ←/→ page the list too, but only while the search box is empty: with a
    # query the arrows stay in the search box for cursor movement (fixing
    # typos), same gating as the `t` toggle below.
    @kb.add("left", eager=True, filter=Condition(lambda: search_buffer.text == ""))
    def _page_left(_event) -> None:
        sync_layout()
        state.move(-state.rows)

    @kb.add("right", eager=True, filter=Condition(lambda: search_buffer.text == ""))
    def _page_right(_event) -> None:
        sync_layout()
        state.move(state.rows)

    @kb.add("home", eager=True)
    def _home(_event) -> None:
        sync_layout()
        state.jump(0)

    @kb.add("end", eager=True)
    def _end(_event) -> None:
        sync_layout()
        state.jump(len(state.items) - 1)

    @kb.add("escape", eager=True)
    def _escape(event) -> None:
        event.app.exit(result=None)

    # Only toggle while the search box is empty, otherwise snapshot ids like
    # "24w14potato" (which contain 't') could never be typed as a query.
    @kb.add("t", eager=True, filter=Condition(lambda: search_buffer.text == ""))
    def _toggle(_event) -> None:
        search_buffer.text = ""
        state.toggle()

    # No Mojang version id contains 'x', so it is safe to reserve it for clearing.
    @kb.add("x", eager=True)
    def _clear(_event) -> None:
        search_buffer.text = ""
        state.clear_query()

    # eager so it beats the merged defaults' no-op `c-c` (`_ignore`).
    @kb.add("c-c", eager=True)
    def _abort(_event) -> None:
        raise KeyboardInterrupt

    return merge_key_bindings([kb, load_key_bindings()])
