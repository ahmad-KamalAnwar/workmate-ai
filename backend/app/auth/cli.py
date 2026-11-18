"""Create a user. Interactive: prompts for the password.

    docker compose exec api python -m app.auth.cli create-user --email you@example.com

Non-interactive: set WORKMATE_PASSWORD in the environment for that one command.
"""

import argparse
import asyncio
import getpass
import os
import sys

from app.auth.service import create_user
from app.core.config import load_settings
from app.core.db import Database
from app.core.errors import AppError


def _read_password() -> str:
    from_env = os.environ.get("WORKMATE_PASSWORD")
    if from_env:
        return from_env
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        sys.exit("Passwords do not match")
    return first


async def _create_user(email: str, display_name: str | None, password: str) -> None:
    db = Database(load_settings().sqlalchemy_database_url)
    try:
        async with db.sessionmaker() as session:
            user = await create_user(
                session, email=email, password=password, display_name=display_name
            )
        print(f"Created user {user.email} ({user.id})")
    finally:
        await db.dispose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m app.auth.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user", help="create a login user")
    create.add_argument("--email", required=True)
    create.add_argument("--name", dest="display_name")
    args = parser.parse_args(argv)

    try:
        asyncio.run(_create_user(args.email, args.display_name, _read_password()))
    except AppError as exc:
        sys.exit(f"Error: {exc.message}")


if __name__ == "__main__":
    main()
