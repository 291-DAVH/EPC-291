# Sign-in with Google, GitHub, Facebook and LinkedIn

The platform lets a person sign in or sign up with an external account. A provider appears on the sign-in screen only when its **client id and secret** are configured; with none configured the screen shows just the email-or-username form.

## What you set on the server
| Variable | Meaning |
|---|---|
| `EPC_PUBLIC_URL` | public address of the customer app, e.g. `https://app.example.com` (in development `http://localhost:5173`). The provider sends the person back to it. |
| `EPC_SECRET_KEY` | long random text that signs the short cookies of the flow. Set it in production (otherwise it is random per process and a flow can fail if the API runs several processes). |
| `EPC_OAUTH_GOOGLE_CLIENT_ID` / `_CLIENT_SECRET` | Google |
| `EPC_OAUTH_GITHUB_CLIENT_ID` / `_CLIENT_SECRET` | GitHub |
| `EPC_OAUTH_FACEBOOK_CLIENT_ID` / `_CLIENT_SECRET` | Facebook |
| `EPC_OAUTH_LINKEDIN_CLIENT_ID` / `_CLIENT_SECRET` | LinkedIn |

The values come from the provider's developer console and never go in the repository (`.env`, or the secrets of your host).

## What you register at each provider
In every case you create an application and give it this **redirect (callback) URL**, exactly:

`<EPC_PUBLIC_URL>/api/auth/oauth/<provider>/callback`  where `<provider>` is `google`, `github`, `facebook` or `linkedin`.

| Provider | Where | Scopes the platform asks for |
|---|---|---|
| Google | Google Cloud Console, *APIs & Services*, OAuth consent screen and an *OAuth client ID* of type web application | `openid email profile` |
| GitHub | GitHub, *Settings*, *Developer settings*, *OAuth Apps* | `read:user user:email` |
| Facebook | Meta for Developers, a *Consumer* app with *Facebook Login* | `email public_profile` |
| LinkedIn | LinkedIn Developers, an app with the product *Sign In with LinkedIn using OpenID Connect* | `openid profile email` |

The consoles change their screens often: follow the provider's own current instructions for creating an OAuth application; what matters here is the callback URL, the scopes and the client id and secret.

## How it behaves
- **One button signs in and registers.** A person who already has an account (linked, or with the same *verified* email) goes straight in. A new person is asked the kind of subscription (independent or company) and an optional alias, and the account is created without a password.
- **Registration respects `EPC_SIGNUP`.** With sign-up closed, a provider cannot create accounts; an invitation can still be accepted with a provider that vouches for the invited email.
- **Safety rules.** Only customer accounts can use a provider: the engineering team, norm reviewers, inspectors and auditors always use their password. An existing account is linked automatically only when the provider vouches for the email (Google, GitHub's verified email, LinkedIn); Facebook never does, so an existing account is linked from *Account* after signing in with the password. A provider account belongs to one person. The last way to sign in cannot be removed: a person created through a provider sets a password before unlinking it.
- **Every use is recorded** in the platform audit log (`social_signup`, `social_login`, `identity_linked`, `identity_unlinked`).
