# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import services
from distributor.shared_messages import IconInfoData
from notebook.notebook_entry import EntryData, SubListData
from sims4.localization import (
    LocalizationHelperTuning,
    TunableLocalizedString,
    TunableLocalizedStringFactory
)
from sims4.tuning.tunable import TunableReference
from typing import Any, TYPE_CHECKING, cast

from notebook_injector.entry import (
    NotebookInjectorEntry,
    NotebookInjectorEntryKind
)
from notebook_injector.log import NotebookInjectorLog


_Services = cast(
    Any,
    services
)
_TunableLocalizedString = cast(
    Any,
    TunableLocalizedString
)


class NotebookInjectorCountryItemEntry(NotebookInjectorEntry):
    """
    Native EA-style COUNTRY_ITEM notebook entry.

    The represented object definition must be supplied at runtime by
    NotebookEntryLootOp.create_entry_from_participant_definition. The object
    provides the entry title, icon, price, and duplicate identity.

    COUNTRY_ITEM also accepts the same EA-style localized tooltip_fields mapping
    as DEFAULT. The tooltip is authored in XML while the entry title, icon and
    display row continue to come from the runtime object definition.
    """

    if TYPE_CHECKING:
        entry_text_value: Any
        entry_text_flavor: Any
        country_item_definition: Any
        tooltip_fields: Any

    INSTANCE_TUNABLES = {
        'entry_text_value': TunableLocalizedStringFactory(
            description=(
                'Required COUNTRY_ITEM value text factory. Its first and only '
                'token receives the price of the object definition supplied by '
                'NotebookEntryLootOp.create_entry_from_participant_definition.'
            ),
            default=cast(Any, None),
            allow_none=True
        ),
        'entry_text_flavor': _TunableLocalizedString(
            description=(
                'Required COUNTRY_ITEM flavor text displayed between the '
                'formatted object value and entry_text_description.'
            ),
            default=None,
            allow_none=True
        )
    }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs
        )
        self.country_item_definition = None
        self._initialize_country_item_entry()

    def _initialize_country_item_entry(self) -> None:
        """Validate and resolve the object definition supplied by EA's Loot."""
        definition_id = self.entry_object_definition_id

        if not definition_id:
            self._set_runtime_validation_error(
                'entry_kind COUNTRY_ITEM requires an object definition supplied '
                'by NotebookEntryLootOp.create_entry_from_participant_definition. '
                'create_new_entry is only supported by the internal debug class.'
            )
            return

        country_item_definition = _Services.definition_manager().get(
            definition_id
        )

        if country_item_definition is None:
            self._set_runtime_validation_error(
                'COUNTRY_ITEM object definition {} does not exist or its '
                'required pack is unavailable.'.format(
                    definition_id
                )
            )
            return

        price = getattr(
            country_item_definition,
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
                'COUNTRY_ITEM object definition {} has an invalid price value '
                '{!r}; an integer or float is required.'.format(
                    definition_id,
                    price
                )
            )
            return

        if self.entry_text_value is None:
            self._set_runtime_validation_error(
                'entry_kind COUNTRY_ITEM requires entry_text_value.'
            )
            return

        if self.entry_text_flavor is None:
            self._set_runtime_validation_error(
                'entry_kind COUNTRY_ITEM requires entry_text_flavor.'
            )
            return

        if self.entry_text_description is None:
            self._set_runtime_validation_error(
                'entry_kind COUNTRY_ITEM requires entry_text_description.'
            )
            return

        self.country_item_definition = country_item_definition

    def is_definition_based(self) -> bool:
        """COUNTRY_ITEM is generated from the definition supplied by EA's Loot."""
        return True

    def get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Build the native EA Country Living notebook-row layout."""
        if (
            self._runtime_validation_error is not None
            or self.country_item_definition is None
        ):
            return None

        definition = self.country_item_definition

        try:
            value_text = self.entry_text_value(
                definition.price
            )
        except Exception:
            NotebookInjectorLog.logger().exception(
                'Failed to build entry_text_value for COUNTRY_ITEM '
                'definition {}.'.format(
                    definition.id
                )
            )
            return None

        concatenated_text = (
            LocalizationHelperTuning
            .get_new_line_separated_strings(
                value_text,
                self.entry_text_flavor,
                self.entry_text_description
            )
        )

        country_item_sublist = (
            SubListData(
                object_definition=None,
                item_count=0,
                num_objects_required=0,
                is_ingredient=True,
                new_item=False,
                object_display_name=concatenated_text,
                item_icon_info_data=None,
                item_tooltip=None
            ),
        )

        return EntryData(
            entry_text=(
                LocalizationHelperTuning
                .get_object_name(
                    definition
                )
            ),
            entry_text_description=None,
            entry_icon_info_data=IconInfoData(
                obj_def_id=definition.id
            ),
            entry_tooltip=(
                self.__class__._build_entry_tooltip()
            ),
            entry_sublist=country_item_sublist,
            entry_sublist_is_sortable=None
        )

    def has_identical_entries(
        self,
        entries
    ) -> bool:
        """Reject a duplicate COUNTRY_ITEM for the same object definition."""
        for entry in entries:
            if (
                getattr(
                    entry,
                    'entry_kind',
                    None
                )
                != NotebookInjectorEntryKind.COUNTRY_ITEM
            ):
                continue

            if (
                getattr(
                    entry,
                    'entry_object_definition_id',
                    None
                )
                == self.entry_object_definition_id
            ):
                return True

        return False

    @classmethod
    def supports_reference_unlock(cls) -> bool:
        """The public COUNTRY_ITEM requires EA runtime participant data."""
        return False

    @classmethod
    def _validate_country_item_tuning(
        cls,
        errors: list
    ) -> None:
        """Validate required COUNTRY_ITEM text fields and native UI behavior."""
        if cls.entry_text_value is None:
            errors.append(
                'entry_text_value is required for entry_kind COUNTRY_ITEM.'
            )

        if cls.entry_text_flavor is None:
            errors.append(
                'entry_text_flavor is required for entry_kind COUNTRY_ITEM.'
            )

        if cls.entry_text_description is None:
            errors.append(
                'entry_text_description is required for entry_kind COUNTRY_ITEM.'
            )

        if cls.entry_sublist_sortable is True:
            errors.append(
                'entry_sublist_sortable must be False for entry_kind '
                'COUNTRY_ITEM because EA generates one fixed display row.'
            )

        if cls.entry_sublist_include_new is True:
            errors.append(
                'entry_sublist_include_new must be False for entry_kind '
                'COUNTRY_ITEM because EA generates one fixed display row.'
            )

        cls._validate_tooltip_fields(
            errors
        )

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate the native EA COUNTRY_ITEM field contract."""
        errors = []

        if (
            cls.entry_kind
            != NotebookInjectorEntryKind.COUNTRY_ITEM
        ):
            errors.append(
                '{} only supports entry_kind COUNTRY_ITEM.'.format(
                    cls.__name__
                )
            )
            return tuple(
                errors
            )

        cls._validate_bait_only_tuning(
            errors
        )
        cls._validate_country_item_tuning(
            errors
        )
        cls._validate_dynamic_tuning(
            errors,
            'COUNTRY_ITEM',
            'the object definition supplied by '
            'create_entry_from_participant_definition',
            allowed_fields=(
                'entry_text_description',
                'tooltip_fields'
            ),
            allow_custom_tooltip_style=True
        )

        return tuple(
            errors
        )


