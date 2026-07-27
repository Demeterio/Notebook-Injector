# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from notebook.notebook_entry import EntryTooltip
from objects.hovertip import (
    HovertipStyle,
    TooltipFields,
    TooltipFieldsComplete
)
from sims4.localization import (
    LocalizationHelperTuning,
    TunableLocalizedString
)
from sims4.tuning.tunable import TunableTuple
from typing import Any, cast

import notebook_injector.entry as entry_module


_NotebookInjectorEntry = cast(
    Any,
    entry_module.NotebookInjectorEntry
)
_NotebookInjectorEntryKind = cast(
    Any,
    entry_module.NotebookInjectorEntryKind
)
_TunableTuple = cast(Any, TunableTuple)
_TunableLocalizedString = cast(
    Any,
    TunableLocalizedString
)


def _optional_tooltip_text_tunable(
    field_name: str
):
    """
    Create one optional localized tooltip-text tunable.

    An omitted XML field resolves to None and is not sent to EA.
    Entry-kind validation decides whether the field is optional,
    required, or forbidden in that context.
    """
    return _TunableLocalizedString(
        description=(
            'Optional localized text sent to EA tooltip field {}. '
            'Whether this field is allowed or required depends on entry_kind.'
            .format(
                field_name
            )
        ),
        default=None,
        allow_none=True
    )


_TOOLTIP_FIELD_BINDINGS = (
    ('recipe_name', TooltipFields.recipe_name),
    ('recipe_description', TooltipFields.recipe_description),
    ('percentage_left', TooltipFields.percentage_left),
    ('style_name', TooltipFields.style_name),
    ('quality_description', TooltipFields.quality_description),
    ('header', TooltipFields.header),
    ('subtext', TooltipFields.subtext),
    ('crafted_by_text', TooltipFields.crafted_by_text),
    ('rarity_text', TooltipFields.rarity_text),
    ('simoleon_text', TooltipFields.simoleon_text),
    ('relic_description', TooltipFields.relic_description),
    ('season_text', TooltipFields.season_text),
    ('spoiled_time_text', TooltipFields.spoiled_time_text),
    ('simoleon_custom_text', TooltipFields.simoleon_custom_text),
    ('header_subtext', TooltipFields.header_subtext),
    ('header_status', TooltipFields.header_status),
    ('footer_text', TooltipFields.footer_text),
    ('active_seasons_text', TooltipFields.active_seasons_text)
)

_TOOLTIP_FIELD_BY_NAME = {
    field_name: tooltip_field
    for field_name, tooltip_field in _TOOLTIP_FIELD_BINDINGS
}

_TOOLTIP_FIELD_TUNABLES = {
    field_name: _optional_tooltip_text_tunable(
        field_name
    )
    for field_name, _ in _TOOLTIP_FIELD_BINDINGS
}

_ANIMAL_FEED_OPTIONAL_TOOLTIP_FIELD_NAMES = (
    'recipe_name',
    'recipe_description',
    'header'
)

_ANIMAL_FEED_REQUIRED_TOOLTIP_FIELD_NAMES = (
    'subtext',
    'rarity_text'
)

_ANIMAL_FEED_ALLOWED_TOOLTIP_FIELD_NAMES = (
    _ANIMAL_FEED_OPTIONAL_TOOLTIP_FIELD_NAMES
    + _ANIMAL_FEED_REQUIRED_TOOLTIP_FIELD_NAMES
)

_LEGACY_ANIMAL_FEED_TOOLTIP_TUNABLES = (
    'tooltip_title',
    'tooltip_description',
    'tooltip_header',
    'tooltip_subtext',
    'tooltip_rarity'
)


_FLAT_TOOLTIP_FIELDS_TUNABLE = _TunableTuple(
    description=(
        'Flat native EA tooltip fields. DEFAULT and COUNTRY_ITEM may use '
        'any exposed field and every field is optional. ANIMAL_FEED only '
        'allows recipe_name, recipe_description, header, subtext, and '
        'rarity_text; subtext and rarity_text are required. BAIT, RECIPE, '
        'GARDENING_PLANT, and CUSTOM do not accept this field because their '
        'display data is generated or configured through their dedicated API. '
        'Only XML fields explicitly tuned by the modder are sent to EA.'
    ),
    **_TOOLTIP_FIELD_TUNABLES
)


def _get_tuned_tooltip_fields(
    cls
) -> dict:
    """Return only explicitly authored fields, keyed by EA TooltipFields."""
    tuned_fields = getattr(
        cls,
        'tooltip_fields',
        None
    )

    if tuned_fields is None:
        return {}

    result = {}

    for field_name, tooltip_field in (
        _TOOLTIP_FIELD_BINDINGS
    ):
        localized_value = getattr(
            tuned_fields,
            field_name,
            None
        )

        if localized_value is None:
            continue

        result[
            tooltip_field
        ] = localized_value

    return result


