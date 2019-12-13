from typing import Union

import libcst as cst
from libcst import matchers as m

from Infos import *
from UtilFuncs import delete_duplicates, split_attribute, get_function_decorators


class ABCVisitor(cst.CSTVisitor):

    def __init__(self):
        super().__init__()

        self.info: ModuleInfo = ModuleInfo()
        self.class_stack: List[ClassInfo] = []
        self.function_stack: List[FunctionInfo] = []

    def clear_dublicates(self):
        self.info.variables = delete_duplicates(self.info.variables)
        self.info.functions = delete_duplicates(self.info.functions)
        self.info.classes   = delete_duplicates(self.info.classes)

    def reset(self):
        self.info = ModuleInfo()
        self.class_stack = []
        self.function_stack = []


class MyVisitor(ABCVisitor):

    def __init__(self):
        super().__init__()


    def process_variable(self, node: Union[cst.BaseExpression, cst.BaseAssignTargetExpression]):

        if m.matches(node, m.Name()):
            node = cst.ensure_type(node, cst.Name)

            if self.class_stack and not self.function_stack:
                self.class_stack[-1].variables.append(node.value)
            else:
                self.info.variables.append(node.value)

        elif m.matches(node, m.Attribute()):
            node = cst.ensure_type(node, cst.Attribute)

            splitted_attributes = split_attribute(node)

            if splitted_attributes[0] == 'self' and self.class_stack and self.function_stack and len(splitted_attributes) > 1:
                self.class_stack[-1].variables.append(splitted_attributes[1])
            else:
                self.info.variables.append(splitted_attributes[0])

        elif m.matches(node, m.Tuple()):
            node = cst.ensure_type(node, cst.Tuple)
            for el in node.elements:
                self.process_variable(el.value)

        else:
            pass


    def visit_ClassDef(self, node: cst.ClassDef):
        self.class_stack.append(ClassInfo(node.name.value))

    def leave_ClassDef(self, original_node: cst.ClassDef):
        last_class_def = self.class_stack.pop()
        self.info.classes.append(last_class_def)
        self.info.variables.append(last_class_def.name)


    def visit_FunctionDef(self, node: cst.FunctionDef):

        args = [param.name.value for param in node.params.params]
        def_args = [param.name.value for param in node.params.default_params]
        arg = node.params.star_arg
        kwarg = node.params.star_kwarg
        args.extend(def_args)

        for el in [arg, kwarg]:
            if el and not isinstance(el.name, str):
                args.append(el.name.value)


        #self.info.variables.append(node.name.value)
        self.function_stack.append(FunctionInfo(name=node.name.value, arguments=args))

    def leave_FunctionDef(self, original_node: cst.FunctionDef):

        last_function = self.function_stack.pop()

        if self.class_stack:

            # Обработка конструкторов
            if last_function.name == '__init__':
                last_function.name = self.class_stack[-1].name

            decorator_names = get_function_decorators(original_node)
            if 'property' in decorator_names:
                self.class_stack[-1].variables.append(last_function.name)
            else:
                self.class_stack[-1].functions.append(last_function)

        self.info.functions.append(last_function)
        self.info.variables.extend(last_function.arguments)


    def visit_Assign(self, node: cst.Assign):

        # x = y = 5
        # trgts | val

        for target in node.targets:
            target = target.target
            self.process_variable(target)

    def visit_AnnAssign(self, node: cst.AnnAssign):

        # value: int = 5
        # trgt | ann | val

        target = node.target
        self.process_variable(target)


    def visit_Import(self, node: cst.Import):

        for import_name in node.names:
            import_info = ImportInfo(path='.'.join(split_attribute(import_name.name)))

            alias = import_info.name
            if import_name.asname is not None:
                alias = import_name.asname.name.value
            import_info.alias = alias

            self.info.imported.append(import_info)

    def visit_ImportFrom(self, node: cst.ImportFrom):

        import_info = ImportInfo(path='.'.join(split_attribute(node.module)))
        import_info.alias = import_info.name

        if m.matches(node.names, m.ImportStar()):
            import_info.import_as_names['*'] = '*'

        else:
            for name in node.names:
                name_list = split_attribute(name.name)
                alias = name.asname.name.value if name.asname else name_list[-1]
                import_info.import_as_names['.'.join(name_list)] = alias

        self.info.imported.append(import_info)
