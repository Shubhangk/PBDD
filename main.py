import islpy as isl


class Node:
    # Information about (in)equality represented by node
    constraint = None
    is_terminal = None

    # Pointers to true/false subtrees and parent node. Note that there may be multiple parents as the graph is a DAG
    true_branch_node = None
    false_branch_node = None
    parent_nodes = None

    def __init__(self, constraint, is_terminal=False):
        self.true_branch_node = None
        self.false_branch_node = None
        self.parent_nodes = []
        self.constraint = constraint
        self.is_terminal = is_terminal

    def print_node(self):
        print(self.constraint)


# Description: The Quast class below represents quasts for islpy.Sets
class Quast:
    in_node = None  # Terminal node indicating containment inside polyhedron
    out_node = None  # Terminal node indicating non-containment inside polyhedron
    root_node = None  # Root node of the QUAST
    space = None

    def __init__(self, space):
        # Todo -- Under construction.
        self.in_node = Node(constraint="IN", is_terminal=True)
        self.out_node = Node(constraint="OUT", is_terminal=True)
        self.set_space(space)

    def get_space(self):
        return self.space

    def set_space(self, new_space):
        self.space = new_space

    # Description: proxy function for recursively printing QUAST level-by-level
    def print_tree(self):
        self.rec_print_tree(node=self.root_node, level=0)

    # Reference -- https://stackoverflow.com/questions/34012886/print-binary-tree-level-by-level-in-python
    # Description: Recursively prints QUAST level-by-level
    def rec_print_tree(self, node, level):
        if node is not None:
            self.rec_print_tree(node.true_branch_node, level + 1)
            print(' ' * 5 * level + '--->', node.constraint)
            self.rec_print_tree(node.false_branch_node, level + 1)

    def deepclone(self):
        space = self.get_space()
        clone = Quast(space)
        clone.root_node = Node(self.root_node.constraint)
        copy = {self.root_node: clone.root_node, self.in_node: clone.in_node, self.out_node: clone.out_node}
        self.rec_deepclone(self.root_node, clone.root_node, copy)
        return clone

    def rec_deepclone(self, curr_subtree_root, new_subtree_root, copy):
        # base case
        if curr_subtree_root.is_terminal:
            return

        if curr_subtree_root.true_branch_node not in copy.keys():
            copy[curr_subtree_root.true_branch_node] = Node(constraint=curr_subtree_root.true_branch_node.constraint,
                                                            is_terminal=curr_subtree_root.true_branch_node.is_terminal)
        new_subtree_root.true_branch_node = copy[curr_subtree_root.true_branch_node]

        if curr_subtree_root.false_branch_node not in copy.keys():
            copy[curr_subtree_root.false_branch_node] = Node(constraint=curr_subtree_root.false_branch_node.constraint,
                                                             is_terminal=curr_subtree_root.false_branch_node.is_terminal)
        new_subtree_root.false_branch_node = copy[curr_subtree_root.false_branch_node]
        self.rec_deepclone(curr_subtree_root=curr_subtree_root.true_branch_node,
                           new_subtree_root=new_subtree_root.true_branch_node, copy=copy)
        self.rec_deepclone(curr_subtree_root=curr_subtree_root.false_branch_node,
                           new_subtree_root=new_subtree_root.false_branch_node, copy=copy)

    # Description: unions the quast argument into the current Quast instance
    def union(self, quast):
        for node in self.out_node.parent_nodes:
            if node.false_branch_node is self.out_node:
                node.false_branch_node = quast.root_node
            if node.true_branch_node is self.out_node:
                node.true_branch_node = quast.root_node
            quast.root_node.parent_nodes.append(node)
        for node in self.in_node.parent_nodes:
            if node.true_branch_node is self.in_node:
                node.true_branch_node = quast.in_node
            if node.false_branch_node is self.in_node:
                node.false_branch_node = quast.in_node
            quast.in_node.parent_nodes.append(node)

        self.out_node = quast.out_node
        self.in_node = quast.in_node

    # Description: returns a fresh (deep) copy of the union of quast argument into current instance
    # deprecated
    def get_union(self, quast):
        self_copy = self.deepclone()
        quast_copy = quast.deepclone()
        self_copy.union(quast_copy)
        return self_copy

    # Description: complements the current Quast instance
    def complement(self):
        for node in list(set(self.in_node.parent_nodes) | set(self.out_node.parent_nodes)):
            if node.true_branch_node is self.in_node:
                node.true_branch_node = self.out_node
            elif node.true_branch_node is self.out_node:
                node.true_branch_node = self.in_node

            if node.false_branch_node is self.in_node:
                node.false_branch_node = self.out_node
            elif node.false_branch_node is self.out_node:
                node.false_branch_node = self.in_node

        temp_new_out_node_parents = self.in_node.parent_nodes
        self.in_node.parent_nodes = self.out_node.parent_nodes
        self.out_node.parent_nodes = temp_new_out_node_parents

    # Description: returns a fresh (deep) copy of the complement of current Quast instance
    # deprecated
    def get_complement(self):
        self_copy = self.deepclone()
        self_copy.complement()
        return self_copy

    # Description: intersects the current Quast instance with the quast argument.
    def intersect(self, quast):
        for node in self.in_node.parent_nodes:
            if node.true_branch_node == self.in_node:
                node.true_branch_node = quast.root_node
            if node.false_branch_node == self.in_node:
                node.false_branch_node = quast.root_node

        self.in_node = quast.in_node
        for node in quast.out_node.parent_nodes:
            if node.true_branch_node == quast.out_node:
                node.true_branch_node = self.out_node
            if node.false_branch_node == quast.out_node:
                node.false_branch_node = self.out_node
        self.out_node.parent_nodes = self.out_node.parent_nodes + quast.out_node.parent_nodes

    # Description: returns a fresh (deep) copy of the intersection of quast argument with current Quast instance
    # deprecated
    def get_intersection(self, quast):
        self_copy = self.deepclone()
        quast_copy = quast.deepclone()
        self_copy.intersect(quast_copy)
        return self_copy


