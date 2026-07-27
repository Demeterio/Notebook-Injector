# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS

from event_testing.resolver import SingleSimResolver


def get_notebook_tracker(sim):
    if sim is None:
        return None
    sim_info = getattr(sim, 'sim_info', None)
    if sim_info is None:
        return None
    return getattr(sim_info, 'notebook_tracker', None)


def remove_notebook_entries_by_category(
    notebook,
    category_id
) -> None:
    notebook.remove_entries_by_category(category_id)


def remove_notebook_entries_by_subcategory(
    notebook,
    subcategory_id
) -> None:
    notebook.remove_entries_by_subcategory(subcategory_id)


def apply_loot_to_sim_info(
    loot,
    sim_info
) -> None:
    loot.apply_to_resolver(
        SingleSimResolver(sim_info)
    )
