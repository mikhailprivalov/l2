import os
from importlib import import_module
from pprint import pprint

from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.serializer import serializer_factory
from django.db.models import ForeignKey, ManyToManyField
from django.utils.inspect import get_func_args
from django.utils.module_loading import module_dir


class SettingsReference(str):
    """
    Special subclass of string which actually references a current settings
    value. It's treated as the value in memory, but serializes out to a
    settings.NAME attribute reference.
    """

    def __new__(self, value, setting_name):
        return str.__new__(self, value)

    def __init__(self, value, setting_name):
        self.setting_name = setting_name


def fullname(o):
  return o.__module__ + "." + o.__class__.__name__


class OperationWriter:
    def __init__(self, operation, indentation=2):
        self.operation = operation
        self.buff = []
        self.indentation = indentation
        self.data = []

    def serialize(self, app):
        d = {}

        def _write(_arg_name, _arg_value):
            if (_arg_name in self.operation.serialization_expand_args and
                    isinstance(_arg_value, (list, tuple, dict))):
                if isinstance(_arg_value, dict):
                    ds = {}
                    for a, b in _arg_value.items():
                        if any([isinstance(b, str), isinstance(b, list), isinstance(b, dict), isinstance(b, bool), isinstance(b, float), isinstance(b, int)]) or b == None:
                            ds[a] = b
                        else:
                            ds[a] = str(b)
                    d[_arg_name] = ds
                else:
                    f = []
                    for item in _arg_value:
                        if isinstance(item, tuple):
                            if len(item) == 2:
                                props = {}
                                i = item[1].__dict__
                                props["type_name"] = fullname(item[1])
                                props["choices"] = i.get("choices", None)
                                props["blank"] = i.get("blank", True)
                                props["is_null"] = i.get("null", True)
                                props["primary_key"] = i.get("primary_key", False)
                                props["help_text"] = i.get("help_text", '')
                                props["max_length"] = i.get("max_length", None)
                                props["verbose_name"] = i.get("verbose_name", None)
                                if "default" in i:
                                    props["default"] = str(i["default"]) if type(i["default"]) not in [set, list, dict,
                                                                                                       int, float, bool, type(None)] else \
                                    i["default"]
                                else:
                                    props["default"] = None

                                f.append({'name': str(item[0]), 'props': props})
                            else:
                                f.append(list(item))
                        elif any([isinstance(item, str), isinstance(item, list),
                                  isinstance(item, dict), isinstance(item, bool),
                                  isinstance(item, float),
                                  isinstance(item, int)]) or item == None:
                            f.append(item)
                        else:
                            f.append(str(item))
                    d[_arg_name] = f
            elif isinstance(_arg_value, ForeignKey):
                ab = {
                    "many_to_many": bool(_arg_value.many_to_many),
                    "many_to_one": bool(_arg_value.many_to_one),
                    "one_to_many": bool(_arg_value.one_to_many),
                    "one_to_one": bool(_arg_value.one_to_one),
                    "field_str": str(_arg_value),
                    "to": str(_arg_value.remote_field.model).replace("__fake__.", "").replace("<class", "").replace("'", "").replace(">", "").replace(" ", ""),
                }
                d[_arg_name] = ab
                d["related"] = True
            elif isinstance(_arg_value, ManyToManyField):
                ab = {
                    "many_to_many": bool(_arg_value.many_to_many),
                    "many_to_one": bool(_arg_value.many_to_one),
                    "one_to_many": bool(_arg_value.one_to_many),
                    "one_to_one": bool(_arg_value.one_to_one),
                    "field_str": str(_arg_value),
                    "to": str(_arg_value.remote_field.model).replace("__fake__.", "").replace("<class", "").replace("'", "").replace(">", "").replace(" ", ""),
                }
                d[_arg_name] = ab
                d["related"] = True
            elif any([isinstance(_arg_value, str), isinstance(_arg_value, list), isinstance(_arg_value, dict), isinstance(_arg_value, bool), isinstance(_arg_value, float), isinstance(_arg_value, int)]) or _arg_value == None:
                d[_arg_name] = _arg_value
            else:
                d[_arg_name] = str(_arg_value)
        name, args, kwargs = self.operation.deconstruct()
        operation_args = get_func_args(self.operation.__init__)

        for i, arg in enumerate(args):
            arg_value = arg
            arg_name = operation_args[i]
            _write(arg_name, arg_value)

        i = len(args)
        for arg_name in operation_args[i:]:
            if arg_name in kwargs:
                arg_value = kwargs[arg_name]
                _write(arg_name, arg_value)
        if "name" in d:
            d["name"] = app + "." + d["name"]
        return d


class MigrationWriter:
    """
    Take a Migration instance and is able to produce the contents
    of the migration file from it.
    """

    def __init__(self, migration):
        self.migration = migration

    def as_list(self, app):
        operations = []
        for operation in self.migration.operations:
            operations.append(OperationWriter(operation).serialize(app))

        return operations

    @property
    def basedir(self):
        migrations_package_name, _ = MigrationLoader.migrations_module(self.migration.app_label)

        if migrations_package_name is None:
            raise ValueError(
                "Django can't create migrations for app '%s' because "
                "migrations have been disabled via the MIGRATION_MODULES "
                "setting." % self.migration.app_label
            )

        # See if we can import the migrations module directly
        try:
            migrations_module = import_module(migrations_package_name)
        except ImportError:
            pass
        else:
            try:
                return module_dir(migrations_module)
            except ValueError:
                pass

        # Alright, see if it's a direct submodule of the app
        app_config = apps.get_app_config(self.migration.app_label)
        maybe_app_name, _, migrations_package_basename = migrations_package_name.rpartition(".")
        if app_config.name == maybe_app_name:
            return os.path.join(app_config.path, migrations_package_basename)

        # In case of using MIGRATION_MODULES setting and the custom package
        # doesn't exist, create one, starting from an existing package
        existing_dirs, missing_dirs = migrations_package_name.split("."), []
        while existing_dirs:
            missing_dirs.insert(0, existing_dirs.pop(-1))
            try:
                base_module = import_module(".".join(existing_dirs))
            except ImportError:
                continue
            else:
                try:
                    base_dir = module_dir(base_module)
                except ValueError:
                    continue
                else:
                    break
        else:
            raise ValueError(
                "Could not locate an appropriate location to create "
                "migrations package %s. Make sure the toplevel "
                "package exists and can be imported." %
                migrations_package_name)

        final_dir = os.path.join(base_dir, *missing_dirs)
        if not os.path.isdir(final_dir):
            os.makedirs(final_dir)
        for missing_dir in missing_dirs:
            base_dir = os.path.join(base_dir, missing_dir)
            with open(os.path.join(base_dir, "__init__.py"), "w"):
                pass

        return final_dir

    @property
    def filename(self):
        return "%s.py" % self.migration.name

    @property
    def path(self):
        return os.path.join(self.basedir, self.filename)

    @classmethod
    def serialize(cls, value):
        return serializer_factory(value).serialize()
