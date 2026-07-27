# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from notebook.notebook_entry import (
    EntryData,
    EntryTooltip,
    SubListData
)
from objects.hovertip import (
    HovertipStyle,
    TooltipFields
)
from sims4.localization import LocalizationHelperTuning
from typing import Any, TYPE_CHECKING, cast
from ui.notebook_tuning import NotebookTuning
import sims4.hash_util

from notebook_injector.custom_entry_tuning import (
    CUSTOM_EXPANDABLE_FORMAT_VALUE,
    CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
)
from notebook_injector.log import NotebookInjectorLog


_NotebookTuning = cast(
    Any,
    NotebookTuning
)

_CUSTOM_ENTRY_RUNTIME_ID_MAX = (1 << 32) - 1
_CUSTOM_ENTRY_RUNTIME_ID_NAMESPACE = (
    'demeterio.notebook_injector.custom_entry'
)


def normalize_custom_entry_runtime_id(value: int) -> int:
    """
    Return a stable non-zero uint32 accepted by EA's notebook UI protobuf.

    EA normally sends an Object Definition ID through NotebookEntryMessage.entry_id,
    which is a uint32. CUSTOM entries are static and do not own a real object
    definition, so oversized tuning-derived IDs are converted with EA's hash32.

    Values already inside the uint32 range are preserved. This makes migration of
    previously saved CUSTOM entries idempotent instead of hashing them again on
    every load.
    """
    if (
        isinstance(
            value,
            bool
        )
        or not isinstance(
            value,
            int
        )
    ):
        raise TypeError(
            'CUSTOM entry runtime ID must be an integer.'
        )

    if value < 0:
        raise ValueError(
            'CUSTOM entry runtime ID cannot be negative.'
        )

    if 0 < value <= _CUSTOM_ENTRY_RUNTIME_ID_MAX:
        return value

    hash_source = '{}:{:016X}'.format(
        _CUSTOM_ENTRY_RUNTIME_ID_NAMESPACE,
        value
    )
    normalized_value = (
        sims4.hash_util.hash32(
            hash_source
        )
        & _CUSTOM_ENTRY_RUNTIME_ID_MAX
    )

    if normalized_value == 0:
        normalized_value = (
            sims4.hash_util.hash32(
                '{}:fallback'.format(
                    hash_source
                )
            )
            & _CUSTOM_ENTRY_RUNTIME_ID_MAX
        )

    if normalized_value == 0:
        raise ValueError(
            'Unable to generate a non-zero CUSTOM entry runtime ID.'
        )

    return normalized_value


