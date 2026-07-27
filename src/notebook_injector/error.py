# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from traceback import format_exc

from notebook_injector.log import NotebookInjectorLog, ea_log


class NiErrorBase(Exception):
    __slots__ = ('message',)

    _DATA_ERROR = '*DATA_ERROR*'
    _TRACEBACK_ERROR = '{%traceback%}'
    MESSAGE = 'Notebook Injector error.'

    def __init__(self):
        super().__init__()
        self.message = self.MESSAGE

    def err(self, logger=None, **kwargs) -> None:
        if logger is None:
            logger = NotebookInjectorLog.logger()

        base_message = kwargs.get('message', self.message)
        if self._TRACEBACK_ERROR in base_message:
            base_message = base_message.replace(
                self._TRACEBACK_ERROR,
                format_exc(),
                1
            )

        notebook_message = base_message
        context = kwargs.get('context')
        if context:
            notebook_message = '{}\nContext: {}\n\n'.format(
                base_message.rstrip(),
                context
            )

        level = kwargs.get('level', 'error')
        if level == 'warning':
            logger.warning(notebook_message)
            return

        logger.error(notebook_message)
        if kwargs.get('ea_log', True) is True:
            ea_log.error(
                kwargs.get('ea_message', base_message)
            )


class NiErrorScript(NiErrorBase):
    MESSAGE = (
        '...Exception occurred for the Notebook Injector '
        'script.\n{%traceback%}\n\n'
    )


class NiErrorSnippetNoInjectNewEntry(NiErrorBase):
    MESSAGE = (
        '...Exception occurred for this snippet. No notebook '
        'entries have been injected for new categories.'
        '\n{%traceback%}\n\n'
    )


class NiErrorSnippetNoInject(NiErrorBase):
    MESSAGE = (
        '...Exception occurred for this snippet. No data '
        'have been injected.\n{%traceback%}\n\n'
    )


class NiErrorCatUndefinedNoInject(NiErrorBase):
    MESSAGE = (
        '...Category key or category name undefined in this snippet. '
        'No data have been injected.\n\n'
    )


class NiErrorCatFormatNoInject(NiErrorBase):
    MESSAGE = (
        '...Category key must start with an uppercase letter and contain only '
        'letters, numbers or underscores. No data have been injected.\n\n'
    )


class NiErrorCatExistsNoInject(NiErrorBase):
    MESSAGE = (
        '...Category key already exists. No data have been injected.\n\n'
    )


class NiErrorCatUndefinedInSubNoInject(NiErrorBase):
    MESSAGE = (
        '...Category key of the subcategory undefined in this snippet. '
        'No data have been injected.\n\n'
    )


class NiErrorCatInSubDoesNotExistNoInject(NiErrorBase):
    MESSAGE = (
        '...Category key for the subcategory does not exist in this snippet '
        'or in the current notebook category mapping. '
        'No data have been injected.\n\n'
    )


class NiErrorSubUndefinedNoInject(NiErrorBase):
    MESSAGE = (
        '...Subcategory key or subcategory name undefined in this snippet. '
        'No data have been injected.\n\n'
    )


class NiErrorSubFormatNoInject(NiErrorBase):
    MESSAGE = (
        '...Subcategory key must start with an uppercase letter and contain '
        'only letters, numbers or underscores. '
        'No data have been injected.\n\n'
    )


class NiErrorSubExistsNoInject(NiErrorBase):
    MESSAGE = (
        '...Subcategory key already exists. No data have been injected.\n\n'
    )


class NiErrorIsSortableFalseNoInject(NiErrorBase):
    MESSAGE = (
        '..."is_sortable" must be True in "enabled" to use '
        '"include_new_entry". No data have been injected.\n\n'
    )


class NiErrorEntryExistsNoInject(NiErrorBase):
    MESSAGE = (
        '...Notebook entry already has been declared. '
        'No data have been injected.\n\n'
    )


