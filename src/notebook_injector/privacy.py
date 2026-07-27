# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

"""Privacy-safe formatting for filesystem paths written to logs."""

import re
from typing import Optional


_TRACEBACK_FILE_PATTERN = re.compile(
    r'(?P<prefix>\bFile\s+["\'])(?P<path>[^"\']+)(?P<suffix>["\'])'
)
_QUOTED_ABSOLUTE_PATH_PATTERN = re.compile(
    r'(?P<quote>["\'])'
    r'(?P<path>(?:[A-Za-z]:[\\/]|/(?:Users|home|Volumes|private|mnt)/|\\\\)[^"\']+)'
    r'(?P=quote)',
    re.IGNORECASE
)


def privacy_safe_path(value: object) -> str:
    """Return a useful path without exposing user-specific parent folders."""
    text = str(value or '').strip()
    if not text:
        return '<unknown path>'

    normalized = text.replace('\\', '/')
    parts = [
        part
        for part in normalized.split('/')
        if part
    ]

    for index, part in enumerate(parts):
        if part.casefold() == 'the sims 4':
            return '/'.join(parts[index:])

    is_absolute = (
        normalized.startswith('/')
        or normalized.startswith('//')
        or (
            len(normalized) >= 3
            and normalized[1] == ':'
            and normalized[2] == '/'
        )
    )
    if not is_absolute:
        return normalized

    final_name = (
        parts[-1]
        if parts
        else '<unknown>'
    )
    return '<private path>/{}'.format(final_name)


def _replace_known_root(
    text: str,
    known_root: Optional[str]
) -> str:
    """Replace a known physical directory even when it is not quoted."""
    if not known_root:
        return text

    raw_root = str(known_root).strip()
    if not raw_root:
        return text

    safe_root = privacy_safe_path(raw_root)
    variants = {
        raw_root,
        raw_root.replace('\\', '/'),
        raw_root.replace('/', '\\')
    }

    for variant in sorted(
        variants,
        key=len,
        reverse=True
    ):
        if len(variant.strip('\\/')) < 3:
            continue

        text = re.sub(
            re.escape(variant),
            lambda _match: safe_root,
            text,
            flags=re.IGNORECASE
        )

    return text


def privacy_safe_log_text(
    value: object,
    known_root: Optional[str] = None
) -> str:
    """Remove user-specific filesystem paths from a log message."""
    text = str(value)
    text = _replace_known_root(
        text,
        known_root
    )

    def replace_traceback_path(match) -> str:
        return '{}{}{}'.format(
            match.group('prefix'),
            privacy_safe_path(
                match.group('path')
            ),
            match.group('suffix')
        )

    text = _TRACEBACK_FILE_PATTERN.sub(
        replace_traceback_path,
        text
    )

    def replace_quoted_path(match) -> str:
        quote = match.group('quote')
        return '{}{}{}'.format(
            quote,
            privacy_safe_path(
                match.group('path')
            ),
            quote
        )

    return _QUOTED_ABSOLUTE_PATH_PATTERN.sub(
        replace_quoted_path,
        text
    )
