# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

"""Targeted UI behavior for Notebook Injector CUSTOM entries.

EA automatically places a subcategory's ``has_list_text`` or ``no_list_text``
outside the authored entry rows. CUSTOM entries may contain a semantic title,
free text, ingredients and a footer, so this module rebuilds their
EXPANDABLE_DATA rows in the intended order and suppresses EA's automatic copies
for that entry.

Every non-CUSTOM notebook entry keeps EA's original behavior.
"""

from notebook.notebook_entry import EntryData
from notebook.notebook_tracker import NotebookTrackerSimInfo
from sims4.localization import _create_localized_string
from typing import Any, Tuple, cast
from ui.notebook_tuning import NotebookTuning

import notebook_injector.entry as entry_module
from notebook_injector.custom_entry_tuning import (
    CUSTOM_BOLD_UNDERLINE_FORMAT_STRING_ID,
    CUSTOM_ENTRY_KIND_VALUE,
    CUSTOM_EXPANDABLE_FORMAT_VALUE,
    CUSTOM_FOOTER_FORMAT_STRING_ID,
    CUSTOM_FOOTER_SPACED_FORMAT_STRING_ID,
    CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE,
    CUSTOM_LIST_TITLE_FORMAT_STRING_ID,
    CUSTOM_LIST_TITLE_SPACED_FORMAT_STRING_ID,
    CUSTOM_TITLE_BODY_FORMAT_STRING_ID
)
from notebook_injector.log import NotebookInjectorLog


_NotebookInjectorEntry = cast(
    Any,
    entry_module.NotebookInjectorEntry
)
_NotebookTuning = cast(
    Any,
    NotebookTuning
)
_CUSTOM_ENTRY_DATA_MARKER = (
    '_notebook_injector_has_list_text_moved'
)


class NotebookInjectorCustomEntryData(EntryData):
    """EntryData marker used by the targeted notebook tracker UI patch."""

    __slots__ = ()
    _notebook_injector_has_list_text_moved = True


class _EntryListTextsWithoutAutomaticTexts:
    """Delegate every field except EA's automatic list texts."""

    __slots__ = ('_original',)

    def __init__(self, original) -> None:
        self._original = original

    @property
    def has_list_text(self):
        return None

    @property
    def no_list_text(self):
        return None

    def __getattr__(self, name: str):
        return getattr(
            self._original,
            name
        )


class _SubcategoryTuningWithoutAutomaticListTexts:
    """Delegate subcategory tuning while replacing both automatic list texts."""

    __slots__ = (
        '_original',
        'entry_list_texts'
    )

    def __init__(self, original) -> None:
        self._original = original
        self.entry_list_texts = (
            _EntryListTextsWithoutAutomaticTexts(
                original.entry_list_texts
            )
        )

    def __getattr__(self, name: str):
        return getattr(
            self._original,
            name
        )


def _entry_kind_value(owner) -> Any:
    entry_kind = getattr(
        owner,
        'entry_kind',
        None
    )
    return getattr(
        entry_kind,
        'value',
        entry_kind
    )


def _is_custom_entry(owner) -> bool:
    return (
        _entry_kind_value(
            owner
        )
        == CUSTOM_ENTRY_KIND_VALUE
    )


def _format_value(value) -> Any:
    return getattr(
        value,
        'value',
        value
    )


def _subcategory_tuning(entry):
    category_id = _NotebookTuning.get_category_id(
        entry.subcategory_id
    )
    category_tuning = (
        _NotebookTuning
        .NOTEBOOK_CATEGORY_MAPPING[
            category_id
        ]
    )
    return category_tuning.subcategories[
        entry.subcategory_id
    ]


def _format_localized_text(
    format_string_id: int,
    *localized_texts
):
    """Build one localized wrapper from one or more localized string tokens."""
    if (
        not localized_texts
        or any(
            localized_text is None
            for localized_text in localized_texts
        )
    ):
        return None

    return _create_localized_string(
        format_string_id,
        *localized_texts
    )


def _bold_underline_text(localized_text):
    return _format_localized_text(
        CUSTOM_BOLD_UNDERLINE_FORMAT_STRING_ID,
        localized_text
    )


