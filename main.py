import argparse
from db import init_db
from import_csv import import_csv


def main():
    parser = argparse.ArgumentParser(description="finffuts — local finance tracker")
    parser.add_argument("--import", dest="import_path", metavar="FILE", help="Import a Chase CSV file")
    args = parser.parse_args()

    print("Finance app starting...")
    init_db()

    if args.import_path:
        import_csv(args.import_path)


if __name__ == "__main__":
    main()
