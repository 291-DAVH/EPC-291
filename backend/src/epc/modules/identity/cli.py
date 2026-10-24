"""Operator commands (run on the server):

  python -m epc.modules.identity.cli create-admin --email you@office.com --name "Your Name"     # first staff account, asks for the password
  python -m epc.modules.identity.cli create-admin ... --password-env EPC_ADMIN_PASSWORD         # non-interactive (deployment scripts)

Running it again with the same email resets that account's password.
"""
import argparse
import getpass
import os
import sys

from epc.core.errors import DomainError
from epc.modules.identity import service


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="epc-identity")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create-admin", help="create (or reset) a platform staff account")
    c.add_argument("--email", required=True)
    c.add_argument("--name", default="")
    c.add_argument("--role", choices=["admin", "standards"], default="admin", help="admin = engineering staff; standards = norm reviewer (sees only the norms review area)")
    c.add_argument("--password-env", help="read the password from this environment variable instead of asking")
    args = ap.parse_args(argv)
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
