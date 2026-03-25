"""Auth module for seqspec CLI."""

import json
from argparse import ArgumentParser, Namespace, RawTextHelpFormatter

from seqspec.auth import AuthProfile, AuthRegistry, init_profile


def setup_auth_args(parser) -> ArgumentParser:
    subparser = parser.add_parser(
        "auth",
        description="""
Manage remote authentication profiles.

Examples:
seqspec auth init --profile igvf --host api.data.igvf.org --host data.igvf.org --username-env IGVF_ACCESS_KEY_ID --password-env IGVF_ACCESS_KEY_SECRET
seqspec auth path
seqspec auth list
seqspec auth resolve https://api.data.igvf.org/reference-files/...
---
""",
        help="Manage remote authentication profiles",
        formatter_class=RawTextHelpFormatter,
    )
    subparsers = subparser.add_subparsers(dest="auth_command", metavar="<AUTH_CMD>")

    init_parser = subparsers.add_parser("init", help="Create or update an auth profile")
    init_parser.add_argument("--profile", required=True)
    init_parser.add_argument("--host", dest="hosts", action="append", required=True)
    init_parser.add_argument("--kind", default="basic", choices=["basic"])
    init_parser.add_argument("--username-env", required=True)
    init_parser.add_argument("--password-env", required=True)

    subparsers.add_parser("path", help="Show auth config path")
    subparsers.add_parser("list", help="List auth profiles")

    resolve_parser = subparsers.add_parser("resolve", help="Resolve profile for a URL")
    resolve_parser.add_argument("url")
    resolve_parser.add_argument("--auth-profile", default=None)

    return subparser


def run_auth(parser: ArgumentParser, args: Namespace) -> None:
    if args.auth_command == "init":
        value = init_profile(
            args.profile,
            AuthProfile(
                hosts=args.hosts,
                kind=args.kind,
                username_env=args.username_env,
                password_env=args.password_env,
            ),
        )
    elif args.auth_command == "path":
        registry = AuthRegistry.load()
        location = registry.location
        value = {
            "kind": "auth_config_path",
            "source": location["source"],
            "path": str(location["path"]) if location["path"] else None,
            "exists": location["exists"],
        }
    elif args.auth_command == "list":
        registry = AuthRegistry.load()
        value = registry.profile_summaries()
    elif args.auth_command == "resolve":
        registry = AuthRegistry.load()
        value = registry.resolve_summary(args.url, args.auth_profile)
    else:
        parser.error("auth requires a subcommand")
        return

    print(json.dumps(value, indent=2))
