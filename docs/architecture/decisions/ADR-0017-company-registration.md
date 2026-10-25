# ADR-0017: A company registers with its own form, a code sent to its e-mail, and validation by the team

Status: Accepted. Date: 2026-10-24. Extends ADR-0009 and ADR-0016.

## Context
A company is an organization of several people that issues documents in its own name. Registering it with a name and an e-mail, or through a provider such as Google, proves nothing about who is behind it. The person who registers must be someone validated in the corporation, and the people in charge of the platform may need to contact the company to confirm it.

## Decision
- **The company has its own form** (`POST /api/auth/company/register`): country (it decides the rest), legal name, tax identifier, fiscal address (street, number, city, province or state, postal code), contact e-mail of the company (the account's e-mail), the name of the person registering, an optional alias, the administrator's password and the acceptance of the current terms. The simple sign-up and the provider sign-up refuse the company kind: they only create independent professionals.
- **The country decides the checks.** The tax identifier is verified with its own rule (CUIT, RUT, NIT and CIF with their check digit; RFC and RIF by format) and stored in canonical form; the postal code by its country's pattern. The contact e-mail must be on the company's own domain, not a free mailbox. A tax identifier or e-mail already registered answers 409.
- **Two steps.** The form is checked as a whole and a 6-digit code goes to the company's e-mail; only a pending *registration* is stored (password already hashed, code stored hashed), never an account. The code (`POST /api/auth/company/verify`) creates the organization, its owner and the session. It is valid for 30 minutes, has 5 attempts, can be sent again after 60 seconds up to 3 times, and the registration is deleted when it runs out. If the e-mail cannot be delivered nothing is stored.
- **The terms** (version and time accepted, with the address) are recorded in the organization. The text shipped is a draft that legal counsel must review before real customers use it.
- **Validation by the team.** A company that verified its e-mail is *pending*; the team sees what it declared in the console and marks it validated, rejected or back to pending, with a note on how it was confirmed. A rejected company is suspended and its people are signed out. While pending the company can work, and a notice says so. Organizations created by the team, and every organization that existed before, are validated.
- **The declared data are used.** The company's first issuing company (ADR-0016) is created from them: legal name, tax identifier, address and e-mail.
- **E-mail delivery** uses the standard library (`EPC_SMTP_*`); in development without SMTP the message is written to an `outbox` folder and the log, and in other environments sending fails clearly.

## Consequences
- (+) A company is identified, verified by e-mail and confirmable by phone before it is trusted with more than its own data.
- (-) Delivering e-mail is now a deployment requirement for company sign-up. The independent professional's sign-up is the next one to get the same e-mail verification.