def _title_and_body_text(
    title,
    body
):
    return _format_localized_text(
        CUSTOM_TITLE_BODY_FORMAT_STRING_ID,
        title,
        body
    )


def _list_title_text(
    localized_text,
    add_spacing: bool
):
    format_string_id = (
        CUSTOM_LIST_TITLE_SPACED_FORMAT_STRING_ID
        if add_spacing is True
        else CUSTOM_LIST_TITLE_FORMAT_STRING_ID
    )
    return _format_localized_text(
        format_string_id,
        localized_text
    )


def _footer_text(
    localized_text,
    add_spacing: bool
):
    format_string_id = (
        CUSTOM_FOOTER_SPACED_FORMAT_STRING_ID
        if add_spacing is True
        else CUSTOM_FOOTER_FORMAT_STRING_ID
    )
    return _format_localized_text(
        format_string_id,
        localized_text
    )


def _custom_entry_data(
    entry_data,
    entry_sublist
) -> NotebookInjectorCustomEntryData:
    return NotebookInjectorCustomEntryData(
        entry_text=entry_data.entry_text,
        entry_text_description=(
            entry_data.entry_text_description
        ),
        entry_icon_info_data=(
            entry_data.entry_icon_info_data
        ),
        entry_tooltip=entry_data.entry_tooltip,
        entry_sublist=tuple(
            entry_sublist
        ),
        entry_sublist_is_sortable=(
            entry_data.entry_sublist_is_sortable
        )
    )


def _resolve_subcategory_list_text(
    entry,
    field_name: str
):
    """Resolve one automatic list text from the assigned subcategory."""
    try:
        list_texts = (
            _subcategory_tuning(
                entry
            )
            .entry_list_texts
        )
        return getattr(
            list_texts,
            field_name,
            None
        )
    except Exception:
        NotebookInjectorLog.logger().exception(
            'Failed to resolve {} for CUSTOM entry {}. '
            'The related semantic row will be omitted.'.format(
                field_name,
                getattr(
                    entry.__class__,
                    'guid64',
                    'unknown'
                )
            )
        )
        return None


def _resolve_ingredients_title(
    entry,
    content
):
    custom_title = getattr(
        content,
        'ingredients_title',
        None
    )
    if custom_title is not None:
        return custom_title

    return _resolve_subcategory_list_text(
        entry,
        'has_list_text'
    )


def _resolve_no_list_text(entry):
    return _resolve_subcategory_list_text(
        entry,
        'no_list_text'
    )


def _build_semantic_expandable_data(
    entry,
    entry_data,
    ingredient_cache
) -> NotebookInjectorCustomEntryData:
    """Build CUSTOM rows in semantic display order with fixed core styles."""
    rows = []
    entry_class = entry.__class__

    if entry_class.entry_text_description is not None:
        rows.append(
            entry_class._text_row(
                entry_class.entry_text_description
            )
        )

    content = cast(
        Any,
        getattr(
            entry_class,
            'content',
            None
        )
    )
    ingredients = cast(
        Tuple[Any, ...],
        tuple(
            getattr(
                content,
                'ingredients',
                ()
            ) or ()
        )
    )

    if content is not None:
        title = getattr(
            content,
            'title',
            None
        )
        text_blocks = tuple(
            getattr(
                content,
                'text_blocks',
                ()
            ) or ()
        )

        if title is not None and text_blocks:
            rows.append(
                entry_class._text_row(
                    _title_and_body_text(
                        title,
                        text_blocks[0]
                    )
                )
            )
            text_blocks = text_blocks[1:]
        elif title is not None:
            rows.append(
                entry_class._text_row(
                    _bold_underline_text(
                        title
                    )
                )
            )

        for text in text_blocks:
            rows.append(
                entry_class._text_row(
                    text
                )
            )

    if ingredients:
        ingredients_title = _resolve_ingredients_title(
            entry,
            content
        )
        if ingredients_title is not None:
            rows.append(
                entry_class._text_row(
                    _list_title_text(
                        ingredients_title,
                        bool(
                            rows
                        )
                    )
                )
            )

        display_counts = (
            getattr(
                content,
                'display_ingredient_counts',
                False
            )
            is True
        )
        for ingredient in ingredients:
            rows.append(
                entry_class._ingredient_row(
                    ingredient,
                    ingredient_cache,
                    display_counts
                )
            )
    else:
        no_list_text = _resolve_no_list_text(
            entry
        )
        if no_list_text is not None:
            rows.append(
                entry_class._text_row(
                    _list_title_text(
                        no_list_text,
                        bool(
                            rows
                        )
                    )
                )
            )

    footer = getattr(
        content,
        'footer',
        None
    )
    if footer is not None:
        rows.append(
            entry_class._text_row(
                _footer_text(
                    footer,
                    bool(
                        rows
                    )
                )
            )
        )

    return _custom_entry_data(
        entry_data,
        rows
    )


