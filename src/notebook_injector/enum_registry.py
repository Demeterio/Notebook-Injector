# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from typing import Any, cast
from pprint import pformat
from ui.notebook_tuning import (
    NotebookCategories,
    NotebookSubCategories,
    NotebookEntryType
)
from notebook_injector.known_enums import KNOWN_EXTERNAL_NOTEBOOK_ENUMS
from notebook_injector.log import NotebookInjectorLog


_NotebookCategories = cast(
    Any,
    NotebookCategories
)
ENUM_CATEGORIES = 'categories'
ENUM_SUBCATEGORIES = 'subcategories'
ENUM_ENTRY_TYPES = 'entry_types'
CUSTOM_ENUM_MIN = 10
CUSTOM_ENUM_MAX = 8191


class EnumRegistryError(RuntimeError):
    pass


class EnumAllocationError(EnumRegistryError):
    pass


class EnumConflictError(EnumRegistryError):
    pass


_baseline_categories = {}
_baseline_subcategories = {}
_baseline_entry_types = {}

_reserved_category_names = {}
_reserved_subcategory_names = {}
_reserved_entry_type_names = {}

_reserved_category_values = {}
_reserved_subcategory_values = {}
_reserved_entry_type_values = {}

_allocated_categories = {}
_allocated_subcategories = {}
_allocated_entry_types = {}

_expected_categories = {}
_expected_subcategories = {}
_expected_entry_types = {}

_late_additions = []
_conflicts = []

_known_reservations_loaded = False
_notebook_snapshot_taken = False
_entry_type_snapshot_taken = False


def _raw_enum_value(value) -> int:
    if hasattr(value, 'value'):
        return value.value
    return int(value)


def enum_members(enum_class) -> dict:
    name_to_value = getattr(enum_class, 'name_to_value', None)
    if name_to_value is not None:
        return {
            enum_name: _raw_enum_value(enum_value)
            for enum_name, enum_value in name_to_value.items()
        }
    return {
        member.name: member.value
        for member in enum_class
    }


def _enum_class(enum_type: str):
    if enum_type == ENUM_CATEGORIES:
        return NotebookCategories
    if enum_type == ENUM_SUBCATEGORIES:
        return NotebookSubCategories
    if enum_type == ENUM_ENTRY_TYPES:
        return NotebookEntryType
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _baseline(enum_type: str) -> dict:
    if enum_type == ENUM_CATEGORIES:
        return _baseline_categories
    if enum_type == ENUM_SUBCATEGORIES:
        return _baseline_subcategories
    if enum_type == ENUM_ENTRY_TYPES:
        return _baseline_entry_types
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _allocated(enum_type: str) -> dict:
    if enum_type == ENUM_CATEGORIES:
        return _allocated_categories
    if enum_type == ENUM_SUBCATEGORIES:
        return _allocated_subcategories
    if enum_type == ENUM_ENTRY_TYPES:
        return _allocated_entry_types
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _expected(enum_type: str) -> dict:
    if enum_type == ENUM_CATEGORIES:
        return _expected_categories
    if enum_type == ENUM_SUBCATEGORIES:
        return _expected_subcategories
    if enum_type == ENUM_ENTRY_TYPES:
        return _expected_entry_types
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _reserved_names(enum_type: str) -> dict:
    if enum_type == ENUM_CATEGORIES:
        return _reserved_category_names
    if enum_type == ENUM_SUBCATEGORIES:
        return _reserved_subcategory_names
    if enum_type == ENUM_ENTRY_TYPES:
        return _reserved_entry_type_names
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _reserved_values(enum_type: str) -> dict:
    if enum_type == ENUM_CATEGORIES:
        return _reserved_category_values
    if enum_type == ENUM_SUBCATEGORIES:
        return _reserved_subcategory_values
    if enum_type == ENUM_ENTRY_TYPES:
        return _reserved_entry_type_values
    raise ValueError('Unknown notebook enum type: {}'.format(enum_type))


def _add_conflict(conflict: dict) -> None:
    if conflict not in _conflicts:
        _conflicts.append(conflict)


