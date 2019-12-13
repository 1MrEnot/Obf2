from abc import ABC
from keyword import iskeyword
from typing import Union

import libcst as cst
from libcst import matchers as m

from Infos import *
from NameGenerator import NameGenerator
from ObfuscationParams import ObfuscationParams
from UtilFuncs import split_attribute, get_function_decorators


class ABCTransformer(cst.CSTTransformer, ABC):

    def __init__(self, params=ObfuscationParams(), name_generator=NameGenerator()):
        super().__init__()

        self.class_stack: List = []
        self.function_stack: List = []
        self.attribute_stack: List = []
        self.subscript_stack: List = []
        self.leave_name_stoppers: List = []

        self.module_info: ModuleInfo = ModuleInfo()
        self.params: ObfuscationParams = params

        self.obf_symbols = ('0', 'O')
        self.current_name_position: int = 0
        self.name_generator: NameGenerator = name_generator


    @property
    def change_classes(self) -> bool:
        return self.params.change_classes
    @property
    def change_methods(self) -> bool:
        return self.params.change_methods
    @property
    def change_method_arguments(self) -> bool:
        return self.params.change_method_arguments

    @property
    def change_fields(self) -> bool:
        return self.params.change_fields
    @property
    def change_functions(self) -> bool:
        return self.params.change_functions
    @property
    def change_arguments(self) -> bool:
        return self.params.change_arguments
    @property
    def change_variables(self) -> bool:
        return self.params.change_variables

    @property
    def delete_docstrings(self) -> bool:
        return self.params.delete_docstrings
    @property
    def delete_comments(self) -> bool:
        return self.params.delete_comments
    @property
    def delete_annotations(self) -> bool:
        return self.params.delete_annotations


    def forbidden_name(self, name: str) -> bool:
        if (not name or
                name.startswith('__') and name.endswith('__') or
                self.params.is_forbidden_name(name) or
                iskeyword(name)):
            return True

        return False

    def get_encrypted_name(self, old_name: str) -> str:
        return self.name_generator.get_name(old_name)

    def get_new_cst_name(self, old_name: Union[str, cst.Name]) -> cst.Name:

        if m.matches(old_name, m.Name()):
            name = old_name.value
            lpar, rpar = old_name.lpar, old_name.rpar
        else:
            name = old_name
            lpar = rpar = []

        return cst.Name(value=self.get_encrypted_name(name),
                        lpar=lpar,
                        rpar=rpar)

    def renamed(self, old_node: cst.CSTNode):
        return old_node.with_changes(name=self.get_new_cst_name(old_node.name))

    def can_rename(self, name, *types):

        if not name or self.forbidden_name(name) or not self.module_info.can_rename(name, *types):
            return False

        return True

    def can_rename_func_param(self, parameter, function_name):

        if self.forbidden_name(parameter):
            return False

        return self.module_info.can_rename_function_parameter(parameter, function_name)


