class Node(object):
    TERMINAL = 1
    NON_TERMINAL = 0

    def __init__(self, bset, false_branch_node=None, true_branch_node=None, node_type=0):
        self.true_branch_node = true_branch_node
        self.false_branch_node = false_branch_node
        self.bset = bset
        self.node_type = node_type

    def is_terminal(self):
        return self.node_type is Node.TERMINAL

    def print_node(self):
        print("Basic set: " + str(self.bset) + "\nTerminal: " + str(self.node_type == Node.TERMINAL))
