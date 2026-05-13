from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def build_nested_tree(queryset) -> list[dict]:
    """将 treebeard get_tree() 返回的扁平列表转为嵌套 dict 列表。

    每项结构: {'node': Document, 'children': [...]}
    """
    nodes = list(queryset)
    result: list[dict] = []
    # stack 存 (depth, children_list)
    stack: list[tuple[int, list]] = []

    for node in nodes:
        depth = node.get_depth()
        item: dict = {"node": node, "children": []}

        while stack and stack[-1][0] >= depth:
            stack.pop()

        if stack:
            stack[-1][1].append(item)
        else:
            result.append(item)

        stack.append((depth, item["children"]))

    return result
