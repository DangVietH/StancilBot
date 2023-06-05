from .bot_configs import config_var
from .pagination import *


def time_converter(time):
    time_conversion = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    time_pos = ['s', 'm', 'h', 'd']
    time_unit = time[-1]

    if time_unit not in time_pos:
        return -1

    try:
        val = int(time[0])
    except:
        return -2

    return val * time_conversion[time_unit]

