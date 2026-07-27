# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import enum
import services
from distributor.shared_messages import IconInfoData
from interactions.utils.tunable_icon import TunableIconAllPacks
from notebook.notebook_entry import (
    NotebookEntry,
    EntryData,
    EntryTooltip,
    SubEntryData,
    SubListData
)
from objects.collection_manager import ObjectCollectionData
from objects.hovertip import (
    HovertipStyle,
    TooltipFields,
    TooltipFieldsComplete
)
from sims4.localization import (
    LocalizationHelperTuning,
    TunableLocalizedString,
    TunableLocalizedStringFactory
)
from sims4.resources import Types
from sims4.tuning.tunable import (
    Tunable,
    TunableEnumEntry,
    TunableList,
    TunableMapping,
    TunableReference,
    TunableTuple
)
from sims4.tuning.tunable_base import SourceQueries
from ui.notebook_tuning import (
    NotebookCategories,
    NotebookSubCategories,
    NotebookEntryType,
    NotebookCustomTypeTuning
)
from typing import (
    Any,
    Iterable,
    Tuple,
    TYPE_CHECKING,
    cast
)

import notebook_injector.script as script
from notebook_injector.log import NotebookInjectorLog


_EnumInt = cast(Any, getattr(enum, 'Int'))
_Services = cast(Any, services)
_TunableTuple = cast(Any, TunableTuple)
_NotebookEntryType = cast(Any, NotebookEntryType)
_TunableMapping = cast(Any, TunableMapping)
_TunableLocalizedString = cast(
    Any,
    TunableLocalizedString
)
_SECRET_SCANDAL_ENTRY_TYPE = (
    _NotebookEntryType.NOTEBOOK_EXPANDABLE_SECRET_SCANDAL
)
_SECRET_SCANDAL_FORMAT_VALUE = getattr(
    _SECRET_SCANDAL_ENTRY_TYPE,
    'value',
    _SECRET_SCANDAL_ENTRY_TYPE
)


class NotebookInjectorEntryKind(_EnumInt):
    """
    Defines how Notebook Injector builds the notebook entry.

    This enum belongs only to Notebook Injector.
    It is not injected into EA's NotebookEntryType enum.
    """

    DEFAULT = 0
    BAIT = 1
    RECIPE = 2
    ANIMAL_FEED = 3
    COUNTRY_ITEM = 4
    GARDENING_PLANT = 5

    # Value 6 is reserved for the future FAMILY_RECIPE entry kind.
    CUSTOM = 7


