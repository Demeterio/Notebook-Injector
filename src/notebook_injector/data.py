# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import notebook_injector.script as script
from services import get_instance_manager
from sims4.resources import Types, get_resource_key
from _sims4_collections import frozendict # pyright: ignore[reportMissingImports]
from typing import Any, ClassVar, TYPE_CHECKING, cast
from notebook_injector.error import (
    NiErrorSnippetNoInject,
    NiErrorCatUndefinedNoInject,
    NiErrorCatFormatNoInject,
    NiErrorCatExistsNoInject,
    NiErrorCatUndefinedInSubNoInject,
    NiErrorCatInSubDoesNotExistNoInject,
    NiErrorSubUndefinedNoInject,
    NiErrorSubFormatNoInject,
    NiErrorSubExistsNoInject,
    NiErrorAnEntryExistsNoInject,
    NiErrorEntryExistsNoInject,
    NiErrorIsSortableFalseNoInject,
    NiErrorEnumReservedNameNoInject,
    NiErrorEnumAllocationNoInject,
    NiErrorEnumConflictNoInject,
    NiErrorEntryUndefinedNoInject,
    NiErrorSecretScandalFormatNoInject,
    NiErrorUnsupportedEntryTypeNoInject,
    NiErrorEntryValidationNoInject,
    NiErrorEntryDoesNotExistNoInject
)
from notebook_injector.ver import NotebookInjectorInfo
from notebook_injector.log import NotebookInjectorLog, ea_log
from notebook_injector.cheat import NotebookInjectorCheat
from notebook_injector.new_entry import NotebookInjectorNewEntry
from notebook_injector.inject import (
    on_load_complete,
    inject_enum
)
from notebook_injector.entry_validation import (
    is_blocked_notebook_entry_type,
    notebook_entry_class_identity,
    notebook_entry_type_value,
    validate_notebook_injector_entry
)
from notebook_injector.assignment_sanitizer import (
    sanitize_registered_entry_assignments
)
from notebook_injector import registry, enum_registry
from interactions.utils.tunable_icon import TunableIconAllPacks
from sims4.localization import TunableLocalizedString
from sims4.tuning.instances import HashedTunedInstanceMetaclass
from sims4.tuning.tunable import Tunable, TunableTuple, TunableEnumEntry, TunableList, TunableVariant
from ui.notebook_tuning import NotebookEntryType, NotebookTuning, NotebookCategories, NotebookSubCategories


_NotebookCategories = cast(
    Any,
    NotebookCategories
)
_NotebookSubCategories = cast(
    Any,
    NotebookSubCategories
)
_TunableTuple = cast(
    Any,
    TunableTuple
)