def _has_tuned_tooltip_fields(
    cls
) -> bool:
    """Return True when at least one flat tooltip field is authored."""
    return bool(
        cls._get_tuned_tooltip_fields()
    )


def _validate_tooltip_fields(
    cls,
    errors: list
) -> None:
    """Validate the shared flat localized tooltip tuple."""
    tuned_fields = getattr(
        cls,
        'tooltip_fields',
        None
    )

    if tuned_fields is None:
        return

    missing_attributes = []

    for field_name, _ in _TOOLTIP_FIELD_BINDINGS:
        if not hasattr(
            tuned_fields,
            field_name
        ):
            missing_attributes.append(
                field_name
            )

    if missing_attributes:
        errors.append(
            'tooltip_fields has an invalid tuple structure. '
            'Missing fields: {}.'.format(
                ', '.join(
                    missing_attributes
                )
            )
        )
        return

    if (
        cls._has_tuned_tooltip_fields() is False
        and cls.tooltip_style
        != HovertipStyle.HOVER_TIP_DEFAULT
    ):
        errors.append(
            'tooltip_style has no effect because tooltip_fields '
            'contains no localized text.'
        )


def _validate_tooltip_field_policy(
    cls,
    errors: list,
    kind_name: str,
    allowed_field_names,
    required_field_names=()
) -> None:
    """
    Enforce the required, optional, and forbidden fields for one entry kind.

    Fields listed in allowed_field_names but not required_field_names are
    optional. Every other authored tooltip field is forbidden.
    """
    tuned_fields = getattr(
        cls,
        'tooltip_fields',
        None
    )

    if tuned_fields is None:
        tuned_field_names = set()
    else:
        tuned_field_names = {
            field_name
            for field_name, _ in _TOOLTIP_FIELD_BINDINGS
            if getattr(
                tuned_fields,
                field_name,
                None
            ) is not None
        }

    allowed_names = set(
        allowed_field_names
    )
    required_names = set(
        required_field_names
    )

    invalid_policy_names = (
        allowed_names
        | required_names
    ) - set(
        _TOOLTIP_FIELD_BY_NAME
    )

    if invalid_policy_names:
        errors.append(
            'Internal tooltip policy for entry_kind {} references unknown '
            'fields: {}.'.format(
                kind_name,
                ', '.join(
                    sorted(
                        invalid_policy_names
                    )
                )
            )
        )
        return

    required_not_allowed = (
        required_names
        - allowed_names
    )

    if required_not_allowed:
        errors.append(
            'Internal tooltip policy for entry_kind {} marks fields as '
            'required without allowing them: {}.'.format(
                kind_name,
                ', '.join(
                    sorted(
                        required_not_allowed
                    )
                )
            )
        )
        return

    forbidden_names = sorted(
        tuned_field_names
        - allowed_names
    )

    if forbidden_names:
        errors.append(
            'entry_kind {} does not allow the following tooltip_fields: {}. '
            'Allowed fields: {}.'.format(
                kind_name,
                ', '.join(
                    forbidden_names
                ),
                ', '.join(
                    allowed_field_names
                )
            )
        )

    missing_required_names = [
        field_name
        for field_name in required_field_names
        if field_name not in tuned_field_names
    ]

    if missing_required_names:
        errors.append(
            'entry_kind {} requires the following tooltip_fields: {}.'.format(
                kind_name,
                ', '.join(
                    missing_required_names
                )
            )
        )


def _validate_animal_feed_tuning(
    cls,
    errors: list
) -> None:
    """
    Validate ANIMAL_FEED's native EA tooltip contract.

    Optional:
    - recipe_name: falls back to the final product name.
    - recipe_description: falls back to the final product description.
    - header: omitted when not tuned.

    Required:
    - subtext.
    - rarity_text.

    Automatic:
    - TooltipFieldsComplete.simoleon_value from the final product price.

    Every other tooltip_fields member is forbidden.
    """
    cls._validate_tooltip_fields(
        errors
    )
    cls._validate_tooltip_field_policy(
        errors,
        'ANIMAL_FEED',
        _ANIMAL_FEED_ALLOWED_TOOLTIP_FIELD_NAMES,
        _ANIMAL_FEED_REQUIRED_TOOLTIP_FIELD_NAMES
    )