class NotebookInjectorCustomRuntimeMixin:
    """Build a static CUSTOM entry using EA's two supported UI layouts."""

    if TYPE_CHECKING:
        guid64: Any
        entry_object_definition_id: Any
        entry_text: Any
        entry_text_description: Any
        entry_icon_info_data: Any
        entry_sublist: Any
        entry_sublist_is_sortable: Any
        entry_tooltip: Any
        content: Any
        custom_tooltip: Any
        subcategory_id: Any
        _runtime_prepare_error: Any

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs
        )

        runtime_source_id = (
            self.entry_object_definition_id
        )

        if not runtime_source_id:
            runtime_source_id = (
                self.__class__.guid64
            )

        self.entry_object_definition_id = (
            normalize_custom_entry_runtime_id(
                runtime_source_id
            )
        )

    @classmethod
    def supports_reference_unlock(cls) -> bool:
        """CUSTOM entries are fully static and support create_new_entry."""
        return True

    @classmethod
    def uses_fallback_icon(cls) -> bool:
        """Use Notebook Injector's fallback icon when entry_icon is omitted."""
        return True

    @classmethod
    def prepare_runtime_data(cls) -> None:
        """Keep runtime fields clean; EntryData is built when the notebook opens."""
        cls._runtime_prepare_error = None
        cls.entry_sublist = ()
        cls.entry_tooltip = None
        cls.entry_sublist_is_sortable = None

    def is_definition_based(self) -> bool:
        """Use EA's definition-data path to receive the current ingredient cache."""
        return True

    def _get_custom_format_value(self):
        """Resolve the format from the assigned EA subcategory tuning."""
        try:
            category_id = _NotebookTuning.get_category_id(
                self.subcategory_id
            )
            category_tuning = (
                _NotebookTuning
                .NOTEBOOK_CATEGORY_MAPPING[
                    category_id
                ]
            )
            format_type = category_tuning.subcategories[
                self.subcategory_id
            ].format_type
            return int(
                getattr(
                    format_type,
                    'value',
                    format_type
                )
            )
        except Exception:
            NotebookInjectorLog.logger().exception(
                'Failed to resolve the subcategory format for CUSTOM entry {}.'
                .format(
                    getattr(
                        self.__class__,
                        'guid64',
                        'unknown'
                    )
                )
            )
            return None

    @classmethod
    def _build_custom_tooltip(cls):
        """Map the flat public tooltip names to EA TooltipFields."""
        tooltip = cls.custom_tooltip
        if tooltip is None:
            return None

        bindings = (
            ('header', TooltipFields.header),
            ('title', TooltipFields.recipe_name),
            ('subtitle', TooltipFields.header_subtext),
            ('accent_primary', TooltipFields.rarity_text),
            (
                'accent_secondary',
                TooltipFields.simoleon_custom_text
            ),
            ('accent_tertiary', TooltipFields.crafted_by_text),
            ('subtext', TooltipFields.subtext),
            ('footer', TooltipFields.footer_text)
        )
        fields = {}

        for public_name, tooltip_field in bindings:
            value = getattr(
                tooltip,
                public_name,
                None
            )
            if value is not None:
                fields[
                    tooltip_field
                ] = value

        if not fields:
            return None

        return EntryTooltip(
            HovertipStyle.HOVER_TIP_DEFAULT,
            fields
        )

    @staticmethod
    def _text_row(text) -> SubListData:
        """Build one EA sublist row containing localized text only."""
        return SubListData(
            object_definition=None,
            item_count=0,
            num_objects_required=0,
            is_ingredient=True,
            new_item=False,
            object_display_name=text,
            item_icon_info_data=None,
            item_tooltip=None
        )

    @staticmethod
    def _definition_count(
        ingredient_cache,
        definition
    ) -> int:
        """Count matching object stacks in EA's current ingredient cache."""
        definition_id = getattr(
            definition,
            'id',
            None
        )
        if definition_id is None:
            return 0

        total = 0
        for ingredient in ingredient_cache or ():
            ingredient_definition = getattr(
                ingredient,
                'definition',
                None
            )
            if getattr(
                ingredient_definition,
                'id',
                None
            ) != definition_id:
                continue

            stack_count = getattr(
                ingredient,
                'stack_count',
                None
            )
            if callable(stack_count):
                try:
                    current_count = stack_count()
                except Exception:
                    current_count = 1
            else:
                current_count = 1

            if (
                isinstance(
                    current_count,
                    bool
                )
                or not isinstance(
                    current_count,
                    int
                )
                or current_count < 1
            ):
                current_count = 1

            total += current_count

        return total

    @classmethod
    def _ingredient_row(
        cls,
        ingredient,
        ingredient_cache,
        display_counts: bool
    ) -> SubListData:
        """Build one ingredient row, optionally with a current/required count."""
        definition = ingredient.object_definition
        required_count = (
            ingredient.required_count
            if display_counts is True
            else 0
        )
        current_count = (
            cls._definition_count(
                ingredient_cache,
                definition
            )
            if display_counts is True
            else 0
        )

        return SubListData(
            object_definition=None,
            item_count=current_count,
            num_objects_required=required_count,
            is_ingredient=True,
            new_item=False,
            object_display_name=(
                LocalizationHelperTuning
                .get_object_name(
                    definition
                )
            ),
            item_icon_info_data=None,
            item_tooltip=None
        )

    @classmethod
    def _build_expandable_rows(
        cls,
        ingredient_cache
    ) -> tuple:
        """Build description, free-text and ingredient rows in a fixed order."""
        rows = []

        if cls.entry_text_description is not None:
            rows.append(
                cls._text_row(
                    cls.entry_text_description
                )
            )

        content = cls.content
        if content is None:
            return tuple(
                rows
            )

        for text in content.text_blocks:
            rows.append(
                cls._text_row(
                    text
                )
            )

        display_counts = (
            content.display_ingredient_counts
            is True
        )
        for ingredient in content.ingredients:
            rows.append(
                cls._ingredient_row(
                    ingredient,
                    ingredient_cache,
                    display_counts
                )
            )

        return tuple(
            rows
        )

    def get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Build the EA EntryData matching the assigned subcategory format."""
        format_value = self._get_custom_format_value()

        if format_value == CUSTOM_EXPANDABLE_FORMAT_VALUE:
            entry_description = None
            entry_sublist = self.__class__._build_expandable_rows(
                ingredient_cache
            )
        elif (
            format_value
            == CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
        ):
            entry_description = self.entry_text_description
            entry_sublist = ()
        else:
            NotebookInjectorLog.logger().error(
                'CUSTOM entry {} has unsupported subcategory format value {}.'
                .format(
                    getattr(
                        self.__class__,
                        'guid64',
                        'unknown'
                    ),
                    format_value
                )
            )
            return None

        return EntryData(
            entry_text=self.entry_text,
            entry_text_description=entry_description,
            entry_icon_info_data=self.entry_icon_info_data,
            entry_tooltip=(
                self.__class__
                ._build_custom_tooltip()
            ),
            entry_sublist=entry_sublist,
            entry_sublist_is_sortable=None
        )