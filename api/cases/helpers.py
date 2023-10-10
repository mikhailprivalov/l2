from utils import tree_directions_case as tree_directions
from anytree import Node, RenderTree


def get_case_direction_tree(num_dir):
    root_dir = tree_directions.root_direction(num_dir)
    if not root_dir or not root_dir[-1]:
        return {}
    num_root_dir = root_dir[-1][-3]
    result = tree_directions.get_research_by_dir(num_root_dir)
    num_iss = result[0][0]

    # отсортировать по подчинениям - построить бинарное дерево
    tree_dir = tree_directions.hosp_tree_direction(num_iss)
    final_tree = {}

    node_dir = Node({'order': '-1', 'direction': '', 'research_title': '', 'correct_level': True, 'color': '', 'cancel': False, 'issledovaniye': '', 'parent_iss': ''})
    for j in tree_dir:
        research_title = j[12] if j[12] else j[9]
        temp_s = {'order': '-1', 'direction': j[0], 'research_title': research_title, 'correct_level': True, 'color': '', 'cancel': j[14], 'issledovaniye': j[5], 'parent_iss': j[3]}
        if not j[3]:
            final_tree[j[5]] = Node(temp_s, parent=node_dir)
        else:
            final_tree[j[5]] = Node(temp_s, parent=final_tree.get(j[3]))

    data_sort = []
    count_level_second = 0
    correct_level = True
    for row in RenderTree(node_dir):
        order = int(len(row.pre) / 4)
        if order == 2:
            count_level_second += 1
            if count_level_second > 1:
                correct_level = False
                row.node.name['correct_level'] = correct_level
                row.node.name['color'] = 'red'
        if not correct_level and order > 2:
            row.node.name['color'] = '#d35400'
            row.node.name['correct_level'] = correct_level

        row.node.name['order'] = order
        data_sort.append(row.node.name)

    data_sort.pop(0)
    return data_sort
