# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from typing import Any, Set, cast

from services import get_instance_manager
from sims4.resources import Types
from ui.notebook_tuning import (
    NotebookCategories,
    NotebookEntryType,
    NotebookSubCategories,
    NotebookTuning
)

import notebook_injector.script as script
from notebook_injector import registry
from notebook_injector.entry_validation import (
    is_blocked_notebook_entry_type,
    notebook_entry_class_identity,
    notebook_entry_type_value,
    validate_notebook_injector_entry
)
from notebook_injector.log import NotebookInjectorLog, ea_log
from notebook_injector.new_entry import NotebookInjectorNewEntry


_NotebookCategories = cast(
    Any,
    NotebookCategories
)
_NotebookSubCategories = cast(
    Any,
    NotebookSubCategories
)
_sanitized_assignments = None


def _resolve_assignment_format(
    subcategory_key: str,
    custom_subcategories: dict
):
    if subcategory_key in custom_subcategories:
        return custom_subcategories[
            subcategory_key
        ]['format']

    if script.subcat_check(
        subcategory_key
    ) is False:
        raise ValueError(
            'Target subcategory {} does not exist.'.format(
                subcategory_key
            )
        )

    category_key = (
        registry
        .find_category_key_for_existing_subcategory(
            subcategory_key
        )
    )
    if category_key is None:
        raise ValueError(
            'Existing subcategory {} has no category in '
            'NOTEBOOK_CATEGORY_MAPPING.'.format(
                subcategory_key
            )
        )

    notebook_mapping = cast(
        Any,
        NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
    )
    category_mapping = notebook_mapping[
        _NotebookCategories[
            category_key
        ]
    ]

    return category_mapping.subcategories[
        _NotebookSubCategories[
            subcategory_key
        ]
    ].format_type


def _log_skipped_assignment(
    assignment_key,
    assignment,
    errors
) -> None:
    source_name = assignment.get(
        'source_tuning_name',
        'unknown'
    )
    NotebookInjectorLog.logger().error(
        'Invalid Notebook Injector entry assignment skipped.\n'
        'Assignment: {}\n'
        'Tuning: {}\n'
        'Subcategory: {}\n'
        'Errors:\n{}\n'.format(
            assignment_key,
            source_name,
            assignment.get(
                'subcategory_key',
                'unknown'
            ),
            '\n'.join(
                '- {}'.format(
                    error
                )
                for error in errors
            )
        )
    )
    ea_log.error(
        'Notebook Injector skipped invalid entry assignment {}. '
        'Check demeterio_notebookinjector_log.txt.'.format(
            assignment_key
        )
    )


def sanitize_registered_entry_assignments(
    custom_subcategories=None
) -> dict:
    """
    Return valid assignments so one addon cannot block every other addon.

    custom_subcategories may contain a previously sanitized mapping.
    When omitted, all registered custom subcategories are used.
    """
    global _sanitized_assignments

    if _sanitized_assignments is not None:
        return dict(
            _sanitized_assignments
        )

    raw_assignments = registry.registered_entry_assignments()

    if not raw_assignments:
        _sanitized_assignments = {}
        return {}

    if custom_subcategories is None:
        custom_subcategories = (
            registry.registered_subcategories()
        )

    custom_subcategories = dict(
        custom_subcategories
    )
    notebook_entry_manager = get_instance_manager(
        Types.NOTEBOOK_ENTRY
    )
    existing_entries = NotebookInjectorNewEntry.new_entries()
    already_registered: Set[int] = set()

    if isinstance(
        existing_entries,
        dict
    ):
        for entry_id in existing_entries:
            if (
                isinstance(
                    entry_id,
                    int
                )
                and not isinstance(
                    entry_id,
                    bool
                )
            ):
                already_registered.add(
                    entry_id
                )

    already_registered.discard(
        0
    )

    accepted_assignments = {}
    claimed_entry_ids = set(
        already_registered
    )

    for assignment_key in sorted(
        raw_assignments
    ):
        assignment = raw_assignments[
            assignment_key
        ]
        errors = []
        assignment_entry_ids = tuple(
            assignment.get(
                'entries',
                ()
            )
        )

        try:
            subcategory_key = assignment.get(
                'subcategory_key'
            )
            if not isinstance(
                subcategory_key,
                str
            ) or not subcategory_key:
                errors.append(
                    'subcategory_key is missing or invalid.'
                )
                format_type = None
            else:
                try:
                    format_type = _resolve_assignment_format(
                        subcategory_key,
                        custom_subcategories
                    )
                except Exception as exception:
                    errors.append(
                        str(
                            exception
                        )
                    )
                    format_type = None

            if not assignment_entry_ids:
                errors.append(
                    'No notebook entries are defined.'
                )

            if (
                format_type
                == NotebookEntryType
                .NOTEBOOK_EXPANDABLE_SECRET_SCANDAL
            ):
                errors.append(
                    'NOTEBOOK_EXPANDABLE_SECRET_SCANDAL is not supported.'
                )

            format_value = None
            if format_type is not None:
                format_value = notebook_entry_type_value(
                    format_type
                )

            local_entry_ids = set()

            for entry_id in assignment_entry_ids:
                if (
                    not isinstance(
                        entry_id,
                        int
                    )
                    or isinstance(
                        entry_id,
                        bool
                    )
                    or entry_id <= 0
                ):
                    errors.append(
                        'Notebook entry ID {!r} is invalid.'.format(
                            entry_id
                        )
                    )
                    continue

                if entry_id in local_entry_ids:
                    errors.append(
                        'Notebook entry {} is duplicated inside this '
                        'assignment.'.format(
                            entry_id
                        )
                    )
                    continue

                local_entry_ids.add(
                    entry_id
                )

                if entry_id in claimed_entry_ids:
                    errors.append(
                        'Notebook entry {} is already registered by another '
                        'accepted assignment.'.format(
                            entry_id
                        )
                    )
                    continue

                entry = notebook_entry_manager.get(
                    entry_id
                )
                if entry is None:
                    errors.append(
                        'Notebook entry {} does not exist.'.format(
                            entry_id
                        )
                    )
                    continue

                if is_blocked_notebook_entry_type(
                    entry
                ):
                    entry_module, entry_class_name = (
                        notebook_entry_class_identity(
                            entry
                        )
                    )
                    errors.append(
                        'Notebook entry {} uses unsupported class {}.{}.'.format(
                            entry_id,
                            entry_module,
                            entry_class_name
                        )
                    )
                    continue

                if format_value is not None:
                    validation_errors = (
                        validate_notebook_injector_entry(
                            entry,
                            format_value
                        )
                    )
                    errors.extend(
                        'Entry {}: {}'.format(
                            entry_id,
                            error
                        )
                        for error in validation_errors
                    )

        except Exception:
            NotebookInjectorLog.logger().exception(
                'Unexpected exception while sanitizing entry assignment {}.'.format(
                    assignment_key
                )
            )
            errors.append(
                'Unexpected assignment validation exception. '
                'Check the Notebook Injector log.'
            )

        if errors:
            _log_skipped_assignment(
                assignment_key,
                assignment,
                errors
            )
            continue

        accepted_assignments[
            assignment_key
        ] = assignment
        claimed_entry_ids.update(
            assignment_entry_ids
        )

    _sanitized_assignments = dict(
        accepted_assignments
    )
    return dict(
        _sanitized_assignments
    )