class NotebookInjectorDataHelper(script.Objectless):
    __slots__ = ()

    @staticmethod
    def validate_min_version(tuning, logger) -> None:
        min_version = int(
            getattr(tuning, 'min_version', 1) or 1
        )
        current_version = NotebookInjectorInfo.version()
        required_version = (
            NotebookInjectorInfo.required_version()
        )
        if required_version is None:
            required_version = 0
        NotebookInjectorCheat.mods(
            tuning,
            min_version
        )
        logger.debug(
            f'Core ABI version required: {min_version}'
        )
        if (
            min_version > current_version
            and min_version > required_version
        ):
            NotebookInjectorInfo.required_version(
                min_version
            )
            logger.warning(
                'Minimum core ABI version of Notebook Injector '
                f'required: v{min_version}. Issues can occur.'
            )

    @staticmethod
    def category_exists_for_subcategory(
        category_key: str,
        pending_categories: dict
    ) -> bool:
        if category_key in pending_categories:
            return True
        if script.cat_check(category_key) is False:
            return False
        try:
            category = _NotebookCategories[
                category_key
            ]
        except Exception:
            return False
        notebook_mapping = cast(
            Any,
            NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
        )
        return category in notebook_mapping

    @staticmethod
    def existing_category_target(category_target):
        if hasattr(category_target, 'existing_category'):
            category = category_target.existing_category
            if category is None or category == NotebookCategories.INVALID:
                return None
            return category.name
        return None

    @staticmethod
    def custom_category_target(category_target):
        if hasattr(category_target, 'custom_category_key'):
            return category_target.custom_category_key
        return None

    @staticmethod
    def category_target_key(category_target):
        existing_category = NotebookInjectorDataHelper.existing_category_target(category_target)
        if existing_category:
            return existing_category
        custom_category = NotebookInjectorDataHelper.custom_category_target(category_target)
        if custom_category:
            return custom_category
        return None

    @staticmethod
    def existing_subcategory_target(subcategory_target):
        if hasattr(subcategory_target, 'existing_subcategory'):
            subcategory = subcategory_target.existing_subcategory
            if subcategory is None or subcategory == NotebookSubCategories.INVALID:
                return None
            return subcategory.name
        return None

    @staticmethod
    def custom_subcategory_target(subcategory_target):
        if hasattr(subcategory_target, 'custom_subcategory_key'):
            return subcategory_target.custom_subcategory_key
        return None

    @staticmethod
    def subcategory_target_key(subcategory_target):
        existing_subcategory = NotebookInjectorDataHelper.existing_subcategory_target(subcategory_target)
        if existing_subcategory:
            return existing_subcategory
        custom_subcategory = NotebookInjectorDataHelper.custom_subcategory_target(subcategory_target)
        if custom_subcategory:
            return custom_subcategory
        return None

    @staticmethod
    def copy_existing_category_mapping(category) -> dict:
        notebook_mapping = cast(
            Any,
            NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
        )
        existing_mapping = notebook_mapping.get(
            category
        )
        if existing_mapping is None:
            return {}
        copied_mapping = dict(existing_mapping)
        copied_mapping['subcategories'] = dict(
            copied_mapping.get(
                'subcategories',
                {}
            )
        )
        return copied_mapping

    @staticmethod
    def mapping_format(d_cat: dict, d_subcat: dict) -> dict:
        final_dict = {}
        if d_cat:
            for key, value in d_cat.items():
                final_dict[_NotebookCategories[key]] = {
                    'category_description': value['description'],
                    'category_icon': value['icon'],
                    'category_large_icon': value['large_icon'],
                    'category_name': value['name'],
                    'display_subcategory_title': value['display_subcategory_title'],
                    'subcategories': {}
                }
        if d_subcat:
            for key, value in d_subcat.items():
                category = _NotebookCategories[value['category_key']]
                if category not in final_dict:
                    final_dict[category] = NotebookInjectorDataHelper.copy_existing_category_mapping(category)
                dict_temp_texts = {
                    'has_list_text': value['has_list_text'],
                    'no_list_text': value['no_list_text']
                }
                if value['sortable'] is True:
                    dict_temp_sort = {'include_new_entry': value['sortable_include_new_entry']}
                    dict_temp_sort = script.immutable_slots(dict_temp_sort)
                else:
                    dict_temp_sort = None
                dict_temp = {
                    'entry_list_texts': script.immutable_slots(dict_temp_texts),
                    'format_type': value['format'],
                    'is_sortable': dict_temp_sort,
                    'show_max_entries': value['max_entries'],
                    'subcategory_icon': value['icon'],
                    'subcategory_name': value['subcategory_name'],
                    'subcategory_tooltip': value['tooltip']
                }
                final_dict[category]['subcategories'].update({
                    _NotebookSubCategories[key]: script.immutable_slots(dict_temp)
                })
        return final_dict

    @staticmethod
    def update_tuning(d: dict) -> dict:
        current_mapping = cast(
            Any,
            NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
        )
        final_dict = {}
        for key, value in current_mapping.items():
            final_dict[key] = value
        for key, value in d.items():
            final_dict[key] = value
            final_dict[key]['subcategories'] = frozendict(
                final_dict[key]['subcategories']
            )
            final_dict[key] = script.immutable_slots(
                final_dict[key]
            )
        delattr(
            NotebookTuning,
            'NOTEBOOK_CATEGORY_MAPPING'
        )
        setattr(
            NotebookTuning,
            'NOTEBOOK_CATEGORY_MAPPING',
            final_dict
        )
        return final_dict
    
    @staticmethod
    def optional_value(value):
        return value if value else None

    @staticmethod
    def optional_positive_int(value):
        if value and value > 0:
            return value
        return None


