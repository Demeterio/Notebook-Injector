# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

import notebook_injector.script as script
from services import get_instance_manager, get_active_sim
from sims4.resources import Types
from sims4.commands import Command, CommandType, CheatOutput
from notebook_injector import game_api
from notebook_injector.log import NotebookInjectorLog
from notebook_injector.ver import NotebookInjectorInfo
from notebook_injector import enum_registry
from notebook_injector.compatibility import (
    NotebookInjectorEnumCompatibility
)
from re import search as regex
from ui.notebook_tuning import (
    NotebookCategories,
    NotebookSubCategories,
    NotebookTuning
)
from typing import Any, cast


def _log_cheat_start(
    logger,
    cheatcode: str
) -> None:
    logger.info(
        'Cheatcode: {}'.format(
            cheatcode
        )
    )
    logger.info('Start...')


def _complete_cheat(
    logger,
    output,
    data: str,
    succeed: bool
) -> None:
    logger.info(
        'Succeed: {}'.format(
            succeed
        )
    )
    logger.info('...Completed\n\n')
    output(data)


def _resolve_notebook_enum_member(
    enum_class,
    raw_value: str
):
    """
    Resolve an enum member from either its integer value or its key.

    Keys are matched case-insensitively so the debug commands remain easy
    to use while still logging the canonical EA/custom enum key.
    """

    value_text = str(raw_value).strip()

    if not value_text:
        return None

    members = enum_registry.enum_members(
        enum_class
    )
    member_name = None

    if regex(
        r'^-?\d+$',
        value_text
    ) is not None:
        requested_value = int(
            value_text
        )

        for enum_name, enum_value in members.items():
            if enum_value == requested_value:
                member_name = enum_name
                break

    else:
        normalized_name = value_text.lower()

        for enum_name in members:
            if enum_name.lower() == normalized_name:
                member_name = enum_name
                break

    if member_name is None:
        return None

    try:
        return cast(
            Any,
            enum_class
        )[member_name]
    except Exception:
        return None


def _notebook_subcategory_exists(
    subcategory
) -> bool:
    mapping = cast(
        Any,
        NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
    )

    for category_mapping in mapping.values():
        if hasattr(
            category_mapping,
            'subcategories'
        ):
            subcategories = (
                category_mapping.subcategories
            )
        else:
            subcategories = category_mapping.get(
                'subcategories',
                {}
            )

        if subcategory in subcategories:
            return True

    return False


class NotebookInjectorCheat(script.Objectless):
    __slots__ = ()

    _cat_list = {}
    _subcat_list = {}
    _mods_list = {}

    _MANAGER_LOOT = get_instance_manager(
        Types.ACTION
    )

    @classmethod
    def get_cat_list(cls) -> dict:
        return dict(
            cls._cat_list
        )

    @classmethod
    def get_subcat_list(cls) -> dict:
        return dict(
            cls._subcat_list
        )

    @classmethod
    def get_mods_list(cls) -> dict:
        return dict(
            cls._mods_list
        )

    @classmethod
    def mods(
        cls,
        mod,
        version
    ) -> None:
        cls._mods_list[
            mod
        ] = 'core ABI v{}'.format(
            version
        )

    @classmethod
    def datas(
        cls,
        code_data: int,
        data
    ) -> None:
        if code_data == 0:
            cls._cat_list.update(
                data
            )

        elif code_data == 1:
            cls._subcat_list.update(
                data
            )

    @classmethod
    def apply_loot(
        cls,
        loot,
        sim
    ) -> tuple:
        logger = NotebookInjectorLog.logger()

        loot = cls._MANAGER_LOOT.get(
            loot
        )

        if loot is None or sim is None:
            return False, 2

        try:
            game_api.apply_loot_to_sim_info(
                loot,
                sim
            )
            return True, 0

        except Exception:
            logger.exception(
                '...Exception occurred while applying '
                'the requested loot to the Sim'
            )
            return False, 1