def _register_known_members(
    enum_type: str,
    owner_key: str,
    display_name: str,
    members: dict,
    include_categories_in_picker: bool
) -> None:
    reserved_names = _reserved_names(enum_type)
    reserved_values = _reserved_values(enum_type)
    for enum_name, enum_value in members.items():
        if not isinstance(enum_name, str) or not enum_name:
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'invalid_reserved_name',
                'owner': owner_key,
                'enum_name': enum_name
            })
            continue
        if (
            not isinstance(enum_value, int)
            or isinstance(enum_value, bool)
        ):
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'invalid_reserved_value',
                'owner': owner_key,
                'enum_name': enum_name,
                'enum_value': enum_value
            })
            continue
        reservation = {
            'owner': owner_key,
            'display_name': display_name,
            'enum_name': enum_name,
            'value': enum_value,
            'include_categories_in_picker': (
                include_categories_in_picker
                if enum_type == ENUM_CATEGORIES
                else False
            )
        }
        normalized_name = enum_name.lower()
        existing_name_reservation = reserved_names.get(normalized_name)
        if (
            existing_name_reservation is not None
            and (
                existing_name_reservation['value'] != enum_value
                or existing_name_reservation['owner'] != owner_key
            )
        ):
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'reserved_name_conflict',
                'enum_name': enum_name,
                'requested': reservation,
                'existing': existing_name_reservation
            })
            continue
        existing_value_reservation = reserved_values.get(enum_value)
        if (
            existing_value_reservation is not None
            and existing_value_reservation['enum_name'].lower()
            != normalized_name
        ):
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'reserved_value_conflict',
                'enum_value': enum_value,
                'requested': reservation,
                'existing': existing_value_reservation
            })
            continue
        reserved_names[normalized_name] = reservation
        reserved_values[enum_value] = reservation


def load_known_reservations() -> None:
    global _known_reservations_loaded
    if _known_reservations_loaded is True:
        return
    logger = NotebookInjectorLog.logger()
    logger.debug('Function: Load known external notebook enum reservations')
    logger.debug('Start...')
    for owner_key, mod_data in sorted(
        KNOWN_EXTERNAL_NOTEBOOK_ENUMS.items()
    ):
        display_name = mod_data.get('display_name', owner_key)
        include_categories_in_picker = (
            mod_data.get('include_categories_in_picker', False) is True
        )
        _register_known_members(
            ENUM_CATEGORIES,
            owner_key,
            display_name,
            mod_data.get('categories', {}),
            include_categories_in_picker
        )
        _register_known_members(
            ENUM_SUBCATEGORIES,
            owner_key,
            display_name,
            mod_data.get('subcategories', {}),
            False
        )
        _register_known_members(
            ENUM_ENTRY_TYPES,
            owner_key,
            display_name,
            mod_data.get('entry_types', {}),
            False
        )
    _known_reservations_loaded = True
    logger.debug(
        'Known category reservations:\n\n{}\n'.format(
            pformat(_reserved_category_names, width=200)
        )
    )
    logger.debug(
        'Known subcategory reservations:\n\n{}\n'.format(
            pformat(_reserved_subcategory_names, width=200)
        )
    )
    logger.debug(
        'Known entry type reservations:\n\n{}\n'.format(
            pformat(_reserved_entry_type_names, width=200)
        )
    )
    logger.debug('...Completed\n\n')


def _validate_reservations_against_baseline(
    enum_type: str
) -> None:
    baseline = _baseline(enum_type)
    reserved_names = _reserved_names(enum_type)
    reserved_values = _reserved_values(enum_type)
    baseline_by_normalized_name = {
        enum_name.lower(): (enum_name, enum_value)
        for enum_name, enum_value in baseline.items()
    }
    baseline_names_by_value = {}
    for enum_name, enum_value in baseline.items():
        baseline_names_by_value.setdefault(
            enum_value,
            []
        ).append(enum_name)
    for normalized_name, reservation in reserved_names.items():
        baseline_name_data = baseline_by_normalized_name.get(
            normalized_name
        )
        if (
            baseline_name_data is not None
            and baseline_name_data[1] != reservation['value']
        ):
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'reserved_name_has_unexpected_value',
                'reservation': reservation,
                'existing_name': baseline_name_data[0],
                'existing_value': baseline_name_data[1]
            })
    for enum_value, reservation in reserved_values.items():
        existing_names = baseline_names_by_value.get(
            enum_value,
            ()
        )
        reservation_name = reservation[
            'enum_name'
        ].lower()
        reservation_name_exists = any(
            existing_name.lower() == reservation_name
            for existing_name in existing_names
        )
        if existing_names and not reservation_name_exists:
            _add_conflict({
                'phase': 'reservation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'reserved_value_owned_by_other_name',
                'reservation': reservation,
                'existing_names': tuple(existing_names)
            })


