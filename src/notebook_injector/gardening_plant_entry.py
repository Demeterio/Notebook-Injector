# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import itertools
import services
from distributor.shared_messages import IconInfoData
from notebook.notebook_entry import EntryData, SubListData
from objects.collection_manager import (
    CollectionIdentifier,
    ObjectCollectionData
)
from objects.gardening.gardening_tuning import GardeningTuning
from sims4.localization import (
    LocalizationHelperTuning,
    TunableLocalizedStringFactory
)
from sims4.tuning.tunable import TunableReference
from typing import Any, Callable, Iterable, Tuple, TYPE_CHECKING, cast

from notebook_injector.entry import (
    NotebookInjectorEntry,
    NotebookInjectorEntryKind
)
from notebook_injector.log import NotebookInjectorLog


_Services = cast(Any, services)


class NotebookInjectorGardeningPlantEntry(NotebookInjectorEntry):
    """
    Native EA-style GARDENING_PLANT notebook entry.

    The public entry must be unlocked through
    NotebookEntryLootOp.create_entry_from_participant. EA then calls the
    Gardening Component's get_notebook_information method, which converts a
    plant or harvestable participant into the root harvestable definition ID
    expected by NotebookEntryGardeningPlant.
    """

    if TYPE_CHECKING:
        entry_text_rarity: Any
        entry_text_value: Any
        entry_text_splicing: Any
        gardening_fruit_definition: Any
        gardening_tuned_values: Any
        gardening_plant_definition: Any

    INSTANCE_TUNABLES = {
        'entry_text_rarity': TunableLocalizedStringFactory(
            description=(
                'Required GARDENING_PLANT rarity text factory. Token '
                '{0.String} receives EA\'s localized Gardening collection '
                'rarity text.'
            ),
            default=cast(Any, None),
            allow_none=True
        ),
        'entry_text_value': TunableLocalizedStringFactory(
            description=(
                'Required GARDENING_PLANT value text factory. Token {0.Money} '
                'receives EA\'s average harvestable value, calculated from the '
                'root harvestable Object Definition price divided by five.'
            ),
            default=cast(Any, None),
            allow_none=True
        ),
        'entry_text_splicing': TunableLocalizedStringFactory(
            description=(
                'Required GARDENING_PLANT grafting text factory. Object token '
                'P0 receives the harvestable used for grafting and P1 receives '
                'the resulting harvestable.'
            ),
            default=cast(Any, None),
            allow_none=True
        )
    }

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            **kwargs
        )

        self.gardening_fruit_definition = None
        self.gardening_tuned_values = None
        self.gardening_plant_definition = None
        self._initialize_gardening_plant_entry()

    @staticmethod
    def _get_gardening_tuned_values(definition):
        """Return the Gardening Component tuned values for an Object Definition."""
        object_class = getattr(
            definition,
            'cls',
            None
        )

        components = getattr(
            object_class,
            '_components',
            None
        )

        gardening_component = getattr(
            components,
            'gardening',
            None
        )

        return getattr(
            gardening_component,
            '_tuned_values',
            None
        )

    def _initialize_gardening_plant_entry(self) -> None:
        """Validate and resolve the root harvestable supplied by EA Gardening."""
        definition_id = self.entry_object_definition_id

        if not definition_id:
            self._set_runtime_validation_error(
                'entry_kind GARDENING_PLANT requires a Gardening participant. '
                'Use NotebookEntryLootOp.create_entry_from_participant so the '
                'participant Gardening Component can supply its root harvestable '
                'definition. create_entry_from_participant_definition passes the '
                'plant definition directly and is not compatible.'
            )
            return

        fruit_definition = _Services.definition_manager().get(
            definition_id
        )

        if fruit_definition is None:
            self._set_runtime_validation_error(
                'GARDENING_PLANT harvestable Object Definition {} does not exist '
                'or its required pack is unavailable.'.format(
                    definition_id
                )
            )
            return

        gardening_tuned_values = self._get_gardening_tuned_values(
            fruit_definition
        )

        if gardening_tuned_values is None:
            self._set_runtime_validation_error(
                'GARDENING_PLANT Object Definition {} has no tuned Gardening '
                'Component data. The runtime definition must be a harvestable '
                'using EA\'s fruit_component.'.format(
                    definition_id
                )
            )
            return

        plant_definition = getattr(
            gardening_tuned_values,
            'plant',
            None
        )

        if plant_definition is None:
            self._set_runtime_validation_error(
                'GARDENING_PLANT Object Definition {} is not a valid root '
                'harvestable because its Gardening Component has no plant '
                'reference. Use create_entry_from_participant instead of passing '
                'a plant definition directly.'.format(
                    definition_id
                )
            )
            return

        splicing_recipies = getattr(
            gardening_tuned_values,
            'splicing_recipies',
            None
        )

        if not callable(
            getattr(
                splicing_recipies,
                'items',
                None
            )
        ):
            self._set_runtime_validation_error(
                'GARDENING_PLANT harvestable Object Definition {} has '
                'an invalid splicing_recipies value; a mapping is '
                'required.'.format(
                    definition_id
                )
            )
            return

        price = getattr(
            fruit_definition,
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
                'GARDENING_PLANT harvestable Object Definition {} has an invalid '
                'price value {!r}; an integer or float is required.'.format(
                    definition_id,
                    price
                )
            )
            return

        if self.entry_text_value is None:
            self._set_runtime_validation_error(
                'entry_kind GARDENING_PLANT requires entry_text_value.'
            )
            return

        if self.entry_text_splicing is None:
            self._set_runtime_validation_error(
                'entry_kind GARDENING_PLANT requires entry_text_splicing.'
            )
            return

        if self.entry_text_rarity is None:
            self._set_runtime_validation_error(
                'entry_kind GARDENING_PLANT requires entry_text_rarity.'
            )
            return

        gardening_collection_data = ObjectCollectionData.get_collection_data(
            CollectionIdentifier.Gardening
        )

        if gardening_collection_data is None:
            self._set_runtime_validation_error(
                'EA Gardening collection data is unavailable. '
                'GARDENING_PLANT cannot resolve harvestable rarity data.'
            )
            return

        self.gardening_fruit_definition = fruit_definition
        self.gardening_tuned_values = gardening_tuned_values
        self.gardening_plant_definition = plant_definition

    def is_definition_based(self) -> bool:
        """Return True when EA supplied the root harvestable definition ID."""
        return (
            self.entry_object_definition_id
            is not None
        )

    def _build_gardening_value_row(self):
        """Build EA's average harvestable value row."""
        fruit_definition = self.gardening_fruit_definition

        try:
            value_text = self.entry_text_value(
                fruit_definition.price / 5
            )
        except Exception:
            NotebookInjectorLog.logger().exception(
                'Failed to build entry_text_value for GARDENING_PLANT '
                'harvestable definition {}.'.format(
                    fruit_definition.id
                )
            )
            return None

        return SubListData(
            object_definition=None,
            item_count=0,
            num_objects_required=0,
            is_ingredient=True,
            new_item=False,
            object_display_name=value_text,
            item_icon_info_data=None,
            item_tooltip=None
        )

    def _build_gardening_seasons_row(self):
        """Build the optional active-seasons row used when Seasons is available."""
        season_service = _Services.season_service()

        if season_service is None:
            return None

        try:
            active_seasons_text = (
                GardeningTuning
                .get_active_seasons_text_from_plant(
                    self.gardening_plant_definition
                )
            )
        except Exception:
            NotebookInjectorLog.logger().exception(
                'Failed to resolve active seasons for GARDENING_PLANT '
                'harvestable definition {} and plant definition {}.'.format(
                    self.gardening_fruit_definition.id,
                    getattr(
                        self.gardening_plant_definition,
                        'id',
                        'unknown'
                    )
                )
            )
            return None

        if active_seasons_text is None:
            try:
                active_seasons_factory = cast(
                    Any,
                    GardeningTuning.ACTIVE_SEASONS_TEXT
                )
                active_seasons_text = active_seasons_factory(
                    GardeningTuning.ALL_SEASONS_TEXT
                )
            except Exception:
                NotebookInjectorLog.logger().exception(
                    'Failed to build the all-seasons fallback text for '
                    'GARDENING_PLANT harvestable definition {}.'.format(
                        self.gardening_fruit_definition.id
                    )
                )
                return None

        return SubListData(
            object_definition=None,
            item_count=0,
            num_objects_required=0,
            is_ingredient=True,
            new_item=False,
            object_display_name=active_seasons_text,
            item_icon_info_data=None,
            item_tooltip=None
        )

    def _build_gardening_description_row(self):
        """Build EA's plant-description row."""
        return SubListData(
            object_definition=None,
            item_count=0,
            num_objects_required=0,
            is_ingredient=True,
            new_item=False,
            object_display_name=(
                LocalizationHelperTuning
                .get_object_description(
                    self.gardening_plant_definition
                )
            ),
            item_icon_info_data=None,
            item_tooltip=None
        )

    def _build_gardening_splicing_rows(self) -> tuple:
        """Build every grafting recipe row from the harvestable component."""
        rows = []

        splicing_recipies = cast(
            Any,
            getattr(
                self.gardening_tuned_values,
                'splicing_recipies',
                None
            )
        )

        raw_items_method = getattr(
            splicing_recipies,
            'items',
            None
        )

        if not callable(
            raw_items_method
        ):
            NotebookInjectorLog.logger().error(
                'GARDENING_PLANT harvestable definition {} has an invalid '
                'splicing_recipies value while building notebook rows; '
                'a mapping is required.'.format(
                    getattr(
                        self.gardening_fruit_definition,
                        'id',
                        'unknown'
                    )
                )
            )
            return ()

        items_method = cast(
            Callable[
                [],
                Iterable[
                    Tuple[
                        Any,
                        Any
                    ]
                ]
            ],
            raw_items_method
        )

        for splice_fruit, splice_result in items_method():
            if (
                splice_fruit is None
                or splice_result is None
            ):
                NotebookInjectorLog.logger().error(
                    'GARDENING_PLANT harvestable definition {} contains an '
                    'invalid splicing_recipies pair: {!r} -> {!r}.'.format(
                        self.gardening_fruit_definition.id,
                        splice_fruit,
                        splice_result
                    )
                )
                continue

            try:
                splicing_text = self.entry_text_splicing(
                    splice_fruit,
                    splice_result
                )
            except Exception:
                NotebookInjectorLog.logger().exception(
                    'Failed to build entry_text_splicing for GARDENING_PLANT '
                    'harvestable definition {}, splice fruit {}, result {}.'.format(
                        self.gardening_fruit_definition.id,
                        getattr(
                            splice_fruit,
                            'id',
                            'unknown'
                        ),
                        getattr(
                            splice_result,
                            'id',
                            'unknown'
                        )
                    )
                )
                continue

            rows.append(
                SubListData(
                    object_definition=None,
                    item_count=0,
                    num_objects_required=0,
                    is_ingredient=True,
                    new_item=False,
                    object_display_name=splicing_text,
                    item_icon_info_data=None,
                    item_tooltip=None
                )
            )

        return tuple(
            rows
        )

    def _build_gardening_rarity_row(self):
        """Build the rarity row when the harvestable belongs to Gardening."""
        gardening_collection_data = ObjectCollectionData.get_collection_data(
            CollectionIdentifier.Gardening
        )

        if gardening_collection_data is None:
            return None

        collection_objects = itertools.chain(
            gardening_collection_data.object_list,
            gardening_collection_data.bonus_object_list
        )

        for object_data in collection_objects:
            if (
                object_data.collectable_item
                is not self.gardening_fruit_definition
            ):
                continue

            try:
                rarity_mapping = cast(
                    Any,
                    ObjectCollectionData.COLLECTION_RARITY_MAPPING
                )
                rarity_data = rarity_mapping[
                    object_data.rarity
                ]
                rarity_text = self.entry_text_rarity(
                    rarity_data.text_value
                )
            except Exception:
                NotebookInjectorLog.logger().exception(
                    'Failed to resolve Gardening collection rarity for '
                    'GARDENING_PLANT harvestable definition {}.'.format(
                        self.gardening_fruit_definition.id
                    )
                )
                return None

            return SubListData(
                object_definition=None,
                item_count=0,
                num_objects_required=0,
                is_ingredient=True,
                new_item=False,
                object_display_name=rarity_text,
                item_icon_info_data=None,
                item_tooltip=None
            )

        return None

    def get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Build EA's native Gardening notebook layout."""
        if (
            self._runtime_validation_error is not None
            or self.gardening_fruit_definition is None
            or self.gardening_tuned_values is None
            or self.gardening_plant_definition is None
        ):
            return None

        sublist_rows = []

        value_row = self._build_gardening_value_row()
        if value_row is None:
            return None
        sublist_rows.append(
            value_row
        )

        seasons_row = self._build_gardening_seasons_row()
        if seasons_row is not None:
            sublist_rows.append(
                seasons_row
            )

        sublist_rows.append(
            self._build_gardening_description_row()
        )

        sublist_rows.extend(
            self._build_gardening_splicing_rows()
        )

        rarity_row = self._build_gardening_rarity_row()
        if rarity_row is not None:
            sublist_rows.append(
                rarity_row
            )

        return EntryData(
            entry_text=(
                LocalizationHelperTuning
                .get_object_name(
                    self.gardening_fruit_definition
                )
            ),
            entry_text_description=None,
            entry_icon_info_data=IconInfoData(
                obj_def_id=(
                    self.gardening_fruit_definition.id
                )
            ),
            entry_tooltip=None,
            entry_sublist=sublist_rows,
            entry_sublist_is_sortable=None
        )

    def has_identical_entries(
        self,
        entries
    ) -> bool:
        """Reject a duplicate entry for the same root harvestable definition."""
        for entry in entries:
            if (
                getattr(
                    entry,
                    'entry_kind',
                    None
                )
                != NotebookInjectorEntryKind.GARDENING_PLANT
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
        """The public entry requires EA Gardening runtime participant data."""
        return False

    @classmethod
    def _validate_gardening_only_tuning(
        cls,
        errors: list
    ) -> None:
        """Validate fields required by the native Gardening entry layout."""
        if cls.entry_text_value is None:
            errors.append(
                'entry_text_value is required for entry_kind GARDENING_PLANT.'
            )

        if cls.entry_text_splicing is None:
            errors.append(
                'entry_text_splicing is required for entry_kind GARDENING_PLANT.'
            )

        if cls.entry_text_rarity is None:
            errors.append(
                'entry_text_rarity is required for entry_kind GARDENING_PLANT.'
            )

        if cls.entry_sublist_sortable is True:
            errors.append(
                'entry_sublist_sortable must be False for entry_kind '
                'GARDENING_PLANT because EA controls the generated row order.'
            )

        if cls.entry_sublist_include_new is True:
            errors.append(
                'entry_sublist_include_new must be False for entry_kind '
                'GARDENING_PLANT because EA controls the generated row order.'
            )

    @classmethod
    def _validate_non_gardening_fields(
        cls,
        errors: list
    ) -> None:
        """Reject BAIT source and size fields while allowing shared rarity text."""
        forbidden_fields = []

        if cls.bait_fish_definition is not None:
            forbidden_fields.append(
                'bait_fish_definition'
            )

        if cls.bait_snippets:
            forbidden_fields.append(
                'bait_snippets'
            )

        if cls.entry_text_size_mapping:
            forbidden_fields.append(
                'entry_text_size_mapping'
            )

        if forbidden_fields:
            errors.append(
                'The following fields are not allowed for entry_kind '
                'GARDENING_PLANT: {}.'.format(
                    ', '.join(
                        forbidden_fields
                    )
                )
            )

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate the native EA GARDENING_PLANT field contract."""
        errors = []

        if (
            cls.entry_kind
            != NotebookInjectorEntryKind.GARDENING_PLANT
        ):
            errors.append(
                '{} only supports entry_kind GARDENING_PLANT.'.format(
                    cls.__name__
                )
            )
            return tuple(
                errors
            )

        cls._validate_gardening_only_tuning(
            errors
        )
        cls._validate_non_gardening_fields(
            errors
        )
        cls._validate_dynamic_tuning(
            errors,
            'GARDENING_PLANT',
            'the root harvestable and its EA Gardening Component'
        )

        return tuple(
            errors
        )


class NotebookInjectorDebugGardeningPlantEntry(
    NotebookInjectorGardeningPlantEntry
):
    """
    Internal static preview for debug packages and documentation screenshots.

    A fixed harvestable definition is converted into the constructor data that
    EA normally obtains from a plant or harvestable through
    create_entry_from_participant. This class is not part of the public modder
    API and must not be used with a plant definition.
    """

    if TYPE_CHECKING:
        debug_gardening_fruit_definition: Any

    INSTANCE_TUNABLES = {
        'debug_gardening_fruit_definition': TunableReference(
            _Services.definition_manager(),
            description=(
                'Required internal debug harvestable Object Definition using '
                'EA\'s fruit_component. This enables create_new_entry and '
                'demeterio.ni_loot for previews. A plant definition is invalid.'
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
        """Supply the fixed harvestable only when EA gave no runtime source."""
        if (
            args
            or 'entry_object_definition_id' in kwargs
        ):
            return

        debug_definition = getattr(
            cls,
            'debug_gardening_fruit_definition',
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
        """Allow create_new_entry only for the internal static preview."""
        return (
            cls.debug_gardening_fruit_definition
            is not None
        )

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate the public Gardening contract plus the debug harvestable."""
        errors = list(
            super().validate_tuning()
        )

        debug_definition = cls.debug_gardening_fruit_definition

        if debug_definition is None:
            errors.append(
                'debug_gardening_fruit_definition is required for '
                'NotebookInjectorDebugGardeningPlantEntry.'
            )
            return tuple(
                errors
            )

        tuned_values = cls._get_gardening_tuned_values(
            debug_definition
        )

        if tuned_values is None:
            errors.append(
                'debug_gardening_fruit_definition must use an EA Gardening '
                'Component.'
            )
        else:
            if getattr(
                tuned_values,
                'plant',
                None
            ) is None:
                errors.append(
                    'debug_gardening_fruit_definition must be a harvestable '
                    'using fruit_component, not a plant definition.'
                )

            splicing_recipies = getattr(
                tuned_values,
                'splicing_recipies',
                None
            )

            if not callable(
                getattr(
                    splicing_recipies,
                    'items',
                    None
                )
            ):
                errors.append(
                    'debug_gardening_fruit_definition must provide '
                    'splicing_recipies as a mapping.'
                )

        return tuple(
            errors
        )
