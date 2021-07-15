import inspect


class Node(object):
    # Constant representing whether terminal node
    TERMINAL = 1
    NON_TERMINAL = 0
    #
    # # Information about (in)equality represented by node
    # bset = None
    # node_type = None
    #
    # # Pointers to true/false subtrees and parent node. Note that there may be multiple parents as the graph is a DAG
    # true_branch_node = None
    # false_branch_node = None

    # Description: overriding this function should make the class immutable (except at initialization)
    def __setattr__(self, *args):
        # allow write only during initialization
        if inspect.stack()[1][3] == '__init__':
            object.__setattr__(self, *args)
        else:
            raise TypeError('Attempting to modify an immutable Node object')

    def __init__(self, bset, false_branch_node=None, true_branch_node=None, node_type=0):
        self.true_branch_node = true_branch_node
        self.false_branch_node = false_branch_node
        self.bset = bset
        self.node_type = node_type

    def is_terminal(self):
        return self.node_type is Node.TERMINAL

    def print_node(self):
        print("Basic set: " + str(self.bset) + "\nTerminal: " + str(self.node_type == Node.TERMINAL))
