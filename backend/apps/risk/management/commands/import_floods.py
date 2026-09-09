import csv
from datetime import datetime

from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand, CommandError

from apps.risk.models import FloodEvent


class Command(BaseCommand):
    help = "Import historical flood events from a CSV file."
    required_columns = {"name", "event_date", "latitude", "longitude", "severity", "source"}

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--district", default="")
        parser.add_argument("--source-prefix", default="csv")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        path = options["csv_path"]
        try:
            fh = open(path, newline="", encoding="utf-8")
        except OSError as exc:
            raise CommandError(str(exc)) from exc

        created = updated = skipped = 0
        with fh:
            reader = csv.DictReader(fh)
            columns = set(reader.fieldnames or [])
            missing = self.required_columns - columns
            if missing:
                raise CommandError(f"Missing columns: {sorted(missing)}")

            for row_number, row in enumerate(reader, start=2):
                try:
                    source = f'{options["source-prefix"]}:{row["source"]}'.strip(":")
                    source_record_id = row.get("id") or str(row_number)
                    event = {
                        "name": row["name"].strip(),
                        "event_date": datetime.strptime(row["event_date"], "%Y-%m-%d").date(),
                        "district": (row.get("district") or options["district"]).strip(),
                        "location": Point(float(row["longitude"]), float(row["latitude"]), srid=4326),
                        "severity": float(row["severity"]),
                        "rainfall_mm": float(row["rainfall_mm"]) if row.get("rainfall_mm") else None,
                        "water_level_m": float(row["water_level_m"]) if row.get("water_level_m") else None,
                        "source": source,
                        "source_record_id": source_record_id,
                        "metadata": {"import_row": row_number},
                    }
                except (KeyError, ValueError, TypeError) as exc:
                    skipped += 1
                    self.stderr.write(f"row {row_number}: skipped: {exc}")
                    continue

                if options["dry_run"]:
                    created += 1
                    continue

                _, was_created = FloodEvent.objects.update_or_create(
                    source=source,
                    source_record_id=source_record_id,
                    defaults=event,
                )
                created += int(was_created)
                updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f"Import complete: created={created} updated={updated} skipped={skipped}"
        ))
