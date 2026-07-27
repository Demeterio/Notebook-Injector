# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import notebook_injector.script as script
from typing import Union, Any, cast
from notebook_injector.error import NiErrorSnippetNoInjectNewEntry
from services import get_instance_manager
from sims4.resources import Types, get_resource_key
from notebook_injector.log import NotebookInjectorLog, ea_log
from notebook_injector.inject import on_load_complete
from notebook_injector.entry_validation import (
    is_blocked_notebook_entry_type,
    notebook_entry_class_identity,
    is_notebook_injector_entry,
    validate_notebook_injector_entry
)
from ui.notebook_tuning import (
    NotebookSubCategories,
    NotebookCategories
)


_NotebookCategories = cast(
    Any,
    NotebookCategories
)
_NotebookSubCategories = cast(
    Any,
    NotebookSubCategories
)


class NotebookInjectorNewEntry(script.Objectless):
    __slots__ = ()

    _MANAGER = get_instance_manager(
        Types.NOTEBOOK_ENTRY
    )
    _ICON_CATEGORY = 13064804991310247349
    _ICON_CATEGORY_LARGE = 13336255117406566768
    _ICON_ENTRY = 17876602681987197861
    _ICON_SUBCAT = 11225659531180693579
    _entries = {
        0: (
            'category',
            'subcategory',
            'format_type'
        )
    }
    _refresh_entries = False

    @classmethod
    def get_manager(cls) -> Any:
        return cls._MANAGER

    @classmethod
    def get_icon_category(cls) -> int:
        return cls._ICON_CATEGORY

    @classmethod
    def get_icon_category_large(cls) -> int:
        return cls._ICON_CATEGORY_LARGE

    @classmethod
    def get_icon_entry(cls) -> int:
        return cls._ICON_ENTRY

    @classmethod
    def get_icon_subcat(cls) -> int:
        return cls._ICON_SUBCAT

    @classmethod
    def refresh_entries(
        cls,
        v=None
    ) -> Union[bool, None]:
        if type(v) is not bool:
            return cls._refresh_entries

        cls._refresh_entries = v

    @classmethod
    def get_cat_subcat(
        cls,
        entry_id
    ) -> tuple:
        if entry_id in cls._entries:
            return (
                cls._entries[
                    entry_id
                ][0],
                cls._entries[
                    entry_id
                ][1],
                cls._entries[
                    entry_id
                ][2]
            )

        return (
            _NotebookCategories.INVALID.name,
            _NotebookSubCategories.INVALID.name,
            None
        )

    @classmethod
    def new_entries(
        cls,
        d=None
    ) -> Union[dict, bool]:
        entries = cls._entries

        if d is None or type(d) is not dict:
            return entries

        if any(
            entry_id in entries
            for entry_id in d
        ):
            return False

        entries.update(
            d
        )
        return True

    @classmethod
    def get_all_new_entries(cls) -> tuple:
        cls._entries = dict(
            sorted(
                cls._entries.items(),
                key=lambda item: item[0]
            )
        )
        entries = []

        for entry_id in cls._entries:
            if not entry_id:
                continue

            add_entry = cls._MANAGER.get(
                entry_id
            )
            if add_entry:
                entries.append(
                    add_entry
                )
                continue

            NotebookInjectorLog.logger().warning(
                'Notebook entry does not exist: {}\n'.format(
                    entry_id
                )
            )

        return tuple(
            entries
        )


