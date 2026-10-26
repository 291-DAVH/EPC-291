"""Company registration: country decides the fields, the whole form is checked, a code goes to the company's e-mail, and the team validates the company afterwards."""
import re
import unittest

from epc.core import mail
from epc.core.config import settings
from epc.modules.identity import countries, registration
from tests.integration.test_identity_api import PW, Base

FORM = {"country": "AR", "org_name": "Metal SRL", "tax_id": "30-70308853-4", "street": "Av. San Martín", "number": "1234", "locality": "Mendoza", "region": "Mendoza", "postal_code": "M5500",
        "contact_email": "admin@metal.com.ar", "name": "Raúl Gómez", "username": "raul.admin", "password": PW, "accept_terms": True}


class Registration(Base):
    def setUp(self):
        super().setUp()
        settings.signup = "open"
        self.sent = []
        mail.set_transport(lambda to, subject, body: self.sent.append((to, subject, body)))

    def tearDown(self):
        mail.set_transport(None)
        registration.CODE_ATTEMPTS, registration.RESEND_SECONDS = 5, 60
        super().tearDown()

    def form(self, **over):
        return {**FORM, "terms_version": self.client().get("/api/auth/terms").json()["version"], **over}

    def code(self):
        return re.search(r"\b(\d{6})\b", self.sent[-1][2]).group(1)

    def start(self, c=None, **over):
        c = c or self.client()
        r = c.post("/api/auth/company/register", json=self.form(**over))
        return c, r


class TestCountriesAndTerms(Registration):
    def test_the_country_decides_the_tax_identifier_and_the_address_labels(self):
        cat = {c["code"]: c for c in self.client().get("/api/auth/countries").json()}
        self.assertEqual({k: v["tax"]["id"] for k, v in cat.items()}, {"AR": "CUIT", "VE": "RIF", "MX": "RFC", "CO": "NIT", "CL": "RUT", "ES": "CIF"})
        self.assertEqual((cat["AR"]["region"]["es"], cat["CO"]["region"]["es"], cat["CL"]["region"]["es"]), ("Provincia", "Departamento", "Región"))
        for code, c in cat.items():
            self.assertIsNotNone(countries.check_tax_id(code, c["tax"]["example"]), code)                  # the example shown to the person is itself valid

    def test_tax_identifiers_are_checked_with_their_own_rule(self):
        good = {"AR": "30-70308853-4", "CL": "60.805.000-0", "CO": "800197268-4", "ES": "A58818501", "MX": "ABC010203XY1", "VE": "J-12345678-9"}
        for country, value in good.items():
            self.assertIsNotNone(countries.check_tax_id(country, value), country)
        bad = {"AR": ["30-70308853-5", "20-12345678-6", "123"], "CL": ["60.805.000-1"], "CO": ["800197268-5"], "ES": ["A58818502", "B12345678"], "MX": ["ABC011303XY1"], "VE": ["X-12345678-9"]}
        for country, values in bad.items():
            for v in values:
                self.assertIsNone(countries.check_tax_id(country, v), (country, v))
        self.assertEqual(countries.check_tax_id("AR", "30703088534"), "30-70308853-4")                    # typed without hyphens: stored in its canonical form

    def test_the_terms_are_served_in_both_languages(self):
        es, en = (self.client().get(f"/api/auth/terms?lang={lg}").json() for lg in ("es", "en"))
        self.assertEqual(es["version"], en["version"])
        self.assertIn("persona validada", es["text"])
        self.assertIn("validated person", en["text"])