class NotebookInjectorCategory(
    metaclass=HashedTunedInstanceMetaclass,
    manager=get_instance_manager(Types.SNIPPET)
):
    if TYPE_CHECKING:
        guid64: ClassVar[int]
        category_key: ClassVar[Any]
        category_description: ClassVar[Any]
        category_icon: ClassVar[Any]
        category_large_icon: ClassVar[Any]
        category_name: ClassVar[Any]
        display_subcategory_title: ClassVar[Any]
        min_version: ClassVar[Any]
    INSTANCE_TUNABLES = {
        'min_version': Tunable(
            description='Core ABI version of Notebook Injector required to run this category snippet',
            tunable_type=int,
            default=1),
        'category_key': Tunable(
            description='Unique key of the custom notebook category',
            tunable_type=str,
            default=None),
        'category_description': TunableLocalizedString(
            description='Description corresponding to the notebook category',
            default=None, # pyright: ignore[reportArgumentType]
            allow_none=True),
        'category_icon': TunableIconAllPacks(
            description='Icon to display on the notebook UI corresponding to the category',
            allow_none=True),
        'category_large_icon': TunableIconAllPacks(
            description='Large icon to display on the notebook UI corresponding to the category',
            allow_none=True),
        'category_name': TunableLocalizedString(
            description='Name displayed corresponding to the category',
            allow_none=False),
        'display_subcategory_title': Tunable(
            description='If checked, the selected subcategory name will be displayed in the notebook category page',
            tunable_type=bool,
            default=False)
    }

    @classmethod
    def _tuning_loaded_callback(cls) -> None:
        logger = NotebookInjectorLog.logger()
        logger.debug(f'Class/tuning XML: {cls}')
        logger.debug('Start...')
        error_context = None
        try:
            NotebookInjectorDataHelper.validate_min_version(cls, logger)
            if cls.category_key is None or cls.category_name is None:
                raise NiErrorCatUndefinedNoInject
            elif script.tuning_key_name(cls.category_key) is False:
                raise NiErrorCatFormatNoInject
            reservation = enum_registry.reserved_category_info(
                cls.category_key
            )
            if reservation is not None:
                error_context = (
                    'Enum type: category; key: {}; '
                    'reserved owner: {}; reserved value: {}.'
                ).format(
                    cls.category_key,
                    reservation['display_name'],
                    reservation['value']
                )
                raise NiErrorEnumReservedNameNoInject
            elif script.cat_check(cls.category_key) is True or registry.has_registered_category(cls.category_key):
                raise NiErrorCatExistsNoInject
            fallback_category_icon = get_resource_key(NotebookInjectorNewEntry.get_icon_category(), Types.PNG)
            fallback_category_large_icon = get_resource_key(NotebookInjectorNewEntry.get_icon_category_large(), Types.PNG)
            icon_category = cls.category_icon if cls.category_icon else fallback_category_icon
            icon_category_large = cls.category_large_icon if cls.category_large_icon else fallback_category_large_icon
            if not icon_category_large:
                icon_category_large = fallback_category_large_icon
            registry.register_category(cls.category_key, {
                'name': cls.category_name,
                'description': (
                    cls.category_description
                    if cls.category_description
                    else None
                ),
                'icon': icon_category,
                'large_icon': icon_category_large,
                'display_subcategory_title': (
                    cls.display_subcategory_title is True
                ),
                'source_tuning_id': cls.guid64,
                'source_tuning_name': cls.__name__
            })
            logger.debug(f'Category registered: {cls.category_key}')
            logger.debug('...Completed\n\n')
        except NiErrorCatUndefinedNoInject:
            NiErrorCatUndefinedNoInject().err(logger)
        except NiErrorCatFormatNoInject:
            NiErrorCatFormatNoInject().err(logger)
        except NiErrorCatExistsNoInject:
            NiErrorCatExistsNoInject().err(logger)
        except NiErrorEnumReservedNameNoInject:
            NiErrorEnumReservedNameNoInject().err(
                logger,
                context=error_context,
                ea_log=False
            )
        except Exception:
            NiErrorSnippetNoInject().err(logger)

    def __repr__(self) -> str:
        return f'<NotebookInjectorCategory:({self.__name__})>'

    def __str__(self) -> str:
        return self.__name__


