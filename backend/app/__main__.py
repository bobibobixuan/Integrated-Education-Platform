"""python -m app <command>"""
import argparse
import sys

from app.cli import migrate_upgrade, migrate_status, migrate_downgrade


def main():
    parser = argparse.ArgumentParser(description="Integrated-Education-Platform")
    subparsers = parser.add_subparsers(dest="command")

    migrate_parser = subparsers.add_parser("migrate", help="数据库迁移管理")
    migrate_parser.add_argument("--upgrade", action="store_true", help="执行待执行的迁移")
    migrate_parser.add_argument("--status", action="store_true", help="查看迁移状态")
    migrate_parser.add_argument("--downgrade", type=str, nargs="?", const="-1", help="回滚到指定版本")

    args = parser.parse_args()

    if args.command == "migrate":
        if args.upgrade:
            migrate_upgrade()
        elif args.status:
            migrate_status()
        elif args.downgrade is not None:
            migrate_downgrade(args.downgrade)
        else:
            migrate_status()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