def snapshot_entry_types() -> None:
    global _entry_type_snapshot_taken
    global _baseline_entry_types
    if _entry_type_snapshot_taken is True:
        return
    load_known_reservations()
    logger = NotebookInjectorLog.logger()
    logger.debug('Function: Snapshot NotebookEntryType enum')
    logger.debug('Start...')
    _baseline_entry_types = enum_members(NotebookEntryType)
    _validate_reservations_against_baseline(ENUM_ENTRY_TYPES)
    _entry_type_snapshot_taken = True
    logger.debug(
        'NotebookEntryType baseline:\n\n{}\n'.format(
            pformat(_baseline_entry_types, width=200)
        )
    )
    logger.debug('...Completed\n\n')


def snapshot_notebook_enums() -> None:
    global _notebook_snapshot_taken
    global _baseline_categories
    global _baseline_subcategories
    if _notebook_snapshot_taken is True:
        return
    load_known_reservations()
    logger = NotebookInjectorLog.logger()
    logger.debug('Function: Snapshot notebook category enums')
    logger.debug('Start...')
    _baseline_categories = enum_members(NotebookCategories)
    _baseline_subcategories = enum_members(NotebookSubCategories)
    _validate_reservations_against_baseline(ENUM_CATEGORIES)
    _validate_reservations_against_baseline(ENUM_SUBCATEGORIES)
    _notebook_snapshot_taken = True
    logger.debug(
        'NotebookCategories baseline:\n\n{}\n'.format(
            pformat(_baseline_categories, width=200)
        )
    )
    logger.debug(
        'NotebookSubCategories baseline:\n\n{}\n'.format(
            pformat(_baseline_subcategories, width=200)
        )
    )
    logger.debug('...Completed\n\n')


def _ensure_requested_names_are_available(
    enum_type: str,
    requested_names
) -> None:
    baseline = _baseline(enum_type)
    allocated = _allocated(enum_type)
    reserved_names = _reserved_names(enum_type)
    baseline_names = {
        enum_name.lower(): enum_name
        for enum_name in baseline
    }
    requested_normalized_names = {}
    for enum_name in requested_names:
        normalized_name = enum_name.lower()
        previous_name = requested_normalized_names.get(normalized_name)
        if previous_name is not None and previous_name != enum_name:
            _add_conflict({
                'phase': 'allocation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'duplicate_requested_name',
                'enum_name': enum_name,
                'existing_name': previous_name
            })
            raise EnumConflictError(
                'Duplicate requested enum name: {}'.format(enum_name)
            )
        requested_normalized_names[normalized_name] = enum_name
        if enum_name in allocated:
            continue
        existing_name = baseline_names.get(normalized_name)
        if existing_name is not None:
            _add_conflict({
                'phase': 'allocation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'requested_name_already_exists',
                'enum_name': enum_name,
                'existing_name': existing_name,
                'existing_value': baseline[existing_name]
            })
            raise EnumConflictError(
                'Requested enum name already exists: {}'.format(
                    enum_name
                )
            )
        reservation = reserved_names.get(normalized_name)
        if reservation is not None:
            _add_conflict({
                'phase': 'allocation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'requested_name_is_reserved',
                'enum_name': enum_name,
                'reservation': reservation
            })
            raise EnumConflictError(
                'Requested enum name is reserved: {}'.format(enum_name)
            )


def _occupied_values(enum_type: str) -> set:
    occupied = set(_baseline(enum_type).values())
    occupied.update(_reserved_values(enum_type).keys())
    occupied.update(_allocated(enum_type).values())
    return occupied


