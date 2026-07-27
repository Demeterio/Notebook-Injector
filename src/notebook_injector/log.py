# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import notebook_injector.script as script
from logging import DEBUG, INFO, Formatter, getLogger
from logging.handlers import RotatingFileHandler
from os import pardir, path
from sims4.log import Logger
from typing import Any, Union

from notebook_injector.privacy import privacy_safe_log_text


_RAW_EA_LOG = Logger(
    'NotebookInjector',
    default_owner='demeterio'
)


class _PrivacySafeEALog(script.Objectless):
    """Sanitize messages before forwarding them to the EA logger."""

    __slots__ = ()

    @classmethod
    def error(cls, message, *args, **kwargs) -> None:
        try:
            _RAW_EA_LOG.error(
                privacy_safe_log_text(
                    message,
                    known_root=NotebookInjectorLog._LOG_DIRECTORY
                ),
                *args,
                **kwargs
            )
        except Exception:
            pass


class _NotebookInjectorFormatter(Formatter):
    """Format log records without exposing private filesystem paths."""

    def format(self, record) -> str:
        rendered = super().format(record)
        return privacy_safe_log_text(
            rendered,
            known_root=NotebookInjectorLog._LOG_DIRECTORY
        )


class NotebookInjectorLog(script.Objectless):
    __slots__ = ()

    _debug_init = False
    _debug_log = False
    _get_log = getLogger(
        'demeterio_notebook_injector'
    )
    _BASEDIR = path.join(
        path.dirname(
            path.realpath(__file__)
        ),
        pardir
    )
    _PATH_LOG = path.normpath(
        path.join(
            _BASEDIR,
            pardir,
            'demeterio_notebookinjector_log.txt'
        )
    )
    _SESSION_SEPARATOR = (
        '------------------------------------------------------------------------'
    )
    _LOG_DIRECTORY = path.dirname(
        _PATH_LOG
    )
    _FORMATTER = _NotebookInjectorFormatter(
        fmt=(
            '%(asctime)s,%(msecs)d %(levelname)-8s '
            '[%(filename)s:%(module)s:%(funcName)s:%(lineno)d] '
            '%(message)s'
        ),
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    @staticmethod
    def _rotation_namer(default_name: str) -> str:
        try:
            base_name, rotation_index = default_name.rsplit('.', 1)
        except ValueError:
            return default_name
        root_name, extension = path.splitext(base_name)
        if not extension:
            return default_name
        return '{}.{}{}'.format(
            root_name,
            rotation_index,
            extension
        )

    @classmethod
    def debug_log(
        cls,
        v=None
    ) -> Union[bool, None]:
        if v is None:
            return cls._debug_log
        if type(v) is bool:
            cls._debug_log = v
        return None

    @classmethod
    def _write_session_header(cls) -> None:
        if cls._debug_log is True:
            mode_text = (
                'NEW GAME SESSION | Log mode: DEBUG | '
                'Debuglog package detected'
            )
        else:
            mode_text = (
                'NEW GAME SESSION | Log mode: INFO | '
                'Standard log and cheat commands'
            )

        cls._get_log.info(
            cls._SESSION_SEPARATOR
        )
        cls._get_log.info(
            mode_text
        )
        cls._get_log.info(
            '{}\n'.format(
                cls._SESSION_SEPARATOR
            )
        )

    @classmethod
    def logger(cls) -> Any:
        if cls._debug_init is False:
            for handler in tuple(cls._get_log.handlers):
                cls._get_log.removeHandler(handler)
                handler.close()

            cls._get_log.propagate = False

            if cls._debug_log is True:
                log_level = DEBUG
                max_bytes = 1048576
            else:
                log_level = INFO
                max_bytes = 262144

            cls._get_log.setLevel(log_level)

            log_handler = RotatingFileHandler(
                filename=cls._PATH_LOG,
                maxBytes=max_bytes,
                backupCount=1,
                encoding='utf-8'
            )
            log_handler.namer = cls._rotation_namer
            log_handler.setFormatter(cls._FORMATTER)
            log_handler.setLevel(log_level)

            cls._get_log.addHandler(log_handler)

            cls._write_session_header()
            cls._debug_init = True

        return cls._get_log


ea_log = _PrivacySafeEALog
