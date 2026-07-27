# Demeterio: Notebook Injector (script for The Sims 4)
# Date: 2022-07 / 2026-07
# Python 3.7.9 - Visual Studio Code 1.128.1 with Pylance 2026.2.1
# Version: see _CORE_ABI_VERSION and _RELEASE_VERSION below
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import notebook_injector.script as script
from event_testing.resolver import SingleSimResolver
from notebook_injector.error import NiErrorNoActiveSim, NiErrorScript
from services import get_instance_manager, get_active_sim
from sims4.resources import Types
from typing import Union
from zone import Zone
from notebook_injector.inject import inject
from notebook_injector.log import NotebookInjectorLog
from notebook_injector.compatibility import (
    NotebookInjectorEnumCompatibility
)


class NotebookInjectorInfo(script.Objectless):
    __slots__ = ()

    _CORE_ABI_VERSION = 1
    _RELEASE_VERSION = '1.3.1'
    _PACKAGE_TOKEN = 'f43a9d18c6b24e70a52fd9b84c0e1376'
    _required_version = 0

    @classmethod
    def version(cls) -> int:
        return cls._CORE_ABI_VERSION

    @classmethod
    def release_version(cls) -> str:
        return cls._RELEASE_VERSION

    @classmethod
    def package_token(cls) -> str:
        return cls._PACKAGE_TOKEN

    @classmethod
    def required_version(cls, v=None) -> Union[int, None]:
        if type(v) is not int:
            return cls._required_version
        else:
            cls._required_version = v

    @classmethod
    def has_required_version(cls) -> bool:
        if cls._CORE_ABI_VERSION < cls._required_version:
            return True
        else:
            return False


class NotebookInjectorVersion(NotebookInjectorInfo):
    __slots__ = ()
    _COMMAND = 'demeterio.ni_version'
    _VERSION_LOOT = 16258381577336529382
    _TITLE_VERSION_STR = 0xAE2715E9
    _TEXT_VERSION_STR = 0xAE2715EE

    @classmethod
    def version_loot(cls) -> int:
        return cls._VERSION_LOOT

    @classmethod
    def display_notification(cls) -> None:
        logger = NotebookInjectorLog.logger()
        loot = get_instance_manager(Types.ACTION).get(cls._VERSION_LOOT)
        if loot is None:
            logger.warning('...Version notification loot does not exist. Notification cannot be displayed.')
            return
        sim = get_active_sim()
        if sim is None:
            NiErrorNoActiveSim().err(logger, data='required version notification')
            return
        text_with_tokens = script.string_simple_or_tokens(
            cls._TEXT_VERSION_STR,
            str(cls.required_version()),
            cls._COMMAND
        )
        title = script.string_simple_or_tokens(cls._TITLE_VERSION_STR)
        updated_values = loot.loot_actions[0].dialog._tuned_values.clone_with_overrides(
            text=text_with_tokens,
            title=title
        )
        setattr(loot.loot_actions[0].dialog, '_tuned_values', updated_values)
        loot.apply_to_resolver(SingleSimResolver(sim.sim_info))


@inject(Zone, 'on_loading_screen_animation_finished')
def _after_loading_screen(
    original,
    self,
    *args,
    **kwargs
) -> None:
    original(self, *args, **kwargs)
    logger = NotebookInjectorLog.logger()
    logger.debug(
        'Function: Display notifications after loading screen'
    )
    logger.debug('Start...')
    try:
        if NotebookInjectorInfo.has_required_version() is True:
            NotebookInjectorVersion.display_notification()

            logger.warning(
                'Notification is displayed. A different '
                'version is required. Issues can occur.'
            )
    except Exception:
        NiErrorScript().err(logger)
    try:
        NotebookInjectorEnumCompatibility.check_and_log()
    except Exception:
        NiErrorScript().err(logger)
    logger.debug('...Completed\n\n')