from enum import IntEnum


class FormFactor(IntEnum):
    """
    The labels for the Brother QL series are supplied either as die-cut (pre-sized), or for more flexibility the continuous label tapes offer the ability to vary the label length.
    """

    #: rectangular die-cut labels
    DIE_CUT = 1
    #: endless (continouse) labels
    ENDLESS = 2
    #: round die-cut labels
    ROUND_DIE_CUT = 3
    #: endless P-touch labels
    PTOUCH_ENDLESS = 4