class NiErrorAnEntryExistsNoInject(NiErrorBase):
    MESSAGE = (
        '...A notebook entry already has been declared. '
        'No data have been injected.\n'
        'These entries are correct:\n\n{%entries%}'
    )

    def err(
        self,
        logger=None,
        entries: str = NiErrorBase._DATA_ERROR,
        **kwargs
    ) -> None:
        super().err(
            logger,
            message=self.message.replace('{%entries%}', entries, 1),
            **kwargs
        )


class NiErrorNoActiveSim(NiErrorBase):
    MESSAGE = (
        '...No active Sim available while running {%data%}. '
        'Action has been skipped.\n\n'
    )

    def err(
        self,
        logger=None,
        data: str = NiErrorBase._DATA_ERROR,
        **kwargs
    ) -> None:
        super().err(
            logger,
            message=self.message.replace('{%data%}', data, 1),
            level='warning',
            **kwargs
        )


class NiErrorEnumReservedNameNoInject(NiErrorBase):
    MESSAGE = (
        '...The requested notebook enum name is reserved '
        'for a known external mod. No data have been '
        'injected.\n\n'
    )


class NiErrorEnumAllocationNoInject(NiErrorBase):
    MESSAGE = (
        '...Notebook Injector could not allocate a free '
        'enum value. No data have been injected. Check '
        'the enum diagnostics in the Notebook Injector '
        'log.\n\n'
    )


class NiErrorEnumConflictNoInject(NiErrorBase):
    MESSAGE = (
        '...A notebook enum conflict was detected. '
        'No data have been injected.\n\n'
        '{%details%}\n\n'
    )

    def err(
        self,
        logger=None,
        details: str = NiErrorBase._DATA_ERROR,
        **kwargs
    ) -> None:
        kwargs.setdefault(
            'ea_message',
            (
                '...A notebook enum conflict was detected. '
                'No data have been injected. Check the '
                'Notebook Injector log for details.\n\n'
            )
        )
        super().err(
            logger,
            message=self.message.replace('{%details%}', details, 1),
            **kwargs
        )


class NiErrorEnumLateConflict(NiErrorBase):
    MESSAGE = (
        '...A mod modified notebook enums after Notebook '
        'Injector completed its injections. Notebook '
        'categories or subcategories may not work '
        'correctly.\n\n{%details%}\n\n'
    )

    def err(
        self,
        logger=None,
        details: str = NiErrorBase._DATA_ERROR,
        **kwargs
    ) -> None:
        kwargs.setdefault(
            'ea_message',
            (
                '...A mod modified notebook enums after '
                'Notebook Injector completed its injections. '
                'Check the Notebook Injector log for details.\n\n'
            )
        )
        super().err(
            logger,
            message=self.message.replace('{%details%}', details, 1),
            **kwargs
        )


class NiErrorEntryUndefinedNoInject(NiErrorBase):
    MESSAGE = (
        '...No notebook entries are defined in this '
        'entry assignment snippet. No data have been '
        'injected.\n\n'
    )


class NiErrorSecretScandalFormatNoInject(NiErrorBase):
    MESSAGE = (
        '...NOTEBOOK_EXPANDABLE_SECRET_SCANDAL is '
        'reserved for the EA secrets and scandals '
        'notebook system. Notebook Injector does not '
        'support this subcategory format. No data have '
        'been injected.\n\n'
    )


class NiErrorUnsupportedEntryTypeNoInject(NiErrorBase):
    MESSAGE = (
        '...This notebook entry type is not supported by '
        'Notebook Injector. No data have been injected.\n\n'
    )


class NiErrorEntryValidationNoInject(NiErrorBase):
    MESSAGE = (
        '...A NotebookInjectorEntry contains invalid or '
        'incompatible tuning data. This entry assignment '
        'has not been injected.\n\n'
    )


class NiErrorEntryDoesNotExistNoInject(NiErrorBase):
    MESSAGE = (
        '...A notebook entry referenced by an entry '
        'assignment does not exist. No data have been '
        'injected.\n\n'
    )