class MyTransformer(ABCTransformer):

    def __init__(self, params):
        super().__init__(params)


    def obf_function_name(self, func: cst.Call, updated_node):

        func_name = func.func

        # Обфускация имени функции
        if m.matches(func_name, m.Attribute()) and self.change_methods and self.can_rename(func_name.attr.value, 'cf'):
            func_name = cst.ensure_type(func_name, cst.Attribute)
            func_name = func_name.with_changes(attr=self.get_new_cst_name(func_name.attr))
            updated_node = updated_node.with_changes(func=func_name)

        elif m.matches(func_name, m.Name()) and (self.change_functions and self.can_rename(func_name.value, 'f') or
                                                 self.change_classes and self.can_rename(func_name.value, 'c')):
            func_name = cst.ensure_type(func_name, cst.Name)
            func_name = self.get_new_cst_name(func_name.value)
            updated_node = updated_node.with_changes(func=func_name)

        else:
            pass


        return updated_node

    def new_obf_function_name(self, func: cst.Call):

        func_name = func.func

        # Обфускация имени функции
        if m.matches(func_name, m.Attribute()):
            func_name = cst.ensure_type(func_name, cst.Attribute)

            # Переименовывание имени
            if self.change_variables:
                func_name = func_name.with_changes(value=self.obf_universal(func_name.value, 'v'))

            # Переименовывание метода
            if self.change_methods:
                func_name = func_name.with_changes(attr=self.obf_universal(func_name.attr, 'cf'))

        elif m.matches(func_name, m.Name()):
            func_name = cst.ensure_type(func_name, cst.Name)
            if (self.change_functions or self.change_classes) and self.can_rename(func_name.value, 'c', 'f'):
                func_name = self.get_new_cst_name(func_name.value)

        else:
            pass

        func = func.with_changes(func=func_name)

        return func

    def obf_function_args(self, func: cst.Call):

        new_args = []
        func_root = func.func
        func_name = ''

        if m.matches(func_root, m.Name()):
            func_name = cst.ensure_type(func_root, cst.Name).value
        elif m.matches(func_root, m.Attribute()):
            func_name = split_attribute(cst.ensure_type(func_root, cst.Attribute))[-1]

        if self.change_arguments or self.change_method_arguments:

            for arg in func.args:
                # Значения аргументов
                arg = arg.with_changes(value=self.obf_universal(arg.value))
                # Имена аргументов
                if arg.keyword is not None and self.can_rename_func_param(arg.keyword.value, func_name):
                    new_keyword = self.get_new_cst_name(arg.keyword) if arg.keyword is not None else None
                    arg = arg.with_changes(keyword=new_keyword)

                new_args.append(arg)

        func = func.with_changes(args=new_args)

        return func

    def obf_var(self, var: cst.Name, updated_node: cst.Attribute):

        name = var.value

        if self.change_fields and self.can_rename(name, 'cv'):
            attr = self.get_new_cst_name(name)
            updated_node = updated_node.with_changes(attr=attr)

        elif self.change_variables and self.can_rename(name, 'v'):
            updated_node = updated_node.with_changes()


        return updated_node

    def obf_slice(self, sub_slice: Union[cst.Index, cst.Slice, List[cst.SubscriptElement]]):

        if m.matches(sub_slice, m.Index()):
            sub_slice = self.obf_universal(sub_slice.value)

        elif m.matches(sub_slice, m.Slice()):

            sub_slice = cst.ensure_type(sub_slice, cst.Slice)
            sub_slice = sub_slice.with_changes(lower=self.obf_universal(sub_slice.lower),
                                               upper=self.obf_universal(sub_slice.upper),
                                               step=self.obf_universal(sub_slice.step))

        elif m.matches(sub_slice, m.SubscriptElement()):
            sub_slice = cst.ensure_type(sub_slice, cst.SubscriptElement)
            sub_slice = sub_slice.with_changes(slice=self.obf_universal(sub_slice.slice))

        else:
            pass
            # print(f"NOT IMPLEMENTED obf_slice")



        return sub_slice

    def obf_universal(self, node: cst.CSTNode, *types):

        if m.matches(node, m.Name()):
            types = ('a', 'ca', 'v', 'cv') if not types else types
            node = cst.ensure_type(node, cst.Name)
            if self.can_rename(node.value, *types):
                node = self.get_new_cst_name(node)


        elif m.matches(node, m.NameItem()):
            node = cst.ensure_type(node, cst.NameItem)
            node = node.with_changes(name=self.obf_universal(node.name))

        elif m.matches(node, m.Call()):

            node = cst.ensure_type(node, cst.Call)
            if self.change_methods or self.change_functions:
                node = self.new_obf_function_name(node)
            if self.change_arguments or self.change_method_arguments:
                node = self.obf_function_args(node)



        elif m.matches(node, m.Attribute()):
            node = cst.ensure_type(node, cst.Attribute)
            value = node.value
            attr = node.attr

            self.obf_universal(value)
            self.obf_universal(attr)

        elif m.matches(node, m.AssignTarget()):
            node = cst.ensure_type(node, cst.AssignTarget)
            node = node.with_changes(target=self.obf_universal(node.target))

        elif m.matches(node, m.List() | m.Tuple()):
            node = cst.ensure_type(node, cst.List) if m.matches(node, m.List()) else cst.ensure_type(node, cst.Tuple)
            new_elements = []
            for el in node.elements:
                new_elements.append(self.obf_universal(el))
            node = node.with_changes(elements=new_elements)
        elif m.matches(node, m.Subscript()):
            node = cst.ensure_type(node, cst.Subscript)
            new_slice = []
            for el in node.slice:
                new_slice.append(el.with_changes(slice=self.obf_slice(el.slice)))
            node = node.with_changes(slice=new_slice)
            node = node.with_changes(value=self.obf_universal(node.value))
        elif m.matches(node, m.Element()):
            node = cst.ensure_type(node, cst.Element)
            node = node.with_changes(value=self.obf_universal(node.value))

        elif m.matches(node, m.Dict()):
            node = cst.ensure_type(node, cst.Dict)
            new_elements = []
            for el in node.elements:
                new_elements.append(self.obf_universal(el))
            node = node.with_changes(elements=new_elements)
        elif m.matches(node, m.DictElement()):
            node = cst.ensure_type(node, cst.DictElement)
            new_key = self.obf_universal(node.key)
            new_val = self.obf_universal(node.value)
            node = node.with_changes(key=new_key, value=new_val)
        elif m.matches(node, m.StarredDictElement()):
            node = cst.ensure_type(node, cst.StarredDictElement)
            node = node.with_changes(value=self.obf_universal(node.value))

        elif m.matches(node, m.If() | m.While()):
            node = cst.ensure_type(node, cst.IfExp) if m.matches(node, cst.If | cst.IfExp) else cst.ensure_type(node, cst.While)
            node = node.with_changes(test=self.obf_universal(node.test))
        elif m.matches(node, m.IfExp()):
            node = cst.ensure_type(node, cst.IfExp)
            node = node.with_changes(body=self.obf_universal(node.body))
            node = node.with_changes(test=self.obf_universal(node.test))
            node = node.with_changes(orelse=self.obf_universal(node.orelse))

        elif m.matches(node, m.Comparison()):
            node = cst.ensure_type(node, cst.Comparison)
            new_compars = []
            for target in node.comparisons:
                new_compars.append(self.obf_universal(target))

            node = node.with_changes(left=self.obf_universal(node.left))
            node = node.with_changes(comparisons=new_compars)
        elif m.matches(node, m.ComparisonTarget()):
            node = cst.ensure_type(node, cst.ComparisonTarget)
            node = node.with_changes(comparator=self.obf_universal(node.comparator))

        elif m.matches(node, m.FormattedString()):
            node = cst.ensure_type(node, cst.FormattedString)
            new_parts = []
            for part in node.parts:
                new_parts.append(self.obf_universal(part))
            node = node.with_changes(parts=new_parts)
        elif m.matches(node, m.FormattedStringExpression()):
            node = cst.ensure_type(node, cst.FormattedStringExpression)
            node = node.with_changes(expression=self.obf_universal(node.expression))

        elif m.matches(node, m.BinaryOperation() | m.BooleanOperation()):
            node = cst.ensure_type(node, cst.BinaryOperation) if m.matches(node, m.BinaryOperation()) else cst.ensure_type(node, cst.BooleanOperation)
            node = node.with_changes(left=self.obf_universal(node.left),
                                     right=self.obf_universal(node.right))
        elif m.matches(node, m.UnaryOperation()):
            node = cst.ensure_type(node, cst.UnaryOperation)
            node = node.with_changes(expression=self.obf_universal(node.expression))

        elif m.matches(node, m.ListComp()):
            node = cst.ensure_type(node, cst.ListComp)
            node = node.with_changes(elt=self.obf_universal(node.elt))
            node = node.with_changes(for_in=self.obf_universal(node.for_in))

        elif m.matches(node, m.DictComp()):
            node = cst.ensure_type(node, cst.DictComp)
            node = node.with_changes(key=self.obf_universal(node.key))
            node = node.with_changes(value=self.obf_universal(node.value))
            node = node.with_changes(for_in=self.obf_universal(node.for_in))

        elif m.matches(node, m.CompFor()):
            node = cst.ensure_type(node, cst.CompFor)
            new_ifs = []

            node = node.with_changes(target=self.obf_universal(node.target))
            node = node.with_changes(iter=self.obf_universal(node.iter))
            for el in node.ifs:
                new_ifs.append(self.obf_universal(el))
            node = node.with_changes(ifs=new_ifs)
        elif m.matches(node, m.CompIf()):
            node = cst.ensure_type(node, cst.CompIf)
            node = node.with_changes(test=self.obf_universal(node.test))

        elif m.matches(node, m.Integer() | m.Float() | m.SimpleString()):
            pass

        else:
            pass
            # print(node)

        return node



    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call):

        if self.change_variables or self.change_fields or self.change_arguments or self.change_method_arguments:
            updated_node = self.obf_function_args(updated_node)

        updated_node = self.new_obf_function_name(updated_node)

        return updated_node

    def leave_Decorator(self, original_node: cst.Decorator, updated_node: cst.Decorator):

        updated_node = updated_node.with_changes(decorator=self.obf_universal(updated_node.decorator, 'f'))

        return updated_node

    def leave_Expr(self, original_node: cst.Expr, updated_node: cst.Expr):

        updated_node = updated_node.with_changes(value=self.obf_universal(updated_node.value))

        return updated_node



    def visit_Attribute(self, node: cst.Attribute):
        self.attribute_stack.append(node.attr.value)

    def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute):
        self.attribute_stack.pop()

        # x.y. z
        tail = updated_node.value
        head = updated_node.attr

        attrs = split_attribute(tail)

        # Обфускация метода/поля
        if m.matches(head, m.Name()):
            head = cst.ensure_type(head, cst.Name)
            updated_node = self.obf_var(head, updated_node)


        elif m.matches(head, m.Call()):
            head = cst.ensure_type(head, cst.Call)
            updated_node = self.obf_function_name(head, updated_node)

        else:
            pass

        # Обфускация имени
        if m.matches(tail, m.Name()):
            tail = cst.ensure_type(tail, cst.Name)
            if self.can_rename(tail.value, 'v', 'a', 'ca'):
                updated_node = updated_node.with_changes(value=self.get_new_cst_name(tail.value))

        elif m.matches(tail, m.Subscript()):
            tail = cst.ensure_type(tail, cst.Subscript)

        else:
            pass


        return updated_node


    def leave_Comment(self, original_node: cst.Comment, updated_node: cst.Comment):
        if self.delete_comments:
            updated_node = updated_node.with_changes(value='#')

        return updated_node


    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name):

        DEBUG = True

        if self.attribute_stack or self.leave_name_stoppers or DEBUG:
            return updated_node

        name = updated_node.value
        if self.can_rename(name, 'v', 'a', 'ca'):
            updated_node = self.get_new_cst_name(name)

        return updated_node


    def visit_FunctionDef(self, original_node: cst.FunctionDef):
        self.function_stack.append(original_node.name.value)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef):

        # Удаление аннотаций
        if self.delete_annotations:
            old_params = original_node.params.params
            old_default_params = original_node.params.default_params

            small_params = [i.with_changes(annotation=None) for i in old_params]
            small_default_params = [i.with_changes(annotation=None) for i in old_default_params]

            new_params = original_node.params.with_changes(params=small_params,
                                                           default_params=small_default_params)

            updated_node = updated_node.with_changes(params=new_params,
                                                     returns=None)

        # Удаление многострочных комментариев
        if self.delete_docstrings:
            pass

        # Замена аргументов
        if (self.change_method_arguments and self.class_stack) or\
                (self.change_arguments and not self.class_stack):

            all_params = updated_node.params

            new_params = []
            new_default_params = []

            for argument in all_params.params:
                # Обфускация имени аргумента
                if self.can_rename(argument.name.value, 'a', 'ca'):
                    argument = argument.with_changes(name=self.get_new_cst_name(argument.name))

                new_params.append(argument)

            for argument in all_params.default_params:
                # Обфкскация значения по умолчанию
                argument = argument.with_changes(default=self.obf_universal(argument.default))
                # Обфускация имени аргумента
                if self.can_rename(argument.name.value, 'a', 'ca'):
                    argument = argument.with_changes(name=self.get_new_cst_name(argument.name))


                new_default_params.append(argument)



            arg, kwarg = all_params.star_arg, all_params.star_kwarg
            new_all_params = all_params.with_changes(params=new_params, default_params=new_default_params)

            if arg is not None and not isinstance(arg.name, str) and self.can_rename(arg.name.value, 'a', 'ca'):
                new_star_arg = arg.with_changes(name=self.get_new_cst_name(arg.name.value))
                new_all_params = new_all_params.with_changes(star_arg=new_star_arg)
            if kwarg is not None and not isinstance(kwarg.name, str) and self.can_rename(kwarg.name.value, 'a', 'ca'):
                new_star_kwarg = kwarg.with_changes(name=self.get_new_cst_name(kwarg.name.value))
                new_all_params = new_all_params.with_changes(star_kwarg=new_star_kwarg)

            updated_node = updated_node.with_changes(params=new_all_params)


        is_property = 'property' in get_function_decorators(updated_node)

        # Замена названия
        if (self.can_rename(updated_node.name.value, 'f', 'cf', 'cv') and
                ((self.class_stack and ((self.change_methods and self.change_fields) or (self.change_fields and not self.change_methods and is_property) or (not self.change_fields and self.change_methods and not is_property))) or
                 (not self.class_stack and self.change_functions))):
            updated_node = self.renamed(updated_node)

        self.function_stack.pop()

        return updated_node


    def visit_ClassDef(self, original_node: cst.ClassDef):
        self.class_stack.append(original_node.name.value)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef):

        self.class_stack.pop()


        if not self.change_classes:
            return updated_node

        class_name = updated_node.name.value
        new_bases = []

        if self.can_rename(class_name, 'c'):
            updated_node = self.renamed(updated_node)

        for base in updated_node.bases:
            full_name = base.value

            if m.matches(full_name, m.Name()):
                full_name = cst.ensure_type(full_name, cst.Name)
                if self.can_rename(full_name.value, 'c'):
                    base = base.with_changes(value=self.get_new_cst_name(full_name.value))
            elif m.matches(full_name, m.Attribute()):
                # TODO поддержка импортов
                pass
            else:
                pass

            new_bases.append(base)

        updated_node = updated_node.with_changes(bases=new_bases)


        return updated_node


    def visit_Subscript(self, node: cst.Subscript):
        self.subscript_stack.append(node.value)

    def leave_Subscript(self, original_node: cst.Subscript, updated_node: cst.Subscript):
        self.subscript_stack.pop()
        return updated_node


    # TODO Обфускация импортов
    def leave_Import(self, original_node: cst.Import, updated_node: cst.Import):



        return updated_node

    def leave_ImportFrom(self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom):

        new_names = []

        if m.matches(updated_node.names, m.ImportStar()):
            new_names = updated_node.names
        else:
            for el in updated_node.names:
                el_name = el.name.value
                if self.can_rename(el_name) and self.name_generator.in_dictionary(el_name):
                    el = el.with_changes(name=self.get_new_cst_name(el_name))
                new_names.append(el)

        updated_node = updated_node.with_changes(names=new_names)

        return updated_node


    def leave_Global(self, original_node: cst.Global, updated_node: cst.Global):

        new_names = []

        for el in updated_node.names:
            new_names.append(self.obf_universal(el, 'v'))

        return updated_node.with_changes(names=new_names)

    def leave_Nonlocal(self, original_node: cst.Nonlocal, updated_node: cst.Nonlocal):

        new_names = []

        for el in updated_node.names:
            new_names.append(self.obf_universal(el, 'v'))

        return updated_node.with_changes(names=new_names)





    def leave_Assign(self, original_node: cst.Assign, updated_node: cst.Assign):

        new_targets = []
        new_value = self.obf_universal(updated_node.value)
        for el in updated_node.targets:
            new_targets.append(self.obf_universal(el, 'v', 'a', 'ca'))

        updated_node = updated_node.with_changes(targets=new_targets)
        updated_node = updated_node.with_changes(value=new_value)

        return updated_node

    def leave_AnnAssign(self, original_node: cst.AnnAssign, updated_node: cst.AnnAssign):

        if updated_node.value is None:
            new_val = cst.Name(value='None', lpar=[], rpar=[])
        else:
            new_val = self.obf_universal(updated_node.value, 'v', 'a', 'ca')

        updated_node = updated_node.with_changes(value=new_val)
        updated_node = updated_node.with_changes(target=self.obf_universal(updated_node.target, 'v', 'a', 'ca'))

        if self.delete_annotations:
            space = cst.SimpleWhitespace(value=' ')
            updated_node = cst.Assign(targets=[cst.AssignTarget(target=updated_node.target,
                                                                whitespace_before_equal=space,
                                                                whitespace_after_equal=space,
                                                                )],
                                      value=updated_node.value,
                                      semicolon=updated_node.semicolon)

            # new_annotation = updated_node.annotation.with_changes(annotation=None)
            # updated_node = updated_node.with_changes(annotation=new_annotation)



        return updated_node

    def leave_AugAssign(self, original_node: cst.AugAssign, updated_node: cst.AugAssign):

        updated_node = updated_node.with_changes(target=self.obf_universal(updated_node.target),
                                                 value=self.obf_universal(updated_node.value))

        return updated_node

    def leave_If(self, original_node: cst.If, updated_node: cst.If):

        updated_node = updated_node.with_changes(test=self.obf_universal(updated_node.test))

        return updated_node

    def leave_IfExp(self, original_node: cst.IfExp, updated_node: cst.IfExp):

        updated_node = updated_node.with_changes(test=self.obf_universal(updated_node.test))

        return updated_node

    def leave_While(self, original_node: cst.While, updated_node: cst.While):

        updated_node = updated_node.with_changes(test=self.obf_universal(updated_node.test))

        return updated_node

    def leave_For(self, original_node: cst.For, updated_node: cst.For):

        updated_node = updated_node.with_changes(target=self.obf_universal(updated_node.target))
        updated_node = updated_node.with_changes(iter=self.obf_universal(updated_node.iter))

        return updated_node

    def leave_Del(self, original_node: cst.Del, updated_node: cst.Del):

        updated_node = updated_node.with_changes(target=self.obf_universal(updated_node.target))
        return updated_node

    def leave_Return(self, original_node: cst.Return, updated_node: cst.Return):
        updated_node = updated_node.with_changes(value=self.obf_universal(updated_node.value))
        return updated_node