def _allocate_ascending(
    enum_type: str,
    requested_names,
    minimum: int,
    maximum: int
) -> dict:
    requested_names = tuple(
        requested_names
    )
    _ensure_requested_names_are_available(
        enum_type,
        requested_names
    )
    occupied_values = _occupied_values(
        enum_type
    )
    allocated = _allocated(
        enum_type
    )
    result = {}
    candidate = minimum
    for enum_name in sorted(requested_names):
        if enum_name in allocated:
            result[
                enum_name
            ] = allocated[enum_name]
            continue
        while (
            candidate <= maximum
            and candidate in occupied_values
        ):
            candidate += 1
        if candidate > maximum:
            _add_conflict({
                'phase': 'allocation',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'allocation_range_exhausted',
                'minimum': minimum,
                'maximum': maximum
            })
            raise EnumAllocationError(
                'No free {} enum value remains.'.format(
                    enum_type
                )
            )
        result[
            enum_name
        ] = candidate
        occupied_values.add(
            candidate
        )
        candidate += 1
    logger = NotebookInjectorLog.logger()
    logger.debug(
        'Allocated {}:\n\n{}\n'.format(
            enum_type,
            pformat(result, width=200)
        )
    )
    return result


def allocate_categories(requested_names) -> dict:
    return _allocate_ascending(
        ENUM_CATEGORIES,
        requested_names,
        CUSTOM_ENUM_MIN,
        CUSTOM_ENUM_MAX
    )


def allocate_subcategories(requested_names) -> dict:
    return _allocate_ascending(
        ENUM_SUBCATEGORIES,
        requested_names,
        CUSTOM_ENUM_MIN,
        CUSTOM_ENUM_MAX
    )


def allocate_entry_types(requested_names) -> dict:
    enum_type = ENUM_ENTRY_TYPES
    requested_names = tuple(
        requested_names
    )
    _ensure_requested_names_are_available(
        enum_type,
        requested_names
    )
    occupied_values = _occupied_values(
        enum_type
    )
    allocated = _allocated(
        enum_type
    )
    result = {}
    candidate = 0
    for enum_name in sorted(requested_names):
        if enum_name in allocated:
            result[
                enum_name
            ] = allocated[enum_name]
            continue
        while candidate in occupied_values:
            candidate += 1
        result[
            enum_name
        ] = candidate
        occupied_values.add(
            candidate
        )
        candidate += 1
    logger = NotebookInjectorLog.logger()
    logger.debug(
        'Allocated entry types:\n\n{}\n'.format(
            pformat(result, width=200)
        )
    )
    return result


def record_injection_result(
    enum_type: str,
    injection_result: dict
) -> bool:
    conflicts = injection_result.get('conflicts', ())
    if conflicts:
        for conflict in conflicts:
            final_conflict = dict(conflict)

            final_conflict.update({
                'phase': 'injection',
                'critical': True,
                'enum_type': enum_type
            })
            _add_conflict(final_conflict)
        return False
    committed_members = {}
    committed_members.update(
        injection_result.get(
            'already_present',
            {}
        )
    )
    committed_members.update(
        injection_result.get(
            'added',
            {}
        )
    )
    _allocated(enum_type).update(
        committed_members
    )
    return True


def capture_expected_entry_types() -> None:
    global _expected_entry_types
    _expected_entry_types = enum_members(NotebookEntryType)


def capture_expected_notebook_enums() -> None:
    global _expected_categories
    global _expected_subcategories
    _expected_categories = enum_members(NotebookCategories)
    _expected_subcategories = enum_members(NotebookSubCategories)


def is_reserved_category_name(category_key: str) -> bool:
    if not isinstance(category_key, str):
        return False
    return category_key.lower() in _reserved_category_names


def is_reserved_subcategory_name(
    subcategory_key: str
) -> bool:
    if not isinstance(subcategory_key, str):
        return False
    return subcategory_key.lower() in _reserved_subcategory_names


def is_reserved_entry_type_name(entry_type_key: str) -> bool:
    if not isinstance(entry_type_key, str):
        return False
    return entry_type_key.lower() in _reserved_entry_type_names