# Description: The BasicQuast class below represents quasts for islpy.BasicSets.
# Parent Class(es): Quast
class BasicQuast(Quast):
    def __init__(self, basic_set):
        # Todo -- Error handling
        self.in_node = Node(constraint="IN", is_terminal=True)
        self.out_node = Node(constraint="OUT", is_terminal=True)
        for constraint in basic_set.get_constraints():
            self.add_node(constraint)
        self.space = self.root_node.constraint.get_space()

    def add_node(self, constraint):
        node = Node(constraint)
        if self.root_node is None:
            self.root_node = node
            node.true_branch_node = self.in_node
            node.false_branch_node = self.out_node
            self.out_node.parent_nodes.append(node)
            self.in_node.parent_nodes.append(node)
        else:
            parent = self.in_node.parent_nodes[0]  # For convex polyhedra, there will always be 1 parent for in_node.
            parent.true_branch_node = node
            self.in_node.parent_nodes[0] = node
            self.out_node.parent_nodes.append(
                node)  # While constructing the QUAST, number of out_node parents can only increase for convex polyhedra
            node.true_branch_node = self.in_node
            node.false_branch_node = self.out_node
            node.parent_node = parent

    # proxy function for recursive reconstruction of basic set from current QUAST representation
    def reconstruct_basic_set(self):
        bset = isl.BasicSet.universe(
            space=self.get_space())  # creates basic set of entire universe with dimension of the space of the polyhedra in the current Quast
        return self.rec_reconstruct_basic_set(basic_set=bset, node=self.root_node, level=0)

    # recursively reconstructs basic set from current QUAST representation
    def rec_reconstruct_basic_set(self, basic_set, node, level):
        if node is not None and not node.is_terminal:
            basic_set = self.rec_reconstruct_basic_set(basic_set, node.true_branch_node, level + 1)
            basic_set = basic_set.add_constraint(node.constraint)
            basic_set = self.rec_reconstruct_basic_set(basic_set, node.false_branch_node, level + 1)
        return basic_set

    # def deepclone(self):
    #     return BasicQuast(self.reconstruct_basic_set())


def Test1():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    Q = BasicQuast(A)
    Q.print_tree()


def Test2():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    print("Quast for A:")
    a.print_tree()
    B = isl.BasicSet("{[x,y]: x <= -1 and y <=5 }")
    b = BasicQuast(B)
    print("Quast for B:")
    b.print_tree()
    a.union(b)
    print("Union of quasts\n")
    a.print_tree()


def Test3():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    a.print_tree()
    print("\nComplement Tree\n")
    a.complement()
    a.print_tree()


def Test4():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    a.complement()
    B = isl.BasicSet("{[x,y]: x <= -1 and y <=5 }")
    b = BasicQuast(B)
    a.union(b)
    a.print_tree()


def Test5():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    B = isl.BasicSet("{[x,y]: y >= 7 }")
    a = BasicQuast(A)
    b = BasicQuast(B)
    a.intersect(b)
    a.print_tree()

def Test6():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 and x < 20 and y <= 99}")
    Q = BasicQuast(A)
    print("Quast:\n")
    Q.print_tree()
    Q_clone = Q.deepclone()
    print("Clone Quast:\n")
    Q_clone.print_tree()

Test6()