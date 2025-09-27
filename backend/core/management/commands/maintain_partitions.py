"""
maintain_partitions module
"""

import json
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.database_partitioning import database_partitioner


class Command(BaseCommand):
    help = "Maintain database partitions by creating new ones and archiving old ones"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )
        parser.add_argument(
            "--table",
            type=str,
            help="Specific table to maintain",
        )
        parser.add_argument(
            "--months-ahead",
            type=int,
            default=3,
            help="Number of months ahead to create partitions for (default: 3)",
        )
        parser.add_argument(
            "--force-archive",
            action="store_true",
            help="Force archiving of partitions regardless of retention policy",
        )
        parser.add_argument(
            "--no-compress",
            action="store_true",
            help="Do not compress archived partitions",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed output",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        table_name = options["table"]
        months_ahead = options["months_head"]
        force_archive = options["force_archive"]
        no_compress = options["no_compress"]
        json_output = options["json"]
        verbose = options["verbose"]

        # Check if partitioning is supported
        if not database_partitioner.is_partitioning_supported():
            result = {
                "error": "Database partitioning is not supported",
                "message": "Partitioning requires PostgreSQL 10.0 or later",
            }

            if json_output:
                self.stdout.write(json.dumps(result, indent=2))
            else:
                self.stdout.write(self.style.ERROR(result["error"]))
                self.stdout.write(result["message"])

            return

        self.stdout.write(
            self.style.SUCCESS("Running database partition maintenance...")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("[DRY RUN MODE] - No changes will be made")
            )

        # Run maintenance tasks
        result = database_partitioner.maintain_partitions()

        # Create future partitions for specific table if specified
        if table_name:
            create_result = database_partitioner.create_time_partitions(
                table_name, months_ahead
            )
            result["future_partitions"] = create_result

        # Apply compression settings
        if no_compress:
            for config in database_partitioner.partition_configs.values():
                config.compression_enabled = False

        # Display results
        if json_output:
            self.stdout.write(json.dumps(result, indent=2))
        else:
            self._display_maintenance_results(result, verbose, dry_run)

        # Show next maintenance schedule
        self._show_next_maintenance_schedule()

    def _display_maintenance_results(self, result: dict, verbose: bool, dry_run: bool):
        """Display maintenance results in human-readable format."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PARTITION MAINTENANCE RESULTS")
        self.stdout.write("=" * 50)

        self.stdout.write(
            f'Maintenance Timestamp: {result.get("maintenance_timestamp", "N/A")}'
        )
        self.stdout.write(f'Tables Processed: {result.get("tables_processed", 0)}')
        self.stdout.write(f'Partitions Created: {result.get("partitions_created", 0)}')
        self.stdout.write(
            f'Partitions Archived: {result.get("partitions_archived", 0)}'
        )

        if result.get("errors"):
            self.stdout.write("\n" + self.style.ERROR("Errors encountered:"))
            for error in result["errors"]:
                self.stdout.write(self.style.ERROR(f"  ✗ {error}"))

        if verbose and result.get("tables_status"):
            self.stdout.write("\n" + "=" * 40)
            self.stdout.write("DETAILED TABLE STATUS")
            self.stdout.write("=" * 40)

            for table_name, table_result in result["tables_status"].items():
                self.stdout.write(f"\nTable: {table_name}")
                self.stdout.write(f'  Status: {table_result.get("status", "unknown")}')

                if table_result.get("partitions_created", 0) > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Created {table_result["partitions_created"]} new partitions'
                        )
                    )

                if table_result.get("partitions_archived", 0) > 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  Archived {table_result["partitions_archived"]} old partitions'
                        )
                    )

                # Show specific actions taken
                if table_result.get("actions"):
                    self.stdout.write("  Actions:")
                    for action in table_result["actions"]:
                        self.stdout.write(f"    • {action}")

        # Show future partitions if created
        if result.get("future_partitions"):
            future_result = result["future_partitions"]
            self.stdout.write("\n" + "=" * 40)
            self.stdout.write("FUTURE PARTITIONS CREATED")
            self.stdout.write("=" * 40)

            table_name = future_result.get("table_name", "Unknown")
            partitions_created = future_result.get("partitions_created", 0)
            partitions_list = future_result.get("partitions_created", [])

            self.stdout.write(f"Table: {table_name}")
            self.stdout.write(f"Future Partitions Created: {partitions_created}")

            if verbose and partitions_list:
                self.stdout.write("New Partitions:")
                for partition in partitions_list:
                    self.stdout.write(f"  • {partition}")

        # Show archive information
        if result.get("tables_status"):
            archived_info = self._collect_archived_info(result["tables_status"])
            if archived_info:
                self.stdout.write("\n" + "=" * 40)
                self.stdout.write("ARCHIVED PARTITIONS")
                self.stdout.write("=" * 40)

                for table_name, archived_partitions in archived_info.items():
                    self.stdout.write(f"{table_name}:")
                    for archive in archived_partitions:
                        self.stdout.write(f"  • {archive}")

        # Summary
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("MAINTENANCE SUMMARY")
        self.stdout.write("=" * 40)

        total_tables = result.get("tables_processed", 0)
        total_created = result.get("partitions_created", 0)
        total_archived = result.get("partitions_archived", 0)
        total_errors = len(result.get("errors", []))

        self.stdout.write(f"Total Tables Processed: {total_tables}")
        self.stdout.write(f"Total Partitions Created: {total_created}")
        self.stdout.write(f"Total Partitions Archived: {total_archived}")
        self.stdout.write(f"Total Errors: {total_errors}")

        if dry_run:
            self.stdout.write(
                "\n"
                + self.style.WARNING("[DRY RUN] No changes were made to the database.")
            )

        # Status indicators
        if total_errors == 0:
            self.stdout.write(
                self.style.SUCCESS("\n✓ Maintenance completed successfully")
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Maintenance completed with {total_errors} errors"
                )
            )

    def _collect_archived_info(self, tables_status: dict) -> dict:
        """Collect information about archived partitions."""
        archived_info = {}

        for table_name, table_result in tables_status.items():
            if table_result.get("archived_partitions"):
                archived_info[table_name] = table_result["archived_partitions"]

        return archived_info

    def _show_next_maintenance_schedule(self):
        """Show when the next maintenance should be run."""
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("NEXT MAINTENANCE SCHEDULE")
        self.stdout.write("=" * 40)

        # Calculate recommended next run time
        now = timezone.now()
        next_daily = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if next_daily <= now:
            next_daily += timedelta(days=1)

        next_weekly = now + timedelta(days=7)
        next_monthly = now + timedelta(days=30)

        self.stdout.write(
            f'Next Daily Maintenance: {next_daily.strftime("%Y-%m-%d %H:%M")}'
        )
        self.stdout.write(
            f'Next Weekly Maintenance: {next_weekly.strftime("%Y-%m-%d %H:%M")}'
        )
        self.stdout.write(
            f'Next Monthly Maintenance: {next_monthly.strftime("%Y-%m-%d %H:%M")}'
        )

        self.stdout.write("\nRecommended cron schedules:")
        self.stdout.write("• Daily: 0 2 * * * (2 AM every day)")
        self.stdout.write("• Weekly: 0 2 * * 0 (2 AM every Sunday)")
        self.stdout.write("• Monthly: 0 2 1 * * (2 AM on 1st of each month)")

        # Monitoring recommendations
        self.stdout.write("\nMonitoring Recommendations:")
        self.stdout.write("• Monitor partition sizes to identify growth patterns")
        self.stdout.write("• Set up alerts for partition creation failures")
        self.stdout.write("• Monitor archive storage usage")
        self.stdout.write("• Track query performance on partitioned tables")

        # Automation tips
        self.stdout.write("\nAutomation Tips:")
        self.stdout.write("• Set up cron job for daily maintenance")
        self.stdout.write("• Use database triggers for automatic partition creation")
        self.stdout.write("• Implement monitoring and alerting")
        self.stdout.write("• Test disaster recovery procedures regularly")
