# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

"""
Install CUSTOM as an entry_kind on the existing NotebookInjectorEntry class.

This module intentionally does not expose a second public notebook-entry class.
Modder XML continues to use:

    c="NotebookInjectorEntry"
    i="notebook_entry"
    m="notebook_injector.entry"

Only entry_kind changes to CUSTOM. The specialized implementation remains split
into internal helper modules so the public XML contract stays small and stable.
"""

from typing import Any, cast

import notebook_injector.entry as entry_module
from notebook_injector.custom_entry_runtime import (
    NotebookInjectorCustomRuntimeMixin,
    normalize_custom_entry_runtime_id
)
from notebook_injector.custom_entry_tuning import (
    CUSTOM_ENTRY_INSTANCE_TUNABLES,
    CUSTOM_ENTRY_KIND_VALUE
)
from notebook_injector.custom_entry_validation import (
    NotebookInjectorCustomValidationMixin
)
from notebook_injector.custom_entry_ui import (
    install_custom_entry_ui_extension
)


_NotebookInjectorEntry = cast(
    Any,
    entry_module.NotebookInjectorEntry
)


def _entry_kind_value(owner) -> Any:
    entry_kind = getattr(
        owner,
        'entry_kind',
        None
    )
    return getattr(
        entry_kind,
        'value',
        entry_kind
    )


def _is_custom_entry(owner) -> bool:
    return (
        _entry_kind_value(
            owner
        )
        == CUSTOM_ENTRY_KIND_VALUE
    )


def _classmethod_function(owner, name: str):
    """Return the underlying function from a classmethod descriptor."""
    descriptor = vars(
        owner
    )[name]
    return descriptor.__func__


def _copy_descriptor(
    source,
    target,
    name: str
) -> None:
    """Copy a normal, static, or class method without losing its descriptor."""
    setattr(
        target,
        name,
        vars(
            source
        )[name]
    )


