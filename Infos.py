from typing import List, Dict


class FunctionInfo:
    def __init__(self, name: str = '', arguments: list = None):

        self.name: str = name
        self.arguments: List[str] = arguments

    def __contains__(self, item):

        if item in self.arguments or item == self.name:
            return True

        return False


class ClassInfo:
    def __init__(self, name: str = '', variables: list = None, functions: list = None):

        if functions is None:
            functions = []
        if variables is None:
            variables = []

        self.name: str = name
        self.variables: List[str, ...] = variables
        self.functions: List[FunctionInfo, ...] = functions

    def __contains__(self, item):

        if item == self.name or item in self.variables:
            return True

        for el in self.functions:
            if item in el:
                return True

        return False

    def __repr__(self):

        return f"{self.name}: \n\tVars: {self.variables} \n\tFunc: {self.function_names}\n"

    @property
    def function_names(self) -> List[str]:
        return [el.name for el in self.functions]

    @property
    def function_arguments(self) -> List[str]:
        res = []
        for func in self.functions:
            res.extend(func.arguments)
        return res


    def get_function_by_name(self, function_name) -> FunctionInfo:
        for el in self.functions:
            if function_name == el.name:
                return el


class ImportInfo:

    def __init__(self, path='', alias=''):

        self.name: str = path
        self.alias: str = alias
        self.import_as_names: Dict[str, str] = dict()
        self.module_link = None

    def __repr__(self):
        return f"Name: {self.name} \n\tAllias: {self.alias} \n\tImports: {self.import_as_names}\n"


class ModuleInfo:

    def __init__(self, classes: List[ClassInfo] = None, functions: List[FunctionInfo] = None, variables: List[str] = None):

        if classes is None:
            classes = []
        if functions is None:
            functions = []
        if variables is None:
            variables = []

        self.imported: List[ImportInfo] = []

        self.classes: List[ClassInfo, ...] = classes
        self.functions: List[FunctionInfo, ...] = functions
        self.variables: List[str] = variables


    def __contains__(self, item):
        if item in self.variables:
            return True

        for el in self.functions:
            if item in el:
                return True

        for el in self.classes:
            if item in el:
                return True


        return False

    def get_all_functions_by_name(self, function_name):

        res = []

        for function in self.functions:
            if function_name == function.name:
                res.append(function)

        return res

    def get_all_classes_by_name(self, class_name):
        res = []

        for cls in self.classes:
            if class_name == cls.name:
                res.append(cls)

        return res


    def get_function_by_name(self, function_name):

        for func in self.functions:
            if func.name == function_name:
                return func

    def get_class_by_name(self, class_name):

        for cls in self.classes:
            if cls.name == class_name:
                return cls

    def get_import_by_name(self, import_name):
        for el in self.imported:
            if el.name == import_name:
                return el

    @property
    def function_names(self):
        res = [el.name for el in self.functions]
        return res

    @property
    def function_arguments(self):
        res = []
        for func in self.functions:
            res.extend(func.arguments)
        return res

    @property
    def method_arguments(self):
        res = []
        for cls in self.classes:
            res.extend(cls.function_arguments)
        return res

    @property
    def class_names(self):
        return [cls.name for cls in self.classes]

    @property
    def method_names(self):
        res = []
        for cls in self.classes:
            res.extend(cls.function_names)
        return res

    @property
    def field_names(self):
        res = []
        for cls in self.classes:
            res.extend(cls.variables)
        return res


    @property
    def all_function_names(self):
        res = self.function_names
        for cls in self.classes:
            res.extend(cls.function_names)
        return res

    @property
    def all_function_arguments(self):
        res = self.function_arguments
        for cls in self.classes:
            res.extend(cls.function_arguments)
        return res


    def get_functions_by_name(self, function_name):

        res: List[FunctionInfo] = []

        for func in self.functions:
            if function_name == func.name:
                res.append(func)
                break

        for cls in self.classes:
            res.append(cls.get_function_by_name(function_name))

        if len(res) > 1:
            print('get_functions_by_name: fond many functions')

        return res

    def can_rename(self, name: str, *type_codes: str) -> bool:

        codes = {
            'v': self.variables,
            'cv': self.field_names,

            'f': self.function_names,
            'cf': self.method_names,
            'c': self.class_names,

            'a': self.function_arguments,
            'ca': self.method_arguments
        }
        bad_name = ''
        type_codes = type_codes if type_codes else codes.keys()

        for code in type_codes:
            if (code in codes) and (name in codes[code]):
                return True

        if name == bad_name:
            print(type_codes)
            print(f"No {name} in {self.get_lists_by_codes(codes, *type_codes)}")

        return False

    def get_lists_by_codes(self, codes_dict, *type_codes):

        res = []

        for code in type_codes:
            if code in codes_dict:
                res.append(codes_dict[code])

        return res

    def can_rename_function_parameter(self, parameter: str, function_name: str):
        funcs = self.get_all_functions_by_name(function_name)
        classes = self.get_all_classes_by_name(function_name)

        res_list = []
        if funcs:
            res_list.extend(funcs)
        if classes:
            #res_list.extend(classes)
            pass

        for function in res_list:
            if parameter in function.arguments:
                return True
            else:
                pass
                # print(f"NO {parameter} IN {function.arguments}")

        return False
