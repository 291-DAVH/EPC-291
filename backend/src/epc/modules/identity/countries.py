"""Countries a company can register from: the name of its tax identifier and how it is checked, the address fields and the postal code.

The country decides the form (labels) and the checks: a tax id that fails its own country's rule is refused before anything is stored. Where the identifier carries a
check digit (CUIT, RUT, NIT, CIF) it is verified; for the others (RFC, RIF) the format is. [VERIFICAR] before relying on it in production for a new country.
"""
import re
from typing import Callable, Dict, Optional, Tuple

TaxCheck = Callable[[str], Optional[str]]          # raw -> canonical form, or None when it is not valid


def _digits(s: str) -> str:
    return re.sub(r"[^0-9]", "", s)


def _clean(s: str) -> str:
    return re.sub(r"[\s.\-_/]", "", (s or "").strip().upper())


def tax_ar(raw: str) -> Optional[str]:
    """CUIT of a legal entity: 11 digits, prefix 30, 33 or 34, check digit modulo 11."""
    d = _digits(raw)
    if len(d) != 11 or d[:2] not in ("30", "33", "34"):
        return None
    total = sum(int(a) * b for a, b in zip(d[:10], (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)))
    r = 11 - total % 11
    dv = {11: 0}.get(r, r)
    if dv == 10 or dv != int(d[10]):
        return None
    return f"{d[:2]}-{d[2:10]}-{d[10]}"


def tax_cl(raw: str) -> Optional[str]:
    """RUT: body of 7 or 8 digits and a check digit (0-9 or K), modulo 11."""
    c = _clean(raw)
    if not re.fullmatch(r"\d{7,8}[0-9K]", c):
        return None
    body, dv = c[:-1], c[-1]
    total = sum(int(ch) * (2 + i % 6) for i, ch in enumerate(reversed(body)))
    r = 11 - total % 11
    want = "0" if r == 11 else "K" if r == 10 else str(r)
    return f"{body}-{dv}" if dv == want else None


def tax_co(raw: str) -> Optional[str]:
    """NIT with its verification digit: 8 to 10 digits and the digit, modulo 11."""
    c = _clean(raw)
    if not re.fullmatch(r"\d{9,11}", c):
        return None
    body, dv = c[:-1], int(c[-1])
    weights = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)
    total = sum(int(ch) * w for ch, w in zip(reversed(body), weights))
    r = total % 11
    return f"{body}-{dv}" if dv == (r if r < 2 else 11 - r) else None


def tax_es(raw: str) -> Optional[str]:
    """CIF of an entity: a letter, seven digits and a control (digit or letter, by the kind of entity)."""
    c = _clean(raw)
    if not re.fullmatch(r"[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]", c):
        return None
    digits = c[1:8]
    even = sum(int(digits[i]) for i in (1, 3, 5))
    odd = sum(sum(divmod(int(digits[i]) * 2, 10)) for i in (0, 2, 4, 6))
    control = (10 - (even + odd) % 10) % 10
    letter, ctl = "JABCDEFGHI"[control], c[8]
    if c[0] in "PQRSNW":
        ok = ctl == letter
    elif c[0] in "ABEH":
        ok = ctl == str(control)
    else:
        ok = ctl in (letter, str(control))
    return c if ok else None


def tax_mx(raw: str) -> Optional[str]:
    """RFC of a legal entity (12 characters): three letters (or & Ñ), date AAMMDD and three of homoclave. The format is checked."""
    c = (raw or "").strip().upper().replace(" ", "").replace("-", "")
    m = re.fullmatch(r"[A-ZÑ&]{3}(\d{2})(\d{2})(\d{2})[A-Z0-9]{3}", c)
    if not m or not 1 <= int(m.group(2)) <= 12 or not 1 <= int(m.group(3)) <= 31:
        return None
    return c


def tax_ve(raw: str) -> Optional[str]:
    """RIF of a legal entity or government body: J or G and nine digits. The format is checked."""
    c = _clean(raw)
    m = re.fullmatch(r"([JG])(\d{8})(\d)", c)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


