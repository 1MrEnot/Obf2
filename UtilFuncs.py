from typing import List, Union

import libcst as cst
from libcst import matchers as m


def delete_duplicates(arr: List):
    return list(set(arr))


def split_attribute(node: Union[cst.Attribute, cst.Name, cst.BaseExpression]) -> List[str]:


    if m.matches(node, m.Attribute()):
        node = cst.ensure_type(node, cst.Attribute)
        res = split_attribute(node.value)
        res.append(node.attr.value)
        return res

    elif m.matches(node, m.Call()):
        node = cst.ensure_type(node, cst.Call)
        res = split_attribute(node.func)
        if m.matches(node.func, m.Name()):
            node_func = cst.ensure_type(node.func, cst.Name)
            res.append(node_func.value)
        return res

    else:
        return [node.value]


def get_function_decorators(node: cst.FunctionDef) -> List[str]:
    decorator_names = []
    for el in node.decorators:
        if m.matches(el.decorator, m.Name()):
            name = cst.ensure_type(el.decorator, cst.Name)
            decorator_names.append(name.value)

    return decorator_names