def _dynamic_forbidden_fields(
    cls,
    allowed_fields=()
) -> list:
    """Return static fields that conflict with dynamic display."""
    allowed_field_names = set(
        allowed_fields
    )
    field_values = (
        ('entry_text', cls.entry_text),
        ('entry_text_description', cls.entry_text_description),
        ('entry_icon', cls.entry_icon),
        ('entry_sublist', cls.entry_sublist),
        (
            'tooltip_fields',
            cls._has_tuned_tooltip_fields()
        )
    )
    collection_fields = {
        'entry_sublist'
    }
    boolean_fields = {
        'tooltip_fields'
    }
    forbidden_fields = []

    for name, value in field_values:
        if name in allowed_field_names:
            continue

        if name in collection_fields:
            if value:
                forbidden_fields.append(
                    name
                )

        elif name in boolean_fields:
            if value is True:
                forbidden_fields.append(
                    name
                )

        elif value is not None:
            forbidden_fields.append(
                name
            )

    return forbidden_fields


def _validate_dynamic_tuning(
    cls,
    errors: list,
    kind_name: str,
    source_description: str,
    allowed_fields=(),
    allow_custom_tooltip_style: bool = False
) -> None:
    """Reject fields generated by a definition-based entry kind."""
    normalized_allowed_fields = tuple(
        allowed_fields
    )

    if (
        cls.entry_kind
        == _NotebookInjectorEntryKind.ANIMAL_FEED
    ):
        normalized_allowed_fields = (
            'tooltip_fields',
        )

    forbidden_fields = cls._dynamic_forbidden_fields(
        normalized_allowed_fields
    )

    if forbidden_fields:
        errors.append(
            'entry_kind {} does not allow the following fields '
            'because their values are generated from {}: {}.'.format(
                kind_name,
                source_description,
                ', '.join(
                    forbidden_fields
                )
            )
        )

    if (
        allow_custom_tooltip_style is not True
        and cls.tooltip_style
        != HovertipStyle.HOVER_TIP_DEFAULT
    ):
        errors.append(
            'entry_kind {} does not allow a custom tooltip_style '
            'because its tooltip uses EA\'s HOVER_TIP_DEFAULT layout '
            'generated from {}.'.format(
                kind_name,
                source_description
            )
        )


def _build_entry_tooltip(cls):
    """Convert the shared flat tuple into EA's EntryTooltip."""
    tooltip_fields = cls._get_tuned_tooltip_fields()

    if not tooltip_fields:
        return None

    return EntryTooltip(
        cls.tooltip_style,
        tooltip_fields
    )


def _initialize_recipe_entry(
    self
) -> None:
    """Validate and resolve a Recipe-based final product."""
    kind_name = self._entry_kind_name()
    recipe_id = self.recipe_object_definition_id

    if not recipe_id:
        self._set_runtime_validation_error(
            'entry_kind {} requires a Recipe tuning. '
            'Use the NotebookEntryLootOp variant '
            'create_entry_from_recipe instead of '
            'create_new_entry.'.format(
                kind_name
            )
        )
        return

    recipe_definition = self.get_recipe_definition()

    if recipe_definition is None:
        self._set_runtime_validation_error(
            'Recipe tuning {} does not exist or its required pack '
            'is unavailable for entry_kind {}.'.format(
                recipe_id,
                kind_name
            )
        )
        return

    self.final_product = getattr(
        recipe_definition,
        'final_product_definition',
        None
    )

    if self.final_product is None:
        self._set_runtime_validation_error(
            'Recipe tuning {} has no final_product_definition '
            'for entry_kind {}.'.format(
                recipe_id,
                kind_name
            )
        )
        return

    if (
        self.entry_kind
        == _NotebookInjectorEntryKind.ANIMAL_FEED
    ):
        price = getattr(
            self.final_product,
            'price',
            None
        )

        if (
            isinstance(
                price,
                bool
            )
            or not isinstance(
                price,
                (
                    int,
                    float
                )
            )
        ):
            self._set_runtime_validation_error(
                'ANIMAL_FEED final product {} has an invalid price '
                'value {!r}; an integer or float is required.'.format(
                    getattr(
                        self.final_product,
                        'id',
                        'unknown'
                    ),
                    price
                )
            )
            return

        tuned_tooltip_fields = (
            self.__class__
            ._get_tuned_tooltip_fields()
        )

        if (
            tuned_tooltip_fields.get(
                TooltipFields.subtext
            )
            is None
        ):
            self._set_runtime_validation_error(
                'entry_kind ANIMAL_FEED requires '
                'tooltip_fields.subtext for EA-style flavor text.'
            )
            return

        if (
            tuned_tooltip_fields.get(
                TooltipFields.rarity_text
            )
            is None
        ):
            self._set_runtime_validation_error(
                'entry_kind ANIMAL_FEED requires '
                'tooltip_fields.rarity_text for EA-style rarity text.'
            )
            return

    if self.entry_object_definition_id is None:
        self.entry_object_definition_id = (
            self.final_product.id
        )