@Command(
    'demeterio.ni_loot',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_loot(
    id_loot: str,
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_loot {}'.format(
            id_loot
        )
    )

    try:
        if regex(
            r'^(?:\d)+$',
            id_loot
        ) is None:
            logger.warning(
                '...Loot ID is not a valid number: {}.'
                .format(
                    id_loot
                )
            )

            _complete_cheat(
                logger,
                output,
                (
                    'Notebook Injector: Loot ID is not a '
                    'valid number. Please check the cheatcode: '
                    'demeterio.ni_loot 1234'
                ),
                False
            )
            return

        sim = get_active_sim()

        if sim is None:
            logger.warning(
                '...No active Sim selected. '
                'No loot applied'
            )

            _complete_cheat(
                logger,
                output,
                (
                    'Notebook Injector: No active Sim '
                    'selected. No loot applied'
                ),
                False
            )
            return

        result = (
            NotebookInjectorCheat.apply_loot(
                int(id_loot),
                sim.sim_info
            )
        )

        if result[0] is True:
            logger.info(
                'Loot {} applied to the Sim'.format(
                    id_loot
                )
            )

            data = (
                'Notebook Injector: '
                'Loot applied to the Sim'
            )
            succeed = True

        elif result[1] == 1:
            data = (
                'Notebook Injector: An error occurred '
                'while applying the loot. '
                'Please check the log file'
            )
            succeed = False

        else:
            logger.warning(
                '...Loot does not exist. '
                'No loot applied to the Sim'
            )

            data = (
                'Notebook Injector: Loot does not exist. '
                'No loot applied to the Sim'
            )
            succeed = False

        _complete_cheat(
            logger,
            output,
            data,
            succeed
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_loot'
        )

        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: An error occurred, '
                'no loot applied. Please check the log file'
            ),
            False
        )


@Command(
    'demeterio.ni_getlist',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_getlist(
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_getlist'
    )

    try:
        cat_list = (
            NotebookInjectorCheat.get_cat_list()
        )
        subcat_list = (
            NotebookInjectorCheat.get_subcat_list()
        )

        if cat_list:
            logger.info(
                '{} category(ies)'.format(
                    len(cat_list)
                )
            )
            logger.info(
                'Categories:\n\n{}\n'.format(
                    script.format_debug(
                        cat_list
                    )
                )
            )
        else:
            logger.info(
                'No Notebook Injector category registered'
            )

        if subcat_list:
            logger.info(
                '{} subcategory(ies)'.format(
                    len(subcat_list)
                )
            )
            logger.info(
                'Subcategories:\n\n{}\n'.format(
                    script.format_debug(
                        subcat_list
                    )
                )
            )
        else:
            logger.info(
                'No Notebook Injector subcategory registered'
            )

        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: Log file created '
                'with registered categories and '
                'subcategories'
            ),
            True
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_getlist'
        )

        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: An error occurred, '
                'no list available in log file. '
                'Please check the log file'
            ),
            False
        )


@Command(
    'demeterio.ni_clearcat',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_clear_category(
    category_value: str,
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_clearcat {}'.format(
            category_value
        )
    )

    try:
        category = _resolve_notebook_enum_member(
            NotebookCategories,
            category_value
        )
        mapping = cast(
            Any,
            NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
        )

        if (
            category is None
            or category == NotebookCategories.INVALID
            or category not in mapping
        ):
            logger.warning(
                '...Notebook category does not exist: {}'
                .format(
                    category_value
                )
            )
            _complete_cheat(
                logger,
                output,
                (
                    'Notebook Injector: Category does not exist. '
                    'Use an enum key or value from '
                    'demeterio.ni_getenums'
                ),
                False
            )
            return

        sim = get_active_sim()

        if sim is None:
            _complete_cheat(
                logger,
                output,
                'Notebook Injector: No active Sim selected',
                False
            )
            return

        notebook = game_api.get_notebook_tracker(
            sim
        )

        if notebook is None:
            _complete_cheat(
                logger,
                output,
                'Notebook Injector: Active Sim has no notebook tracker',
                False
            )
            return

        game_api.remove_notebook_entries_by_category(
            notebook,
            category
        )

        logger.info(
            'Notebook category cleared: {} ({})'.format(
                category.name,
                category.value
            )
        )
        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: All entries in category '
                '{} ({}) were removed'
            ).format(
                category.name,
                category.value
            ),
            True
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_clearcat'
        )
        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: An error occurred while '
                'clearing the category. Please check the log file'
            ),
            False
        )


