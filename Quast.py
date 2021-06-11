import islpy as isl

from Node import *


# Description: The Quast class below represents quasts for islpy.Sets
class Quast:
    in_node = None  # Terminal node indicating containment inside polyhedron
    out_node = None  # Terminal node indicating non-containment inside polyhedron
    root_node = None  # Root node of the QUAST
    space = None

    def __init__(self, set=None, space=None):
        if set is not None:
            T = None
            for basic_set in set.get_basic_sets():
                if T is None:
                    T = BasicQuast(basic_set)
                else:
                    T = T.union(BasicQuast(basic_set))
            self.root_node = T.root_node
            self.in_node = T.in_node
            self.out_node = T.out_node
            if space is None:
                space = T.get_space()
            self.set_space(space)
        else:
            self.in_node = Node(constraint="IN", node_type=Node.IN_NODE)
            self.out_node = Node(constraint="OUT", node_type=Node.OUT_NODE)
            self.set_space(space)
            self.root_node = None

    def get_space(self):
        return self.space

    def set_space(self, new_space):
        self.space = new_space

    def get_parent_list(self, node):
        return self.__get_parent_list(node, self.root_node)

    # Description: Checks whether current node is a parent of target and continues recursively searching in
    # children of current. Returns a list of all parents
    def __get_parent_list(self, target, current):
        if current is target or current is None:
            return []
        is_current_parent = []
        if current.true_branch_node is target or current.false_branch_node is target:
            is_current_parent = [current]
        parents_from_true_branch = self.__get_parent_list(target, current.true_branch_node)
        parents_from_false_branch = self.__get_parent_list(target, current.false_branch_node)
        return parents_from_true_branch + parents_from_false_branch + is_current_parent

    def union(self, quast):
        union_quast = Quast()
        union_quast.root_node = union_quast.__union(node1=self.root_node, node2=quast.root_node)
        union_quast.set_space(union_quast.root_node.constraint.get_space())
        return union_quast

    def __union(self, node1, node2):
        if node1 is None:
            if node2.node_type is node2.IN_NODE:
                return self.in_node
            elif node2.node_type is node2.OUT_NODE:
                return self.out_node
            else:
                true_branch_node = self.__union(node1=node1, node2=node2.true_branch_node)
                false_branch_node = self.__union(node1=node1, node2=node2.false_branch_node)
                return Node(constraint=node2.constraint, false_branch_node=false_branch_node,
                            true_branch_node=true_branch_node)
        if node1.node_type is node1.IN_NODE:
            return self.in_node
        elif node1.node_type is node1.OUT_NODE:
            return self.__union(node1=None, node2=node2)
        else:
            true_branch_node = self.__union(node1=node1.true_branch_node, node2=node2)
            false_branch_node = self.__union(node1=node1.false_branch_node, node2=node2)
            return Node(constraint=node1.constraint, false_branch_node=false_branch_node,
                        true_branch_node=true_branch_node)

    def complement(self):
        complement_quast = Quast(space=self.get_space())
        complement_quast.root_node = Node(constraint=self.root_node.constraint,
                                          true_branch_node=self.__complement(self.root_node.true_branch_node,
                                                                                complement_quast),
                                          false_branch_node=self.__complement(self.root_node.false_branch_node,
                                                                                 complement_quast))
        return complement_quast

    def __complement(self, curr_node, complement_quast):
        if curr_node == self.in_node:
            return complement_quast.out_node
        elif curr_node == self.out_node:
            return complement_quast.in_node
        else:
            return Node(constraint=curr_node.constraint,
                        true_branch_node=self.__complement(curr_node.true_branch_node, complement_quast),
                        false_branch_node=self.__complement(curr_node.false_branch_node, complement_quast))

    def intersect(self, quast):
        intersection_quast = Quast()
        intersection_quast.root_node = intersection_quast.__intersect(node1=self.root_node, node2=quast.root_node)
        intersection_quast.set_space(intersection_quast.root_node.constraint.get_space())
        return intersection_quast

    def __intersect(self, node1, node2):
        if node1 is None:
            if node2.node_type is node2.IN_NODE:
                return self.in_node
            elif node2.node_type is node2.OUT_NODE:
                return self.out_node
            else:
                true_branch_node = self.__intersect(node1=node1, node2=node2.true_branch_node)
                false_branch_node = self.__intersect(node1=node1, node2=node2.false_branch_node)
                return Node(constraint=node2.constraint, false_branch_node=false_branch_node,
                            true_branch_node=true_branch_node)
        if node1.node_type is node1.IN_NODE:
            return self.__intersect(node1=None, node2=node2)
        elif node1.node_type is node1.OUT_NODE:
            return self.out_node
        else:
            true_branch_node = self.__intersect(node1=node1.true_branch_node, node2=node2)
            false_branch_node = self.__intersect(node1=node1.false_branch_node, node2=node2)
            return Node(constraint=node1.constraint, false_branch_node=false_branch_node,
                        true_branch_node=true_branch_node)

    def reconstruct_set(self):
        basic_set_list = self.__reconstruct_set(self.root_node, [])
        final_set = basic_set_list[0]
        for basic_set in basic_set_list:
            final_set = final_set.union(basic_set)
        return final_set

    def __reconstruct_set(self, curr_node, curr_constraints):
        if curr_node is self.out_node:
            return []
        elif curr_node is self.in_node:
            bset = isl.BasicSet.universe(self.get_space())
            for constraint in curr_constraints:
                bset = bset.add_constraint(constraint)
            if bset.is_empty():
                return []
            else:
                return [bset]
        else:
            curr_constraints.append(curr_node.constraint)
            bsets_from_true = self.__reconstruct_set(curr_node.true_branch_node, curr_constraints)
            curr_constraints.pop()
            curr_constraints.append(self.negate_constraint(curr_node.constraint))
            bsets_from_false = self.__reconstruct_set(curr_node.false_branch_node, curr_constraints)
            curr_constraints.pop()
            return bsets_from_true + bsets_from_false

    def negate_constraint(self, constraint):
        coefficients = constraint.get_coefficients_by_name()
        for var in coefficients.keys():
            coefficients[var] = coefficients[var].neg()

        negated_constraint = constraint.set_coefficients_by_name(coefficients)
        negated_constraint = negated_constraint.set_constant_val(negated_constraint.get_constant_val() - 1)
        return negated_constraint

    # Description: proxy function for recursively printing QUAST level-by-level
    def print_tree(self):
        self.__print_tree(node=self.root_node, level=0)

    # Reference -- https://stackoverflow.com/questions/34012886/print-binary-tree-level-by-level-in-python
    # Description: Recursively prints QUAST level-by-level
    def __print_tree(self, node, level):
        if node is not None:
            self.__print_tree(node.true_branch_node, level + 1)
            print(' ' * 5 * level + '--->', node.constraint)
            self.__print_tree(node.false_branch_node, level + 1)

class BasicQuast(Quast):

    def __init__(self, basic_set=None):
        self.in_node = Node(constraint="IN", node_type=Node.IN_NODE)
        self.out_node = Node(constraint="OUT", node_type=Node.OUT_NODE)
        self.root_node = None
        self.space = None

        if basic_set is not None:
            constraints = basic_set.get_constraints()
            if len(constraints) is not 0:
                self.root_node = Node(constraint=constraints[0], false_branch_node=self.out_node,
                                      true_branch_node=self.add_node(constraints=constraints, i=1))
                self.space = self.root_node.constraint.get_space()

    def add_node(self, constraints, i):
        if i is len(constraints):
            return self.in_node
        else:
            return Node(constraint=constraints[i], false_branch_node=self.out_node,
                        true_branch_node=self.add_node(constraints=constraints, i=i + 1))