from enum import IntEnum

class Source(IntEnum):
    DESTINATION_CHARGER = 1     # Tesla D, from tesla oficial web
    SUPERCHARGER = 2            # Tesla SC. from tesla oficial web
    ELECTROMAPS = 3             # Page Electromaps, now is not used
    PLUGSHARE = 4               # Plugshare web
    CHARGEHUB = 5               # Page Chargehub, now is not used
