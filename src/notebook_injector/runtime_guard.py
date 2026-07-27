# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from notebook.notebook_tracker import NotebookTrackerSimInfo

from notebook_injector.inject import inject
from notebook_injector.log import NotebookInjectorLog, ea_log


def _runtime_entry_error(notebook_entry):
    """Return the error that must prevent an entry from entering the tracker."""
    entry_class = notebook_entry.__class__

    prepare_error = getattr(
        entry_class,
        '_runtime_prepare_error',
        None
    )
    if prepare_error:
        return prepare_error

    validation_error = getattr(
        notebook_entry,
        '_runtime_validation_error',
        None
    )
    if validation_error:
        return validation_error

    supports_reference_unlock = getattr(
        entry_class,
        'supports_reference_unlock',
        None
    )

    if supports_reference_unlock is None:
        return None

    try:
        supports_reference = supports_reference_unlock()
    except Exception:
        NotebookInjectorLog.logger().exception(
            'Failed to evaluate supports_reference_unlock for {}.'.format(
                getattr(
                    entry_class,
                    '__name__',
                    entry_class
                )
            )
        )
        return (
            'Notebook Injector could not validate the entry unlock source.'
        )

    if supports_reference is True:
        return None

    if getattr(
        notebook_entry,
        'entry_object_definition_id',
        None
    ):
        return None

    if getattr(
        notebook_entry,
        'sub_entries',
        ()
    ):
        return None

    return (
        'This dynamic entry requires runtime data from the correct EA '
        'NotebookEntryLootOp variant.'
    )


@inject(
    NotebookTrackerSimInfo,
    'unlock_entry'
)
def _guard_notebook_injector_unlock(
    original,
    self,
    notebook_entry,
    *args,
    **kwargs
):
    """Prevent invalid Notebook Injector entries from becoming saved ghosts."""
    if (
        getattr(
            notebook_entry,
            'IS_NOTEBOOK_INJECTOR_ENTRY',
            False
        )
        is True
    ):
        error = _runtime_entry_error(
            notebook_entry
        )

        if error is not None:
            entry_class = notebook_entry.__class__
            tuning_id = getattr(
                entry_class,
                'guid64',
                'unknown'
            )
            entry_kind = getattr(
                getattr(
                    notebook_entry,
                    'entry_kind',
                    None
                ),
                'name',
                getattr(
                    notebook_entry,
                    'entry_kind',
                    'unknown'
                )
            )

            NotebookInjectorLog.logger().error(
                'Notebook Injector blocked an invalid entry before it was '
                'added to the Sim notebook.\n'
                'Entry: {}\n'
                'Tuning ID: {}\n'
                'Entry kind: {}\n'
                'Error: {}\n'.format(
                    getattr(
                        entry_class,
                        '__name__',
                        entry_class
                    ),
                    tuning_id,
                    entry_kind,
                    error
                )
            )
            ea_log.error(
                'Notebook Injector blocked invalid notebook entry tuning {}. '
                'Check demeterio_notebookinjector_log.txt.'.format(
                    tuning_id
                )
            )
            return None

    return original(
        self,
        notebook_entry,
        *args,
        **kwargs
    )
