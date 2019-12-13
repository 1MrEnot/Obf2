import os

import libcst as cst

import Transformers as Tp
from Infos import ClassInfo, ModuleInfo
from NameGenerator import NameGenerator
from ObfuscationParams import ObfuscationParams
from Transformers import MyTransformer
from Visitors import MyVisitor


class Module:

    def __init__(self, path, new_name=None, obf_params=None, visitor=None):

        # Запись пути, старого и нового имени модуля
        self.old_path: str
        self.old_name: str
        self.old_path, self.old_name = os.path.split(path)
        # print(f"Opened {self.old_path}\\{self.old_name}")

        if obf_params is None:
            obf_params = Tp.ObfuscationParams()
        self.params: ObfuscationParams = obf_params

        # Создание нового пути и имени файла
        new_name = self.old_name if new_name is None else new_name
        self.new_name: str = f"{self.prefix}{new_name}"
        self.new_path: str = os.path.join(self.old_path, self.new_name)

        if visitor is None:
            visitor = MyVisitor()

        # Инициализация визитора        (сохраняет информацию о модуле)
        #               трансформера    (переименовывает)
        self.visitor: MyVisitor = visitor
        self.transformer: MyTransformer = MyTransformer(params=self.params)

        # Инициализация дерева модуля
        self.tree = cst.parse_module(open(path, 'r', encoding="utf-8").read())
        self.obfuscated_tree: cst.Module = self.tree

        # Создание словаря обфусцированных имён
        self.name_generator: NameGenerator = NameGenerator()


    @property
    def prefix(self):
        return self.params.prefix

    @property
    def change_classes(self):
        return self.params.change_classes

    @property
    def change_methods(self):
        return self.params.change_methods

    @property
    def change_method_arguments(self):
        return self.params.change_method_arguments

    @property
    def change_fields(self):
        return self.params.change_fields


    @property
    def change_functions(self):
        return self.params.change_functions

    @property
    def change_arguments(self):
        return self.params.change_arguments

    @property
    def change_variables(self):
        return self.params.change_variables


    @property
    def delete_docstrings(self):
        return self.params.delete_docstrings

    @property
    def delete_comments(self):
        return self.params.delete_comments

    @property
    def delete_annotations(self):
        return self.params.delete_annotations

    def add_data_from_imported_modules(self):

        for imp in self.visitor.info.imported:

            if not imp.module_link:
                continue


            importing_module_info = imp.module_link.visitor.info
            names_dict = imp.import_as_names

            if not names_dict:
                module_info: ModuleInfo = imp.module_link.visitor.info
                new_class = ClassInfo()
                new_class.name = imp.name
                new_class.functions = module_info.functions
                new_class.variables = module_info.variables
                self.visitor.info.classes.append(new_class)
                continue


            for name in names_dict:

                if name == '*':
                    self.visitor.info.variables.extend(importing_module_info.variables)
                    self.visitor.info.functions.extend(importing_module_info.functions)
                    self.visitor.info.classes.extend(importing_module_info.classes)
                    continue

                if name in importing_module_info.variables:
                    self.visitor.info.variables.append(names_dict[name])
                if name in importing_module_info.function_names:
                    func = importing_module_info.get_function_by_name(name)
                    func.name = names_dict[name]
                    self.visitor.info.functions.append(func)
                if name in importing_module_info.class_names:
                    cls = importing_module_info.get_class_by_name(name)
                    cls.name = names_dict[name]
                    self.visitor.info.classes.append(cls)

        self.visitor.clear_dublicates()

    def collect_data(self):
        self.obfuscated_tree.visit(self.visitor)
        self.visitor.clear_dublicates()
        self.transformer.module_info = self.visitor.info

    def obfuscate(self):
        self.transformer.name_generator = self.name_generator
        self.obfuscated_tree = self.obfuscated_tree.visit(self.transformer)
        self.name_generator = self.transformer.name_generator

    def save(self, save_path=None):
        if save_path is None:
            save_path = self.new_path

        res_file = open(save_path, 'w')
        res_file.write(self.obfuscated_tree.code)
        res_file.close()

        # print(f'Saved: {self.new_path}')
