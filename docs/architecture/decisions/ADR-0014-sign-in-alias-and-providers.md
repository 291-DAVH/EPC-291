# ADR-0014: Sign-in with an alias and with external providers

Status: Accepted. Date: 2026-10-24. Extends ADR-0009 and ADR-0013.

## Decision
- **One box, email or alias.** `users.username` is an optional alias (lowercase, 3 to 30 characters, never containing `@`, unique, a few reserved names). The sign-in form takes one value: with an `@` it is an email, without it an alias. Failed attempts are throttled and audited by the typed value, whichever it is.
- **External providers** (Google, GitHub, Facebook, LinkedIn) by OAuth 2 authorization code, with PKCE where the provider supports it, implemented with the standard library (no new dependency). The state, the PKCE verifier and the data of a person still registering travel in short cookies signed with `EPC_SECRET_KEY`; nothing is kept on the server between the two redirects. A provider is offered only when its client id and secret are configured.
- **Who may use a provider**: customer accounts only. Internal accounts (staff, reviewer, inspector, auditor) never sign in through a provider, even if a link existed.
- **Linking is by verified email or by an explicit act.** An existing account is linked automatically only when the provider vouches for the email; otherwise the owner links the provider from their account after signing in. `identities (provider, subject)` is unique: a provider account belongs to one person.
- **Registering**: the same button; a new person chooses the subscription kind and the account is created with no password, only if sign-up is open or through an invitation addressed to the email the provider vouches for. Such an account can set a password without a current one; its last way to sign in cannot be removed.
- Everything is written to the audit log.

## Consequences
- (+) Fewer passwords to manage for customers, and the protections of ADR-0013 (matrix, audit, tenant isolation) apply unchanged: a provider only decides *who is signing in*.
- (-) Needs the keys of each provider to be created and kept by whoever runs the platform (`docs/oauth-providers.md`). Provider flows could not be exercised against the real services in this environment: they are covered by tests with simulated providers and must be tried once with real keys. Two-factor authentication and email delivery remain pending.
