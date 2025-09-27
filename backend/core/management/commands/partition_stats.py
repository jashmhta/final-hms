"""
partition_stats module
"""

import json

from django.core.management.base import BaseCommand
from django.db import connections

from core.database_optimization import database_optimizer
from core.database_partitioning import database_partitioner


class Command(BaseCommand):
    help = "Display database partitioning statistics and health information"

    def add_arguments(self, parser):
        parser.add_argument(
            "--table",
            type=str,
            help="Specific table to show stats for",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results in JSON format",
        )
        parser.add_argument(
            "--detailed",
            action="store_true",
            help="Show detailed partition information",
        )
        parser.add_argument(
            "--health-check",
            action="store_true",
            help="Run health check on partitions",
        )
        parser.add_argument(
            "--recommendations",
            action="store_true",
            help="Show optimization recommendations",
        )

    def handle(self, *args, **options):
        table_name = options["table"]
        json_output = options["json"]
        detailed = options["detailed"]
        health_check = options["health_check"]
        recommendations = options["recommendations"]

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

        # Get partition statistics
        stats = database_partitioner.get_partition_stats(table_name)

        if recommendations:
            # Get optimization recommendations
            recs = database_partitioner.get_partition_recommendations()
            stats["recommendations"] = recs

        if health_check:
            # Run health check
            health_result = self._run_health_check()
            stats["health_check"] = health_result

        if json_output:
            self.stdout.write(json.dumps(stats, indent=2))
        else:
            self._display_stats(stats, detailed, health_check, recommendations)

    def _run_health_check(self):
        """Run health check on database partitions."""
        health = {
            "overall_status": "healthy",
            "issues": [],
            "warnings": [],
            "partitions_checked": 0,
            "unhealthy_partitions": [],
        }

        try:
            with database_optimizer.get_database_connection() as connection:
                with connection.cursor() as cursor:
                    # Check for partition-specific issues
                    cursor.execute(
                        """
                        SELECT
                            schemaname,
                            tablename,
                            partstrat,
                            partattrs,
                            partcount
                        FROM pg_partitions
                        WHERE schemaname = 'public'
                    """
                    )

                    partitions_info = cursor.fetchall()
                    health["partitions_checked"] = len(partitions_info)

                    # Check for empty partitions
                    cursor.execute(
                        """
                        SELECT
                            schemaname,
                            tablename,
                            pg_total_relation_size(schemaname||'.'||tablename) as size
                        FROM pg_tables
                        WHERE tablename LIKE '%_partitioned_%'
                        AND pg_total_relation_size(schemaname||'.'||tablename) = 0
                    """
                    )

                    empty_partitions = cursor.fetchall()
                    if empty_partitions:
                        health["warnings"].append(
                            f"Found {len(empty_partitions)} empty partitions"
                        )
                        for partition in empty_partitions:
                            health["warnings"].append(
                                f"  Empty partition: {partition[1]}"
                            )

                    # Check for oversized partitions (>1GB)
                    cursor.execute(
                        """
                        SELECT
                            schemaname,
                            tablename,
                            pg_total_relation_size(schemaname||'.'||tablename) as size
                        FROM pg_tables
                        WHERE tablename LIKE '%_partitioned_%'
                        AND pg_total_relation_size(schemaname||'.'||tablename) > 1073741824
                    """
                    )

                    oversized_partitions = cursor.fetchall()
                    if oversized_partitions:
                        health["warnings"].append(
                            f"Found {len(oversized_partitions)} oversized partitions (>1GB)"
                        )
                        for partition in oversized_partitions:
                            size_gb = partition[2] / (1024 * 1024 * 1024)
                            health["warnings"].append(
                                f"  Oversized partition: {partition[1]} ({size_gb:.1f} GB)"
                            )

                    # Check for partition count issues
                    for partition_info in partitions_info:
                        table_name = partition_info[1]
                        partition_count = partition_info[4]

                        if partition_count > 100:
                            health["warnings"].append(
                                f"Table {table_name} has {partition_count} partitions (consider archiving)"
                            )

        except Exception as e:
            health["overall_status"] = "error"
            health["issues"].append(f"Error running health check: {str(e)}")

        return health

    def _display_stats(
        self, stats: dict, detailed: bool, health_check: bool, recommendations: bool
    ):
        """Display partition statistics in human-readable format."""
        self.stdout.write("=" * 60)
        self.stdout.write("DATABASE PARTITIONING STATISTICS")
        self.stdout.write("=" * 60)

        if not stats.get("partitioning_enabled", False):
            self.stdout.write(
                self.style.ERROR("Partitioning is not enabled or supported")
            )
            return

        # General information
        self.stdout.write(f'Timestamp: {stats.get("timestamp", "N/A")}')
        self.stdout.write(
            f'Partitioning Enabled: {stats.get("partitioning_enabled", False)}'
        )
        self.stdout.write(f'Total Partitioned Tables: {len(stats.get("tables", {}))}')

        # Table-specific statistics
        if stats.get("tables"):
            self.stdout.write("\n" + "=" * 40)
            self.stdout.write("TABLE PARTITIONING DETAILS")
            self.stdout.write("=" * 40)

            for table_name, table_stats in stats["tables"].items():
                self.stdout.write(f"\nTable: {table_name}")

                if table_stats.get("error"):
                    self.stdout.write(
                        self.style.ERROR(f'  Error: {table_stats["error"]}')
                    )
                    continue

                # Basic statistics
                partition_count = table_stats.get("partition_count", 0)
                total_rows = table_stats.get("total_rows", 0)
                total_size_mb = table_stats.get("total_size_mb", 0)

                self.stdout.write(
                    f'  Partition Strategy: {table_stats.get("partition_strategy", "N/A")}'
                )
                self.stdout.write(
                    f'  Partition Attributes: {table_stats.get("partition_attributes", "N/A")}'
                )
                self.stdout.write(f"  Partition Count: {partition_count}")
                self.stdout.write(f"  Total Rows: {total_rows:,}")
                self.stdout.write(f"  Total Size: {total_size_mb:.1f} MB")

                # Partition distribution
                if total_rows > 0 and partition_count > 0:
                    avg_rows_per_partition = total_rows / partition_count
                    avg_size_per_partition = total_size_mb / partition_count
                    self.stdout.write(
                        f"  Avg Rows/Partition: {avg_rows_per_partition:,.0f}"
                    )
                    self.stdout.write(
                        f"  Avg Size/Partition: {avg_size_per_partition:.1f} MB"
                    )

                # Detailed partition information
                if detailed and table_stats.get("partitions"):
                    self.stdout.write(f"\n  Partitions:")
                    for partition in table_stats["partitions"]:
                        partition_name = partition.get("partition_name", "N/A")
                        row_count = partition.get("row_count", 0)
                        size_mb = partition.get("size_mb", 0)

                        self.stdout.write(
                            f"    {partition_name}: {row_count:,} rows, {size_mb:.1f} MB"
                        )

        # Health check results
        if health_check and stats.get("health_check"):
            health = stats["health_check"]
            self.stdout.write("\n" + "=" * 40)
            self.stdout.write("PARTITION HEALTH CHECK")
            self.stdout.write("=" * 40)

            self.stdout.write(f'Overall Status: {health["overall_status"]}')
            self.stdout.write(f'Partitions Checked: {health["partitions_checked"]}')

            if health.get("issues"):
                self.stdout.write("\nIssues:")
                for issue in health["issues"]:
                    self.stdout.write(self.style.ERROR(f"  ✗ {issue}"))

            if health.get("warnings"):
                self.stdout.write("\nWarnings:")
                for warning in health["warnings"]:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))

            if not health.get("issues") and not health.get("warnings"):
                self.stdout.write(self.style.SUCCESS("✓ All partitions are healthy"))

        # Optimization recommendations
        if recommendations and stats.get("recommendations"):
            recs = stats["recommendations"]
            self.stdout.write("\n" + "=" * 40)
            self.stdout.write("OPTIMIZATION RECOMMENDATIONS")
            self.stdout.write("=" * 40)

            if not recs:
                self.stdout.write("No specific recommendations at this time.")
            else:
                for i, rec in enumerate(recs, 1):
                    priority_color = (
                        self.style.ERROR
                        if rec["priority"] == "high"
                        else self.style.WARNING
                    )
                    self.stdout.write(f'\n{i}. {rec["table"]}')
                    self.stdout.write(f'   Priority: {priority_color(rec["priority"])}')
                    self.stdout.write(f'   Recommendation: {rec["recommendation"]}')
                    self.stdout.write(f'   Strategy: {rec["strategy"]}')
                    self.stdout.write(f'   Reason: {rec["reason"]}')
                    self.stdout.write(f'   Benefit: {rec["estimated_benefit"]}')

        # Performance tips
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("PERFORMANCE TIPS")
        self.stdout.write("=" * 40)

        self.stdout.write("• Monitor partition sizes and redistribute data if needed")
        self.stdout.write("• Regularly archive old partitions to maintain performance")
        self.stdout.write("• Use partition pruning in queries for better performance")
        self.stdout.write("• Consider compressing archived partitions to save space")
        self.stdout.write("• Set up automated maintenance to create future partitions")
        self.stdout.write(
            "• Monitor query performance to identify partition access patterns"
        )

        # Next steps
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("NEXT COMMANDS")
        self.stdout.write("=" * 40)

        self.stdout.write(
            "• Setup partitioning: python manage.py setup_database_partitioning"
        )
        self.stdout.write("• Run maintenance: python manage.py maintain_partitions")
        self.stdout.write(
            "• Create maintenance job: python manage.py setup_database_partitioning --maintenance-only"
        )
        self.stdout.write(
            "• Migrate data: python manage.py setup_database_partitioning --migrate-data"
        )