def reserved_category_info(category_key: str):
    if not isinstance(category_key, str):
        return None
    return _reserved_category_names.get(category_key.lower())


def reserved_subcategory_info(subcategory_key: str):
    if not isinstance(subcategory_key, str):
        return None

    return _reserved_subcategory_names.get(
        subcategory_key.lower()
    )


def has_startup_conflicts() -> bool:
    return any(
        conflict.get('critical') is True
        and conflict.get('phase') != 'runtime'
        for conflict in _conflicts
    )


def startup_conflicts_text() -> str:
    startup_conflicts = [
        conflict
        for conflict in _conflicts
        if conflict.get('phase') != 'runtime'
    ]
    return pformat(startup_conflicts, width=200)


def managed_category_members() -> set:
    managed = set()
    for enum_name, enum_value in _allocated_categories.items():
        try:
            member = _NotebookCategories[enum_name]
        except Exception:
            continue
        if member.value == enum_value:
            managed.add(member)
    for reservation in _reserved_category_names.values():
        if reservation['include_categories_in_picker'] is not True:
            continue
        try:
            member = _NotebookCategories[
                reservation['enum_name']
            ]
        except Exception:
            continue
        if member.value == reservation['value']:
            managed.add(member)
    return managed


def _validate_runtime_enum(enum_type: str) -> None:
    enum_class = _enum_class(enum_type)
    expected = _expected(enum_type)
    current = enum_members(enum_class)
    reserved_names = _reserved_names(enum_type)
    reserved_values = _reserved_values(enum_type)
    expected_values = {
        enum_value: enum_name
        for enum_name, enum_value in expected.items()
    }
    for enum_name, expected_value in expected.items():
        current_value = current.get(enum_name)
        if current_value is None:
            _add_conflict({
                'phase': 'runtime',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'expected_member_missing',
                'enum_name': enum_name,
                'expected_value': expected_value
            })
            continue
        if current_value != expected_value:
            _add_conflict({
                'phase': 'runtime',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'expected_member_value_changed',
                'enum_name': enum_name,
                'expected_value': expected_value,
                'current_value': current_value
            })
    for enum_name, enum_value in current.items():
        if enum_name in expected:
            continue
        reservation = reserved_names.get(enum_name.lower())
        late_addition = {
            'enum_type': enum_type,
            'enum_name': enum_name,
            'enum_value': enum_value,
            'known_reservation': reservation
        }
        _late_additions.append(late_addition)
        if (
            reservation is not None
            and reservation['value'] != enum_value
        ):
            _add_conflict({
                'phase': 'runtime',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'late_reserved_name_wrong_value',
                'enum_name': enum_name,
                'current_value': enum_value,
                'reservation': reservation
            })
        reserved_owner = reserved_values.get(enum_value)
        if (
            reserved_owner is not None
            and reserved_owner['enum_name'].lower()
            != enum_name.lower()
        ):
            _add_conflict({
                'phase': 'runtime',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'late_member_uses_reserved_value',
                'enum_name': enum_name,
                'enum_value': enum_value,
                'reservation': reserved_owner
            })
        expected_owner = expected_values.get(enum_value)
        if (
            expected_owner is not None
            and expected_owner != enum_name
        ):
            _add_conflict({
                'phase': 'runtime',
                'critical': True,
                'enum_type': enum_type,
                'reason': 'late_member_uses_expected_value',
                'enum_name': enum_name,
                'enum_value': enum_value,
                'expected_owner': expected_owner
            })
    names_by_normalized_name = {}
    for enum_name in current:
        normalized_name = enum_name.lower()

        names_by_normalized_name.setdefault(
            normalized_name,
            []
        ).append(enum_name)
    for normalized_name, enum_names in (
        names_by_normalized_name.items()
    ):
        if len(enum_names) <= 1:
            continue
        late_names = [
            enum_name
            for enum_name in enum_names
            if enum_name not in expected
        ]
        if not late_names:
            continue
        _add_conflict({
            'phase': 'runtime',
            'critical': True,
            'enum_type': enum_type,
            'reason': (
                'late_case_insensitive_name_collision'
            ),
            'normalized_name': normalized_name,
            'enum_names': tuple(enum_names),
            'late_enum_names': tuple(late_names)
        })
    names_by_value = {}
    for enum_name, enum_value in current.items():
        names_by_value.setdefault(
            enum_value,
            []
        ).append(enum_name)
    for enum_value, enum_names in names_by_value.items():
        if len(enum_names) <= 1:
            continue
        late_names = [
            enum_name
            for enum_name in enum_names
            if enum_name not in expected
        ]
        if not late_names:
            continue
        _add_conflict({
            'phase': 'runtime',
            'critical': True,
            'enum_type': enum_type,
            'reason': 'late_duplicate_runtime_value',
            'enum_value': enum_value,
            'enum_names': tuple(enum_names),
            'late_enum_names': tuple(late_names)
        })


