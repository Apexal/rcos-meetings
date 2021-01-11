from typing import Dict


def emtpy_to_none(dct: Dict):
    new_dict = dict()
    for key, val in dct.items():
        if val == '':
            new_dict[key] = None
        else:
            new_dict[key] = val
    return new_dict
