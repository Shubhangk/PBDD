import islpy
import islpy as isl
from graphviz import Digraph
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

    ################################
    # Getters and Setters
    ################################
    def get_space(self):
        return self.space

    def set_space(self, new_space):
        self.space = new_space

    ####################################
    # Quast API for set operations
    ####################################

    def union(self, quast):
        if self.get_space() != quast.get_space():
            raise Exception("spaces don't match")
        union_quast = Quast(space=self.get_space())
        union_quast.root_node = union_quast.__union(node1=self.root_node, node2=quast.root_node, new_node2=[None])
        return union_quast

    def complement(self):
        complement_quast = Quast(space=self.get_space())
        complement_quast.root_node = Node(constraint=self.root_node.constraint,
                                          true_branch_node=self.__complement(self.root_node.true_branch_node,
                                                                             complement_quast),
                                          false_branch_node=self.__complement(self.root_node.false_branch_node,
                                                                              complement_quast))
        return complement_quast

    def intersect(self, quast):
        if self.get_space() != quast.get_space():
            raise Exception("spaces don't match")
        intersection_quast = Quast(space=self.get_space())
        intersection_quast.root_node = intersection_quast.__intersect(node1=self.root_node, node2=quast.root_node,
                                                                      new_node2=[None])
        return intersection_quast

    def reconstruct_set(self):
        basic_set_list = self.__reconstruct_set(self.root_node, [])
        final_set = basic_set_list[0] if len(basic_set_list) > 0 else isl.BasicSet.empty(self.get_space())
        for basic_set in basic_set_list:
            final_set = final_set.union(basic_set)
        return final_set

    def print_tree(self):
        self.__print_tree(node=self.root_node, level=0)

    def visualize_tree(self):
        dot = Digraph(format="pdf", comment='Quast Visualization')
        arcs = set()
        self.__visualize_tree(arcs, self.root_node)
        nodes = set()
        for arc in arcs:
            if arc[0] not in nodes:
                dot.node(str(id(arc[0])), self.__get_visualization_label(arc[0].constraint))
            if arc[1] not in nodes:
                dot.node(str(id(arc[1])), self.__get_visualization_label(arc[1].constraint))
            dot.edge(str(id(arc[0])), str(id(arc[1])), label=arc[2])
        if arcs == set():
            dot.node('root', self.root_node.constraint)
        print(dot.source)
        dot.render('visualization-output/quast', view=True)

    def is_empty(self):
        return self.reconstruct_set().is_empty()

    def is_equal(self, quast):
        return self.reconstruct_set() == quast.reconstruct_set()

    def apply(self, basic_map):
        return Quast(self.reconstruct_set().apply(basic_map))

    def project_out(self, dim_type, first, n):
        return Quast(self.reconstruct_set().project_out(dim_type, first, n))

    def lexmin(self):
        return Quast(self.reconstruct_set().lexmin())

    def lexmax(self):
        return Quast(self.reconstruct_set().lexmax())

    def product(self, quast):
        return Quast(self.reconstruct_set().product(quast.reconstruct_set()))

    def flat_product(self, quast):
        extension_space = quast.get_space()
        extended_space = self.__get_extended_space(extension_space)
        extended_space_self = Quast(space=extended_space)
        extended_space_quast = Quast(space=extended_space)
        self.__project_quast_into_extended_space(self.root_node, extended_space, extended_space_self, False)
        quast.__project_quast_into_extended_space(quast.root_node, extended_space, extended_space_quast, True)
        return extended_space_self.intersect(extended_space_quast)

    def extend_space(self, extension_space):
        extended_space = self.__get_extended_space(extension_space)
        extended_space_quast = Quast(space=extended_space)
        self.__project_quast_into_extended_space(self.root_node, extended_space, extended_space_quast)
        return extended_space_quast

    ######################################################################
    # Quast API for optimizing tree representation of underlying sets
    ######################################################################

    def prune_redundant_branches(self):
        self.__prune_redundant_branches(self.root_node, [])

    def prune_emptyset_branches(self):
        MAX_MODIFICATIONS = 1000
        num_modifications = 0
        modified = True
        while modified and num_modifications < MAX_MODIFICATIONS:
            modified = self.__detect_and_prune_emptyset_branch(self.root_node, [], [])

    def prune_equal_children_node(self):
        return self.__prune_equal_children_node(self.root_node)

    def prune_isomorphic_subtrees(self):
        node_set = self.__get_node_set()
        memo_table = {}
        for node1 in node_set:
            for node2 in node_set:
                if node1 is not node2 and self.__are_subtrees_isomorphic(node1, node2, memo_table):
                    can_reach_node1 = self.__get_reachable_subDAG_as_dict(node1)
                    if node2 in can_reach_node1:
                        can_reach_node2 = self.__get_reachable_subDAG_as_dict(node2)
                        can_reach_node2[node2] = node1
                        self.__update_subDAG(can_reach_node2, self.root_node)
                    else:
                        can_reach_node1[node1] = node2
                        self.__update_subDAG(can_reach_node1, self.root_node)

    def simplify(self):
        self.prune_redundant_branches()
        self.prune_emptyset_branches()
        self.prune_isomorphic_subtrees()
        self.prune_equal_children_node()

    ########################################################################
    # Internal implementation of set operations in quast representation
    ########################################################################

    def __negate_constraint(self, constraint):
        coefficients = constraint.get_coefficients_by_name()
        for var in coefficients.keys():
            coefficients[var] = coefficients[var].neg()

        negated_constraint = constraint.set_coefficients_by_name(coefficients)
        negated_constraint = negated_constraint.set_constant_val(negated_constraint.get_constant_val() - 1)
        return negated_constraint

    def __intersect(self, node1, node2, new_node2):
        if node1 is None:
            if node2.node_type is node2.IN_NODE:
                return self.in_node
            elif node2.node_type is node2.OUT_NODE:
                return self.out_node
            else:
                true_branch_node = self.__intersect(node1=node1, node2=node2.true_branch_node, new_node2=new_node2)
                false_branch_node = self.__intersect(node1=node1, node2=node2.false_branch_node, new_node2=new_node2)
                return Node(constraint=node2.constraint, false_branch_node=false_branch_node,
                            true_branch_node=true_branch_node)
        if node1.node_type is node1.IN_NODE:
            if new_node2[0] is None:
                new_node2[0] = self.__intersect(node1=None, node2=node2, new_node2=new_node2)
            return new_node2[0]
        elif node1.node_type is node1.OUT_NODE:
            return self.out_node
        else:
            true_branch_node = self.__intersect(node1=node1.true_branch_node, node2=node2, new_node2=new_node2)
            false_branch_node = self.__intersect(node1=node1.false_branch_node, node2=node2, new_node2=new_node2)
            return Node(constraint=node1.constraint, false_branch_node=false_branch_node,
                        true_branch_node=true_branch_node)

    def __complement(self, curr_node, complement_quast):
        if curr_node == self.in_node:
            return complement_quast.out_node
        elif curr_node == self.out_node:
            return complement_quast.in_node
        else:
            return Node(constraint=curr_node.constraint,
                        true_branch_node=self.__complement(curr_node.true_branch_node, complement_quast),
                        false_branch_node=self.__complement(curr_node.false_branch_node, complement_quast))

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
        elif curr_node.true_branch_node is curr_node.false_branch_node:
            return self.__reconstruct_set(curr_node.true_branch_node, curr_constraints)
        else:
            curr_constraints.append(curr_node.constraint)
            bsets_from_true = self.__reconstruct_set(curr_node.true_branch_node, curr_constraints)
            curr_constraints.pop()
            curr_constraints.append(self.__negate_constraint(curr_node.constraint))
            bsets_from_false = self.__reconstruct_set(curr_node.false_branch_node, curr_constraints)
            curr_constraints.pop()
            return bsets_from_true + bsets_from_false

    # Reference -- https://stackoverflow.com/questions/34012886/print-binary-tree-level-by-level-in-python
    # Description: Recursively prints QUAST level-by-level
    def __print_tree(self, node, level):
        if node is not None:
            self.__print_tree(node.true_branch_node, level + 1)
            print(' ' * 5 * level + '--->', node.constraint)
            self.__print_tree(node.false_branch_node, level + 1)

    def __union(self, node1, node2, new_node2):
        if node1 is None:
            if node2.node_type is node2.IN_NODE:
                return self.in_node
            elif node2.node_type is node2.OUT_NODE:
                return self.out_node
            else:
                true_branch_node = self.__union(node1=node1, node2=node2.true_branch_node, new_node2=new_node2)
                false_branch_node = self.__union(node1=node1, node2=node2.false_branch_node, new_node2=new_node2)
                return Node(constraint=node2.constraint, false_branch_node=false_branch_node,
                            true_branch_node=true_branch_node)
        if node1.node_type is node1.IN_NODE:
            return self.in_node
        elif node1.node_type is node1.OUT_NODE:
            if new_node2[0] is None:
                new_node2[0] = self.__union(node1=None, node2=node2, new_node2=new_node2)
            return new_node2[0]
        else:
            true_branch_node = self.__union(node1=node1.true_branch_node, node2=node2, new_node2=new_node2)
            false_branch_node = self.__union(node1=node1.false_branch_node, node2=node2, new_node2=new_node2)
            return Node(constraint=node1.constraint, false_branch_node=false_branch_node,
                        true_branch_node=true_branch_node)

    def __visualize_tree(self, arcs, node):
        if node.is_terminal():
            return
        else:
            true_branch_arc = (node, node.true_branch_node, "T")
            false_branch_arc = (node, node.false_branch_node, "F")
            arcs.add(true_branch_arc)
            arcs.add(false_branch_arc)
            self.__visualize_tree(arcs, node.true_branch_node)
            self.__visualize_tree(arcs, node.false_branch_node)

    def __get_visualization_label(self, constraint):
        return str(constraint).split(":")[-1].split("}")[0]

    def __extend_space(self, curr_node, extended_space_quast, old_to_new_ids_map):
        # Todo -- complete
        if curr_node is self.in_node:
            return extended_space_quast.in_node
        elif curr_node is self.out_node:
            return extended_space_quast.out_node
        else:
            new_space = extended_space_quast.get_space()
            old_constraint = curr_node.constraint
            old_id_dict = old_constraint.get_space().get_id_dict()

            new_name_to_coeff_map = {}
            for old_id in old_id_dict:
                # get the coefficient from old constraint
                (old_type, old_pos) = old_id_dict[old_id]
                coeff = old_constraint.get_coefficient_val(type=old_type, pos=old_pos)

                # get the name of new dimension corresponding to old dimension
                new_id = old_to_new_ids_map[old_id]
                new_dim_name = new_id.get_name()

                # add {name -> coefficient} to the coefficient dictionary
                new_name_to_coeff_map[new_dim_name] = coeff

            # set constant of new constraint as that of old constraint
            constant = old_constraint.get_constant_val()
            new_name_to_coeff_map[1] = constant

            # create new constraint and return new node
            new_constraint = isl.Constraint.ineq_from_names(new_space, new_name_to_coeff_map)
            new_true_branch_node = self.__extend_space(curr_node.true_branch_node, extended_space_quast, new_space,
                                                       old_to_new_ids_map)
            new_false_branch_node = self.__extend_space(curr_node.false_branch_node, extended_space_quast, new_space,
                                                        old_to_new_ids_map)
            return Node(constraint=new_constraint, true_branch_node=new_true_branch_node,
                        false_branch_node=new_false_branch_node)

    def __get_extended_space_and_map(self, extension_space):
        # Assumes that there are only islpy.dim_type.out type of dimensions.
        num_extension_out_dims = extension_space.get_space().dim(isl.dim_type.out)
        extended_space = self.get_space().add_dims(islpy.dim_type.out, num_extension_out_dims)
        old_ids1 = list(self.space.get_id_dict().keys())
        old_ids2 = list(extension_space.get_id_dict().keys())
        var_name = old_ids1[0].get_name()
        for pos in range(len(old_ids1) + len(old_ids2)):
            extended_space = extended_space.set_dim_id(isl.dim_type.out, pos, isl.Id(var_name + str(pos)))
        new_ids = list(extended_space.get_id_dict().keys())
        mapping = {}
        len_old_ids1 = len(old_ids1)
        for i in range(len(new_ids)):
            if i < len_old_ids1:
                mapping[old_ids1[i]] = new_ids[i]
            else:
                mapping[old_ids2[i - len_old_ids1]] = new_ids[i - len_old_ids1]
        return extended_space, mapping

    def __project_quast_into_extended_space(self, curr_node, extended_space, extended_space_quast, quast_in_extension_space=False):
        if curr_node.node_type is Node.IN_NODE:
            return extended_space_quast.in_node
        elif curr_node.node_type is Node.OUT_NODE:
            return extended_space_quast.out_node
        else:
            extended_true_branch = self.__project_quast_into_extended_space(curr_node.true_branch_node, extended_space,
                                                                            extended_space_quast, quast_in_extension_space)
            extended_false_branch = self.__project_quast_into_extended_space(curr_node.false_branch_node, extended_space,
                                                                            extended_space_quast, quast_in_extension_space)
            extended_node = Node(constraint=self.__project_constraint_into_extended_space(curr_node.constraint, extended_space, quast_in_extension_space),
                                 true_branch_node=extended_true_branch, false_branch_node=extended_false_branch)
            if curr_node is self.root_node:
                extended_space_quast.root_node = extended_node
            return extended_node

    def __get_extended_space(self, extension_space):
        num_new_dims = self.get_space().dim(isl.dim_type.out) + extension_space.dim(isl.dim_type.out)
        new_space = self.get_space().extend(0, 0, num_new_dims)
        for i in range(num_new_dims):
            new_space = new_space.set_dim_id(isl.dim_type.out, i, isl.Id("x" + str(i)))
        return new_space

    def __project_constraint_into_extended_space(self, constraint, extended_space, constraint_in_extension_space):
        new_constraint = isl.Constraint.ineq_from_names(extended_space, {})
        num_out_dims = constraint.get_space().dim(isl.dim_type.out)
        coefficients = [0]*num_out_dims if constraint_in_extension_space else []
        for i in range(num_out_dims):
            coefficients.append(constraint.get_coefficient_val(pos=i, type=isl.dim_type.out))
        new_constraint = new_constraint.set_coefficients(dim_tp=isl.dim_type.out, args=coefficients)
        new_constraint = new_constraint.set_constant_val(constraint.get_constant_val())
        return new_constraint

    ########################################################################
    # Internal implementation of quast optimization functions
    ########################################################################

    def __detect_and_prune_emptyset_branch(self, node, root_to_node_path, constraint_list):
        if node.is_terminal():
            return False
        elif self.__is_constraint_valid(node.constraint, constraint_list):
            root_to_node_path.append([node, False])
            self.__prune_branch(root_to_node_path, i=0)
            node = root_to_node_path.pop()[0]
            return True
        elif self.__is_constraint_valid(self.__negate_constraint(node.constraint), constraint_list):
            root_to_node_path.append([node, True])
            self.__prune_branch(root_to_node_path, i=0)
            node = root_to_node_path.pop()[0]
            return True
        constraint_list.append(node.constraint)
        root_to_node_path.append([node, True])
        modified = self.__detect_and_prune_emptyset_branch(node.true_branch_node, root_to_node_path, constraint_list)
        if modified:
            return True
        constraint_list.pop()
        node = root_to_node_path.pop()[0]
        constraint_list.append(self.__negate_constraint(node.constraint))
        root_to_node_path.append([node, False])
        modified = self.__detect_and_prune_emptyset_branch(node.false_branch_node, root_to_node_path, constraint_list)
        constraint_list.pop()
        node = root_to_node_path.pop()[0]
        return modified

    def __prune_branch(self, root_to_node_path, i=0):
        node, branch = root_to_node_path[i][0], root_to_node_path[i][1]
        if i == len(root_to_node_path) - 1:
            return node.false_branch_node if branch is True else node.true_branch_node
        else:
            new_true_branch_node = self.__prune_branch(root_to_node_path,
                                                       i + 1) if branch is True else node.true_branch_node
            new_false_branch_node = self.__prune_branch(root_to_node_path,
                                                        i + 1) if branch is False else node.false_branch_node
            new_node = Node(constraint=node.constraint, false_branch_node=new_false_branch_node,
                            true_branch_node=new_true_branch_node)
            if i == 0:
                self.root_node = new_node
            root_to_node_path[i] = [new_node, branch]
            return new_node

    def __prune_redundant_branches(self, node, root_to_node_path):
        if node.is_terminal():
            return
        for [vertex, branch] in root_to_node_path:
            if self.__are_nodes_equal(node, vertex):
                root_to_node_path.append([node, not branch])
                self.__prune_branch(root_to_node_path)
                node = root_to_node_path.pop()[0]
                self.__prune_redundant_branches(node.true_branch_node if branch else node.false_branch_node,
                                                root_to_node_path)
                return
            elif self.__are_nodes_equal(Node(constraint=self.__negate_constraint(node.constraint)), vertex):
                root_to_node_path.append([node, branch])
                self.__prune_branch(root_to_node_path)
                node = root_to_node_path.pop()[0]
                self.__prune_redundant_branches(node.false_branch_node if branch else node.true_branch_node,
                                                root_to_node_path)
                return
        root_to_node_path.append([node, True])
        self.__prune_redundant_branches(node.true_branch_node, root_to_node_path)
        node = root_to_node_path.pop()[0]
        root_to_node_path.append([node, False])
        self.__prune_redundant_branches(node.false_branch_node, root_to_node_path)
        node = root_to_node_path.pop()[0]

    def __prune_equal_children_node(self, curr_node):
        if curr_node.is_terminal():
            return None
        elif curr_node.true_branch_node is curr_node.false_branch_node:
            reachable_dict1 = self.__update_predecessors_of_same_child_node(target=curr_node,
                                                                            reachable_dict=self.__get_reachable_subDAG_as_dict(
                                                                                curr_node))
            reachable_dict2 = self.__prune_equal_children_node(curr_node.true_branch_node)
            return reachable_dict1 if reachable_dict2 is None else reachable_dict2
        else:
            reachable_dict = self.__prune_equal_children_node(curr_node=curr_node.true_branch_node)
            if reachable_dict is not None:
                curr_node = reachable_dict[curr_node]
            reachable_dict = self.__prune_equal_children_node(curr_node=curr_node.false_branch_node)
            if reachable_dict is not None:
                curr_node = reachable_dict[curr_node]
            if curr_node.true_branch_node is curr_node.false_branch_node:
                reachable_dict = self.prune_equal_children_node(curr_node)
            return reachable_dict

    def __are_subtrees_isomorphic(self, root1, root2, memo_table):
        if (root1, root2) in memo_table:
            return memo_table[(root1, root2)]
        elif (root2, root1) in memo_table:
            return memo_table[(root2, root1)]
        elif root1.is_terminal() or root2.is_terminal():
            return root1 is root2
        else:
            are_isomorphic = self.__are_nodes_equal(root1, root2) and self.__are_subtrees_isomorphic(
                root1.true_branch_node, root2.true_branch_node, memo_table) and self.__are_subtrees_isomorphic(
                root1.false_branch_node, root2.false_branch_node, memo_table)
            memo_table[(root1, root2)] = are_isomorphic
            memo_table[(root2, root1)] = are_isomorphic
            return are_isomorphic

    def __update_predecessors_of_same_child_node(self, reachable_dict, target):
        reachable_dict[target] = target.true_branch_node
        self.__update_subDAG(reachable_dict, self.root_node)
        reachable_dict.pop(target, None)
        return reachable_dict

    def __update_subDAG(self, old_to_new_nodes_dict, curr_node):
        if curr_node not in old_to_new_nodes_dict:
            return curr_node
        else:
            if old_to_new_nodes_dict[curr_node] is None:
                new_true_branch_node = self.__update_subDAG(old_to_new_nodes_dict,
                                                            curr_node.true_branch_node)
                new_false_branch_node = self.__update_subDAG(old_to_new_nodes_dict,
                                                             curr_node.false_branch_node)
                new_curr_node = Node(curr_node.constraint, false_branch_node=new_false_branch_node,
                                     true_branch_node=new_true_branch_node)
                old_to_new_nodes_dict[curr_node] = new_curr_node
            if curr_node is self.root_node:
                self.root_node = old_to_new_nodes_dict[curr_node]
            return old_to_new_nodes_dict[curr_node]

    def __get_reachable_subDAG_as_dict(self, target):
        reachable_dict = {}
        self.__add_reachable_subDAG_into_dict(target=target, curr_node=self.root_node, reachable_dict=reachable_dict)
        return reachable_dict

    ####################################################################
    # Internal helper functions
    ####################################################################

    def __get_parent_list(self, target, current=None):
        if current is None:
            current = self.root_node  # should only execute during the top level recursive call
        elif current is target:
            return []  # target can never be its own parent in future recursive calls as the Quast is a DAG

        is_current_parent = []
        if current.true_branch_node is target or current.false_branch_node is target:
            is_current_parent = [current]

        if current.true_branch_node is not None:
            parents_from_true_branch = self.__get_parent_list(target, current.true_branch_node)
        else:
            parents_from_true_branch = []

        if current.false_branch_node is not None:
            parents_from_false_branch = self.__get_parent_list(target, current.false_branch_node)
        else:
            parents_from_false_branch = []

        return parents_from_true_branch + parents_from_false_branch + is_current_parent

    def __is_constraint_valid(self, constraint, constraint_list):
        bset = isl.BasicSet.universe(self.get_space()).add_constraints(constraint_list)
        halfspace = isl.BasicSet.from_constraint(constraint)
        return bset.is_subset(halfspace)

    def __are_nodes_equal(self, node1, node2):
        constraint1 = node1.constraint
        constraint2 = node2.constraint
        return constraint1.get_space() == constraint2.get_space() and (
                constraint1.get_coefficients_by_name() == constraint2.get_coefficients_by_name())

    def __add_reachable_subDAG_into_dict(self, target, curr_node, reachable_dict):
        if curr_node is target:
            return True
        elif curr_node.is_terminal():
            return False
        else:
            is_true_reachable = self.__add_reachable_subDAG_into_dict(target, curr_node.true_branch_node,
                                                                      reachable_dict)
            is_false_reachable = self.__add_reachable_subDAG_into_dict(target, curr_node.false_branch_node,
                                                                       reachable_dict)
            if is_true_reachable or is_false_reachable:
                reachable_dict[curr_node] = None

    # Description: returns a set of all nodes in the current quast
    # Return: Python.set of Nodes
    def __get_node_set(self, node_set=None, curr_node=None):
        if node_set is None:
            node_set = set()
            curr_node = self.root_node
        if curr_node.is_terminal():
            return node_set
        node_set.add(curr_node)
        node_set = self.__get_node_set(node_set=node_set, curr_node=curr_node.true_branch_node)
        node_set = self.__get_node_set(node_set=node_set, curr_node=curr_node.false_branch_node)
        return node_set


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

