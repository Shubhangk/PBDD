import inspect


class Node(object):
    # Constant representing whether/which terminal node
    IN_NODE = 1
    OUT_NODE = 2
    NON_TERMINAL = 0

    # Information about (in)equality represented by node
    constraint = None
    node_type = None

    # Pointers to true/false subtrees and parent node. Note that there may be multiple parents as the graph is a DAG
    true_branch_node = None
    false_branch_node = None

    # Description: overriding this function should make the class immutable (except at initialization)
    # Reference -- http://www.odosmatthewscoding.com/2018/10/how-to-make-python-class-immutable.html
    def __setattr__(self, *args):
        if inspect.stack()[1][3] == '__init__':  # allow write on initialization
            object.__setattr__(self, *args)
        else:
            raise TypeError('Attempting to modify an immutable Node object')

    def __init__(self, constraint, false_branch_node=None, true_branch_node=None, node_type=0):
        self.true_branch_node = true_branch_node
        self.false_branch_node = false_branch_node
        self.constraint = constraint
        self.node_type = node_type

    def is_terminal(self):
        return self.node_type is self.IN_NODE or self.node_type is self.OUT_NODE

    def print_node(self):
        print("Constraint: " + str(self.constraint) + "\nType: " + str(self.node_type))