class NotebookInjectorDebugCountryItemEntry(
    NotebookInjectorCountryItemEntry
):
    """
    Internal COUNTRY_ITEM test entry for debug packages and screenshots.

    This class converts a fixed debug definition into the same constructor data
    that EA normally supplies through create_entry_from_participant_definition,
    allowing a normal create_new_entry Loot to be applied with demeterio.ni_loot.
    """

    if TYPE_CHECKING:
        debug_country_item_definition: Any

    INSTANCE_TUNABLES = {
        'debug_country_item_definition': TunableReference(
            _Services.definition_manager(),
            description=(
                'Required internal debug definition used to preview the native '
                'COUNTRY_ITEM layout through create_new_entry and '
                'demeterio.ni_loot. Do not use this class in public mod tuning.'
            ),
            allow_none=True,
            pack_safe=True
        )
    }

    def __init__(self, *args, **kwargs):
        self.__class__._build_debug_constructor_data(
            args,
            kwargs
        )
        super().__init__(
            *args,
            **kwargs
        )

    @classmethod
    def _build_debug_constructor_data(
        cls,
        args: tuple,
        kwargs: dict
    ) -> None:
        """Supply fixed debug data only when EA did not provide runtime data."""
        if (
            args
            or 'entry_object_definition_id' in kwargs
        ):
            return

        debug_definition = getattr(
            cls,
            'debug_country_item_definition',
            None
        )

        if debug_definition is None:
            return

        kwargs['entry_object_definition_id'] = getattr(
            debug_definition,
            'id',
            None
        )

    @classmethod
    def supports_reference_unlock(cls) -> bool:
        """Allow create_new_entry only for the internal debug preview class."""
        return (
            cls.debug_country_item_definition
            is not None
        )

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate the public contract plus the fixed debug definition."""
        errors = list(
            super().validate_tuning()
        )
        debug_definition = cls.debug_country_item_definition

        if debug_definition is None:
            errors.append(
                'debug_country_item_definition is required for '
                'NotebookInjectorDebugCountryItemEntry.'
            )
            return tuple(
                errors
            )

        price = getattr(
            debug_definition,
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
            errors.append(
                'debug_country_item_definition must provide a numeric price.'
            )

        return tuple(
            errors
        )
