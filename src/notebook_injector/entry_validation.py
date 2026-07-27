# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from typing import Iterable, cast
from notebook_injector.log import NotebookInjectorLog


BLOCKED_NOTEBOOK_ENTRY_CLASSES = frozenset({
    (
        'sims.secrets.sim_secrets_notebook_entries',
        'NotebookEntryScandalSecretItem'
    ),
    (
        'notebook.country_living_notebook_entries',
        'NotebookEntryCountryItemSansDefinition'
    )
})


def notebook_entry_class_identity(entry) -> tuple:
    """
    Return the Python module and class name used by a notebook entry tuning.
    """

    return (
        getattr(entry, '__module__', ''),
        getattr(
            entry,
            '__name__',
            entry.__class__.__name__
        )
    )


def is_blocked_notebook_entry_type(entry) -> bool:
    """
    Return True when the notebook entry uses an unsupported EA class.
    """

    entry_identity = notebook_entry_class_identity(
        entry
    )

    if entry_identity in BLOCKED_NOTEBOOK_ENTRY_CLASSES:
        return True

    entry_mro = getattr(
        entry,
        '__mro__',
        ()
    )

    for parent_class in entry_mro:
        parent_identity = (
            getattr(parent_class, '__module__', ''),
            getattr(parent_class, '__name__', '')
        )

        if (
            parent_identity
            in BLOCKED_NOTEBOOK_ENTRY_CLASSES
        ):
            return True

    return False


def notebook_entry_type_value(format_type) -> int:
    """
    Return the raw integer value of an EA NotebookEntryType.

    Depending on the game API and available type stubs, an enum member
    may already behave like an integer or may expose a value attribute.
    """

    return int(
        getattr(
            format_type,
            'value',
            format_type
        )
    )


def is_notebook_injector_entry(entry) -> bool:
    """
    Return True for entries created with NotebookInjectorEntry.
    """

    return (
        getattr(
            entry,
            'IS_NOTEBOOK_INJECTOR_ENTRY',
            False
        )
        is True
    )


def validate_notebook_injector_entry(
    entry,
    format_type=None
) -> tuple:
    """
    Validate a NotebookInjectorEntry and its target subcategory format.

    Native EA notebook entries return no validation errors here.
    Unexpected validation exceptions are isolated to the current entry.
    """
    if is_notebook_injector_entry(entry) is False:
        return ()

    try:
        errors = list(
            entry.validate_tuning()
        )

        if format_type is not None:
            format_value = notebook_entry_type_value(
                format_type
            )

            if (
                entry.supports_subcategory_format(
                    format_value
                )
                is False
            ):
                errors.append(
                    'The target subcategory format value {} is not '
                    'supported by entry kind {}.'.format(
                        format_value,
                        getattr(
                            entry.entry_kind,
                            'name',
                            entry.entry_kind
                        )
                    )
                )
            else:
                format_validator = getattr(
                    entry,
                    'validate_subcategory_format',
                    None
                )
                if callable(
                    format_validator
                ):
                    errors.extend(
                        cast(
                            Iterable[str],
                            format_validator(
                                format_value
                            )
                        )
                    )

        return tuple(
            errors
        )

    except Exception:
        NotebookInjectorLog.logger().exception(
            'Unexpected exception while validating Notebook Injector '
            'entry {}.'.format(
                getattr(
                    entry,
                    '__name__',
                    entry
                )
            )
        )

        return (
            'Unexpected exception while validating this entry. '
            'Check the Notebook Injector log.',
        )
