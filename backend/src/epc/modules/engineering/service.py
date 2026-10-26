"""The code lives in `files` (what the engineering folder holds and how it is shown) and `criteria` (design criteria and their report);
this module keeps the names callers have always used (`engineering.service.overview`, ...) so none of them changes."""


from epc.modules.engineering.files import (  # noqa: F401
    CALC_SUFFIX,
    _doc,
    _file,
    _kind,
    calculation_view,
    overview,
    svg_file,
    text_view,
)
from epc.modules.engineering.criteria import (  # noqa: F401
    SLUG_RE,
    SOURCES,
    _T,
    _catalog,
    _clean,
    _now,
    _spec,
    criteria_view,
    report,
    reset_criterion,
    set_criterion,
)