def install_custom_entry_ui_extension() -> None:
    """Install CUSTOM-only validation, semantic rows and tracker UI patches."""
    if getattr(
        _NotebookInjectorEntry,
        '_NOTEBOOK_INJECTOR_CUSTOM_UI_INSTALLED',
        False
    ) is True:
        return

    validate_descriptor = vars(
        _NotebookInjectorEntry
    )['validate_subcategory_format']
    original_validate_subcategory_format = (
        validate_descriptor.__func__
    )
    original_get_definition_notebook_data = vars(
        _NotebookInjectorEntry
    )['get_definition_notebook_data']
    original_fill_notebook_entry_data = vars(
        NotebookTrackerSimInfo
    )['_fill_notebook_entry_data']

    @classmethod
    def patched_validate_subcategory_format(
        cls,
        format_value: int
    ) -> tuple:
        errors = list(
            original_validate_subcategory_format(
                cls,
                format_value
            )
        )

        if (
            _is_custom_entry(
                cls
            ) is True
            and _format_value(
                format_value
            ) == CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
            and cls.entry_text_description is not None
        ):
            errors.append(
                'CUSTOM assigned to ICON_DESCRIPTION_DATA does not allow '
                'entry_text_description because EA does not display it in '
                'this layout. Use custom_tooltip instead.'
            )

        return tuple(
            errors
        )

    def patched_get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        entry_data = original_get_definition_notebook_data(
            self,
            ingredient_cache
        )

        if (
            entry_data is None
            or _is_custom_entry(
                self
            ) is False
        ):
            return entry_data

        format_value = _format_value(
            self._get_custom_format_value()
        )

        if format_value == CUSTOM_EXPANDABLE_FORMAT_VALUE:
            return _build_semantic_expandable_data(
                self,
                entry_data,
                ingredient_cache
            )

        if format_value == CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE:
            # Defensive runtime fallback. Validation normally rejects the field,
            # but no invisible description is ever sent to the EA UI.
            return EntryData(
                entry_text=entry_data.entry_text,
                entry_text_description=None,
                entry_icon_info_data=(
                    entry_data.entry_icon_info_data
                ),
                entry_tooltip=entry_data.entry_tooltip,
                entry_sublist=entry_data.entry_sublist,
                entry_sublist_is_sortable=(
                    entry_data.entry_sublist_is_sortable
                )
            )

        return entry_data

    def patched_fill_notebook_entry_data(
        self,
        notebook_subcategory_message,
        subcategory_tuning,
        entry,
        entry_def_id,
        definition_based,
        new_entry
    ):
        if getattr(
            entry,
            _CUSTOM_ENTRY_DATA_MARKER,
            False
        ) is True:
            subcategory_tuning = (
                _SubcategoryTuningWithoutAutomaticListTexts(
                    subcategory_tuning
                )
            )

        return original_fill_notebook_entry_data(
            self,
            notebook_subcategory_message,
            subcategory_tuning,
            entry,
            entry_def_id,
            definition_based,
            new_entry
        )

    _NotebookInjectorEntry.validate_subcategory_format = (
        patched_validate_subcategory_format
    )
    _NotebookInjectorEntry.get_definition_notebook_data = (
        patched_get_definition_notebook_data
    )
    NotebookTrackerSimInfo._fill_notebook_entry_data = (
        patched_fill_notebook_entry_data
    )
    _NotebookInjectorEntry._NOTEBOOK_INJECTOR_CUSTOM_UI_INSTALLED = True
