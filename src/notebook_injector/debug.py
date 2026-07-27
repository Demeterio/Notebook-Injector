# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from os import path, pardir
from notebook_injector.log import NotebookInjectorLog


class NotebookInjectorDebug(NotebookInjectorLog):
    __slots__ = ()

    _BASEDIR = path.join(
        path.dirname(
            path.realpath(__file__)
        ),
        pardir
    )
    _DEBUG_PACKAGE_FILENAME = (
        'Demeterio_NotebookInjector_Debuglog.package'
    )
    _PATH_DEBUG_PACKAGE = path.normpath(
        path.join(
            _BASEDIR,
            pardir,
            _DEBUG_PACKAGE_FILENAME
        )
    )

    @classmethod
    def enable_debug_log_if_package_exists(cls) -> None:
        if (
            NotebookInjectorLog._debug_log is False
            and path.exists(
                cls._PATH_DEBUG_PACKAGE
            )
        ):
            NotebookInjectorLog._debug_log = True


NotebookInjectorDebug.enable_debug_log_if_package_exists()
