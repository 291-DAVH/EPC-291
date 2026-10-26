"""The code lives in `validation` (what a board may contain), `boards` (reading, saving and removing boards), `results` (the calculation and the memo of a board)
and `jobs` (generating the drawings); this module keeps the names callers have always used (`sld.service.save`, ...) so none of them changes."""


from epc.modules.sld.validation import (  # noqa: F401
    CABLE_TYPES,
    KINDS,
    MAX_CIRCUITS,
    OPTIONS,
    PHASES,
    SYSTEMS,
    TOPOLOGIES,
    UNITS,
    _name,
    options,
    validate,
)
from epc.modules.sld.boards import (  # noqa: F401
    BOARD_TITLEBLOCK,
    DISCIPLINE,
    _blank,
    _parties_line,
    _resolve,
    _supply_errors,
    boards,
    create_board,
    example,
    remove_board,
    save,
    status,
    titleblock,
    view,
)
from epc.modules.sld.results import (  # noqa: F401
    _hash,
    _upstream,
    calculation,
    memo,
)
from epc.modules.sld.jobs import (  # noqa: F401
    _LOCKS,
    _job,
    _lock,
    generate,
)
