# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from typing import Any, cast
from ui.notebook_tuning import NotebookSubCategories, NotebookTuning


_registered_categories = {}
_registered_subcategories = {}
_registered_entry_assignments = {}
_NotebookSubCategories = cast(Any, NotebookSubCategories)


def register_category(category_key: str, category_data: dict) -> None:
    _registered_categories[category_key] = category_data


def register_subcategory(
    subcategory_key: str,
    subcategory_data: dict
) -> None:
    _registered_subcategories[subcategory_key] = subcategory_data


def register_entry_assignment(
    assignment_key: int,
    assignment_data: dict
) -> None:
    _registered_entry_assignments[assignment_key] = assignment_data


def registered_categories() -> dict:
    return dict(_registered_categories)


def registered_subcategories() -> dict:
    return dict(_registered_subcategories)


def registered_entry_assignments() -> dict:
    return dict(_registered_entry_assignments)


def has_registered_category(category_key: str) -> bool:
    return category_key.lower() in {
        key.lower() for key in _registered_categories
    }


def has_registered_subcategory(subcategory_key: str) -> bool:
    return subcategory_key.lower() in {
        key.lower() for key in _registered_subcategories
    }


def find_category_key_for_existing_subcategory(
    subcategory_key: str
):
    subcategory = _NotebookSubCategories[subcategory_key]
    notebook_mapping = cast(
        Any,
        NotebookTuning.NOTEBOOK_CATEGORY_MAPPING
    )
    for category, mapping in notebook_mapping.items():
        if hasattr(mapping, 'subcategories'):
            subcategories = mapping.subcategories
        else:
            subcategories = mapping.get('subcategories', {})
        if subcategory in subcategories:
            return category.name
    return None