class NotebookInjectorSubcategory(
    metaclass=HashedTunedInstanceMetaclass,
    manager=get_instance_manager(Types.SNIPPET)
):
    if TYPE_CHECKING:
        guid64: ClassVar[int]
        min_version: ClassVar[Any]
        category_target: ClassVar[Any]
        subcategory_key: ClassVar[Any]
        list_texts: ClassVar[Any]
        format_type: ClassVar[Any]
        show_max_entries: ClassVar[Any]
        is_sortable: ClassVar[Any]
        subcategory_icon: ClassVar[Any]
        subcategory_name: ClassVar[Any]
        subcategory_tooltip: ClassVar[Any]
    INSTANCE_TUNABLES = {
        'min_version': Tunable(
            description='Core ABI version of Notebook Injector required to run this subcategory snippet',
            tunable_type=int,
            default=1),
        'category_target': TunableVariant(
            description='Notebook category that will contain this subcategory',
            existing_category=_TunableTuple(
                existing_category=TunableEnumEntry(
                    description='Existing EA/game notebook category',
                    tunable_type=NotebookCategories,
                    default=NotebookCategories.INVALID)),
            custom_category=_TunableTuple(
                custom_category_key=Tunable(
                    description='Custom Notebook Injector category key',
                    tunable_type=str,
                    default=None)),
            default='custom_category'),
        'subcategory_key': Tunable(
            description='Unique key of the custom notebook subcategory',
            tunable_type=str,
            default=None),
        'list_texts': _TunableTuple(
            description='Text that will be shown in entry list',
            has_list_text=TunableLocalizedString(
                description='Text that will be shown when entry has list',
                default=None, # pyright: ignore[reportArgumentType]
                allow_none=True),
            no_list_text=TunableLocalizedString(
                description='Text that will be shown when entry has no list',
                default=None, # pyright: ignore[reportArgumentType]
                allow_none=True)),
        'format_type': TunableEnumEntry(
            description='Type of entry this subcategory will display',
            tunable_type=NotebookEntryType,
            default=NotebookEntryType.EXPANDABLE_DATA),
        'show_max_entries': Tunable(
            description='UI will use this value to display the amount of missing entries for the subcategory',
            tunable_type=int,
            default=0),
        'is_sortable': _TunableTuple(
            description='Settings for sorting entries',
            enabled=Tunable(
                description='If checked, entries of subcategory will be sorted alphabetically',
                tunable_type=bool,
                default=False),
            include_new_entry=Tunable(
                description='If checked, entries that have new entry tag will be sorted. Enabled must be True',
                tunable_type=bool,
                default=False)),
        'subcategory_icon': TunableIconAllPacks(
            description='Icon to display on the notebook UI corresponding to a subcategory',
            allow_none=True),
        'subcategory_name': TunableLocalizedString(
            description='Name corresponding to a notebook subcategory',
            allow_none=False),
        'subcategory_tooltip': TunableLocalizedString(
            description='Tooltip to be displayed when a player mouses over a subcategory icon',
            default=None, # pyright: ignore[reportArgumentType]
            allow_none=True)
    }

    @classmethod
    def _tuning_loaded_callback(cls) -> None:
        logger = NotebookInjectorLog.logger()
        logger.debug(f'Class/tuning XML: {cls}')
        logger.debug('Start...')
        error_context = None
        try:
            NotebookInjectorDataHelper.validate_min_version(cls, logger)
            category_key = NotebookInjectorDataHelper.category_target_key(cls.category_target)
            if category_key is None:
                raise NiErrorCatUndefinedInSubNoInject
            elif NotebookInjectorDataHelper.custom_category_target(cls.category_target) is not None \
                    and script.tuning_key_name(category_key) is False:
                raise NiErrorCatFormatNoInject
            if cls.subcategory_key is None or cls.subcategory_name is None:
                raise NiErrorSubUndefinedNoInject
            elif script.tuning_key_name(cls.subcategory_key) is False:
                raise NiErrorSubFormatNoInject
            reservation = enum_registry.reserved_subcategory_info(
                cls.subcategory_key
            )
            if reservation is not None:
                error_context = (
                    'Enum type: subcategory; key: {}; '
                    'reserved owner: {}; reserved value: {}.'
                ).format(
                    cls.subcategory_key,
                    reservation['display_name'],
                    reservation['value']
                )
                raise NiErrorEnumReservedNameNoInject
            elif script.subcat_check(cls.subcategory_key) is True or registry.has_registered_subcategory(cls.subcategory_key):
                raise NiErrorSubExistsNoInject
            elif cls.is_sortable.include_new_entry is True and cls.is_sortable.enabled is False:
                raise NiErrorIsSortableFalseNoInject
            elif (
                cls.format_type
                == NotebookEntryType
                .NOTEBOOK_EXPANDABLE_SECRET_SCANDAL
            ):
                raise NiErrorSecretScandalFormatNoInject
            icon_subcat = cls.subcategory_icon
            if not icon_subcat:
                icon_subcat = get_resource_key(NotebookInjectorNewEntry.get_icon_subcat(), Types.PNG)
                if not icon_subcat:
                    icon_subcat = None
            registry.register_subcategory(cls.subcategory_key, {
                'category_key': category_key,
                'subcategory_name': cls.subcategory_name,
                'has_list_text': (
                    NotebookInjectorDataHelper.optional_value(
                        cls.list_texts.has_list_text
                    )
                ),
                'no_list_text': (
                    NotebookInjectorDataHelper.optional_value(
                        cls.list_texts.no_list_text
                    )
                ),
                'format': (
                    cls.format_type
                    if cls.format_type
                    else NotebookEntryType.EXPANDABLE_DATA
                ),
                'max_entries': (
                    NotebookInjectorDataHelper.optional_positive_int(
                        cls.show_max_entries
                    )
                ),
                'sortable': cls.is_sortable.enabled is True,
                'sortable_include_new_entry': (
                    cls.is_sortable.include_new_entry is True
                ),
                'icon': icon_subcat,
                'tooltip': (
                    cls.subcategory_tooltip
                    if cls.subcategory_tooltip is not None
                    else cls.subcategory_name
                ),
                'source_tuning_id': cls.guid64,
                'source_tuning_name': cls.__name__
            })
            logger.debug(f'Subcategory registered: {cls.subcategory_key}')
            logger.debug('...Completed\n\n')
        except NiErrorCatUndefinedInSubNoInject:
            NiErrorCatUndefinedInSubNoInject().err(logger)
        except NiErrorCatFormatNoInject:
            NiErrorCatFormatNoInject().err(logger)
        except NiErrorSubUndefinedNoInject:
            NiErrorSubUndefinedNoInject().err(logger)
        except NiErrorSubFormatNoInject:
            NiErrorSubFormatNoInject().err(logger)
        except NiErrorSubExistsNoInject:
            NiErrorSubExistsNoInject().err(logger)
        except NiErrorIsSortableFalseNoInject:
            NiErrorIsSortableFalseNoInject().err(logger)
        except NiErrorEnumReservedNameNoInject:
            NiErrorEnumReservedNameNoInject().err(
                logger,
                context=error_context,
                ea_log=False
            )
        except NiErrorSecretScandalFormatNoInject:
            NiErrorSecretScandalFormatNoInject().err(
                logger
            )
        except Exception:
            NiErrorSnippetNoInject().err(logger)

    def __repr__(self) -> str:
        return f'<NotebookInjectorSubcategory:({self.__name__})>'

    def __str__(self) -> str:
        return self.__name__


