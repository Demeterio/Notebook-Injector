# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from objects.hovertip import HovertipStyle
from typing import Any, TYPE_CHECKING, cast

from notebook_injector.custom_entry_tuning import (
    CUSTOM_ENTRY_KIND_VALUE,
    CUSTOM_EXPANDABLE_FORMAT_VALUE,
    CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
)


_CUSTOM_TOOLTIP_FIELDS = (
    'header',
    'title',
    'subtitle',
    'accent_primary',
    'accent_secondary',
    'accent_tertiary',
    'subtext',
    'footer'
)


class NotebookInjectorCustomValidationMixin:
    """Validate the flat CUSTOM XML contract and its target EA UI format."""

    if TYPE_CHECKING:
        entry_kind: Any
        entry_text: Any
        entry_text_description: Any
        entry_icon: Any
        entry_sublist: Any
        entry_sublist_sortable: bool
        entry_sublist_include_new: bool
        tooltip_fields: Any
        tooltip_style: Any
        content: Any
        custom_tooltip: Any
        bait_fish_definition: Any
        bait_snippets: Any
        entry_text_rarity: Any
        entry_text_size_mapping: Any

    @classmethod
    def _has_custom_content(cls) -> bool:
        """Return True when the flat content block contains display rows."""
        content = getattr(
            cls,
            'content',
            None
        )
        return (
            content is not None
            and (
                getattr(
                    content,
                    'title',
                    None
                ) is not None
                or bool(
                    content.text_blocks
                )
                or getattr(
                    content,
                    'ingredients_title',
                    None
                ) is not None
                or bool(
                    content.ingredients
                )
                or getattr(
                    content,
                    'footer',
                    None
                ) is not None
            )
        )

    @classmethod
    def _has_custom_tooltip(cls) -> bool:
        """Return True when at least one flat CUSTOM tooltip field is tuned."""
        tooltip = getattr(
            cls,
            'custom_tooltip',
            None
        )
        if tooltip is None:
            return False

        return any(
            getattr(
                tooltip,
                field_name,
                None
            ) is not None
            for field_name in _CUSTOM_TOOLTIP_FIELDS
        )

    @classmethod
    def _validate_forbidden_fields(
        cls,
        errors: list
    ) -> None:
        forbidden = []

        if cls.bait_fish_definition is not None:
            forbidden.append(
                'bait_fish_definition'
            )
        if cls.bait_snippets:
            forbidden.append(
                'bait_snippets'
            )
        if cls.entry_text_rarity is not None:
            forbidden.append(
                'entry_text_rarity'
            )
        if cls.entry_text_size_mapping:
            forbidden.append(
                'entry_text_size_mapping'
            )
        if cls.entry_sublist:
            forbidden.append(
                'entry_sublist'
            )
        if (
            cast(
                Any,
                cls
            )._has_tuned_tooltip_fields() is True
        ):
            forbidden.append(
                'tooltip_fields'
            )
        if (
            cls.tooltip_style
            != HovertipStyle.HOVER_TIP_DEFAULT
        ):
            forbidden.append(
                'tooltip_style'
            )

        if forbidden:
            errors.append(
                'CUSTOM does not allow the following fields: {}.'
                .format(
                    ', '.join(
                        forbidden
                    )
                )
            )

    @classmethod
    def _validate_content(
        cls,
        errors: list
    ) -> None:
        """Validate authored rows in the flat semantic content tuple."""
        if cls._has_custom_content() is False:
            return

        content = cls.content
        ingredients = tuple(
            content.ingredients or ()
        )

        if (
            getattr(
                content,
                'ingredients_title',
                None
            ) is not None
            and not ingredients
        ):
            errors.append(
                'content.ingredients_title requires at least one '
                'content.ingredients item.'
            )

        for index, text in enumerate(
            content.text_blocks
        ):
            if text is None:
                errors.append(
                    'content text_blocks item {} requires localized text.'
                    .format(
                        index
                    )
                )

        for index, ingredient in enumerate(
            ingredients
        ):
            if ingredient.object_definition is None:
                errors.append(
                    'content ingredient {} requires an available '
                    'object_definition.'.format(
                        index
                    )
                )

            required_count = ingredient.required_count
            if (
                isinstance(
                    required_count,
                    bool
                )
                or not isinstance(
                    required_count,
                    int
                )
                or required_count < 1
            ):
                errors.append(
                    'content ingredient {} requires required_count >= 1.'
                    .format(
                        index
                    )
                )

    @classmethod
    def _validate_custom_tooltip(
        cls,
        errors: list
    ) -> None:
        """Require at least one field only when custom_tooltip is present."""
        tooltip = getattr(
            cls,
            'custom_tooltip',
            None
        )
        if tooltip is None:
            return

        if cls._has_custom_tooltip() is False:
            errors.append(
                'custom_tooltip requires at least one tuned field: {}.'
                .format(
                    ', '.join(
                        _CUSTOM_TOOLTIP_FIELDS
                    )
                )
            )

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate fields that do not depend on the target subcategory."""
        entry_kind_value = getattr(
            cls.entry_kind,
            'value',
            cls.entry_kind
        )
        if entry_kind_value != CUSTOM_ENTRY_KIND_VALUE:
            return (
                '{} only supports entry_kind CUSTOM.'.format(
                    cls.__name__
                ),
            )

        errors = []

        if cls.entry_text is None:
            errors.append(
                'entry_text is required for entry_kind CUSTOM.'
            )

        if cls.entry_sublist_sortable is True:
            errors.append(
                'entry_sublist_sortable must be False for entry_kind CUSTOM.'
            )

        if cls.entry_sublist_include_new is True:
            errors.append(
                'entry_sublist_include_new must be False for entry_kind CUSTOM.'
            )

        cls._validate_forbidden_fields(
            errors
        )
        cls._validate_content(
            errors
        )
        cls._validate_custom_tooltip(
            errors
        )

        return tuple(
            errors
        )

    @classmethod
    def supports_subcategory_format(
        cls,
        format_value: int
    ) -> bool:
        """CUSTOM supports only EA expandable and icon-description layouts."""
        return format_value in (
            CUSTOM_EXPANDABLE_FORMAT_VALUE,
            CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
        )

    @classmethod
    def validate_subcategory_format(
        cls,
        format_value: int
    ) -> tuple:
        """Validate fields whose meaning depends on the target UI layout."""
        errors = []

        if format_value == CUSTOM_EXPANDABLE_FORMAT_VALUE:
            if (
                cls.entry_text_description is None
                and cls._has_custom_content() is False
            ):
                errors.append(
                    'CUSTOM assigned to EXPANDABLE_DATA requires '
                    'entry_text_description or content with title, text_blocks, '
                    'ingredients or footer.'
                )

        elif (
            format_value
            == CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE
        ):
            if cls._has_custom_content() is True:
                errors.append(
                    'CUSTOM assigned to ICON_DESCRIPTION_DATA does not allow '
                    'content because EA does not display an entry sublist in '
                    'this layout.'
                )

        return tuple(
            errors
        )
