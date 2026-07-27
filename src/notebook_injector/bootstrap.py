# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from notebook_injector import enum_registry
from notebook_injector.error import NiErrorScript
from notebook_injector.log import NotebookInjectorLog


logger = NotebookInjectorLog.logger()

logger.debug(
    'Function: Snapshot native NotebookEntryType enum'
)
logger.debug('Start...')

try:
    enum_registry.load_known_reservations()
    enum_registry.snapshot_entry_types()
    enum_registry.capture_expected_entry_types()

    logger.debug(
        'Native NotebookEntryType enum snapshot completed.'
    )
    logger.debug('...Completed\n\n')

except Exception:
    NiErrorScript().err(logger)
    raise