class NotebookInjectorEntryAssignment(
    metaclass=HashedTunedInstanceMetaclass,
    manager=get_instance_manager(Types.SNIPPET)
):
    if TYPE_CHECKING:
        guid64: ClassVar[int]
        min_version: ClassVar[Any]
        subcategory_target: ClassVar[Any]
        entries: ClassVar[Any]
    INSTANCE_TUNABLES = {
        'min_version': Tunable(
            description='Core ABI version of Notebook Injector required to run this entry assignment snippet',
            tunable_type=int,
            default=1),
        'subcategory_target': TunableVariant(
            description='Notebook subcategory that will contain these entries',
            existing_subcategory=_TunableTuple(
                existing_subcategory=TunableEnumEntry(
                    description='Existing EA/game notebook subcategory',
                    tunable_type=NotebookSubCategories,
                    default=NotebookSubCategories.INVALID)),
            custom_subcategory=_TunableTuple(
                custom_subcategory_key=Tunable(
                    description='Custom Notebook Injector subcategory key',
                    tunable_type=str,
                    default=None)),
            default='custom_subcategory'),
        'entries': TunableList(
            description='Notebook entries to register in this subcategory',
            tunable=Tunable(
                description='Notebook entry tuning id',
                default=None,
                tunable_type=int),
            allow_none=True,
            unique_entries=True)
    }

    @classmethod
    def _tuning_loaded_callback(cls) -> None:
        logger = NotebookInjectorLog.logger()
        logger.debug(f'Class/tuning XML: {cls}')
        logger.debug('Start...')
        try:
            NotebookInjectorDataHelper.validate_min_version(cls, logger)
            subcategory_key = NotebookInjectorDataHelper.subcategory_target_key(cls.subcategory_target)
            if subcategory_key is None:
                raise NiErrorSubUndefinedNoInject
            elif NotebookInjectorDataHelper.custom_subcategory_target(cls.subcategory_target) is not None \
                    and script.tuning_key_name(subcategory_key) is False:
                raise NiErrorSubFormatNoInject
            if not cls.entries:
                raise NiErrorEntryUndefinedNoInject
            registry.register_entry_assignment(cls.guid64, {
                'subcategory_key': subcategory_key,
                'entries': tuple(cls.entries),
                'source_tuning_id': cls.guid64,
                'source_tuning_name': cls.__name__
            })
            logger.debug(f'Entry assignment added for subcategory: {subcategory_key}')
            logger.debug('...Completed\n\n')
        except NiErrorSubUndefinedNoInject:
            NiErrorSubUndefinedNoInject().err(logger)
        except NiErrorSubFormatNoInject:
            NiErrorSubFormatNoInject().err(logger)
        except NiErrorEntryUndefinedNoInject:
            NiErrorEntryUndefinedNoInject().err(logger)
        except Exception:
            NiErrorSnippetNoInject().err(logger)

    def __repr__(self) -> str:
        return f'<NotebookInjectorEntryAssignment:({self.__name__})>'

    def __str__(self) -> str:
        return self.__name__


