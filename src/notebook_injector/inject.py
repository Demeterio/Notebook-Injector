# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from inspect import ismethod
from functools import wraps
from notebook_injector.error import NiErrorScript
from services import get_instance_manager
from typing import Any


def inject(target_object, target_function_name, safe=False) -> Any:
    if safe and not hasattr(target_object, target_function_name):
        def _self_wrap(wrap_function) -> Any:
            return wrap_function

        return _self_wrap

    def _wrap_original_function(original_function, new_function) -> Any:
        @wraps(original_function)
        def _wrapped_function(*args, **kwargs):
            if type(original_function) is property:
                return new_function(original_function.fget, *args, **kwargs)
            else:
                return new_function(original_function, *args, **kwargs)

        if ismethod(original_function):
            return classmethod(_wrapped_function)
        elif type(original_function) is property:
            return property(_wrapped_function)
        else:
            return _wrapped_function

    def _injected(wrap_function) -> Any:
        original_function = getattr(target_object, target_function_name)
        setattr(target_object, target_function_name, _wrap_original_function(original_function, wrap_function))

        return wrap_function

    return _injected


def on_load_complete(manager_type) -> Any:
    def wrapper(function) -> None:
        def safe_function(manager, *_, **__):
            try:
                function(manager)
            except Exception:
                NiErrorScript().err()

        get_instance_manager(manager_type).add_on_load_complete(safe_function)

    return wrapper


def _raw_enum_value(value) -> int:
    if hasattr(value, 'value'):
        return value.value
    return int(value)


def _enum_members(enum_class) -> dict:
    name_to_value = getattr(
        enum_class,
        'name_to_value',
        None
    )
    if name_to_value is not None:
        return {
            enum_name: _raw_enum_value(enum_value)
            for enum_name, enum_value
            in name_to_value.items()
        }
    return {
        member.name: member.value
        for member in enum_class
    }


def inject_enum(enum_class, members: dict) -> dict:
    added = {}
    already_present = {}
    conflicts = []
    pending_members = {}
    existing_members = _enum_members(
        enum_class
    )
    existing_names_by_normalized_name = {}
    existing_names_by_value = {}
    for existing_name, existing_value in (
        existing_members.items()
    ):
        normalized_name = existing_name.lower()
        existing_names_by_normalized_name.setdefault(
            normalized_name,
            []
        ).append(existing_name)
        existing_names_by_value.setdefault(
            existing_value,
            []
        ).append(existing_name)
    requested_name_by_normalized_name = {}
    requested_name_by_value = {}
    for enum_name, enum_value in members.items():
        if (
            not isinstance(enum_name, str)
            or not enum_name
        ):
            conflicts.append(
            {
                'name': enum_name,
                'value': enum_value,
                'reason': 'invalid_requested_name'
            })
            continue
        if (
            not isinstance(enum_value, int)
            or isinstance(enum_value, bool)
        ):
            conflicts.append(
            {
                'name': enum_name,
                'value': enum_value,
                'reason': 'invalid_requested_value'
            })
            continue
        normalized_name = enum_name.lower()
        previous_requested_name = (
            requested_name_by_normalized_name.get(
                normalized_name
            )
        )
        if (
            previous_requested_name is not None
            and previous_requested_name != enum_name
        ):
            conflicts.append(
            {
                'name': enum_name,
                'requested_value': enum_value,
                'existing_requested_name': (
                    previous_requested_name
                ),
                'reason': (
                    'batch_case_insensitive_name_conflict'
                )
            })
            continue
        requested_name_by_normalized_name[
            normalized_name
        ] = enum_name
        if enum_name in existing_members:
            existing_value = existing_members[
                enum_name
            ]
            if existing_value == enum_value:
                already_present[
                    enum_name
                ] = enum_value
            else:
                conflicts.append(
                {
                    'name': enum_name,
                    'requested_value': enum_value,
                    'existing_value': existing_value,
                    'reason': 'name_conflict'
                })
            continue
        existing_case_matches = (
            existing_names_by_normalized_name.get(
                normalized_name,
                ()
            )
        )
        if existing_case_matches:
            conflicts.append(
            {
                'name': enum_name,
                'requested_value': enum_value,
                'existing_names': tuple(
                    existing_case_matches
                ),
                'reason': (
                    'case_insensitive_name_conflict'
                )
            })
            continue
        existing_value_owners = (
            existing_names_by_value.get(
                enum_value,
                ()
            )
        )
        if existing_value_owners:
            conflicts.append(
            {
                'name': enum_name,
                'value': enum_value,
                'existing_names': tuple(
                    existing_value_owners
                ),
                'reason': 'value_conflict'
            })
            continue
        previous_requested_value_owner = (
            requested_name_by_value.get(
                enum_value
            )
        )
        if previous_requested_value_owner is not None:
            conflicts.append(
            {
                'name': enum_name,
                'value': enum_value,
                'existing_requested_name': (
                    previous_requested_value_owner
                ),
                'reason': 'batch_value_conflict'
            })
            continue
        requested_name_by_value[
            enum_value
        ] = enum_name
        pending_members[
            enum_name
        ] = enum_value
    if conflicts:
        return {
            'added': {},
            'already_present': already_present,
            'conflicts': tuple(conflicts)
        }
    if not pending_members:
        return {
            'added': {},
            'already_present': already_present,
            'conflicts': ()
        }
    with enum_class.make_mutable():
        for enum_name, enum_value in (
            pending_members.items()
        ):
            enum_class._add_new_enum_value(
                enum_name,
                enum_value
            )

            added[
                enum_name
            ] = enum_value
    return {
        'added': added,
        'already_present': already_present,
        'conflicts': ()
    }