def _get_animal_feed_tooltip(
    self,
    entry_definition
):
    """
    Build EA's Animal Feed tooltip from native TooltipFields.

    recipe_name and recipe_description fall back to the final product.
    header is optional. subtext and rarity_text are required by validation.
    simoleon_value is always generated from the final product price.
    """
    tuned_tooltip_fields = (
        self.__class__
        ._get_tuned_tooltip_fields()
    )

    recipe_name = tuned_tooltip_fields.get(
        TooltipFields.recipe_name
    )

    if recipe_name is None:
        recipe_name = (
            LocalizationHelperTuning
            .get_object_name(
                entry_definition
            )
        )

    recipe_description = tuned_tooltip_fields.get(
        TooltipFields.recipe_description
    )

    if recipe_description is None:
        recipe_description = (
            LocalizationHelperTuning
            .get_object_description(
                entry_definition
            )
        )

    tooltip_fields = {
        TooltipFields.recipe_name: recipe_name,
        TooltipFields.recipe_description: recipe_description,
        TooltipFields.subtext: (
            tuned_tooltip_fields[
                TooltipFields.subtext
            ]
        ),
        TooltipFields.rarity_text: (
            tuned_tooltip_fields[
                TooltipFields.rarity_text
            ]
        ),
        TooltipFieldsComplete.simoleon_value: (
            entry_definition.price
        )
    }

    header = tuned_tooltip_fields.get(
        TooltipFields.header
    )

    if header is not None:
        tooltip_fields[
            TooltipFields.header
        ] = header

    return EntryTooltip(
        HovertipStyle.HOVER_TIP_DEFAULT,
        tooltip_fields
    )


def _remove_legacy_animal_feed_tooltip_tunables() -> None:
    """
    Remove the five pre-1.1 aliases from the public XML contract.

    The class is patched before EA generates any notebook-entry tuning type,
    so XML using these names is rejected instead of silently ignored.
    """
    instance_tunables = getattr(
        _NotebookInjectorEntry,
        'INSTANCE_TUNABLES',
        None
    )

    pop_method = getattr(
        instance_tunables,
        'pop',
        None
    )

    if callable(
        pop_method
    ):
        for field_name in (
            _LEGACY_ANIMAL_FEED_TOOLTIP_TUNABLES
        ):
            pop_method(
                field_name,
                None
            )

    class_attributes = vars(
        _NotebookInjectorEntry
    )

    for field_name in (
        _LEGACY_ANIMAL_FEED_TOOLTIP_TUNABLES
    ):
        if field_name in class_attributes:
            delattr(
                _NotebookInjectorEntry,
                field_name
            )


# Replace the public tooltip Tunable before XML tuning instances are generated.
# TunedInstanceMetaclass.add_tunable_to_instance updates both INSTANCE_TUNABLES
# and the class-level default used by generated tuning types.
_NotebookInjectorEntry.add_tunable_to_instance(
    'tooltip_fields',
    _FLAT_TOOLTIP_FIELDS_TUNABLE
)

_remove_legacy_animal_feed_tooltip_tunables()

# Keep the existing public class and XML contract while replacing only the
# methods whose behavior depended on the old mapping or ANIMAL_FEED aliases.
_NotebookInjectorEntry._get_tuned_tooltip_fields = classmethod(
    _get_tuned_tooltip_fields
)
_NotebookInjectorEntry._has_tuned_tooltip_fields = classmethod(
    _has_tuned_tooltip_fields
)
_NotebookInjectorEntry._validate_tooltip_fields = classmethod(
    _validate_tooltip_fields
)
_NotebookInjectorEntry._validate_tooltip_field_policy = classmethod(
    _validate_tooltip_field_policy
)
_NotebookInjectorEntry._validate_animal_feed_tuning = classmethod(
    _validate_animal_feed_tuning
)
_NotebookInjectorEntry._dynamic_forbidden_fields = classmethod(
    _dynamic_forbidden_fields
)
_NotebookInjectorEntry._validate_dynamic_tuning = classmethod(
    _validate_dynamic_tuning
)
_NotebookInjectorEntry._build_entry_tooltip = classmethod(
    _build_entry_tooltip
)
_NotebookInjectorEntry._initialize_recipe_entry = (
    _initialize_recipe_entry
)
_NotebookInjectorEntry._get_animal_feed_tooltip = (
    _get_animal_feed_tooltip
)
