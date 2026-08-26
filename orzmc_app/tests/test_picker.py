"""Picker: PickerState pure logic + run_picker TUI integration (pipe input, no TTY)."""

from __future__ import annotations

from prompt_toolkit.data_structures import Size
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput, Output
from prompt_toolkit.utils import get_cwidth

from orzmc import VersionEntry
from orzmc_app.cli.picker import (
    _HELP_LINES,
    LayoutSpec,
    PickerState,
    _layout,
    down_fragments,
    help_fragments,
    list_fragments,
    run_picker,
    title_fragments,
    up_fragments,
)

CATALOG = [
    VersionEntry("1.21.4", "release"),
    VersionEntry("1.21.3", "release"),
    VersionEntry("1.20.4", "release"),
    VersionEntry("25w14a", "snapshot"),
    VersionEntry("b1.7.3", "old_beta"),
    VersionEntry("c0.0.13a", "old_alpha"),
]


class TestPickerState:
    def test_default_channel_is_release_newest_first(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        assert state.channel == "release"
        assert [e.id for e in state.items] == ["1.21.4", "1.21.3", "1.20.4"]
        assert state.selected == "1.21.4"

    def test_cursor_starts_on_latest(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        assert state.index == 0
        assert state.start == 0

    def test_move_clamps_at_edges(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.move(-1)  # above top
        assert state.selected == "1.21.4"
        state.move(10)  # past bottom
        assert state.selected == "1.20.4"

    def test_move_scrolls_viewport_to_keep_cursor_visible(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.move(15)
        assert state.index == 15
        assert state.start == 6  # cursor sits on the bottom visible row
        assert state.visible_items()[0].id == "1.24"
        assert state.visible_items()[-1].id == "1.15"
        assert state.selected == "1.15"

    def test_move_scrolls_window_up_again(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.move(15)  # index 15, start 6
        state.move(-9)  # index 6, still on the top visible row
        assert state.start == 6
        state.move(-1)  # index 5 < start 6 → scroll up
        assert state.start == 5
        assert state.selected == "1.25"

    def test_jump_to_end_and_home(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.jump(29)
        assert state.selected == "1.1"
        assert state.start == 20
        state.jump(0)
        assert state.selected == "1.30"
        assert state.start == 0

    def test_toggle_switches_channel_and_resets_cursor(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("1.20")
        state.move(1)
        state.toggle()
        assert state.channel == "snapshot"
        assert state.query == ""
        assert state.index == 0
        # snapshot channel covers every non-release manifest type
        assert [e.id for e in state.items] == ["25w14a", "b1.7.3", "c0.0.13a"]

    def test_query_filters_within_current_channel(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        # "b1.7.3" lives in the snapshot channel, so a release-scoped search
        # finds nothing for it.
        state.set_query("B1")
        assert state.items == []
        state.set_query("1.20")
        assert [e.id for e in state.items] == ["1.20.4"]
        assert state.selected == "1.20.4"
        # after switching to the snapshot channel the same id matches
        state.toggle()
        state.set_query("b1.7")
        assert [e.id for e in state.items] == ["b1.7.3"]

    def test_query_empty_resets_to_channel(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("b1")
        state.clear_query()
        assert state.query == ""
        assert [e.id for e in state.items] == ["1.21.4", "1.21.3", "1.20.4"]

    def test_empty_items_are_safe(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("zzz-nomatch")
        assert state.items == []
        assert state.selected is None
        assert state.visible_items() == []
        state.move(1)  # must not raise on an empty list
        assert state.selected is None

    def test_visible_items_is_default_viewport_of_ten(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        assert len(state.visible_items()) == 10
        assert state.visible_items()[0].id == "1.30"
        assert state.visible_items()[-1].id == "1.21"


class TestLayout:
    """Responsive layout table for assorted terminal sizes."""

    def test_wide_full_height_shows_all_help(self) -> None:
        spec = _layout(24, 120)
        assert spec.view_rows == 10
        assert spec.help_lines == 3

    def test_medium_shows_all_help(self) -> None:
        spec = _layout(40, 80)  # DummyOutput default size
        assert spec.view_rows == 10
        assert spec.help_lines == 3

    def test_short_terminal_hides_help_and_shrinks_viewport(self) -> None:
        spec = _layout(8, 20)  # too narrow for even the first help line
        assert spec.view_rows == 4
        assert spec.help_lines == 0

    def test_very_short_terminal_keeps_two_rows(self) -> None:
        spec = _layout(6, 20)
        assert spec.view_rows == 2
        assert spec.help_lines == 0

    def test_tiny_terminal_keeps_one_row(self) -> None:
        spec = _layout(2, 10)
        assert spec.view_rows == 1
        assert spec.help_lines == 0

    def test_narrow_terminal_hides_help_even_with_height(self) -> None:
        # 40 rows tall but 24 columns wide: not even the first help line fits.
        spec = _layout(40, 24)
        assert spec.view_rows == 10
        assert spec.help_lines == 0

    def test_tall_but_short_terminal_keeps_one_row(self) -> None:
        spec = _layout(5, 120)  # 5 rows: no help, one list row
        assert spec.view_rows == 1
        assert spec.help_lines == 0

    def test_short_wide_terminal_stacks_all_help_above_min_list(self) -> None:
        spec = _layout(10, 120)  # 10 rows → 3 list rows + all 3 help lines
        assert spec.view_rows == 3
        assert spec.help_lines == 3

    def test_short_wide_terminal_drops_help_to_keep_list(self) -> None:
        spec = _layout(9, 120)  # 9 rows: only 2 help lines keep the list ≥ 3
        assert spec.view_rows == 3
        assert spec.help_lines == 2

    def test_narrow_medium_shows_only_fitting_help_lines(self) -> None:
        spec = _layout(24, 30)  # only the first (25-col) help line fits
        assert spec.view_rows == 10
        assert spec.help_lines == 1


class TestSetRows:
    def test_shrink_keeps_cursor_on_screen(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.move(15)  # index 15, start 6
        state.set_rows(5)
        assert state.rows == 5
        assert state.index == 15
        assert state.start == 11  # cursor forced onto the bottom visible row
        assert state.selected == "1.15"
        assert state.visible_items()[-1].id == "1.15"

    def test_grow_keeps_cursor_and_window(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.move(15)  # index 15, start 6
        state.set_rows(20)
        assert state.rows == 20
        assert state.index == 15
        assert state.start == 6  # cursor already visible, window unchanged
        assert state.selected == "1.15"

    def test_rows_are_clamped_to_at_least_one(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_rows(0)
        assert state.rows == 1

    def test_empty_list_is_safe(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("zzz-nomatch")
        state.set_rows(3)
        assert state.rows == 3
        assert state.index == 0
        assert state.start == 0
        assert state.selected is None


class TestRenderFragments:
    def test_title_plain_channel_and_count(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        assert title_fragments(state, 80) == [("class:picker.title", "正式版 · 3 个")]

    def test_title_search_mode(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("1.20")
        assert title_fragments(state, 80) == [("class:picker.title", "搜索 “1.20” · 正式版 · 1 个")]

    def test_title_search_mode_names_the_current_channel(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.toggle()  # snapshot channel
        state.set_query("b1.7")
        assert title_fragments(state, 80) == [("class:picker.title", "搜索 “b1.7” · 测试版 · 1 个")]

    def test_list_selected_row_is_pure_reverse_highlight(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        rows = list_fragments(state, 80)
        assert rows[0] == ("class:picker.selected", "1.21.4")
        # selection is conveyed purely by the reverse-video style: no pointer,
        # no alignment placeholder.
        assert not any("▶" in frag[1] for frag in rows)
        assert not any(frag[1] == "  " for frag in rows)

    def test_list_unselected_rows_have_no_marker(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        rows = list_fragments(state, 80)
        assert ("class:picker.item", "1.21.3") in rows
        assert ("class:picker.item", "1.20.4") in rows

    def test_list_snapshot_suffix_is_muted(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.toggle()  # snapshot channel, cursor on first snapshot
        rows = list_fragments(state, 80)
        assert rows[0] == ("class:picker.selected", "25w14a")
        assert ("class:picker.muted", " (snapshot)") in rows

    def test_list_highlight_matches_query(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("1.20")
        rows = list_fragments(state, 80)
        assert ("class:picker.selected class:picker.match", "1.20") in rows

    def test_list_highlight_is_multi_segment(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("1")
        rows = list_fragments(state, 80)
        # "1.21.4" = '1','.','2','1','.','4': two hits of "1" (positions 0 and 3)
        # split by the plain ".2" between them.
        assert ("class:picker.selected class:picker.match", "1") in rows
        assert ("class:picker.selected", ".2") in rows

    def test_list_highlight_is_case_insensitive(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.toggle()  # snapshot channel: "b1.7.3" lives here
        state.set_query("B1")
        rows = list_fragments(state, 80)
        assert ("class:picker.selected class:picker.match", "b1") in rows

    def test_list_empty_with_query_hints_clear(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("zzz-nomatch")
        assert list_fragments(state, 80) == [("class:picker.empty", "无匹配版本 — 按 x 清空过滤")]

    def test_list_empty_catalog(self) -> None:
        state = PickerState(catalog=())
        assert list_fragments(state, 80) == [("class:picker.empty", "无匹配版本")]

    def test_list_ultra_narrow_falls_back_to_truncated_plain_row(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        rows = list_fragments(state, 4)  # "1.21.4" is 6 columns wide
        # selected row falls back to a single truncated fragment, with no
        # per-segment match styling split.
        assert rows[0] == ("class:picker.selected", "1.2…")

    def test_up_indicator_when_scrolled(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.move(15)  # start 6
        assert up_fragments(state) == [("class:picker.scroll", "↑ 还有 6 个")]

    def test_down_indicator_when_more_below(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        assert down_fragments(state) == [("class:picker.scroll", "↓ 还有 20 个")]
        state.move(15)  # start 6
        assert down_fragments(state) == [("class:picker.scroll", "↓ 还有 14 个")]

    def test_no_indicator_at_top(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        assert up_fragments(state) == []

    def test_no_down_indicator_at_bottom(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        state = PickerState(catalog=catalog, rows=10)
        state.jump(29)  # start 20, end of list
        assert down_fragments(state) == []

    def test_no_indicators_on_empty_list(self) -> None:
        state = PickerState(catalog=tuple(CATALOG))
        state.set_query("zzz-nomatch")
        assert up_fragments(state) == []
        assert down_fragments(state) == []

    def test_help_fragments_hidden_without_room(self) -> None:
        spec = LayoutSpec(view_rows=4, help_lines=0)
        assert help_fragments(spec) == []

    def test_help_fragments_render_one_line(self) -> None:
        spec = LayoutSpec(view_rows=10, help_lines=1)
        assert help_fragments(spec) == [("class:picker.hint", _HELP_LINES[0])]

    def test_help_fragments_render_leading_lines(self) -> None:
        spec = LayoutSpec(view_rows=10, help_lines=2)
        assert help_fragments(spec) == [
            ("class:picker.hint", _HELP_LINES[0]),
            ("", "\n"),
            ("class:picker.hint", _HELP_LINES[1]),
        ]

    def test_help_fragments_render_all_lines(self) -> None:
        spec = LayoutSpec(view_rows=10, help_lines=3)
        assert help_fragments(spec) == [
            ("class:picker.hint", _HELP_LINES[0]),
            ("", "\n"),
            ("class:picker.hint", _HELP_LINES[1]),
            ("", "\n"),
            ("class:picker.hint", _HELP_LINES[2]),
        ]

    def test_help_lines_are_ordered_by_non_decreasing_width(self) -> None:
        # the layout slices a leading block that must fit the column budget
        widths = [get_cwidth(line) for line in _HELP_LINES]
        assert widths == sorted(widths)


class NarrowOutput(DummyOutput):
    """A DummyOutput that reports a small terminal size (rows, columns)."""

    def __init__(self, rows: int = 8, columns: int = 30) -> None:
        self._size = Size(rows=rows, columns=columns)

    def get_size(self) -> Size:
        return self._size


def _pick(catalog, keys: str, output: Output | None = None) -> str | None:
    """Drive the full TUI through a pipe input; DummyOutput swallows rendering."""
    with create_pipe_input() as pipe:
        pipe.send_text(keys)
        return run_picker(catalog, input=pipe, output=output or DummyOutput())


class TestRunPicker:
    def test_enter_returns_latest(self) -> None:
        assert _pick(CATALOG, "\r") == "1.21.4"

    def test_down_arrow_then_enter_selects_second(self) -> None:
        assert _pick(CATALOG, "\x1b[B\r") == "1.21.3"

    def test_down_twice_then_enter_selects_third(self) -> None:
        assert _pick(CATALOG, "\x1b[B\x1b[B\r") == "1.20.4"

    def test_search_filters_within_current_channel(self) -> None:
        assert _pick(CATALOG, "1.20\r") == "1.20.4"

    def test_search_requires_channel_switch_for_snapshot_ids(self) -> None:
        # "b1.7.3" is a snapshot, absent from the release list: a scoped search
        # finds nothing (Enter falls back to None), but toggling first with 't'
        # (empty search) switches to snapshots where it matches.
        assert _pick(CATALOG, "b1.7\r") is None
        assert _pick(CATALOG, "tb1.7\r") == "b1.7.3"

    def test_right_arrow_pages_down_one_viewport(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        # 10-row viewport: → moves the highlight a full page down.
        assert _pick(catalog, "\x1b[C\r") == "1.20"

    def test_left_arrow_pages_back_up(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        assert _pick(catalog, "\x1b[C\x1b[D\r") == "1.30"

    def test_left_right_arrows_edit_the_search_box_while_typing(self) -> None:
        # with a query the arrows move the text cursor instead of paging:
        # → must not page (which would select "1.20"), it just leaves the
        # first filtered hit highlighted.
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(30, 0, -1))
        assert _pick(catalog, "1.2\x1b[C\r") == "1.29"

    def test_toggle_then_enter_selects_first_snapshot(self) -> None:
        assert _pick(CATALOG, "t\r") == "25w14a"

    def test_escape_returns_none(self) -> None:
        assert _pick(CATALOG, "\x1b") is None

    def test_narrow_window_arrows_select_correct_row(self) -> None:
        # 8x30 terminal → 3-row viewport + 1 help line. Six releases so the
        # channel outgrows the viewport; 3rd row down = index 3.
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(6, 0, -1))
        assert _pick(catalog, "\x1b[B\x1b[B\x1b[B\r", output=NarrowOutput()) == "1.3"

    def test_narrow_window_scrolls_past_viewport(self) -> None:
        # 4th down takes index 4 > viewport 3, so the window scrolls down by one.
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(6, 0, -1))
        assert _pick(catalog, "\x1b[B\x1b[B\x1b[B\x1b[B\r", output=NarrowOutput()) == "1.2"

    def test_narrow_window_search_still_works(self) -> None:
        catalog = tuple(VersionEntry(f"1.{i}", "release") for i in range(6, 0, -1))
        assert _pick(catalog, "1.4\r", output=NarrowOutput()) == "1.4"

    def test_narrow_window_escape_returns_none(self) -> None:
        assert _pick(CATALOG, "\x1b", output=NarrowOutput()) is None