def _log_skipped_subcategory(
    subcategory_key: str,
    subcategory_data,
    error: str
) -> None:
    """
    Log one invalid custom subcategory without blocking the other addons.
    """
    if isinstance(
        subcategory_data,
        dict
    ):
        category_key = subcategory_data.get(
            'category_key',
            'unknown'
        )
        source_tuning_id = subcategory_data.get(
            'source_tuning_id',
            'unknown'
        )
        source_tuning_name = subcategory_data.get(
            'source_tuning_name',
            'unknown'
        )
    else:
        category_key = 'unknown'
        source_tuning_id = 'unknown'
        source_tuning_name = 'unknown'

    NotebookInjectorLog.logger().error(
        'Invalid Notebook Injector subcategory skipped.\n'
        'Subcategory: {}\n'
        'Category: {}\n'
        'Tuning ID: {}\n'
        'Tuning: {}\n'
        'Error: {}\n'.format(
            subcategory_key,
            category_key,
            source_tuning_id,
            source_tuning_name,
            error
        )
    )

    ea_log.error(
        'Notebook Injector skipped invalid subcategory tuning {}. '
        'Check demeterio_notebookinjector_log.txt.'.format(
            source_tuning_id
        )
    )


def _sanitize_registered_subcategories(
    categories: dict,
    subcategories: dict
) -> dict:
    """
    Return only subcategories whose target category exists.

    One malformed addon must not prevent valid categories, subcategories,
    or entries from other addons from being injected.
    """
    accepted_subcategories = {}

    for subcategory_key in sorted(
        subcategories
    ):
        subcategory_data = subcategories[
            subcategory_key
        ]

        if not isinstance(
            subcategory_data,
            dict
        ):
            _log_skipped_subcategory(
                subcategory_key,
                subcategory_data,
                (
                    'Registered subcategory data is not a dictionary.'
                )
            )
            continue

        category_key = subcategory_data.get(
            'category_key'
        )

        if (
            not isinstance(
                category_key,
                str
            )
            or not category_key
        ):
            _log_skipped_subcategory(
                subcategory_key,
                subcategory_data,
                (
                    'category_key is missing or invalid.'
                )
            )
            continue

        if (
            NotebookInjectorDataHelper
            .category_exists_for_subcategory(
                category_key,
                categories
            )
            is False
        ):
            _log_skipped_subcategory(
                subcategory_key,
                subcategory_data,
                (
                    'Target category {} does not exist.'
                    .format(
                        category_key
                    )
                )
            )
            continue

        accepted_subcategories[
            subcategory_key
        ] = subcategory_data

    return accepted_subcategories


