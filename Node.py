class Node:
    # Information about (in)equality represented by node
    constraint = None
    is_terminal = None

    # Pointers to true/false subtrees and parent node. Note that there may be multiple parents as the graph is a DAG
    true_branch_node = None
    false_branch_node = None

    def __init__(self, constraint, is_terminal=False):
        self.true_branch_node = None
        self.false_branch_node = None
        self.constraint = constraint
        self.is_terminal = is_terminal

    def print_node(self):
        print(self.constraint)