class NotebookInjectorEntry(NotebookEntry):
    """
    Public flat notebook-entry tuning used by Notebook Injector.

    DEFAULT exposes EA's authored NotebookEntry data through flat fields. Its
    tooltip uses an EA-style TooltipFields-to-localized-string mapping.

    BAIT supports two source modes through this same class:

    - Static source: tune bait_fish_definition and optional bait_snippets,
      then unlock with NotebookEntryLootOp.create_new_entry.
    - EA runtime source: omit both static source fields and use an EA Loot
      variant that supplies the fish and bait data through its resolver.

    Runtime constructor data always wins. Static BAIT source data is only
    materialized when the entry is instantiated without runtime fish data.

    RECIPE and ANIMAL_FEED receive their Recipe tuning through
    NotebookEntryLootOp.create_entry_from_recipe. ANIMAL_FEED keeps dedicated
    flat tooltip helper fields because it also injects a numeric Simoleon value.
    """

    if TYPE_CHECKING:
        entry_kind: Any
        entry_text: Any
        entry_text_description: Any
        entry_icon: Any
        entry_sublist: Any
        entry_sublist_sortable: bool
        entry_sublist_is_sortable: Any
        entry_sublist_include_new: bool
        entry_tooltip: Any
        entry_object_definition_id: Any
        entry_text_rarity: Any
        entry_text_size_mapping: Any
        bait_fish_definition: Any
        bait_snippets: Any
        tooltip_style: Any
        tooltip_fields: Any
        tooltip_title: Any
        tooltip_description: Any
        tooltip_header: Any
        tooltip_subtext: Any
        tooltip_rarity: Any
        sub_entries: Any
        final_product: Any
        _runtime_validation_error: Any
        _runtime_prepare_error: Any

    IS_NOTEBOOK_INJECTOR_ENTRY = True

    REMOVE_INSTANCE_TUNABLES = (
        'category_id',
        'subcategory_id',
        'entry_text',
        'entry_icon',
        'entry_text_description',
        'entry_tooltip',
        'entry_sublist',
        'entry_sublist_is_sortable'
    )

    category_id = NotebookCategories.INVALID
    subcategory_id = NotebookSubCategories.INVALID
    entry_tooltip = None
    entry_sublist_is_sortable = None
    _runtime_prepare_error = None

    INSTANCE_TUNABLES = {
        'entry_kind': TunableEnumEntry(
            description='Logic used to build this notebook entry.',
            tunable_type=NotebookInjectorEntryKind,
            default=NotebookInjectorEntryKind.DEFAULT
        ),

        # ------------------------------------------------------
        # BAIT source data
        # ------------------------------------------------------

        'bait_fish_definition': TunableReference(
            _Services.definition_manager(),
            description=(
                'Optional static BAIT source. Tune the fish Object Definition '
                'when this entry must be unlockable through create_new_entry. '
                'Omit it when EA supplies the fish at runtime through '
                'create_entry_from_participant, '
                'create_entry_from_participant_definition, or '
                'create_entry_from_fishing_data.'
            ),
            allow_none=True,
            pack_safe=True
        ),

        'bait_snippets': TunableList(
            description=(
                'Optional static BAIT source. EA FishingBait snippets displayed '
                'as discovered bait rows when this entry is instantiated through '
                'create_new_entry. Omit this list for the EA runtime source mode.'
            ),
            tunable=TunableReference(
                _Services.snippet_manager(),
                description='EA FishingBait snippet to display.',
                pack_safe=True
            ),
            unique_entries=True
        ),

        # ------------------------------------------------------
        # Optional BAIT display overrides
        # ------------------------------------------------------

        'entry_text_rarity': TunableLocalizedStringFactory(
            description=(
                'Optional BAIT rarity text factory. Token {0.String} receives '
                'EA\'s localized collection rarity value. Omit this field to '
                'use entry_text_rarity from '
                'NotebookCustomTypeTuning.BAIT_NOTEBOOK_ENTRY.'
            ),
            default=cast(Any, None),
            allow_none=True
        ),

        'entry_text_size_mapping': _TunableMapping(
            description=(
                'Optional BAIT fish-size text overrides. Keys must match the '
                'exact fish_type value from the fish Object Tuning. Omit this '
                'list to use the complete entry_text_size_mapping from '
                'NotebookCustomTypeTuning.BAIT_NOTEBOOK_ENTRY. Missing keys '
                'also fall back individually to the native EA mapping.'
            ),
            key_type=Tunable(
                description=(
                    'Exact fish_type value used by the fish Object Tuning.'
                ),
                tunable_type=str,
                default=None,
                source_query=(
                    SourceQueries.SwingEnumNamePattern.format('fishType')
                )
            ),
            value_type=TunableLocalizedString(
                description='Localized size text displayed in the tooltip.'
            )
        ),

        # ------------------------------------------------------
        # Common entry data
        # ------------------------------------------------------

        'entry_text': _TunableLocalizedString(
            description='Main text or title displayed for the entry.',
            default=None,
            allow_none=True
        ),

        'entry_text_description': _TunableLocalizedString(
            description=(
                'Optional detailed description displayed for the entry. '
                'Omit this field when no description is required.'
            ),
            default=None,
            allow_none=True
        ),

        'entry_icon': TunableIconAllPacks(
            description=(
                'Optional flat image resource displayed for the notebook entry. '
                'Notebook Injector uses its fallback icon when omitted.'
            ),
            allow_none=True
        ),

        # ------------------------------------------------------
        # Static sublist
        # ------------------------------------------------------

        'entry_sublist': TunableList(
            description=(
                'Optional static list of object definitions associated '
                'with this notebook entry.'
            ),
            tunable=_TunableTuple(
                object_definition=TunableReference(
                    _Services.definition_manager(),
                    description=(
                        'Object definition displayed in the entry sublist.'
                    )
                ),
                num_objects_required=Tunable(
                    description=(
                        'Number of objects required for this sublist item.'
                    ),
                    tunable_type=int,
                    default=0
                )
            )
        ),

        'entry_sublist_sortable': Tunable(
            description=(
                'If True, the entry sublist is sorted alphabetically.'
            ),
            tunable_type=bool,
            default=False
        ),

        'entry_sublist_include_new': Tunable(
            description=(
                'If True, new sublist items are included in sorting. '
                'entry_sublist_sortable must also be True.'
            ),
            tunable_type=bool,
            default=False
        ),

        # ------------------------------------------------------
        # EA-style localized tooltip mapping
        # ------------------------------------------------------

        'tooltip_style': TunableEnumEntry(
            description=(
                'EA HovertipStyle used when tooltip_fields contains data. '
                'Definition-based entry kinds may require EA\'s default style.'
            ),
            tunable_type=HovertipStyle,
            default=HovertipStyle.HOVER_TIP_DEFAULT
        ),

        'tooltip_fields': _TunableMapping(
            description=(
                'Localized EA tooltip fields used by DEFAULT and compatible '
                'specialized kinds such as COUNTRY_ITEM. The key is a '
                'TooltipFields enum value and the value is its localized text. '
                'Every TooltipFields value accepted by EA is exposed initially '
                'so its actual notebook rendering can be tested in game.'
            ),
            key_type=TunableEnumEntry(
                description='EA tooltip protocol field populated by this text.',
                tunable_type=TooltipFields,
                default=TooltipFields.recipe_name
            ),
            value_type=TunableLocalizedString(
                description='Localized value sent to the selected tooltip field.'
            )
        ),

        # ------------------------------------------------------
        # ANIMAL_FEED tooltip helpers
        # ------------------------------------------------------

        'tooltip_title': _TunableLocalizedString(
            description=(
                'Optional ANIMAL_FEED tooltip title. Omit it to use the final '
                'product name from the Recipe.'
            ),
            default=None,
            allow_none=True
        ),

        'tooltip_description': _TunableLocalizedString(
            description=(
                'Optional ANIMAL_FEED tooltip description. Omit it to use the '
                'final product description from the Recipe.'
            ),
            default=None,
            allow_none=True
        ),

        'tooltip_header': _TunableLocalizedString(
            description=(
                'Optional ANIMAL_FEED small text displayed above the tooltip title.'
            ),
            default=None,
            allow_none=True
        ),

        'tooltip_subtext': _TunableLocalizedString(
            description=(
                'Required ANIMAL_FEED flavor text displayed below the title.'
            ),
            default=None,
            allow_none=True
        ),

        'tooltip_rarity': _TunableLocalizedString(
            description=(
                'Required ANIMAL_FEED rarity text.'
            ),
            default=None,
            allow_none=True
        )
    }

    @classmethod
    def uses_fallback_icon(cls) -> bool:
        """Return True when Notebook Injector may apply its fallback icon."""
        return (
            cls.entry_kind
            == NotebookInjectorEntryKind.DEFAULT
        )

    @classmethod
    def supports_reference_unlock(cls) -> bool:
        """
        Return True when this entry can be instantiated without runtime data.

        DEFAULT entries are always static. BAIT entries support reference
        unlocks only when bait_fish_definition supplies the required fish.
        RECIPE and ANIMAL_FEED require create_entry_from_recipe.
        """
        if (
            cls.entry_kind
            == NotebookInjectorEntryKind.DEFAULT
        ):
            return True

        return (
            cls.entry_kind
            == NotebookInjectorEntryKind.BAIT
            and cls.bait_fish_definition is not None
        )

    @classmethod
    def _build_static_bait_constructor_data(
        cls,
        args: tuple,
        kwargs: dict
    ) -> None:
        """
        Materialize static BAIT XML into EA's constructor arguments.

        This runs only when no positional or keyword runtime fish argument was
        supplied. It supports create_new_entry without changing EA runtime Loot
        behavior or notebook save/load reconstruction.
        """
        if (
            cls.entry_kind
            != NotebookInjectorEntryKind.BAIT
            or args
            or 'entry_object_definition_id' in kwargs
        ):
            return

        fish_definition = getattr(
            cls,
            'bait_fish_definition',
            None
        )

        if fish_definition is None:
            return

        kwargs['entry_object_definition_id'] = getattr(
            fish_definition,
            'id',
            None
        )

        if 'sub_entries' not in kwargs:
            kwargs['sub_entries'] = tuple(
                SubEntryData(
                    bait_snippet.guid64,
                    True
                )
                for bait_snippet in (
                    getattr(
                        cls,
                        'bait_snippets',
                        ()
                    )
                    or ()
                )
                if bait_snippet is not None
            )

    def _set_runtime_validation_error(
        self,
        message: str
    ) -> None:
        """Record and log an error that prevents dynamic entry generation."""
        self._runtime_validation_error = message
        entry_class = self.__class__

        NotebookInjectorLog.logger().error(
            'Invalid dynamic NotebookInjectorEntry.\n'
            'Entry: {}\n'
            'Tuning ID: {}\n'
            'Entry kind: {}\n'
            'Error: {}\n'.format(
                getattr(
                    entry_class,
                    '__name__',
                    entry_class
                ),
                getattr(
                    entry_class,
                    'guid64',
                    'unknown'
                ),
                getattr(
                    self.entry_kind,
                    'name',
                    self.entry_kind
                ),
                message
            )
        )

    def __init__(self, *args, **kwargs):
        self.__class__._build_static_bait_constructor_data(
            args,
            kwargs
        )

        super().__init__(
            *args,
            **kwargs
        )

        self.final_product = None
        self._runtime_validation_error = None

        if (
            self.entry_kind
            == NotebookInjectorEntryKind.BAIT
        ):
            self._initialize_bait_entry()

        elif self.entry_kind in (
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            self._initialize_recipe_entry()

    # ------------------------------------------------------------------
    # BAIT
    # ------------------------------------------------------------------

    @staticmethod
    def _get_bait_shared_entry():
        """Return EA's native bait entry containing shared UI tuning."""
        return getattr(
            NotebookCustomTypeTuning,
            'BAIT_NOTEBOOK_ENTRY',
            None
        )

    def _initialize_bait_entry(self) -> None:
        """Validate the fish definition required by a BAIT entry instance."""
        fish_definition_id = self.entry_object_definition_id

        if not fish_definition_id:
            self._set_runtime_validation_error(
                'entry_kind BAIT requires a fish object definition. '
                'For create_new_entry, tune bait_fish_definition on the entry. '
                'For EA runtime discovery, use '
                'create_entry_from_participant_definition, '
                'create_entry_from_participant, or '
                'create_entry_from_fishing_data.'
            )
            return

        fish_definition = _Services.definition_manager().get(
            fish_definition_id
        )

        if fish_definition is None:
            self._set_runtime_validation_error(
                'Fish object definition {} does not exist or its required '
                'pack is unavailable.'.format(
                    fish_definition_id
                )
            )
            return

        if self._get_bait_shared_entry() is None:
            self._set_runtime_validation_error(
                'EA NotebookCustomTypeTuning.BAIT_NOTEBOOK_ENTRY '
                'is unavailable.'
            )
            return

        fish_class = getattr(
            fish_definition,
            'cls',
            None
        )

        if (
            fish_class is None
            or not hasattr(
                fish_class,
                'fish_type'
            )
        ):
            self._set_runtime_validation_error(
                'Object definition {} is not a valid fish definition '
                'because its object class has no fish_type.'.format(
                    fish_definition_id
                )
            )

    def _get_bait_rarity_factory(self):
        """Resolve the custom rarity factory or the native EA fallback."""
        custom_factory = getattr(
            self,
            'entry_text_rarity',
            None
        )

        if custom_factory is not None:
            return custom_factory

        shared_entry = self._get_bait_shared_entry()

        if shared_entry is None:
            return None

        return getattr(
            shared_entry,
            'entry_text_rarity',
            None
        )

    def _get_bait_size_text_factory(
        self,
        fish_type
    ):
        """Resolve a custom size string, falling back per key to EA."""
        custom_mapping = getattr(
            self,
            'entry_text_size_mapping',
            ()
        )

        if custom_mapping:
            custom_text = custom_mapping.get(
                fish_type
            )

            if custom_text is not None:
                return custom_text

        shared_entry = self._get_bait_shared_entry()

        if shared_entry is None:
            return None

        native_mapping = getattr(
            shared_entry,
            'entry_text_size_mapping',
            None
        )

        if native_mapping is None:
            return None

        return native_mapping.get(
            fish_type
        )

    def _get_bait_rarity_text(
        self,
        fish_definition
    ):
        """Build the localized rarity text for the fish tooltip."""
        rarity_factory = self._get_bait_rarity_factory()

        if rarity_factory is None:
            return None

        _, collectible_data, _ = (
            ObjectCollectionData
            .get_collection_info_by_definition(
                fish_definition.id
            )
        )

        if collectible_data is None:
            NotebookInjectorLog.logger().error(
                'Failed to find collection rarity data for BAIT fish '
                'definition {}.'.format(
                    fish_definition.id
                )
            )
            return None

        try:
            rarity_mapping = cast(
                Any,
                ObjectCollectionData.COLLECTION_RARITY_MAPPING
            )

            rarity_data = rarity_mapping[
                collectible_data.rarity
            ]

        except Exception:
            NotebookInjectorLog.logger().exception(
                'Failed to resolve collection rarity mapping for BAIT fish '
                'definition {}.'.format(
                    fish_definition.id
                )
            )
            return None

        return rarity_factory(
            rarity_data.text_value
        )

    def _get_bait_size_text(
        self,
        fish_definition
    ):
        """Resolve the localized fish-size text."""
        fish_type = getattr(
            getattr(
                fish_definition,
                'cls',
                None
            ),
            'fish_type',
            None
        )

        size_text = self._get_bait_size_text_factory(
            fish_type
        )

        if size_text is not None:
            return size_text

        NotebookInjectorLog.logger().error(
            'Failed to resolve fish size text for BAIT fish definition '
            '{} with fish_type {}. No custom value or native EA fallback '
            'was found.'.format(
                fish_definition.id,
                fish_type
            )
        )

        return None

    def _get_bait_tooltip(
        self,
        fish_definition
    ):
        """Build the standard EA fishing-bait tooltip."""
        tooltip_fields = {
            TooltipFields.recipe_name: (
                LocalizationHelperTuning
                .get_object_name(
                    fish_definition
                )
            ),
            TooltipFields.recipe_description: (
                LocalizationHelperTuning
                .get_object_description(
                    fish_definition
                )
            )
        }

        size_text = self._get_bait_size_text(
            fish_definition
        )
        rarity_text = self._get_bait_rarity_text(
            fish_definition
        )

        if size_text is not None:
            tooltip_fields[
                TooltipFields.subtext
            ] = size_text

        if rarity_text is not None:
            tooltip_fields[
                TooltipFields.rarity_text
            ] = rarity_text

        return EntryTooltip(
            HovertipStyle.HOVER_TIP_DEFAULT,
            tooltip_fields
        )

    def _get_bait_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Build the fish entry and discovered bait subentries."""
        if self._runtime_validation_error is not None:
            return None

        fish_definition = _Services.definition_manager().get(
            self.entry_object_definition_id
        )

        if fish_definition is None:
            return None

        snippet_manager = _Services.snippet_manager()
        bait_sublist = []

        for sub_entry in reversed(
            self.sub_entries
        ):
            bait_data = snippet_manager.get(
                sub_entry.sub_entry_id
            )

            if bait_data is None:
                NotebookInjectorLog.logger().error(
                    'BAIT sub-entry snippet {} does not exist or its '
                    'required pack is unavailable. '
                    'Fish definition: {}.'.format(
                        sub_entry.sub_entry_id,
                        fish_definition.id
                    )
                )
                return None

            bait_icon_definition = getattr(
                bait_data,
                'bait_icon_definition',
                None
            )

            if bait_icon_definition is None:
                NotebookInjectorLog.logger().error(
                    'BAIT sub-entry snippet {} has no '
                    'bait_icon_definition.'.format(
                        sub_entry.sub_entry_id
                    )
                )
                return None

            bait_sublist.append(
                SubListData(
                    object_definition=None,
                    item_count=0,
                    num_objects_required=0,
                    is_ingredient=True,
                    new_item=(
                        sub_entry.new_sub_entry
                    ),
                    object_display_name=(
                        bait_data.bait_name()
                    ),
                    item_icon_info_data=(
                        IconInfoData(
                            obj_def_id=(
                                bait_icon_definition.id
                            )
                        )
                    ),
                    item_tooltip=(
                        bait_data.bait_description()
                    )
                )
            )

        return EntryData(
            entry_text=(
                LocalizationHelperTuning
                .get_object_name(
                    fish_definition
                )
            ),
            entry_text_description=None,
            entry_icon_info_data=IconInfoData(
                obj_def_id=fish_definition.id
            ),
            entry_tooltip=(
                self._get_bait_tooltip(
                    fish_definition
                )
            ),
            entry_sublist=bait_sublist,
            entry_sublist_is_sortable=(
                self.entry_sublist_is_sortable
            )
        )

    def _add_sub_entry(
        self,
        new_sub_entry
    ) -> None:
        """Merge one newly discovered bait without duplicating its ID."""
        for sub_entry in self.sub_entries:
            if (
                sub_entry.sub_entry_id
                == new_sub_entry.sub_entry_id
            ):
                return

        self.sub_entries.append(
            new_sub_entry
        )

    # ------------------------------------------------------------------
    # RECIPE AND ANIMAL_FEED
    # ------------------------------------------------------------------

    def _entry_kind_name(self) -> str:
        """Return the current Notebook Injector entry-kind name."""
        return str(
            getattr(
                self.entry_kind,
                'name',
                self.entry_kind
            )
        )

    def _initialize_recipe_entry(self) -> None:
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
            == NotebookInjectorEntryKind.ANIMAL_FEED
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

            if self.tooltip_subtext is None:
                self._set_runtime_validation_error(
                    'entry_kind ANIMAL_FEED requires tooltip_subtext '
                    'for EA-style flavor text.'
                )
                return

            if self.tooltip_rarity is None:
                self._set_runtime_validation_error(
                    'entry_kind ANIMAL_FEED requires tooltip_rarity '
                    'for EA-style rarity text.'
                )
                return

        if self.entry_object_definition_id is None:
            self.entry_object_definition_id = (
                self.final_product.id
            )

    @property
    def recipe_object_definition_id(self) -> int:
        """Return the Recipe tuning ID stored in the first sub-entry."""
        if self.sub_entries:
            return next(
                iter(
                    self.sub_entries
                )
            ).sub_entry_id

        return 0

    def get_recipe_definition(self):
        """Resolve the Recipe used to build this notebook entry."""
        if self.entry_kind not in (
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            return None

        recipe_manager = services.get_instance_manager(
            Types.RECIPE
        )

        return recipe_manager.get(
            self.recipe_object_definition_id
        )

    def is_definition_based(self) -> bool:
        """Return True for entry kinds generated from definitions."""
        return self.entry_kind in (
            NotebookInjectorEntryKind.BAIT,
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        )

    def _get_recipe_tooltip(
        self,
        entry_definition
    ):
        """Build the standard EA Recipe tooltip."""
        return EntryTooltip(
            HovertipStyle.HOVER_TIP_DEFAULT,
            {
                TooltipFields.recipe_name: (
                    LocalizationHelperTuning
                    .get_object_name(
                        entry_definition
                    )
                ),
                TooltipFields.recipe_description: (
                    LocalizationHelperTuning
                    .get_object_description(
                        entry_definition
                    )
                )
            }
        )

    def _get_animal_feed_tooltip(
        self,
        entry_definition
    ):
        """
        Build EA's Animal Feed tooltip with optional custom title/description.
        """
        tooltip_title = self.tooltip_title
        if tooltip_title is None:
            tooltip_title = (
                LocalizationHelperTuning
                .get_object_name(
                    entry_definition
                )
            )

        tooltip_description = self.tooltip_description
        if tooltip_description is None:
            tooltip_description = (
                LocalizationHelperTuning
                .get_object_description(
                    entry_definition
                )
            )

        tooltip_fields = {
            TooltipFields.recipe_name: tooltip_title,
            TooltipFields.recipe_description: tooltip_description,
            TooltipFields.subtext: self.tooltip_subtext,
            TooltipFields.rarity_text: self.tooltip_rarity,
            TooltipFieldsComplete.simoleon_value: (
                entry_definition.price
            )
        }

        if self.tooltip_header is not None:
            tooltip_fields[
                TooltipFields.header
            ] = self.tooltip_header

        return EntryTooltip(
            HovertipStyle.HOVER_TIP_DEFAULT,
            tooltip_fields
        )

    def _get_recipe_based_tooltip(
        self,
        entry_definition
    ):
        """Dispatch the tooltip builder for a Recipe-based entry kind."""
        if (
            self.entry_kind
            == NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            return self._get_animal_feed_tooltip(
                entry_definition
            )

        return self._get_recipe_tooltip(
            entry_definition
        )

    def _get_recipe_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Build dynamic notebook data for a Recipe-based entry."""
        if self._runtime_validation_error is not None:
            return None

        recipe_definition = self.get_recipe_definition()

        if (
            recipe_definition is None
            or self.final_product is None
        ):
            return None

        ingredients_used = {}
        ingredient_display = []

        if recipe_definition.use_ingredients is not None:
            for tuned_ingredient_factory in (
                recipe_definition
                .sorted_ingredient_requirements
            ):
                ingredient_requirement = (
                    tuned_ingredient_factory()
                )

                ingredient_requirement.attempt_satisfy_ingredients(
                    ingredient_cache,
                    ingredients_used
                )

                ingredient_display.append(
                    SubListData(
                        object_definition=None,
                        item_count=(
                            ingredient_requirement
                            .count_satisfied
                        ),
                        num_objects_required=(
                            ingredient_requirement
                            .count_required
                        ),
                        is_ingredient=True,
                        new_item=False,
                        object_display_name=(
                            ingredient_requirement
                            .display_name
                        ),
                        item_icon_info_data=None,
                        item_tooltip=None
                    )
                )

        return EntryData(
            entry_text=(
                LocalizationHelperTuning
                .get_object_name(
                    self.final_product
                )
            ),
            entry_text_description=None,
            entry_icon_info_data=IconInfoData(
                obj_def_id=self.final_product.id
            ),
            entry_tooltip=(
                self._get_recipe_based_tooltip(
                    self.final_product
                )
            ),
            entry_sublist=ingredient_display,
            entry_sublist_is_sortable=(
                self.entry_sublist_is_sortable
            )
        )

    def get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        """Dispatch definition-based entry generation according to entry_kind."""
        if (
            self.entry_kind
            == NotebookInjectorEntryKind.BAIT
        ):
            return self._get_bait_notebook_data(
                ingredient_cache
            )

        if self.entry_kind in (
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            return self._get_recipe_notebook_data(
                ingredient_cache
            )

        return None

    def has_identical_entries(
        self,
        entries
    ) -> bool:
        """Merge BAIT discoveries and reject duplicate dynamic products."""
        if (
            self.entry_kind
            == NotebookInjectorEntryKind.BAIT
        ):
            for entry in entries:
                if (
                    getattr(
                        entry,
                        'entry_kind',
                        None
                    )
                    != self.entry_kind
                ):
                    continue

                if (
                    getattr(
                        entry,
                        'entry_object_definition_id',
                        None
                    )
                    != self.entry_object_definition_id
                ):
                    continue

                for sub_entry in self.sub_entries:
                    entry._add_sub_entry(
                        sub_entry
                    )

                return True

            return False

        if self.entry_kind in (
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            for entry in entries:
                if (
                    getattr(
                        entry,
                        'entry_kind',
                        None
                    )
                    != self.entry_kind
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

        return super().has_identical_entries(
            entries
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_bait_only_tuning(
        cls,
        errors: list
    ) -> None:
        """Reject every BAIT-only field on other entry kinds."""
        bait_fields = []

        if cls.bait_fish_definition is not None:
            bait_fields.append(
                'bait_fish_definition'
            )

        if cls.bait_snippets:
            bait_fields.append(
                'bait_snippets'
            )

        if cls.entry_text_rarity is not None:
            bait_fields.append(
                'entry_text_rarity'
            )

        if cls.entry_text_size_mapping:
            bait_fields.append(
                'entry_text_size_mapping'
            )

        if bait_fields:
            errors.append(
                'The following fields are only allowed for '
                'entry_kind BAIT: {}.'.format(
                    ', '.join(
                        bait_fields
                    )
                )
            )

    @classmethod
    def _validate_bait_tuning(
        cls,
        errors: list
    ) -> None:
        """Validate optional static BAIT source data."""
        if (
            cls.bait_snippets
            and cls.bait_fish_definition is None
        ):
            errors.append(
                'bait_snippets requires bait_fish_definition. '
                'Either tune both for static create_new_entry usage, '
                'or omit both for EA runtime participant usage.'
            )

    @classmethod
    def _validate_tooltip_fields(
        cls,
        errors: list
    ) -> None:
        """Validate the localized EA TooltipFields mapping."""
        raw_tooltip_fields = cast(
            Any,
            getattr(
                cls,
                'tooltip_fields',
                None
            )
        )

        if not raw_tooltip_fields:
            return

        items_method = getattr(
            raw_tooltip_fields,
            'items',
            None
        )

        if not callable(items_method):
            errors.append(
                'tooltip_fields must be a mapping of TooltipFields keys to '
                'localized strings.'
            )
            return

        tooltip_items = cast(
            Iterable[Tuple[Any, Any]],
            items_method()
        )

        for field, value in tooltip_items:
            if value is None:
                errors.append(
                    'tooltip_fields key {} has no localized value.'.format(
                        getattr(
                            field,
                            'name',
                            field
                        )
                    )
                )

    @classmethod
    def _validate_default_tuning(
        cls,
        errors: list
    ) -> None:
        """Validate fields used by a static DEFAULT entry."""
        if cls.entry_text is None:
            errors.append(
                'entry_text is required for entry_kind DEFAULT.'
            )

        for index, item in enumerate(
            cls.entry_sublist or ()
        ):
            if item.object_definition is None:
                errors.append(
                    'entry_sublist item {} has no '
                    'object_definition.'.format(
                        index
                    )
                )

            if item.num_objects_required < 0:
                errors.append(
                    'entry_sublist item {} has a negative '
                    'num_objects_required value.'.format(
                        index
                    )
                )

        cls._validate_tooltip_fields(
            errors
        )

        animal_feed_helpers = []
        for field_name in (
            'tooltip_title',
            'tooltip_description',
            'tooltip_header',
            'tooltip_subtext',
            'tooltip_rarity'
        ):
            if getattr(
                cls,
                field_name,
                None
            ) is not None:
                animal_feed_helpers.append(
                    field_name
                )

        if animal_feed_helpers:
            errors.append(
                'entry_kind DEFAULT uses tooltip_fields and does not allow '
                'ANIMAL_FEED tooltip helper fields: {}.'.format(
                    ', '.join(
                        animal_feed_helpers
                    )
                )
            )

    @classmethod
    def _validate_animal_feed_tuning(
        cls,
        errors: list
    ) -> None:
        """Validate EA-required and optional ANIMAL_FEED tooltip fields."""
        if cls.tooltip_subtext is None:
            errors.append(
                'tooltip_subtext is required for entry_kind ANIMAL_FEED '
                'because EA uses it as the animal-feed flavor text.'
            )

        if cls.tooltip_rarity is None:
            errors.append(
                'tooltip_rarity is required for entry_kind ANIMAL_FEED '
                'because EA uses it as the animal-feed rarity text.'
            )

    @classmethod
    def _dynamic_forbidden_fields(
        cls,
        allowed_fields=()
    ) -> list:
        """Return static fields that conflict with dynamic display."""
        allowed_field_names = set(
            allowed_fields
        )
        field_values = (
            (
                'entry_text',
                cls.entry_text
            ),
            (
                'entry_text_description',
                cls.entry_text_description
            ),
            (
                'entry_icon',
                cls.entry_icon
            ),
            (
                'entry_sublist',
                cls.entry_sublist
            ),
            (
                'tooltip_fields',
                cls.tooltip_fields
            ),
            (
                'tooltip_title',
                cls.tooltip_title
            ),
            (
                'tooltip_description',
                cls.tooltip_description
            ),
            (
                'tooltip_header',
                cls.tooltip_header
            ),
            (
                'tooltip_subtext',
                cls.tooltip_subtext
            ),
            (
                'tooltip_rarity',
                cls.tooltip_rarity
            )
        )
        collection_fields = {
            'entry_sublist',
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

            elif value is not None:
                forbidden_fields.append(
                    name
                )

        return forbidden_fields

    @classmethod
    def _validate_dynamic_tuning(
        cls,
        errors: list,
        kind_name: str,
        source_description: str,
        allowed_fields=(),
        allow_custom_tooltip_style: bool = False
    ) -> None:
        """Reject fields generated by a definition-based entry kind."""
        forbidden_fields = cls._dynamic_forbidden_fields(
            allowed_fields
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

    @classmethod
    def validate_tuning(cls) -> tuple:
        """Validate the XML fields allowed for each entry kind."""
        errors = []

        implemented_kinds = (
            NotebookInjectorEntryKind.DEFAULT,
            NotebookInjectorEntryKind.BAIT,
            NotebookInjectorEntryKind.RECIPE,
            NotebookInjectorEntryKind.ANIMAL_FEED
        )

        if cls.entry_kind not in implemented_kinds:
            return (
                'Entry kind {} is not implemented yet.'.format(
                    getattr(
                        cls.entry_kind,
                        'name',
                        cls.entry_kind
                    )
                ),
            )

        if (
            cls.entry_sublist_include_new is True
            and cls.entry_sublist_sortable is not True
        ):
            errors.append(
                'entry_sublist_include_new requires '
                'entry_sublist_sortable to be True.'
            )

        if (
            cls.entry_kind
            != NotebookInjectorEntryKind.BAIT
        ):
            cls._validate_bait_only_tuning(
                errors
            )

        if (
            cls.entry_kind
            == NotebookInjectorEntryKind.DEFAULT
        ):
            cls._validate_default_tuning(
                errors
            )

        elif (
            cls.entry_kind
            == NotebookInjectorEntryKind.BAIT
        ):
            cls._validate_bait_tuning(
                errors
            )
            cls._validate_dynamic_tuning(
                errors,
                'BAIT',
                'the fish definition and EA bait tuning'
            )

        elif (
            cls.entry_kind
            == NotebookInjectorEntryKind.RECIPE
        ):
            cls._validate_dynamic_tuning(
                errors,
                'RECIPE',
                'the Recipe tuning'
            )

        elif (
            cls.entry_kind
            == NotebookInjectorEntryKind.ANIMAL_FEED
        ):
            cls._validate_animal_feed_tuning(
                errors
            )
            cls._validate_dynamic_tuning(
                errors,
                'ANIMAL_FEED',
                'the Recipe final product and ANIMAL_FEED tooltip tuning',
                allowed_fields=(
                    'tooltip_title',
                    'tooltip_description',
                    'tooltip_header',
                    'tooltip_subtext',
                    'tooltip_rarity'
                )
            )

        return tuple(
            errors
        )

    @classmethod
    def supports_subcategory_format(
        cls,
        format_value: int
    ) -> bool:
        """Allow every native UI format except Secret Scandal."""
        return (
            format_value
            != _SECRET_SCANDAL_FORMAT_VALUE
        )

    # ------------------------------------------------------------------
    # DEFAULT static data builders
    # ------------------------------------------------------------------

    @classmethod
    def _build_entry_tooltip(cls):
        """Convert tooltip_fields into EA's EntryTooltip structure."""
        raw_tooltip_fields = cast(
            Any,
            getattr(
                cls,
                'tooltip_fields',
                None
            )
        )

        if not raw_tooltip_fields:
            return None

        items_method = getattr(
            raw_tooltip_fields,
            'items',
            None
        )

        if not callable(items_method):
            raise TypeError(
                'tooltip_fields must provide an items() method.'
            )

        tooltip_items = cast(
            Iterable[Tuple[Any, Any]],
            items_method()
        )
        tooltip_fields = dict(
            tooltip_items
        )

        if not tooltip_fields:
            return None

        return EntryTooltip(
            cls.tooltip_style,
            tooltip_fields
        )

    @classmethod
    def _build_entry_sublist_sorting(cls):
        """
        Convert the flat sorting fields into EA's optional sorting data.
        """
        if cls.entry_sublist_sortable is not True:
            return None

        return script.immutable_slots({
            'include_new_entry': (
                cls.entry_sublist_include_new is True
            )
        })

    @classmethod
    def _build_entry_sublist(cls) -> tuple:
        """Convert the flat tuned sublist into EA SubListData objects."""
        if not cls.entry_sublist:
            return ()

        sublist = []

        for item in cls.entry_sublist:
            sublist.append(
                SubListData(
                    object_definition=(
                        item.object_definition
                    ),
                    item_count=0,
                    num_objects_required=(
                        item.num_objects_required
                    ),
                    is_ingredient=False,
                    new_item=False,
                    object_display_name=None,
                    item_icon_info_data=None,
                    item_tooltip=None
                )
            )

        return tuple(
            sublist
        )

    @classmethod
    def prepare_runtime_data(cls) -> None:
        """
        Materialize the EA data structures expected by NotebookEntry.

        A malformed entry is isolated instead of interrupting preparation
        of every other Notebook Injector entry.
        """
        cls._runtime_prepare_error = None

        try:
            if (
                cls.entry_kind
                == NotebookInjectorEntryKind.DEFAULT
            ):
                cls.entry_sublist = cls._build_entry_sublist()
                cls.entry_tooltip = cls._build_entry_tooltip()

            else:
                cls.entry_sublist = ()
                cls.entry_tooltip = None

            cls.entry_sublist_is_sortable = (
                cls._build_entry_sublist_sorting()
            )

        except Exception:
            cls._runtime_prepare_error = (
                'An exception occurred while preparing this entry tuning '
                'for runtime use. Check the Notebook Injector log.'
            )

            cls.entry_sublist = ()
            cls.entry_tooltip = None
            cls.entry_sublist_is_sortable = None

            NotebookInjectorLog.logger().exception(
                'Failed to prepare Notebook Injector entry {} '
                '(tuning {}). The entry will be blocked at unlock '
                'time, while other entries continue loading.'.format(
                    getattr(
                        cls,
                        '__name__',
                        cls
                    ),
                    getattr(
                        cls,
                        'guid64',
                        'unknown'
                    )
                )
            )
