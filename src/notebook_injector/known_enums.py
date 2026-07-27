# Demeterio: Notebook Injector (script for The Sims 4)
# Do not copy, share or modify without my permission
# https://demeterio.tumblr.com
# https://discord.gg/mPyRPScgeS


# These reservations do not inject enum members.
#
# They prevent Notebook Injector from allocating values already known to be
# used by external mods which may load after Notebook Injector.
#
# Example:
#
# KNOWN_EXTERNAL_NOTEBOOK_ENUMS = {
#     'creator.mod_name': {
#         'display_name': 'Creator - Mod Name',
#         'include_categories_in_picker': True,
#         'categories': {
#             'EXTERNAL_CATEGORY': 45000,
#         },
#         'subcategories': {
#             'EXTERNAL_SUBCATEGORY': 45000,
#             'EXTERNAL_SUBCATEGORY_TWO': 45001,
#         },
#         'entry_types': {
#             'EXTERNAL_ENTRY_TYPE': 4,
#         },
#     },
# }

KNOWN_EXTERNAL_NOTEBOOK_ENUMS = {
    'simsonian.missions': {
        'display_name': 'Simsonian - Missions',
        'include_categories_in_picker': True,
        'categories': {
            'SimsonianMissions': 2847914255,
        },
        'subcategories': {
            'SimsonianMissions_Notes': 837764,
            'SimsonianMissions_Relic': 7649607,
            'SimsonianMissions_Lore': 13799425,
        },
        'entry_types': {},
    },
    'lot51.hvac_knowledge': {
        'display_name': 'Lot 51 - HVAC Knowledge',
        'include_categories_in_picker': True,
        'categories': {
            'Lot51HvacKnowledge': 3916477562,
        },
        'subcategories': {
            'Lot51HvacKnowledge_Generic': 3916477562,
        },
        'entry_types': {},
    },
}