def validate_runtime_state() -> dict:
    global _late_additions
    global _conflicts
    _late_additions = []
    _conflicts = [
        conflict
        for conflict in _conflicts
        if conflict.get('phase') != 'runtime'
    ]
    _validate_runtime_enum(ENUM_CATEGORIES)
    _validate_runtime_enum(ENUM_SUBCATEGORIES)
    _validate_runtime_enum(ENUM_ENTRY_TYPES)
    runtime_conflicts = [
        conflict
        for conflict in _conflicts
        if conflict.get('phase') == 'runtime'
    ]
    critical_conflicts = [
        conflict
        for conflict in _conflicts
        if conflict.get('critical') is True
    ]
    return {
        'late_additions': list(_late_additions),
        'conflicts': runtime_conflicts,
        'critical': bool(critical_conflicts)
    }


def conflicts() -> list:
    return list(_conflicts)


def late_additions() -> list:
    return list(_late_additions)


def allocated_categories() -> dict:
    return dict(_allocated_categories)


def allocated_subcategories() -> dict:
    return dict(_allocated_subcategories)


def allocated_entry_types() -> dict:
    return dict(_allocated_entry_types)


def log_diagnostics() -> None:
    logger = NotebookInjectorLog.logger()
    logger.info('Function: Log notebook enum diagnostics')
    logger.info('Start...')
    logger.info(
        'Baseline categories:\n\n{}\n'.format(
            pformat(_baseline_categories, width=200)
        )
    )
    logger.info(
        'Baseline subcategories:\n\n{}\n'.format(
            pformat(_baseline_subcategories, width=200)
        )
    )
    logger.info(
        'Baseline entry types:\n\n{}\n'.format(
            pformat(_baseline_entry_types, width=200)
        )
    )
    logger.info(
        'Reserved categories:\n\n{}\n'.format(
            pformat(_reserved_category_names, width=200)
        )
    )
    logger.info(
        'Reserved subcategories:\n\n{}\n'.format(
            pformat(_reserved_subcategory_names, width=200)
        )
    )
    logger.info(
        'Reserved entry types:\n\n{}\n'.format(
            pformat(_reserved_entry_type_names, width=200)
        )
    )
    logger.info(
        'Allocated categories:\n\n{}\n'.format(
            pformat(_allocated_categories, width=200)
        )
    )
    logger.info(
        'Allocated subcategories:\n\n{}\n'.format(
            pformat(_allocated_subcategories, width=200)
        )
    )
    logger.info(
        'Allocated entry types:\n\n{}\n'.format(
            pformat(_allocated_entry_types, width=200)
        )
    )
    logger.info(
        'Expected categories:\n\n{}\n'.format(
            pformat(_expected_categories, width=200)
        )
    )
    logger.info(
        'Expected subcategories:\n\n{}\n'.format(
            pformat(_expected_subcategories, width=200)
        )
    )
    logger.info(
        'Expected entry types:\n\n{}\n'.format(
            pformat(_expected_entry_types, width=200)
        )
    )
    logger.info(
        'Late additions:\n\n{}\n'.format(
            pformat(_late_additions, width=200)
        )
    )
    logger.info(
        'Conflicts:\n\n{}\n'.format(
            pformat(_conflicts, width=200)
        )
    )
    logger.info('...Completed\n\n')