import binascii

__version__ = "1.2.0"

import layouts

try:
    # noinspection PyUnresolvedReferences
    from typing import Tuple
except ImportError:
    pass

LAYOUTS = {(1, 0, 0): layouts.layout_1}

ADJECTIVES = [
    "Angry",
    "Bored",
    "Curious",
    "Devious",
    "Excited",
    "Fierce",
    "Grumpy",
    "Hungry",
    "Idle",
    "Jealous"
]
ANIMALS = [
    "Antelope",
    "Badger",
    "Cheetah",
    "Dolphin",
    "Eagle",
    "Fox",
    "Gorilla",
    "Hamster",
    "Iguana",
    "Jaguar"
]
BASENAME = "SAP6"


def get_id_indexes():
    import microcontroller  # hidden so can use version.py in documentation
    crc = binascii.crc32(microcontroller.cpu.uid)
    a = crc % 100
    return a // 10, a % 10


def get_short_name() -> str:
    a, b = get_id_indexes()
    return f"{BASENAME}_{chr(a + 0x41)}{chr(b + 0x41)}"


def get_long_name() -> str:
    a, b = get_id_indexes()
    return f"{ADJECTIVES[a]} {ANIMALS[b]}"


def get_sw_version() -> str:
    return __version__


def get_hw_version() -> Tuple[int, int, int]:
    import microcontroller
    version = tuple(microcontroller.nvm[-3:])
    if version == (255, 255, 255):
        version = (1, 0, 0)
    return version


def get_hw_version_as_str() -> str:
    v = get_hw_version()
    return ".".join(str(x) for x in v)


def get_layout() -> layouts.Layout:
    return LAYOUTS[get_hw_version()]
