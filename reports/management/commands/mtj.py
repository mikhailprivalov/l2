import sys
from pprint import pprint

import jsonpickle
import simplejson
from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, router
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.migration import Migration
from django.db.migrations.questioner import (
    NonInteractiveMigrationQuestioner,
)
from django.db.migrations.state import ProjectState

from reports.management.mad import MigrationAutodetector
from reports.management.mw import MigrationWriter


class Command(BaseCommand):
    help = "Creates new migrations for export"

    def add_arguments(self, parser):
        parser.add_argument(
            'args', metavar='app_label', nargs='*',
            help='Specify the app label(s) to create migrations for.',
        )
        parser.add_argument(
            '--dry-run', action='store_true', dest='dry_run',
            help="Just show what migrations would be made; don't actually write them.",
        )
        parser.add_argument(
            '--empty', action='store_true', dest='empty',
            help="Create an empty migration.",
        )
        parser.add_argument(
            '--noinput', '--no-input', action='store_false', dest='interactive',
            help='Tells Django to NOT prompt the user for input of any kind.',
        )
        parser.add_argument(
            '-n', '--name', action='store', dest='name', default=None,
            help="Use this name for migration file(s).",
        )

    def handle(self, *app_labels, **options):
        self.verbosity = options['verbosity']
        self.interactive = options['interactive']
        self.dry_run = options['dry_run']
        self.empty = options['empty']
        self.migration_name = options['name']

        # Make sure the app they asked for exists
        app_labels = set(app_labels)
        bad_app_labels = set()
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError:
                bad_app_labels.add(app_label)
        if bad_app_labels:
            for app_label in bad_app_labels:
                self.stderr.write("App '%s' could not be found. Is it in INSTALLED_APPS?" % app_label)
            sys.exit(2)

        # Load the current graph state. Pass in None for the connection so
        # the loader doesn't try to resolve replaced migrations from DB.
        loader = MigrationLoader(None, ignore_no_migrations=True)

        # Raise an error if any migrations are applied before their dependencies.
        consistency_check_labels = {config.label for config in apps.get_app_configs()}
        # Non-default databases are only checked if database routers used.
        aliases_to_check = connections if settings.DATABASE_ROUTERS else [DEFAULT_DB_ALIAS]
        for alias in sorted(aliases_to_check):
            connection = connections[alias]
            if (connection.settings_dict['ENGINE'] != 'django.db.backends.dummy' and any(
                    # At least one model must be migrated to the database.
                    router.allow_migrate(connection.alias, app_label, model_name=model._meta.object_name)
                    for app_label in consistency_check_labels
                    for model in apps.get_app_config(app_label).get_models()
            )):
                loader.check_consistent_history(connection)

        questioner = NonInteractiveMigrationQuestioner(specified_apps=app_labels, dry_run=self.dry_run)
        ps = ProjectState.from_apps(apps)
        autodetector = MigrationAutodetector(
            ps,
            questioner,
        )

        # If they want to make an empty migration, make one for each app
        if self.empty:
            if not app_labels:
                raise CommandError("You must supply at least one app label when using --empty.")
            # Make a fake changes() result we can pass to arrange_for_graph
            changes = {
                app: [Migration("custom", app)]
                for app in app_labels
            }
            changes = autodetector.arrange_for_graph(
                changes=changes,
                graph=loader.graph,
                migration_name=self.migration_name,
            )
            self.write_migration_files(changes)
            return

        # Detect changes
        changes = autodetector.changes(
            graph=loader.graph,
            trim_to_apps=app_labels or None,
            convert_apps=app_labels or None,
            migration_name=self.migration_name,
        )

        self.write_migration_files(changes)

    def write_migration_files(self, changes):
        o = []
        for app_label, app_migrations in changes.items():
            for migration in app_migrations:
                mw = MigrationWriter(migration)
                ml = mw.as_list(app_label)
                o += ml
        self.stdout.write(jsonpickle.encode(o, unpicklable=False))