@Command(
    'demeterio.ni_clearsubcat',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_clear_subcategory(
    subcategory_value: str,
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_clearsubcat {}'.format(
            subcategory_value
        )
    )

    try:
        subcategory = _resolve_notebook_enum_member(
            NotebookSubCategories,
            subcategory_value
        )

        if (
            subcategory is None
            or subcategory == NotebookSubCategories.INVALID
            or _notebook_subcategory_exists(
                subcategory
            ) is False
        ):
            logger.warning(
                '...Notebook subcategory does not exist: {}'
                .format(
                    subcategory_value
                )
            )
            _complete_cheat(
                logger,
                output,
                (
                    'Notebook Injector: Subcategory does not exist. '
                    'Use an enum key or value from '
                    'demeterio.ni_getenums'
                ),
                False
            )
            return

        sim = get_active_sim()

        if sim is None:
            _complete_cheat(
                logger,
                output,
                'Notebook Injector: No active Sim selected',
                False
            )
            return

        notebook = game_api.get_notebook_tracker(
            sim
        )

        if notebook is None:
            _complete_cheat(
                logger,
                output,
                'Notebook Injector: Active Sim has no notebook tracker',
                False
            )
            return

        game_api.remove_notebook_entries_by_subcategory(
            notebook,
            subcategory
        )

        logger.info(
            'Notebook subcategory cleared: {} ({})'.format(
                subcategory.name,
                subcategory.value
            )
        )
        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: All entries in subcategory '
                '{} ({}) were removed'
            ).format(
                subcategory.name,
                subcategory.value
            ),
            True
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_clearsubcat'
        )
        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: An error occurred while '
                'clearing the subcategory. Please check the log file'
            ),
            False
        )


@Command(
    'demeterio.ni_version',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_version(
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_version'
    )

    data_output = [
        (
            'Notebook Injector: Script release v{}\n'
            .format(
                NotebookInjectorInfo.release_version()
            )
        ),
        (
            'Notebook Injector: Core ABI version v{}\n'
            .format(
                NotebookInjectorInfo.version()
            )
        )
    ]

    if (
        NotebookInjectorInfo
        .has_required_version()
        is True
    ):
        data_output.append(
            (
                'Notebook Injector: Required core ABI '
                'version v{}\n'
            ).format(
                NotebookInjectorInfo.required_version()
            )
        )
    else:
        data_output.append(
            'Notebook Injector: No higher core ABI '
            'version required\n'
        )

    try:
        mods_list = (
            NotebookInjectorCheat.get_mods_list()
        )

        if mods_list:
            logger.info(
                'Mods and required versions:\n\n{}\n'
                .format(
                    script.format_debug(
                        mods_list
                    )
                )
            )
        else:
            logger.info(
                'No mods using Notebook Injector'
            )

        data_output.append(
            'Notebook Injector: Log file created with '
            'versions of mods using Notebook Injector'
        )

        _complete_cheat(
            logger,
            output,
            ''.join(data_output),
            True
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_version'
        )

        data_output.append(
            'Notebook Injector: An error occurred, '
            'no list available in log file. '
            'Please check the log file'
        )

        _complete_cheat(
            logger,
            output,
            ''.join(data_output),
            False
        )


@Command(
    'demeterio.ni_getenums',
    command_type=CommandType.Live
)
def _demeterio_notebookinjector_enums(
    _connection=None
) -> None:
    output = CheatOutput(
        _connection
    )
    logger = NotebookInjectorLog.logger()

    _log_cheat_start(
        logger,
        'demeterio.ni_getenums'
    )

    try:
        critical = (
            NotebookInjectorEnumCompatibility
            .check_and_log(
                force=True
            )
        )

        enum_registry.log_diagnostics()

        if critical is True:
            logger.error(
                '...Critical enum conflicts detected'
            )

            data = (
                'Notebook Injector: Critical enum '
                'conflicts detected. '
                'Please check the log file'
            )
            succeed = False

        else:
            data = (
                'Notebook Injector: Log file created '
                'with Enum diagnostics. '
                'No critical conflict detected'
            )
            succeed = True

        _complete_cheat(
            logger,
            output,
            data,
            succeed
        )

    except Exception:
        logger.exception(
            '...Exception occurred on the cheatcode '
            'demeterio.ni_getenums'
        )

        _complete_cheat(
            logger,
            output,
            (
                'Notebook Injector: An error occurred '
                'while checking enums. '
                'Please check the log file'
            ),
            False
        )
