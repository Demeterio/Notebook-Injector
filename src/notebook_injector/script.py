# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from inspect import getframeinfo, stack
from pprint import pformat
from re import IGNORECASE, compile, fullmatch, sub
from sims4.collections import _ImmutableSlotsBase, make_immutable_slots_class
from sims4.localization import _create_localized_string, LocalizationHelperTuning
from typing import Any, cast
from ui.notebook_tuning import NotebookCategories, NotebookSubCategories


_NotebookCategories = cast(Any, NotebookCategories)
_NotebookSubCategories = cast(Any, NotebookSubCategories)
_CLEAN_HTML = compile(
    '\\t|\\r|\\n|<.*?>|&(?:[a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});',
    IGNORECASE
)


class Objectless:
    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        raise RuntimeError(
            'NotebookInjector: {} should not be instantiated.'.format(cls)
        )


def clean_string(text: str) -> str:
    return sub(_CLEAN_HTML, '', text)


def format_debug(code) -> str:
    return pformat(code, depth=4, indent=4, width=200)


def get_source_from_code() -> str:
    caller = getframeinfo(stack()[1][0])
    return '{}:{}:{}'.format(
        caller.filename,
        caller.function,
        caller.lineno
    )


def string_simple_or_tokens(string, *tokens) -> Any:
    return lambda *_, **__: _create_localized_string(string, *tokens)


def string_raw(string) -> Any:
    return lambda *_, **__: LocalizationHelperTuning.get_raw_text(string)


def tuning_key_name(s: str) -> bool:
    if not isinstance(s, str):
        return False
    return fullmatch(r'[A-Z][A-Za-z0-9_]*', s) is not None


def _enum_names(enum_class) -> tuple:
    name_to_value = getattr(enum_class, 'name_to_value', None)
    if name_to_value is not None:
        return tuple(name_to_value.keys())
    return tuple(member.name for member in enum_class)


def cat_check(s: str) -> bool:
    if not isinstance(s, str):
        return False
    normalized_name = s.lower()
    return any(
        enum_name.lower() == normalized_name
        for enum_name in _enum_names(_NotebookCategories)
    )


def subcat_check(s: str) -> bool:
    if not isinstance(s, str):
        return False
    normalized_name = s.lower()
    return any(
        enum_name.lower() == normalized_name
        for enum_name in _enum_names(_NotebookSubCategories)
    )


def immutable_slots(d: dict) -> _ImmutableSlotsBase:
    return make_immutable_slots_class(d.keys())(d)
