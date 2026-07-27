# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from pprint import pformat
import notebook_injector.script as script
from notebook_injector import enum_registry
from notebook_injector.error import (
    NiErrorEnumLateConflict
)
from notebook_injector.log import NotebookInjectorLog


class NotebookInjectorEnumCompatibility(script.Objectless):
    __slots__ = ()

    _checked = False
    _critical_conflict = False

    @classmethod
    def check_and_log(cls, force=False) -> bool:
        if cls._checked is True and force is not True:
            return cls._critical_conflict
        logger = NotebookInjectorLog.logger()
        logger.debug(
            'Function: Validate notebook enums after loading'
        )
        logger.debug('Start...')
        report = enum_registry.validate_runtime_state()
        late_additions = report['late_additions']
        conflicts = report['conflicts']
        if late_additions:
            logger.warning(
                '...Notebook enum members were added after '
                'Notebook Injector completed its injections.'
                '\n\n{}\n'.format(
                    pformat(late_additions, width=200)
                )
            )
        if conflicts:
            NiErrorEnumLateConflict().err(
                logger,
                details=pformat(conflicts, width=200)
            )
        else:
            logger.debug(
                '...No critical late notebook enum conflict '
                'detected.'
            )
        cls._checked = True
        cls._critical_conflict = report['critical']
        logger.debug('...Completed\n\n')
        return cls._critical_conflict

    @classmethod
    def has_critical_conflict(cls) -> bool:
        return cls._critical_conflict