class TestRegistration(Registration):
    def test_the_whole_form_is_checked_before_anything_is_sent(self):
        c, r = self.start(tax_id="30-70308853-5", postal_code="12", contact_email="persona@gmail.com", accept_terms=False, street="", password="x")
        self.assertEqual(r.status_code, 422)
        self.assertEqual(sorted(r.json()["detail"]["errors"]), ["accept_terms", "contact_email", "password", "postal_code", "street", "tax_id"])
        self.assertEqual(self.sent, [])
        self.assertEqual(self.start(country="XX")[1].status_code, 422)
        self.assertEqual(self.start(terms_version="old")[1].status_code, 422)                              # the version of the terms shown must be the current one
        self.assertIn("contact_email", self.start(contact_email="a@hotmail.com")[1].json()["detail"]["errors"])   # a company's own domain, not a free mailbox

    def test_the_code_goes_to_the_companys_email_and_creates_a_pending_organization(self):
        c, r = self.start()
        self.assertEqual(r.status_code, 201, r.text)
        self.assertEqual(r.json()["email"], "ad***@metal.com.ar")
        self.assertEqual(self.sent[0][0], "admin@metal.com.ar")
        self.assertFalse(c.get("/api/me").json()["authenticated"])                                        # nothing is an account yet
        rid = r.json()["registration"]
        real = self.code()
        wrong = c.post("/api/auth/company/verify", json={"registration": rid, "code": "000000" if real != "000000" else "111111"})
        self.assertEqual(wrong.status_code, 422)
        ok = c.post("/api/auth/company/verify", json={"registration": rid, "code": real})
        self.assertEqual(ok.status_code, 201, ok.text)
        me = c.get("/api/me").json()
        self.assertEqual((me["authenticated"], me["account_type"], me["org"], me["org_kind"], me["org_validation"], me["email"], me["username"]),
                         (True, "corporate_owner", "Metal SRL", "company", "pending", "admin@metal.com.ar", "raul.admin"))
        self.assertEqual(c.post("/api/auth/company/verify", json={"registration": rid, "code": real}).status_code, 404)      # used once
        self.assertEqual(self.client().post("/api/auth/login", json={"login": "raul.admin", "password": PW}).status_code, 200)    # the alias works
        staff = self.staff()
        org = next(o for o in staff.get("/api/identity/orgs").json() if o["name"] == "Metal SRL")
        self.assertEqual((org["validation"], org["country"], org["tax_id"], org["contact_email"], org["address"]["postal_code"], org["registered_by"]),
                         ("pending", "AR", "30-70308853-4", "admin@metal.com.ar", "M5500", "Raúl Gómez"))
        iss = c.get("/api/data/issuers").json()                                                           # what it declared is its first issuing company
        self.assertEqual((iss[0]["legal_name"], iss[0]["tax_id"], iss[0]["email"], iss[0]["address"]), ("Metal SRL", "30-70308853-4", "admin@metal.com.ar", "Av. San Martín 1234, Mendoza, Mendoza, M5500"))
        audit = [e["action"] for e in staff.get("/api/identity/audit?limit=50").json()]
        self.assertIn("company_registration_started", audit)
        self.assertIn("company_registered", audit)

    def test_a_company_or_an_email_cannot_register_twice(self):
        c, r = self.start()
        c.post("/api/auth/company/verify", json={"registration": r.json()["registration"], "code": self.code()})
        other = self.start(contact_email="otro@metal.com.ar", username="otro.admin")[1]
        self.assertEqual((other.status_code, list(other.json()["detail"]["errors"])), (409, ["tax_id"]))
        again = self.start(tax_id="30-70308853-4", contact_email="admin@metal.com.ar", org_name="Otra", username="otra.admin")[1]
        self.assertEqual(again.status_code, 409)

    def test_wrong_codes_are_limited_and_codes_can_be_asked_again_but_not_forever(self):
        registration.RESEND_SECONDS = 0
        c, r = self.start()
        rid = r.json()["registration"]
        self.assertEqual(c.post("/api/auth/company/resend", json={"registration": rid}).status_code, 200)
        self.assertEqual(c.post("/api/auth/company/resend", json={"registration": rid}).status_code, 200)
        self.assertEqual(c.post("/api/auth/company/resend", json={"registration": rid}).status_code, 429)        # three codes at most
        self.assertEqual(len(self.sent), 3)
        real = self.code()
        bad = "999999" if real != "999999" else "888888"
        for _ in range(5):
            c.post("/api/auth/company/verify", json={"registration": rid, "code": bad})
        self.assertEqual(c.post("/api/auth/company/verify", json={"registration": rid, "code": real}).status_code, 429)
        self.assertEqual(c.post("/api/auth/company/verify", json={"registration": rid, "code": real}).status_code, 404)    # the registration is gone: start again

    def test_the_resend_waits_between_codes(self):
        c, r = self.start()
        self.assertEqual(c.post("/api/auth/company/resend", json={"registration": r.json()["registration"]}).status_code, 429)

    def test_registration_is_closed_when_the_platform_closes_it(self):
        settings.signup = "closed"
        self.assertEqual(self.start()[1].status_code, 403)

    def test_a_company_does_not_register_with_the_simple_form(self):
        r = self.client().post("/api/auth/signup", json={"kind": "company", "org_name": "X SRL", "name": "A", "email": "a@x.com", "password": PW})
        self.assertEqual(r.status_code, 422)

    def test_mail_that_cannot_be_delivered_leaves_nothing_behind(self):
        from epc.core.errors import Failure

        def broken(to, subject, body):
            raise Failure("the e-mail could not be sent")
        mail.set_transport(broken)
        self.assertEqual(self.start()[1].status_code, 500)
        mail.set_transport(lambda *a: self.sent.append(a))
        self.assertEqual(self.start()[1].status_code, 201)                                                 # the failed attempt did not hold the tax id or the e-mail


class TestValidationByTheTeam(Registration):
    def register(self):
        c, r = self.start()
        c.post("/api/auth/company/verify", json={"registration": r.json()["registration"], "code": self.code()})
        return c

    def slug(self, staff):
        return next(o["slug"] for o in staff.get("/api/identity/orgs").json() if o["name"] == "Metal SRL")

    def test_the_team_validates_the_company(self):
        owner = self.register()
        staff = self.staff()
        self.assertEqual(owner.get("/api/me").json()["org_validation"], "pending")
        slug = self.slug(staff)
        r = staff.patch(f"/api/identity/orgs/{slug}", json={"validation": "validated", "validation_note": "Confirmado por teléfono con el contador"})
        self.assertEqual((r.status_code, r.json()["validation"], r.json()["validation_note"]), (200, "validated", "Confirmado por teléfono con el contador"))
        self.assertEqual(owner.get("/api/me").json()["org_validation"], "validated")
        self.assertEqual(staff.patch(f"/api/identity/orgs/{slug}", json={"validation": "maybe"}).status_code, 422)

    def test_a_rejected_registration_cannot_work(self):
        owner = self.register()
        staff = self.staff()
        r = staff.patch(f"/api/identity/orgs/{self.slug(staff)}", json={"validation": "rejected", "validation_note": "No se pudo confirmar"})
        self.assertEqual((r.json()["validation"], r.json()["active"]), ("rejected", False))
        self.assertFalse(owner.get("/api/me").json()["authenticated"])                                     # signed out at once
        self.assertIn(self.client().post("/api/auth/login", json={"login": "raul.admin", "password": PW}).status_code, (401, 403))

    def test_organizations_created_by_the_team_are_already_validated(self):
        staff = self.staff()
        r = staff.post("/api/identity/orgs", json={"name": "Alfa SRL", "kind": "company", "seats": 2, "owner_email": "a@alfa.com"})
        self.assertEqual(r.json()["org"]["validation"], "validated")


if __name__ == "__main__":
    unittest.main()
