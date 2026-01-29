import argparse
import io
import ssl
import urllib.request
from typing import Optional

from app import create_app
from app.db import get_session
from app.services.import_service import ImportService


def _iter_file(path: str, limit: Optional[int]):
    with open(path, "r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            if idx == 1:
                continue
            if limit and idx > limit:
                break
            yield line


def _iter_url(url: str, limit: Optional[int], ssl_context: Optional[ssl.SSLContext]):
    with urllib.request.urlopen(url, context=ssl_context) as response:
        text_stream = io.TextIOWrapper(response, encoding="utf-8")
        for idx, line in enumerate(text_stream, start=1):
            if idx == 1:
                continue
            if limit and idx > limit:
                break
            yield line


def main() -> None:
    parser = argparse.ArgumentParser(description="Import vehicle market data")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="Path to inventory file")
    source.add_argument("--url", help="URL to inventory file")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, no DB writes")
    parser.add_argument("--limit", type=int, default=None, help="Limit rows for testing")
    parser.add_argument(
        "--skip-log",
        help="Write skipped VINs and reasons to this file (CSV: vin,reason)",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable SSL certificate verification for URL downloads",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        with get_session(app) as session:
            service = ImportService(
                session=session,
                batch_size=app.config["IMPORT_BATCH_SIZE"],
            )

            if args.url:
                ssl_context = None
                if args.insecure:
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                row_iter = _iter_url(args.url, args.limit, ssl_context)
            else:
                row_iter = _iter_file(args.file, args.limit)

            stats = service.import_rows(row_iter, dry_run=args.dry_run)

    print("Import complete")
    print(f"Total rows: {stats.total_rows}")
    print(f"Inserted rows: {stats.inserted_rows}")
    print(f"Skipped rows: {stats.skipped_rows}")
    if stats.skipped_reasons:
        print("Skipped reasons:")
        for reason, count in sorted(stats.skipped_reasons.items()):
            print(f"  {reason}: {count}")
    if stats.skipped_details:
        if args.skip_log:
            with open(args.skip_log, "w", encoding="utf-8") as handle:
                handle.write("vin,reason\n")
                for vin, reason in stats.skipped_details:
                    handle.write(f"{vin},{reason}\n")
            print(f"Skipped details written to {args.skip_log}")
        else:
            print("Skipped details (vin, reason):")
            for vin, reason in stats.skipped_details:
                print(f"  {vin}: {reason}")


if __name__ == "__main__":
    main()
