"""Operator commands (run on the server or on the development machine):

  python -m epc.modules.identity.cli create-admin --email you@office.com --name "Your Name"     # first staff account, asks for the password
  python -m epc.modules.identity.cli create-admin ... --password-env EPC_ADMIN_PASSWORD         # non-interactive (deployment scripts)
  python -m epc.modules.identity.cli create-admin ... --role standards|inspector|auditor        # other internal accounts
  python -m epc.modules.identity.cli reset-accounts --yes [--audit]                             # DEVELOPMENT ONLY: delete every account and organization

Running create-admin again with the same email resets that account's password.
"""
import argparse
import getpass
import os
import sys

from epc.core.config import settings
from epc.core.errors import DomainError
from epc.modules.identity import service


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc-identity")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-admin", help="create (or reset) an internal account")
    c.add_argument("--email", required=True)
    c.add_argument("--name", default="")
    c.add_argument("--role", choices=["admin", "standards", "inspector", "auditor"], default="admin",
                   help="admin = engineering staff; standards = norm reviewer; inspector / auditor = see only the organizations assigned to them")
    c.add_argument("--password-env", help="read the password from this environment variable instead of asking")
    r = sub.add_parser("reset-accounts", help="DEVELOPMENT ONLY: delete every account, organization, session, invitation and assignment")
    r.add_argument("--yes", action="store_true", help="confirm: without it nothing is deleted")
    r.add_argument("--audit", action="store_true", help="also delete the audit log")
    args = ap.parse_args(argv)
    if args.cmd == "reset-accounts":
        if settings.env == "production":
            print("refused: this is never allowed in production")
            return 1
        if not args.yes:
            print("nothing deleted: add --yes to confirm (every account and organization will be removed; projects on disk are kept)")
            return 1
        try:
            counts = service.reset_accounts(args.audit)
        except DomainError as e:
            print(f"error: {e.detail}")
            return 1
        print("deleted:", ", ".join(f"{k} {v}" for k, v in counts.items()))
        return 0
    password = os.environ.get(args.password_env, "") if args.password_env else getpass.getpass("Password: ")
    if not args.password_env and password != getpass.getpass("Repeat: "):
        print("the passwords differ")
        return 1
    try:
        user = service.bootstrap_admin(args.email, args.name, password, args.role)
    except DomainError as e:
        print(f"error: {e.detail}")
        return 1
    print(f"{args.role} account ready: {user['email']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