def _refresh_single_entry(
    entry,
    icon_entry,
    logger
) -> bool:
    """Refresh one entry and return False without affecting other entries."""
    tuning = getattr(
        entry,
        'guid64',
        'unknown'
    )
    cat_subcat = NotebookInjectorNewEntry.get_cat_subcat(
        tuning
    )

    try:
        if is_blocked_notebook_entry_type(
            entry
        ):
            entry_module, entry_class_name = (
                notebook_entry_class_identity(
                    entry
                )
            )
            logger.error(
                'Unsupported notebook entry type.\n'
                'Entry: {}\n'
                'Tuning ID: {}\n'
                'Python class: {}.{}\n'
                'This entry has not been injected.\n'.format(
                    getattr(
                        entry,
                        '__name__',
                        entry
                    ),
                    tuning,
                    entry_module,
                    entry_class_name
                )
            )
            return False

        validation_errors = validate_notebook_injector_entry(
            entry,
            cat_subcat[2]
        )
        if validation_errors:
            logger.error(
                'Invalid NotebookInjectorEntry.\n'
                'Entry: {}\n'
                'Tuning ID: {}\n'
                'Subcategory format value: {}\n'
                'Errors:\n{}\n'.format(
                    getattr(
                        entry,
                        '__name__',
                        entry
                    ),
                    tuning,
                    cat_subcat[2],
                    '\n'.join(
                        '- {}'.format(
                            error
                        )
                        for error in validation_errors
                    )
                )
            )
            return False

        if is_notebook_injector_entry(
            entry
        ):
            entry.prepare_runtime_data()

            prepare_error = getattr(
                entry,
                '_runtime_prepare_error',
                None
            )
            if prepare_error:
                logger.error(
                    'NotebookInjectorEntry runtime preparation failed.\n'
                    'Entry: {}\n'
                    'Tuning ID: {}\n'
                    'Error: {}\n'.format(
                        getattr(
                            entry,
                            '__name__',
                            entry
                        ),
                        tuning,
                        prepare_error
                    )
                )
                return False

        category = _NotebookCategories[
            cat_subcat[0]
        ]
        subcategory = _NotebookSubCategories[
            cat_subcat[1]
        ]

        if (
            category
            and subcategory
        ):
            entry.category_id = category
            entry.subcategory_id = subcategory

            should_use_fallback_icon = True
            if is_notebook_injector_entry(
                entry
            ):
                should_use_fallback_icon = (
                    entry.uses_fallback_icon()
                )

            if (
                should_use_fallback_icon is True
                and getattr(
                    entry,
                    'entry_icon',
                    None
                ) is None
                and icon_entry
            ):
                entry.entry_icon = icon_entry

            logger.debug(
                '{}'.format(
                    script.format_debug(
                        vars(
                            entry
                        )
                    )
                )
            )
            logger.debug(
                'Done for the notebook entry: {}\n'.format(
                    tuning
                )
            )
            return True

        logger.warning(
            'Category or subcategory missing for the notebook entry: {}\n'.format(
                tuning
            )
        )
        return False

    except Exception:
        logger.exception(
            'Exception while refreshing notebook entry {}. '
            'This entry was skipped; other entries will continue.'.format(
                tuning
            )
        )
        ea_log.error(
            'Notebook Injector skipped notebook entry tuning {} during refresh. '
            'Check demeterio_notebookinjector_log.txt.'.format(
                tuning
            )
        )
        return False


@on_load_complete(
    Types.NOTEBOOK_ENTRY
)
def _refresh_entries(
    manager=NotebookInjectorNewEntry.get_manager()
) -> None:
    if NotebookInjectorNewEntry.refresh_entries() is not True:
        return

    logger = NotebookInjectorLog.logger()
    logger.debug(
        'Function: Refresh XML tuning entries to add new and '
        'correct categories and subcategories'
    )
    logger.debug(
        'Start...\n'
    )

    try:
        icon_entry = get_resource_key(
            NotebookInjectorNewEntry.get_icon_entry(),
            Types.PNG
        )
        if not icon_entry:
            icon_entry = None

        for entry in NotebookInjectorNewEntry.get_all_new_entries():
            _refresh_single_entry(
                entry,
                icon_entry,
                logger
            )

        logger.debug(
            'Entries after reloading:\n\n{}\n'.format(
                script.format_debug(
                    NotebookInjectorNewEntry.new_entries()
                )
            )
        )
        logger.debug(
            '...Completed\n\n'
        )

    except Exception:
        NiErrorSnippetNoInjectNewEntry().err(
            logger
        )