@on_load_complete(Types.SNIPPET)
def _apply_notebook_injector_data(manager=None) -> None: # pyright: ignore[reportGeneralTypeIssues]
    logger = NotebookInjectorLog.logger()
    logger.debug(
        'Function: Apply registered Notebook Injector data'
    )
    logger.debug('Start...')
    dict_cat = dict(
        registry.registered_categories()
    )

    raw_subcategories = dict(
        registry.registered_subcategories()
    )

    dict_subcat = (
        _sanitize_registered_subcategories(
            dict_cat,
            raw_subcategories
        )
    )

    assignments = (
        sanitize_registered_entry_assignments(
            dict_subcat
        )
    )

    dict_entry = {}
    entry_sources = {}
    error_context = None
    try:
        enum_registry.snapshot_notebook_enums()
        enum_registry.capture_expected_notebook_enums()
        if enum_registry.has_startup_conflicts() is True:
            raise enum_registry.EnumConflictError(
                'Known enum reservation conflict.'
            )
        notebook_entry_manager = get_instance_manager(
            Types.NOTEBOOK_ENTRY
        )
        for assignment_key, assignment in assignments.items():
            subcategory_key = assignment['subcategory_key']
            if subcategory_key in dict_subcat:
                category_key = dict_subcat[
                    subcategory_key
                ]['category_key']
                format_type = dict_subcat[
                    subcategory_key
                ]['format']
            elif script.subcat_check(subcategory_key) is True:
                category_key = (
                    registry
                    .find_category_key_for_existing_subcategory(
                        subcategory_key
                    )
                )
                if category_key is None:
                    error_context = (
                        'Existing subcategory {} has no category '
                        'in NOTEBOOK_CATEGORY_MAPPING.'
                    ).format(
                        subcategory_key,
                    )
                    raise NiErrorCatInSubDoesNotExistNoInject
                notebook_mapping = cast(
                    Any,
                    NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
                )
                category_mapping = notebook_mapping[
                    _NotebookCategories[category_key]
                ]
                format_type = category_mapping.subcategories[
                    _NotebookSubCategories[subcategory_key]
                ].format_type
            else:
                error_context = (
                    'Entry assignment {} targets missing '
                    'subcategory {}.'
                ).format(
                    assignment_key,
                    subcategory_key
                )
                raise NiErrorSubUndefinedNoInject
            if (
                format_type
                == NotebookEntryType
                .NOTEBOOK_EXPANDABLE_SECRET_SCANDAL
            ):
                error_context = (
                    'Entry assignment {} targets secret/scandal '
                    'subcategory {}.'
                ).format(
                    assignment_key,
                    subcategory_key
                )
                raise NiErrorSecretScandalFormatNoInject
            for entry_id in assignment['entries']:
                if entry_id in dict_entry:
                    previous_assignment = entry_sources[
                        entry_id
                    ]
                    error_context = (
                        'Notebook entry {} is declared by '
                        'entry assignments {} and {}.'
                    ).format(
                        entry_id,
                        previous_assignment,
                        assignment_key
                    )
                    raise NiErrorEntryExistsNoInject
                entry = notebook_entry_manager.get(entry_id)
                if entry is None:
                    error_context = (
                        'Notebook entry {} referenced by assignment {} '
                        'does not exist.'
                    ).format(
                        entry_id,
                        assignment_key
                    )
                    raise NiErrorEntryDoesNotExistNoInject
                if is_blocked_notebook_entry_type(entry):
                    entry_module, entry_class_name = (
                        notebook_entry_class_identity(entry)
                    )
                    error_context = (
                        'Entry assignment {} references unsupported '
                        'notebook entry {} using class {}.{}.'
                    ).format(
                        assignment_key,
                        entry_id,
                        entry_module,
                        entry_class_name
                    )
                    raise NiErrorUnsupportedEntryTypeNoInject
                format_value = notebook_entry_type_value(
                    format_type
                )
                validation_errors = (
                    validate_notebook_injector_entry(
                        entry,
                        format_value
                    )
                )
                if validation_errors:
                    error_context = (
                        'Invalid NotebookInjectorEntry.\n'
                        'Assignment: {}\n'
                        'Entry: {}\n'
                        'Entry tuning: {}\n'
                        'Subcategory: {}\n'
                        'Format value: {}\n'
                        'Errors:\n{}'
                    ).format(
                        assignment_key,
                        entry_id,
                        getattr(
                            entry,
                            '__name__',
                            entry
                        ),
                        subcategory_key,
                        format_value,
                        '\n'.join(
                            '- {}'.format(error)
                            for error in validation_errors
                        )
                    )
                    raise NiErrorEntryValidationNoInject
                dict_entry[entry_id] = (
                    category_key,
                    subcategory_key,
                    format_value
                )
                entry_sources[entry_id] = assignment_key
        existing_entries = (
            NotebookInjectorNewEntry.new_entries()
        )
        for entry_id in dict_entry:
            if entry_id in existing_entries:
                error_context = (
                    'Notebook entry {} is already registered '
                    'in NotebookInjectorNewEntry.'
                ).format(
                    entry_id
                )
                raise NiErrorEntryExistsNoInject
        category_allocations = {}
        if dict_cat:
            category_allocations = (
                enum_registry.allocate_categories(
                    dict_cat.keys()
                )
            )
        subcategory_allocations = {}
        if dict_subcat:
            subcategory_allocations = (
                enum_registry.allocate_subcategories(
                    dict_subcat.keys()
                )
            )
        if category_allocations:
            logger.debug(
                '{} category enum member(s) to inject'.format(
                    len(category_allocations)
                )
            )
            category_result = inject_enum(
                NotebookCategories,
                category_allocations
            )
            if (
                enum_registry.record_injection_result(
                    enum_registry.ENUM_CATEGORIES,
                    category_result
                )
                is False
            ):
                raise enum_registry.EnumConflictError(
                    'NotebookCategories injection conflict.'
                )
        if subcategory_allocations:
            logger.debug(
                '{} subcategory enum member(s) to inject'.format(
                    len(subcategory_allocations)
                )
            )
            subcategory_result = inject_enum(
                NotebookSubCategories,
                subcategory_allocations
            )
            if (
                enum_registry.record_injection_result(
                    enum_registry.ENUM_SUBCATEGORIES,
                    subcategory_result
                )
                is False
            ):
                raise enum_registry.EnumConflictError(
                    'NotebookSubCategories injection conflict.'
                )
        if dict_cat or dict_subcat:
            logger.debug(
                'Mapping at the beginning:\n\n{}\n'.format(
                    script.format_debug(
                        NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
                    )
                )
            )
            dict_map = (
                NotebookInjectorDataHelper.mapping_format(
                    dict_cat,
                    dict_subcat
                )
            )
            NotebookInjectorDataHelper.update_tuning(dict_map)
            logger.debug(
                'Mapping at the end:\n\n{}\n'.format(
                    script.format_debug(
                        NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
                    )
                )
            )
        if dict_cat:
            NotebookInjectorCheat.datas(0, dict_cat)
        if dict_subcat:
            NotebookInjectorCheat.datas(1, dict_subcat)
        if dict_entry:
            logger.debug(
                'Entries at the beginning:\n\n{}\n'.format(
                    script.format_debug(
                        NotebookInjectorNewEntry.new_entries()
                    )
                )
            )
            entries_added = (
                NotebookInjectorNewEntry.new_entries(dict_entry)
            )
            if entries_added is False:
                raise NiErrorAnEntryExistsNoInject
            logger.debug(
                'Entries at the end:\n\n{}\n'.format(
                    script.format_debug(
                        NotebookInjectorNewEntry.new_entries()
                    )
                )
            )
            NotebookInjectorNewEntry.refresh_entries(True)
        enum_registry.capture_expected_notebook_enums()
        if not dict_cat and not dict_subcat and not dict_entry:
            logger.debug(
                'No Notebook Injector data registered.'
            )
        logger.debug('...Completed\n\n')
    except enum_registry.EnumAllocationError:
        enum_registry.log_diagnostics()
        NiErrorEnumAllocationNoInject().err(logger)
    except enum_registry.EnumConflictError:
        enum_registry.log_diagnostics()
        NiErrorEnumConflictNoInject().err(
            logger,
            details=enum_registry.startup_conflicts_text()
        )
    except NiErrorCatInSubDoesNotExistNoInject:
        NiErrorCatInSubDoesNotExistNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorSubUndefinedNoInject:
        NiErrorSubUndefinedNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorEntryExistsNoInject:
        NiErrorEntryExistsNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorAnEntryExistsNoInject:
        NiErrorAnEntryExistsNoInject().err(
            logger,
            entries=script.format_debug(
                NotebookInjectorNewEntry.new_entries()
            )
        )
    except NiErrorSecretScandalFormatNoInject:
        NiErrorSecretScandalFormatNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorUnsupportedEntryTypeNoInject:
        NiErrorUnsupportedEntryTypeNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorEntryValidationNoInject:
        NiErrorEntryValidationNoInject().err(
            logger,
            context=error_context
        )
    except NiErrorEntryDoesNotExistNoInject:
        NiErrorEntryDoesNotExistNoInject().err(
            logger,
            context=error_context
        )
    except Exception:
        NiErrorSnippetNoInject().err(logger)