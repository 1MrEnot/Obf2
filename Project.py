import copy
import os
import shutil
from typing import List, Dict
from time import sleep

from Module import Module
from NameGenerator import NameGenerator
from ObfuscationParams import ObfuscationParams
from UtilFuncs import delete_duplicates


class Project:

    def __init__(self, oldFolder: str):

        # Установка параметров обфускации
        self.params: ObfuscationParams = ObfuscationParams()

        # Старая и новые папки проекта
        self.oldFolder: str = oldFolder
        path, filename = list(os.path.split(oldFolder))
        self.newFolder: str = os.path.join(path, self.prefix + filename)

        # Сохранение в self.files путей к файлам, которые надо обфусцировать
        # Остальные копируются в новую папку проекта
        self.files: List[str] = self.find_and_copy_files()
        self.module_queue: List[Module] = [Module(file) for file in self.files]

        # Создание словаря обфусцированных имён
        self.name_generator: NameGenerator = NameGenerator()

        # Инициализация графа замисимостей импортов. Ключ - модуль, значение - список импортированных модулей
        self.dependency_graph: Dict[Module, List[Module]] = dict()

    def collect_data(self):
        for mod in self.module_queue:
            mod.collect_data()


    def init_dependency_graph(self):
        for mod in self.module_queue:
            positions = self.get_positions_of_imported_modules(mod)
            connections = delete_duplicates([self.module_queue[num] for num in positions])
            self.dependency_graph[mod] = connections

    def find_and_copy_files(self) -> List[str]:
        fond_files = []

        for root, dirs, files in os.walk(self.oldFolder):
            new_root = root.replace(self.oldFolder, self.newFolder)

            # if not os.path.exists(new_root):
            #     os.mkdir(new_root)

            try:
                os.mkdir(new_root)
            except FileExistsError:
                pass

            for name in files:
                filePath = os.path.join(root, name).replace(r'\\', r'/')
                if filePath.endswith(self.ext):
                    fond_files.append(filePath)
                else:
                    new_file_path = filePath.replace(root, new_root)
                    shutil.copy(filePath, new_file_path)

        return fond_files

    def reshuffle_module_queue(self):
        current_graph = copy.deepcopy(self.dependency_graph)
        last_step_graph = current_graph.copy()
        res = []

        while last_step_graph:
            for edge in current_graph:
                if last_step_graph[edge]:
                    continue
                res.append(edge)
                last_step_graph = delete_edge(last_step_graph, edge)

            current_graph = last_step_graph.copy()

        self.module_queue = res


    def get_module_by_path(self, module_path: str) -> Module:

        for el in self.module_queue:
            if os.path.join(el.old_path, el.old_name) == module_path:
                return el


    def get_module_by_import_in_module(self, module_sequence: str, module: Module):

        current_path = module.old_path
        pieces = module_sequence.split('.')
        last_acceptable_file: str = ''

        while pieces:
            potential_folder = os.path.join(current_path, pieces.pop(0))
            potential_file = potential_folder + self.ext
            fond_fold = False
            fond_file = False

            if os.path.exists(potential_folder):
                current_path = potential_folder
                fond_fold = True

            if os.path.exists(potential_file):
                last_acceptable_file = potential_file
                fond_file = True

            if not (fond_file or fond_fold) and last_acceptable_file:
                break

        actual_file = self.get_module_by_path(last_acceptable_file)
        return actual_file


    def get_positions_of_imported_modules(self, module: Module) -> List[int]:

        res = []

        for imp in module.visitor.info.imported:
            imported_module = self.get_module_by_import_in_module(imp.name, module)
            if imported_module is not None:
                res.append(self.module_queue.index(imported_module))

        return res


    def save_actual_modules_for_import_paths(self, module: Module):

        for imp in module.visitor.info.imported:
            imported_module = self.get_module_by_import_in_module(imp.name, module)
            imp.module_link = imported_module


    def module_data_exchange(self):

        for module in self.module_queue:
            self.save_actual_modules_for_import_paths(module)
            module.add_data_from_imported_modules()


    def obfuscate(self):
        count = 1
        amount = len(self.module_queue)

        for module in self.module_queue:

            new_folder = module.old_path.replace(self.oldFolder, self.newFolder)
            module.new_path = os.path.join(new_folder, module.old_name)

            module.name_generator = self.name_generator

            module.obfuscate()
            module.save()
            count += 1

            self.name_generator = module.name_generator

            debug = False
            if debug:
                print(f"{module.old_name}: \n"
                      f"\t{module.visitor.info.variables}\n"
                      f"\t{module.visitor.info.function_names}\n"
                      f"\t{module.visitor.info.class_names}\n")


    def simple_obfuscation(self):
        self.collect_data()
        self.init_dependency_graph()
        self.reshuffle_module_queue()
        self.module_data_exchange()
        self.obfuscate()


    @property
    def prefix(self):
        return self.params.prefix


    @property
    def ext(self):
        return self.params.py


def graph_repr(graph: Dict[Module, List[Module]]):
    named_graph = dict()
    for key, val in graph.items():
        named_graph[key.old_name] = [el.old_name for el in val]
    return named_graph



def delete_edge(graph: Dict[Module, List[Module]], bad_edge: Module):
    graph_copy = graph.copy()

    for edge in graph.keys():

        if bad_edge in graph_copy[edge]:
            graph_copy[edge].remove(bad_edge)

        if edge == bad_edge:
            del graph_copy[edge]

    return graph_copy