def _install_custom_entry_extension() -> None:
    """Patch the existing public entry class before XML tunings are generated."""
    if getattr(
        _NotebookInjectorEntry,
        '_NOTEBOOK_INJECTOR_CUSTOM_INSTALLED',
        False
    ) is True:
        return

    original_init = vars(
        _NotebookInjectorEntry
    )['__init__']
    original_uses_fallback_icon = _classmethod_function(
        _NotebookInjectorEntry,
        'uses_fallback_icon'
    )
    original_supports_reference_unlock = _classmethod_function(
        _NotebookInjectorEntry,
        'supports_reference_unlock'
    )
    original_prepare_runtime_data = _classmethod_function(
        _NotebookInjectorEntry,
        'prepare_runtime_data'
    )
    original_validate_tuning = _classmethod_function(
        _NotebookInjectorEntry,
        'validate_tuning'
    )
    original_supports_subcategory_format = _classmethod_function(
        _NotebookInjectorEntry,
        'supports_subcategory_format'
    )
    original_is_definition_based = vars(
        _NotebookInjectorEntry
    )['is_definition_based']
    original_get_definition_notebook_data = vars(
        _NotebookInjectorEntry
    )['get_definition_notebook_data']

    custom_prepare_runtime_data = _classmethod_function(
        NotebookInjectorCustomRuntimeMixin,
        'prepare_runtime_data'
    )
    custom_validate_tuning = _classmethod_function(
        NotebookInjectorCustomValidationMixin,
        'validate_tuning'
    )
    custom_supports_subcategory_format = _classmethod_function(
        NotebookInjectorCustomValidationMixin,
        'supports_subcategory_format'
    )
    custom_validate_subcategory_format = _classmethod_function(
        NotebookInjectorCustomValidationMixin,
        'validate_subcategory_format'
    )
    custom_get_definition_notebook_data = vars(
        NotebookInjectorCustomRuntimeMixin
    )['get_definition_notebook_data']

    for tunable_name, tunable in (
        CUSTOM_ENTRY_INSTANCE_TUNABLES.items()
    ):
        _NotebookInjectorEntry.add_tunable_to_instance(
            tunable_name,
            tunable
        )

    for method_name in (
        '_get_custom_format_value',
        '_build_custom_tooltip',
        '_text_row',
        '_definition_count',
        '_ingredient_row',
        '_build_expandable_rows'
    ):
        _copy_descriptor(
            NotebookInjectorCustomRuntimeMixin,
            _NotebookInjectorEntry,
            method_name
        )

    for method_name in (
        '_has_custom_content',
        '_has_custom_tooltip',
        '_validate_forbidden_fields',
        '_validate_content',
        '_validate_custom_tooltip'
    ):
        _copy_descriptor(
            NotebookInjectorCustomValidationMixin,
            _NotebookInjectorEntry,
            method_name
        )

    def patched_init(
        self,
        *args,
        **kwargs
    ):
        original_init(
            self,
            *args,
            **kwargs
        )

        if _is_custom_entry(
            self
        ) is False:
            return

        runtime_source_id = (
            self.entry_object_definition_id
        )

        if not runtime_source_id:
            runtime_source_id = (
                self.__class__.guid64
            )

        self.entry_object_definition_id = (
            normalize_custom_entry_runtime_id(
                runtime_source_id
            )
        )

    @classmethod
    def patched_uses_fallback_icon(cls) -> bool:
        if _is_custom_entry(
            cls
        ) is True:
            return True

        return original_uses_fallback_icon(
            cls
        )

    @classmethod
    def patched_supports_reference_unlock(cls) -> bool:
        if _is_custom_entry(
            cls
        ) is True:
            return True

        return original_supports_reference_unlock(
            cls
        )

    @classmethod
    def patched_prepare_runtime_data(cls) -> None:
        if _is_custom_entry(
            cls
        ) is True:
            custom_prepare_runtime_data(
                cls
            )
            return

        original_prepare_runtime_data(
            cls
        )

    def patched_is_definition_based(self) -> bool:
        if _is_custom_entry(
            self
        ) is True:
            return True

        return original_is_definition_based(
            self
        )

    def patched_get_definition_notebook_data(
        self,
        ingredient_cache=()
    ):
        if _is_custom_entry(
            self
        ) is True:
            return custom_get_definition_notebook_data(
                self,
                ingredient_cache
            )

        return original_get_definition_notebook_data(
            self,
            ingredient_cache
        )

    @classmethod
    def patched_validate_tuning(cls) -> tuple:
        if _is_custom_entry(
            cls
        ) is True:
            return custom_validate_tuning(
                cls
            )

        errors = list(
            original_validate_tuning(
                cls
            )
        )

        if cls._has_custom_content() is True:
            errors.append(
                'content is only allowed for entry_kind CUSTOM.'
            )

        if cls._has_custom_tooltip() is True:
            errors.append(
                'custom_tooltip is only allowed for entry_kind CUSTOM.'
            )

        return tuple(
            errors
        )

    @classmethod
    def patched_supports_subcategory_format(
        cls,
        format_value: int
    ) -> bool:
        if _is_custom_entry(
            cls
        ) is True:
            return custom_supports_subcategory_format(
                cls,
                format_value
            )

        return original_supports_subcategory_format(
            cls,
            format_value
        )

    @classmethod
    def patched_validate_subcategory_format(
        cls,
        format_value: int
    ) -> tuple:
        if _is_custom_entry(
            cls
        ) is True:
            return custom_validate_subcategory_format(
                cls,
                format_value
            )

        return ()

    _NotebookInjectorEntry.__init__ = patched_init
    _NotebookInjectorEntry.uses_fallback_icon = (
        patched_uses_fallback_icon
    )
    _NotebookInjectorEntry.supports_reference_unlock = (
        patched_supports_reference_unlock
    )
    _NotebookInjectorEntry.prepare_runtime_data = (
        patched_prepare_runtime_data
    )
    _NotebookInjectorEntry.is_definition_based = (
        patched_is_definition_based
    )
    _NotebookInjectorEntry.get_definition_notebook_data = (
        patched_get_definition_notebook_data
    )
    _NotebookInjectorEntry.validate_tuning = (
        patched_validate_tuning
    )
    _NotebookInjectorEntry.supports_subcategory_format = (
        patched_supports_subcategory_format
    )
    _NotebookInjectorEntry.validate_subcategory_format = (
        patched_validate_subcategory_format
    )
    _NotebookInjectorEntry._NOTEBOOK_INJECTOR_CUSTOM_INSTALLED = True


_install_custom_entry_extension()
install_custom_entry_ui_extension()
