from Node import *

# Description: The Quast class below represents quasts for islpy.Sets
class Quast:
    in_node = None  # Terminal node indicating containment inside polyhedron
    out_node = None  # Terminal node indicating non-containment inside polyhedron
    root_node = None  # Root node of the QUAST
    space = None

    def __init__(self, space):
        self.in_node = Node(constraint="IN", is_terminal=True)
        self.out_node = Node(constraint="OUT", is_terminal=True)
        self.set_space(space)

    def get_space(self):
        return self.space

    def set_space(self, new_space):
        self.space = new_space

    def get_parent_list(self, node):
        parent_list = []
        self.rec_get_parent_list(node, self.root_node, parent_list)
        return parent_list

    def rec_get_parent_list(self, current, target, parent_list):
        if current is target:
            return
        elif current.true_branch_node is target or current.false_branch_node is target:
            parent_list.append(current)
        self.rec_get_parent_list(current.true_branch_node, target, parent_list)
        self.rec_get_parent_list(current.false_branch_node, target, parent_list)

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
        for node in self.get_parent_list(self.out_node):
            if node.false_branch_node is self.out_node:
                node.false_branch_node = quast.root_node
            if node.true_branch_node is self.out_node:
                node.true_branch_node = quast.root_node

        for node in self.get_parent_list(self.in_node):
            if node.true_branch_node is self.in_node:
                node.true_branch_node = quast.in_node
            if node.false_branch_node is self.in_node:
                node.false_branch_node = quast.in_node

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
        for node in set(self.get_parent_list(self.in_node)) | set(self.get_parent_list(self.out_node)):
            if node.true_branch_node is self.in_node:
                node.true_branch_node = self.out_node
            elif node.true_branch_node is self.out_node:
                node.true_branch_node = self.in_node

            if node.false_branch_node is self.in_node:
                node.false_branch_node = self.out_node
            elif node.false_branch_node is self.out_node:
                node.false_branch_node = self.in_node

    # Description: returns a fresh (deep) copy of the complement of current Quast instance
    # deprecated
    def get_complement(self):
        self_copy = self.deepclone()
        self_copy.complement()
        return self_copy

    # Description: intersects the current Quast instance with the quast argument.
    def intersect(self, quast):
        for node in self.get_parent_list(self.in_node):
            if node.true_branch_node == self.in_node:
                node.true_branch_node = quast.root_node
            if node.false_branch_node == self.in_node:
                node.false_branch_node = quast.root_node

        self.in_node = quast.in_node
        for node in quast.get_parent_list(quast.out_node):
            if node.true_branch_node == quast.out_node:
                node.true_branch_node = self.out_node
            if node.false_branch_node == quast.out_node:
                node.false_branch_node = self.out_node

    # Description: returns a fresh (deep) copy of the intersection of quast argument with current Quast instance
    # deprecated
    def get_intersection(self, quast):
        self_copy = self.deepclone()
        quast_copy = quast.deepclone()
        self_copy.intersect(quast_copy)
        return self_copy
