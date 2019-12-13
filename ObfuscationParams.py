import configparser
import os
from typing import List


class ObfuscationParams:

    def __init__(self, ini_path: str = 'obfuscation_params.ini'):

        config = configparser.ConfigParser()
        config.read(ini_path)

        # Настройка обфускации
        self.change_variables: bool = get_bool_setting(ini_path, 'General', 'change_variables')
        self.change_functions: bool = get_bool_setting(ini_path, 'General', 'change_functions')
        self.change_arguments: bool = get_bool_setting(ini_path, 'General', 'change_arguments')

        self.change_classes: bool = get_bool_setting(ini_path, 'Classes', 'change_classes')
        self.change_fields: bool = get_bool_setting(ini_path, 'Classes', 'change_fields')
        self.change_methods: bool = get_bool_setting(ini_path, 'Classes', 'change_methods')
        self.change_method_arguments: bool = get_bool_setting(ini_path, 'Classes', 'change_method_arguments')

        # Настройка удалений
        self.delete_docstrings: bool = get_bool_setting(ini_path, 'Deletes', 'delete_docstrings')
        self.delete_comments: bool = get_bool_setting(ini_path, 'Deletes', 'delete_comments')
        self.delete_annotations: bool = get_bool_setting(ini_path, 'Deletes', 'delete_annotations')

        # Настройка исключений
        self.forbidden_names: List[str] = get_list_setting(ini_path, 'Forbidden', 'names')
        self.forbidden_starts: List[str] = get_list_setting(ini_path, 'Forbidden', 'starts')
        self.forbidden_ends: List[str] = get_list_setting(ini_path, 'Forbidden', 'ends')
        self.forbidden_entries: List[str] = get_list_setting(ini_path, 'Forbidden', 'entries')

        self.prefix = "OBF_"
        self.py = ".py"

    def is_forbidden_name(self, name: str) -> bool:

        if self.forbidden_names:
            for bad_name in self.forbidden_names:
                if name == bad_name:
                    return True

        if self.forbidden_starts:
            for bad_start in self.forbidden_starts:
                if name.startswith(bad_start):
                    return True

        if self.forbidden_ends:
            for bad_end in self.forbidden_ends:
                if name.endswith(bad_end):
                    return True

        if self.forbidden_entries:
            for bad_entry in self.forbidden_entries:
                if bad_entry in name:
                    return True

        return False


def create_config(path: str) -> None:
    config = configparser.ConfigParser()
    config.add_section("General")
    config.set("General", "change_variables", "1")
    config.set("General", "change_functions", "0")
    config.set("General", "change_arguments", "1")

    config.add_section("Classes")
    config.set("Classes", "change_classes", "0")
    config.set("Classes", "change_fields", "0")
    config.set("Classes", "change_methods", "0")
    config.set("Classes", "change_method_arguments", "1")

    config.add_section("Deletes")
    config.set("Deletes", "delete_docstrings", "0")
    config.set("Deletes", "delete_comments", "1")
    config.set("Deletes", "delete_annotations", "1")

    config.add_section("Forbidden")
    config.set("Forbidden", "names", "self")
    config.set("Forbidden", "starts", "")
    config.set("Forbidden", "ends", "")
    config.set("Forbidden", "entries", "")

    with open(path, "w") as config_file:
        config.write(config_file)


def get_config(path: str) -> configparser.ConfigParser:
    if not os.path.exists(path):
        create_config(path)

    config = configparser.ConfigParser()
    config.read(path)
    return config


def get_setting(path: str, section: str, setting: str) -> str:
    config = get_config(path)
    value = config.get(section, setting)

    return value


def get_bool_setting(path: str, section: str, setting: str) -> bool:
    return bool(int(get_setting(path, section, setting)))


def get_list_setting(path: str, section: str, setting: str) -> List[str]:
    return [el for el in get_setting(path, section, setting).split(',') if el]
