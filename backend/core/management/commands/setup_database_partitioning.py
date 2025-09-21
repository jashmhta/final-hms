import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.conf import settings
from core.database_partitioning import database_partitioner, HealthcareDataCategory
from core.database_optimization import database_optimizer


class Command(BaseCommand):
    help = 'Setup database partitioning for healthcare datasets'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )
        parser.add_argument(
            '--table',
            type=str,
            help='Specific table to partition (default: all configured tables)',
        )
        parser.add_argument(
            '--category',
            type=str,
            choices=[cat.value for cat in HealthcareDataCategory],
            help='Partition only tables in this category',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force partitioning even if table already exists',
        )
        parser.add_argument(
            '--migrate-data',
            action='store_true',
            help='Migrate existing data to partitioned tables',
        )
        parser.add_argument(
            '--maintenance-only',
            action='store_true',
            help='Only run maintenance tasks, do not create new partitions',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        table_name = options['table']
        category = options['category']
        force = options['force']
        migrate_data = options['migrate_data']
        maintenance_only = options['maintenance_only']

        # Check if partitioning is supported
        if not database_partitioner.is_partitioning_supported():
            self.stdout.write(
                self.style.ERROR('Database partitioning is not supported.')
            )
            self.stdout.write(
                'Partitioning requires PostgreSQL 10.0 or later.'
            )
            return

        self.stdout.write(
            self.style.SUCCESS('Setting up database partitioning for healthcare datasets...')
        )

        if maintenance_only:
            self._run_maintenance_tasks(dry_run)
            return

        # Get tables to partition
        tables_to_partition = self._get_tables_to_partition(table_name, category)

        if not tables_to_partition:
            self.stdout.write(
                self.style.WARNING('No tables found to partition.')
            )
            return

        # Show partitioning recommendations
        self._show_recommendations()

        # Create partitioned tables
        results = {}
        for table_name in tables_to_partition:
            if table_name in database_partitioner.partition_configs:
                config = database_partitioner.partition_configs[table_name]

                if migrate_data:
                    result = database_partitioner.migrate_to_partitioned_table(table_name, config)
                else:
                    result = database_partitioner.create_partitioned_table(config)

                results[table_name] = result

                self._display_table_result(table_name, result, dry_run)

        # Setup maintenance job
        if not dry_run:
            job_result = database_partitioner.setup_partition_maintenance_job()
            self._display_job_result(job_result, dry_run)

        # Display final summary
        self._display_summary(results, dry_run)

    def _get_tables_to_partition(self, table_name: str, category: str) -> List[str]:
        """Get list of tables to partition based on filters."""
        tables = []

        if table_name:
            if table_name in database_partitioner.partition_configs:
                tables.append(table_name)
            else:
                self.stdout.write(
                    self.style.WARNING(f'Table {table_name} not found in partitioning configuration.')
                )
        elif category:
            for table_name, config in database_partitioner.partition_configs.items():
                if config.category.value == category:
                    tables.append(table_name)
        else:
            tables = list(database_partitioner.partition_configs.keys())

        return tables

    def _show_recommendations(self):
        """Display partitioning recommendations."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('PARTITIONING RECOMMENDATIONS')
        self.stdout.write('='*50)

        recommendations = database_partitioner.get_partition_recommendations()

        if not recommendations:
            self.stdout.write('No specific partitioning recommendations found.')
            return

        for i, rec in enumerate(recommendations, 1):
            self.stdout.write(f'\n{i}. Table: {rec["table"]}')
            self.stdout.write(f'   Recommendation: {rec["recommendation"]}')
            self.stdout.write(f'   Strategy: {rec["strategy"]}')
            self.stdout.write(f'   Reason: {rec["reason"]}')
            self.stdout.write(f'   Priority: {rec["priority"]}')
            self.stdout.write(f'   Estimated Benefit: {rec["estimated_benefit"]}')

    def _display_table_result(self, table_name: str, result: Dict[str, Any], dry_run: bool):
        """Display results for a specific table."""
        self.stdout.write(f'\n--- Table: {table_name} ---')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN]'))
            return

        if result.get('errors'):
            for error in result['errors']:
                self.stdout.write(self.style.ERROR(f'  Error: {error}'))
            return

        if result.get('migration_completed'):
            self.stdout.write(
                self.style.SUCCESS(f'  Migration completed successfully')
            )
            self.stdout.write(f'  Rows migrated: {result.get("rows_migrated", 0):,}')
            self.stdout.write(f'  Duration: {result.get("duration_seconds", 0):.2f} seconds')
        elif result.get('created'):
            self.stdout.write(
                self.style.SUCCESS(f'  Partitioned table created successfully')
            )
            self.stdout.write(f'  Partitions created: {result.get("partitions_created", 0)}')

        if result.get('warnings'):
            for warning in result['warnings']:
                self.stdout.write(self.style.WARNING(f'  Warning: {warning}'))

    def _display_job_result(self, result: Dict[str, Any], dry_run: bool):
        """Display maintenance job setup result."""
        self.stdout.write('\n--- Maintenance Job Setup ---')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would setup maintenance job'))
            return

        if result.get('job_created'):
            self.stdout.write(
                self.style.SUCCESS(f'  Maintenance job scheduled: {result["job_name"]}')
            )
            self.stdout.write(f'  Schedule: {result["schedule"]}')
        else:
            self.stdout.write(
                self.style.ERROR('  Failed to setup maintenance job')
            )
            for error in result.get('errors', []):
                self.stdout.write(self.style.ERROR(f'    {error}'))

    def _display_summary(self, results: Dict[str, Any], dry_run: bool):
        """Display summary of partitioning setup."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('PARTITIONING SETUP SUMMARY')
        self.stdout.write('='*50)

        total_tables = len(results)
        successful_tables = sum(1 for r in results.values() if not r.get('errors'))
        migrated_tables = sum(1 for r in results.values() if r.get('migration_completed'))
        total_rows_migrated = sum(r.get('rows_migrated', 0) for r in results.values())

        self.stdout.write(f'Total tables processed: {total_tables}')
        self.stdout.write(f'Successfully partitioned: {successful_tables}')
        self.stdout.write(f'Data migrations completed: {migrated_tables}')
        self.stdout.write(f'Total rows migrated: {total_rows_migrated:,}')

        if dry_run:
            self.stdout.write('\n' + self.style.WARNING('[DRY RUN] No changes were made to the database.'))

        # Show next steps
        self.stdout.write('\nNext Steps:')
        self.stdout.write('1. Monitor partition performance with: python manage.py partition_stats')
        self.stdout.write('2. Run maintenance tasks with: python manage.py maintain_partitions')
        self.stdout.write('3. Update application queries to use partitioned tables')
        self.stdout.write('4. Set up monitoring and alerts for partition performance')

    def _run_maintenance_tasks(self, dry_run: bool):
        """Run partition maintenance tasks."""
        self.stdout.write('Running partition maintenance tasks...')

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] Would run maintenance tasks'))
            return

        result = database_partitioner.maintain_partitions()

        self.stdout.write('\n--- Maintenance Results ---')
        self.stdout.write(f'Tables processed: {result.get("tables_processed", 0)}')
        self.stdout.write(f'Partitions created: {result.get("partitions_created", 0)}')
        self.stdout.write(f'Partitions archived: {result.get("partitions_archived", 0)}')

        if result.get('errors'):
            self.stdout.write('\nErrors encountered:')
            for error in result['errors']:
                self.stdout.write(self.style.ERROR(f'  {error}'))

        # Show detailed status for each table
        self.stdout.write('\n--- Table Status ---')
        for table_name, table_result in result.get('tables_status', {}).items():
            status = table_result.get('status', 'unknown')
            partitions_created = table_result.get('partitions_created', 0)
            partitions_archived = table_result.get('partitions_archived', 0)

            self.stdout.write(f'{table_name}: {status}')
            if partitions_created > 0:
                self.stdout.write(f'  Created {partitions_created} new partitions')
            if partitions_archived > 0:
                self.stdout.write(f'  Archived {partitions_archived} old partitions')