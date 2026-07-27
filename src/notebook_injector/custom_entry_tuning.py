# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import services
from sims4.localization import TunableLocalizedString
from sims4.tuning.tunable import (
    Tunable,
    TunableList,
    TunableRange,
    TunableReference,
    TunableTuple
)
from typing import Any, cast


_Services = cast(Any, services)
_TunableLocalizedString = cast(
    Any,
    TunableLocalizedString
)
_TunableTuple = cast(
    Any,
    TunableTuple
)

CUSTOM_ENTRY_KIND_VALUE = 7
CUSTOM_EXPANDABLE_FORMAT_VALUE = 0
CUSTOM_ICON_DESCRIPTION_FORMAT_VALUE = 2

# FNV32 keys reserved by Notebook Injector's core STBL resources.
# Their values are language-neutral formatting wrappers:
#   0x55A33FED = <b>{0.String}</b>
#   0xEF518C04 = <i>{0.String}</i>
#   0xA15BA8C7 = <b><u>{0.String}</u></b>
#   0xD7EEA97E = <b><u>{0.String}</u></b>\n\n{1.String}
#   0x0D6F22CA = <p align="center"><i>◆ {0.String} ◆</i></p>
#   0xC4CFC82C = \n<p align="center"><i>◆ {0.String} ◆</i></p>
#   0xE9225271 = <p align="center">◇ {0.String} ◇</p>
#   0xC4599FCB = \n<p align="center">◇ {0.String} ◇</p>
CUSTOM_BOLD_FORMAT_STRING_ID = 0x55A33FED
CUSTOM_ITALIC_FORMAT_STRING_ID = 0xEF518C04
CUSTOM_BOLD_UNDERLINE_FORMAT_STRING_ID = 0xA15BA8C7
CUSTOM_TITLE_BODY_FORMAT_STRING_ID = 0xD7EEA97E
CUSTOM_LIST_TITLE_FORMAT_STRING_ID = 0x0D6F22CA
CUSTOM_LIST_TITLE_SPACED_FORMAT_STRING_ID = 0xC4CFC82C
CUSTOM_FOOTER_FORMAT_STRING_ID = 0xE9225271
CUSTOM_FOOTER_SPACED_FORMAT_STRING_ID = 0xC4599FCB


class _OptionalFlatTunableTuple(TunableTuple):
    """
    Flat TunableTuple whose omitted XML value is None.

    Native TunableTuple always creates its default immutable tuple, even when the
    XML block is absent. This subclass preserves the flat <U n="..."> contract
    while allowing validation to distinguish an omitted block from a present but
    empty block.
    """

    __slots__ = ()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            **kwargs
        )
        self._default = None

    def load_etree_node(
        self,
        node,
        source,
        expect_error
    ):
        if node is None:
            return None

        return super().load_etree_node(
            node,
            source,
            expect_error
        )


def _optional_localized_string(
    description: str
):
    return _TunableLocalizedString(
        description=description,
        default=None,
        allow_none=True
    )


def _custom_tooltip_tunable():
    """
    Return the optional flat CUSTOM tooltip block.

    Omitting the <U n="custom_tooltip"> block returns None and disables the
    tooltip. When the block is present, validation requires at least one localized
    field, but no individual field, including title, is mandatory.
    """
    return _OptionalFlatTunableTuple(
        header=_optional_localized_string(
            'Optional small text displayed above the tooltip title.'
        ),
        title=_optional_localized_string(
            'Optional main tooltip title.'
        ),
        subtitle=_optional_localized_string(
            'Optional subtitle displayed near the tooltip title.'
        ),
        accent_primary=_optional_localized_string(
            'Optional first emphasized tooltip line.'
        ),
        accent_secondary=_optional_localized_string(
            'Optional second emphasized tooltip line.'
        ),
        accent_tertiary=_optional_localized_string(
            'Optional third emphasized tooltip line.'
        ),
        subtext=_optional_localized_string(
            'Optional text displayed in the lower tooltip section.'
        ),
        footer=_optional_localized_string(
            'Optional footer text displayed at the bottom of the tooltip.'
        ),
        description=(
            'Optional flat HOVER_TIP_DEFAULT layout for CUSTOM entries. Omit '
            'the entire custom_tooltip block to disable the tooltip. When the '
            'block is present, tune at least one field. Every field is '
            'independent and title is not required. Only explicitly tuned '
            'fields are sent to EA.'
        )
    )


def _custom_content_tunable():
    """
    Return the intentionally flat expandable-content block.

    The tuple is considered disabled when every semantic text field and both
    lists are empty. This keeps the XML to one content block without an extra
    enabled/disabled nesting level.
    """
    return _TunableTuple(
        title=_optional_localized_string(
            'Optional section title displayed in bold and underlined. When at '
            'least one text_blocks item exists, the title is merged with the '
            'first text block and separated from it by one blank line.'
        ),
        text_blocks=TunableList(
            description=(
                'Optional localized text rows displayed after the semantic '
                'title and entry_text_description. The first row shares the '
                'title row when title is tuned. Rich-text markup supported by '
                'the game may be authored directly in the STBL values.'
            ),
            tunable=_TunableLocalizedString(
                description='Localized text displayed as one expanded row.',
                default=None,
                allow_none=True
            )
        ),
        ingredients_title=_optional_localized_string(
            'Optional centered italic heading displayed immediately before '
            'ingredients and decorated with solid diamonds. When omitted, the '
            'subcategory has_list_text is used.'
        ),
        display_ingredient_counts=Tunable(
            description=(
                'If True, ingredient rows display the current inventory '
                'quantity and required quantity, such as 0/1.'
            ),
            tunable_type=bool,
            default=True
        ),
        ingredients=TunableList(
            description=(
                'Optional ingredient rows displayed after ingredients_title.'
            ),
            tunable=_TunableTuple(
                object_definition=TunableReference(
                    _Services.definition_manager(),
                    description=(
                        'Object Definition whose localized name is displayed.'
                    ),
                    allow_none=True,
                    pack_safe=True
                ),
                required_count=TunableRange(
                    description=(
                        'Required quantity displayed when '
                        'display_ingredient_counts is True.'
                    ),
                    tunable_type=int,
                    default=1,
                    minimum=1
                )
            )
        ),
        footer=_optional_localized_string(
            'Optional centered footer displayed after all text and ingredient '
            'rows and decorated with hollow diamonds.'
        ),
        description=(
            'Optional expanded content. Omit the entire content block, or leave '
            'title, text_blocks, ingredients_title, ingredients and footer empty, '
            'to disable it. Display order: entry_text_description, title merged '
            'with the first text block when available, remaining text blocks, '
            'centered list text, ingredients, centered footer.'
        )
    )


CUSTOM_ENTRY_INSTANCE_TUNABLES = {
    'content': _custom_content_tunable(),
    'custom_tooltip': _custom_tooltip_tunable()
}