COUNTRIES: Dict[str, dict] = {
    "AR": {"name": {"es": "Argentina", "en": "Argentina"}, "tax": {"id": "CUIT", "check": tax_ar, "example": "30-12345678-1", "hint": {"es": "11 dígitos; prefijo 30, 33 o 34 (persona jurídica)", "en": "11 digits; prefix 30, 33 or 34 (legal entity)"}},
           "region": {"es": "Provincia", "en": "Province"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"[A-Z]?\d{4}([A-Z]{3})?", "example": "X5000ABC"}},
    "VE": {"name": {"es": "Venezuela", "en": "Venezuela"}, "tax": {"id": "RIF", "check": tax_ve, "example": "J-12345678-9", "hint": {"es": "J o G, ocho dígitos y un dígito verificador", "en": "J or G, eight digits and a check digit"}},
           "region": {"es": "Estado", "en": "State"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"\d{4}", "example": "1010"}},
    "MX": {"name": {"es": "México", "en": "Mexico"}, "tax": {"id": "RFC", "check": tax_mx, "example": "ABC010203XY1", "hint": {"es": "12 caracteres (persona moral)", "en": "12 characters (legal entity)"}},
           "region": {"es": "Estado", "en": "State"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"\d{5}", "example": "06600"}},
    "CO": {"name": {"es": "Colombia", "en": "Colombia"}, "tax": {"id": "NIT", "check": tax_co, "example": "900123456-8", "hint": {"es": "con dígito de verificación", "en": "with its verification digit"}},
           "region": {"es": "Departamento", "en": "Department"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"\d{6}", "example": "110111"}},
    "CL": {"name": {"es": "Chile", "en": "Chile"}, "tax": {"id": "RUT", "check": tax_cl, "example": "76.123.456-0", "hint": {"es": "con dígito verificador", "en": "with its check digit"}},
           "region": {"es": "Región", "en": "Region"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"\d{7}", "example": "8320000"}},
    "ES": {"name": {"es": "España", "en": "Spain"}, "tax": {"id": "CIF", "check": tax_es, "example": "A58818501", "hint": {"es": "letra, siete dígitos y control", "en": "letter, seven digits and a control character"}},
           "region": {"es": "Provincia", "en": "Province"}, "postal": {"label": {"es": "Código postal", "en": "Postal code"}, "pattern": r"\d{5}", "example": "28001"}},
}

FREE_MAIL = ("gmail.", "googlemail.", "hotmail.", "outlook.", "live.", "msn.", "yahoo.", "ymail.", "icloud.", "me.com", "proton.", "aol.", "gmx.", "yandex.", "mail.com", "zoho.com")


def tax_label(country: str) -> str:
    return COUNTRIES[country]["tax"]["id"]


def check_tax_id(country: str, raw: str) -> Optional[str]:
    """Canonical tax identifier, or None when it is not valid for that country."""
    c = COUNTRIES.get(country)
    return c["tax"]["check"](raw or "") if c else None


def check_postal(country: str, raw: str) -> Optional[str]:
    c = COUNTRIES.get(country)
    v = re.sub(r"\s", "", (raw or "").upper())
    return v if c and re.fullmatch(c["postal"]["pattern"], v) else None


def is_free_mail(email: str) -> bool:
    domain = (email or "").rsplit("@", 1)[-1].lower()
    return any(domain.startswith(f) or domain == f.rstrip(".") for f in FREE_MAIL)


def catalog() -> list:
    """What the registration form needs: per country, its name, the tax id name/example/hint and the address labels."""
    return [{"code": k, "name": v["name"], "tax": {"id": v["tax"]["id"], "example": v["tax"]["example"], "hint": v["tax"]["hint"]}, "region": v["region"],
             "postal": {"label": v["postal"]["label"], "example": v["postal"]["example"]}} for k, v in COUNTRIES.items()]
