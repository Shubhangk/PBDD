import islpy as isl
from graphviz import Digraph
from V2.Node import *


class Quast:
    """
    Quasi-Affine solution tree representation of islpy.Sets. Each Quast instance has the following variable attributes
        in_node:    Terminal node indicating containment inside underlying islpy.Set
        out_node:   Terminal node indicating non-containment inside underlying islpy.Set
        space:      islpy.Space that the underlying islpy.Set lives in
        root_node:  Root node of the Quast
    """

    def __init__(self, set_=None, space=None, in_node=None, out_node=None):
        if set_ is not None:
            T = None
            for basic_set in set_.get_basic_sets():
                if T is None:
                    T = BasicQuast(basic_set)
                else:
                    T = T.union(BasicQuast(basic_set))
                # T.simplify()
            self.root_node = T.root_node
            self.in_node = T.in_node
            self.out_node = T.out_node
            self.set_space(T.get_space())
        else:
            if space is None:
                raise Exception("Cannot initialize Quast with Space None")
            self.in_node = Node(bset="TERMINAL", node_type=Node.TERMINAL) if in_node is None else in_node
            self.out_node = Node(bset="TERMINAL", node_type=Node.TERMINAL) if out_node is None else out_node
            self.set_space(space)
            self.root_node = None

    ################################################################
    # Data structure specific functions
    ################################################################

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
        union_quast = Quast(space=quast.get_space(), in_node=quast.in_node, out_node=quast.out_node)
        memo = {self.in_node: union_quast.in_node, self.out_node: quast.root_node}
        union_quast.root_node = self.__union(self.root_node, memo)
        # quast1 = self
        # quast2 = quast
        # self.__union(quast1, quast2, self.root_node, union_quast)
        return union_quast

    def intersect(self, quast):
        if self.get_space() != quast.get_space():
            raise Exception("spaces don't match")
        intersection_quast = Quast(space=self.get_space(), in_node=quast.in_node, out_node=quast.out_node)
        quast1 = self
        quast2 = quast
        self.__intersect(quast1, quast2, self.root_node, intersection_quast)
        return intersection_quast

    def reconstruct_set(self):
        basic_set_list = self.__reconstruct_set(self.root_node, [])
        final_set = basic_set_list[0] if len(basic_set_list) > 0 else isl.BasicSet.empty(self.get_space())
        for basic_set in basic_set_list:
            final_set = final_set.union(basic_set)
        return final_set

    def complement(self):
        complement_quast = Quast(space=self.get_space(), in_node=self.out_node, out_node=self.in_node)
        complement_quast.root_node = self.root_node
        return complement_quast

    def visualize_tree(self):
        dot = Digraph(format="pdf", comment='Quast Visualization')
        arcs = set()
        self.__visualize_tree(arcs, self.root_node)
        nodes = set()
        for arc in arcs:
            if arc[0] not in nodes:
                dot.node(str(id(arc[0])), self.__get_visualization_label(arc[0]))
            if arc[1] not in nodes:
                dot.node(str(id(arc[1])), self.__get_visualization_label(arc[1]))
            dot.edge(str(id(arc[0])), str(id(arc[1])), label=arc[2])
        if arcs == set():
            dot.node('root', self.root_node.bset)
        print(dot.source)
        dot.render('visualization-output/quast', view=True)

    def is_empty(self):
        return self.__is_empty(self.root_node, isl.BasicSet.universe(self.get_space()))

    def is_subset(self, quast):
        return self.intersect(quast.complement()).is_empty()

    def is_equal(self, quast):
        return self.reconstruct_set() == quast.reconstruct_set()

    def apply(self, bmap):
        mapped_quast = Quast(space=bmap.range().get_space())
        self.__apply(self.root_node, mapped_quast, bmap)
        return mapped_quast

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

    def add_dims(self, n):
        dim_names = [("x" + str(i)) for i in range(n)]
        extension_space = isl.Space.create_from_names(isl.DEFAULT_CONTEXT, set=dim_names)
        extended_space = self.__get_extended_space(extension_space)
        extended_space_quast = Quast(space=extended_space)
        self.__project_quast_into_extended_space(self.root_node, extended_space, extended_space_quast)
        return extended_space_quast

    def project_out(self, dim_type, first, n, ):
        T = self.__get_tree_expansion()
        project_out_quast = Quast(space=T.get_space())
        root_to_node_path = []
        self.__project_out(T, T.root_node, project_out_quast, root_to_node_path, dim_type, first, n)
        return project_out_quast

    ########################################################################
    # Internal implementation of set operations in quast representation
    ########################################################################

    def __is_empty(self, curr_node, root_to_node_path_bset):
        if curr_node is self.in_node:
            return root_to_node_path_bset.is_empty()
        elif curr_node is self.out_node:
            return True
        elif root_to_node_path_bset.plain_is_empty():
            return True
        else:
            true_root_to_node_path_bset = root_to_node_path_bset.intersect(curr_node.bset)
            is_true_branch_empty = self.__is_empty(curr_node.true_branch_node, true_root_to_node_path_bset)
            if not is_true_branch_empty:
                return False
            false_root_to_node_path_bset = root_to_node_path_bset.intersect(self.__negate_bset(curr_node.bset))
            is_false_branch_empty = self.__is_empty(curr_node.false_branch_node, false_root_to_node_path_bset)
            return is_false_branch_empty

    def __project_out(self, tree_expansion, curr_node, project_out_quast, root_to_node_path, dim_type, first, n):
        if curr_node is tree_expansion.in_node:
            return project_out_quast.in_node
        elif curr_node is tree_expansion.out_node:
            return project_out_quast.out_node
        else:
            path_constraint = isl.BasicSet.universe(self.get_space())
            for bset in root_to_node_path:
                path_constraint = path_constraint.intersect(bset)
            curr_constraint = curr_node.bset.intersect(path_constraint)
            new_constraint = curr_constraint.project_out(dim_type, first, n).gist(
                path_constraint.project_out(dim_type, first, n))

            if new_constraint == isl.BasicSet.universe(new_constraint.get_space()):
                root_to_node_path.append(curr_constraint)
                new_true_branch = self.__project_out(tree_expansion, curr_node.true_branch_node, project_out_quast,
                                                     root_to_node_path, dim_type, first, n)
                root_to_node_path.pop()
                if curr_node is tree_expansion.root_node:
                    project_out_quast.root_node = new_true_branch
                    project_out_quast.set_space(new_constraint.get_space())
                return new_true_branch
            elif new_constraint.is_empty():
                root_to_node_path.append(curr_constraint.complement())
                new_false_branch = self.__project_out(tree_expansion, curr_node.false_branch_node, project_out_quast,
                                                      root_to_node_path, dim_type, first, n)
                root_to_node_path.pop()
                if curr_node is tree_expansion.root_node:
                    project_out_quast.root_node = new_false_branch
                    project_out_quast.set_space(new_constraint.get_space())
                return new_false_branch
            else:
                root_to_node_path.append(curr_constraint)
                new_true_branch = self.__project_out(tree_expansion, curr_node.true_branch_node, project_out_quast,
                                                     root_to_node_path, dim_type, first, n)
                root_to_node_path.pop()
                root_to_node_path.append(curr_constraint.complement())
                new_false_branch = self.__project_out(tree_expansion, curr_node.false_branch_node, project_out_quast,
                                                      root_to_node_path, dim_type, first, n)
                root_to_node_path.pop()
                new_node = Node(new_constraint, true_branch_node=new_true_branch, false_branch_node=new_false_branch)
                if curr_node is tree_expansion.root_node:
                    project_out_quast.root_node = new_node
                    project_out_quast.set_space(new_constraint.get_space())
                return new_node

    def __apply(self, curr_node, mapped_quast, bmap):
        if curr_node is self.in_node:
            return mapped_quast.in_node
        elif curr_node is self.out_node:
            return mapped_quast.out_node
        else:
            new_true_branch = self.__apply(curr_node.true_branch_node, mapped_quast, bmap)
            new_false_branch = self.__apply(curr_node.false_branch_node, mapped_quast, bmap)
            space = curr_node.bset.get_space()
            bset = isl.BasicSet.universe(space).intersect(curr_node.bset)
            new_bset = bset.apply(bmap)
            new_node = Node(bset=new_bset, false_branch_node=new_false_branch,
                            true_branch_node=new_true_branch)
            if curr_node is self.root_node:
                mapped_quast.root_node = new_node
            return new_node

    def __intersect(self, quast1, quast2, quast1_curr_node, intersection_quast):
        if quast1_curr_node is quast1.in_node:
            return quast2.root_node
        elif quast1_curr_node is quast1.out_node:
            return intersection_quast.out_node
        else:
            true_branch_node = self.__intersect(quast1, quast2, quast1_curr_node.true_branch_node, intersection_quast)
            false_branch_node = self.__intersect(quast1, quast2, quast1_curr_node.false_branch_node, intersection_quast)
            bset = quast1_curr_node.bset
            new_node = Node(bset=bset, false_branch_node=false_branch_node, true_branch_node=true_branch_node)
            if quast1_curr_node is quast1.root_node:
                intersection_quast.root_node = new_node
            return new_node

    def __union(self, curr_node, memo):
        if curr_node in memo:
            return memo[curr_node]
        true_branch_node = self.__union(curr_node.true_branch_node, memo)
        false_branch_node = self.__union(curr_node.false_branch_node, memo)
        bset = curr_node.bset
        new_node = Node(bset=bset, false_branch_node=false_branch_node, true_branch_node=true_branch_node)
        memo[curr_node] = new_node
        return new_node


    def __reconstruct_set(self, curr_node, curr_constraints):
        if curr_node is self.out_node:
            return []
        elif curr_node is self.in_node:
            bset = isl.BasicSet.universe(self.get_space())
            for constraint in curr_constraints:
                bset = bset.intersect(constraint)
            if bset.is_empty():
                return []
            else:
                return [bset]
        elif curr_node.true_branch_node is curr_node.false_branch_node:
            return self.__reconstruct_set(curr_node.true_branch_node, curr_constraints)
        else:
            curr_constraints.append(curr_node.bset)
            bsets_from_true = self.__reconstruct_set(curr_node.true_branch_node, curr_constraints)
            curr_constraints.pop()
            curr_constraints.append(self.__negate_bset(curr_node.bset))
            bsets_from_false = self.__reconstruct_set(curr_node.false_branch_node, curr_constraints)
            curr_constraints.pop()
            return bsets_from_true + bsets_from_false

    def __negate_bset(self, bset):
        return bset.complement()

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

    def __get_visualization_label(self, node):
        if not node.is_terminal():
            bset = node.bset
            return str(bset).split(":")[-1].split("}")[0]
        elif node is self.in_node:
            return "IN"
        else:
            return "OUT"

    def __get_extended_space(self, extension_space):
        num_new_dims = self.get_space().dim(isl.dim_type.out) + extension_space.dim(isl.dim_type.out)
        new_space = self.get_space().extend(0, 0, num_new_dims)
        for i in range(num_new_dims):
            new_space = new_space.set_dim_id(isl.dim_type.out, i, isl.Id("x" + str(i)))
        return new_space

    def __project_constraint_into_extended_space(self, constraint, extended_space, constraint_in_extension_space):
        new_constraint = isl.Constraint.ineq_from_names(extended_space, {})
        num_out_dims = constraint.get_space().dim(isl.dim_type.out)
        coefficients = [0] * num_out_dims if constraint_in_extension_space else []
        for i in range(num_out_dims):
            coefficients.append(constraint.get_coefficient_val(pos=i, type=isl.dim_type.out))
        new_constraint = new_constraint.set_coefficients(dim_tp=isl.dim_type.out, args=coefficients)
        new_constraint = new_constraint.set_constant_val(constraint.get_constant_val())
        return new_constraint

    def __project_quast_into_extended_space(self, curr_node, extended_space, extended_space_quast,
                                            quast_in_extension_space=False):
        if curr_node is self.in_node:
            return extended_space_quast.in_node
        elif curr_node is self.out_node:
            return extended_space_quast.out_node
        else:
            extended_true_branch = self.__project_quast_into_extended_space(curr_node.true_branch_node, extended_space,
                                                                            extended_space_quast,
                                                                            quast_in_extension_space)
            extended_false_branch = self.__project_quast_into_extended_space(curr_node.false_branch_node,
                                                                             extended_space,
                                                                             extended_space_quast,
                                                                             quast_in_extension_space)
            extended_bset = isl.BasicSet.universe(extended_space)
            for constraint in curr_node.bset.get_constraints():
                extended_bset = extended_bset.add_constraint(
                    self.__project_constraint_into_extended_space(constraint, extended_space,
                                                                  quast_in_extension_space))
            extended_node = Node(bset=extended_bset, true_branch_node=extended_true_branch,
                                 false_branch_node=extended_false_branch)
            if curr_node is self.root_node:
                extended_space_quast.root_node = extended_node
            return extended_node

    def __get_tree_expansion(self):
        expansion_quast = Quast(space=self.get_space())
        self.__expand_quast_into_tree(self.root_node, expansion_quast)
        return expansion_quast

    def __expand_quast_into_tree(self, curr_node, expansion_quast):
        if curr_node is self.in_node:
            return expansion_quast.in_node
        elif curr_node is self.out_node:
            return expansion_quast.out_node
        else:
            expanded_true_branch_node = self.__expand_quast_into_tree(curr_node.true_branch_node, expansion_quast)
            expanded_false_branch_node = self.__expand_quast_into_tree(curr_node.false_branch_node, expansion_quast)
            new_node = Node(bset=curr_node.bset, true_branch_node=expanded_true_branch_node,
                            false_branch_node=expanded_false_branch_node)
            if curr_node is self.root_node:
                expansion_quast.root_node = new_node
            return new_node

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
            num_modifications = num_modifications + 1

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
    # Internal implementation of quast optimization functions
    ########################################################################

    def __is_constraint_valid(self, bset, constraint_list):
        basic_set = isl.BasicSet.universe(self.get_space())
        for constraint in constraint_list:
            basic_set = basic_set.intersect(constraint)
        return basic_set.is_subset(bset)

    def __detect_and_prune_emptyset_branch(self, node, root_to_node_path, constraint_list):
        if node.is_terminal():
            return False
        elif self.__is_constraint_valid(node.bset, constraint_list):
            root_to_node_path.append([node, False])
            self.__prune_branch(root_to_node_path, i=0)
            node = root_to_node_path.pop()[0]
            return True
        elif self.__is_constraint_valid(self.__negate_bset(node.bset), constraint_list):
            root_to_node_path.append([node, True])
            self.__prune_branch(root_to_node_path, i=0)
            node = root_to_node_path.pop()[0]
            return True
        constraint_list.append(node.bset)
        root_to_node_path.append([node, True])
        modified = self.__detect_and_prune_emptyset_branch(node.true_branch_node, root_to_node_path, constraint_list)
        if modified:
            return True
        constraint_list.pop()
        node = root_to_node_path.pop()[0]
        constraint_list.append(self.__negate_bset(node.bset))
        root_to_node_path.append([node, False])
        modified = self.__detect_and_prune_emptyset_branch(node.false_branch_node, root_to_node_path, constraint_list)
        constraint_list.pop()
        node = root_to_node_path.pop()[0]
        return modified

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
            elif self.__are_nodes_equal(Node(bset=self.__negate_bset(node.bset)), vertex):
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

    def __prune_branch(self, root_to_node_path, i=0):
        node, branch = root_to_node_path[i][0], root_to_node_path[i][1]
        if i == len(root_to_node_path) - 1:
            return node.false_branch_node if branch is True else node.true_branch_node
        else:
            new_true_branch_node = self.__prune_branch(root_to_node_path,
                                                       i + 1) if branch is True else node.true_branch_node
            new_false_branch_node = self.__prune_branch(root_to_node_path,
                                                        i + 1) if branch is False else node.false_branch_node
            new_node = Node(bset=node.bset, false_branch_node=new_false_branch_node,
                            true_branch_node=new_true_branch_node)
            if i == 0:
                self.root_node = new_node
            root_to_node_path[i] = [new_node, branch]
            return new_node

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
                new_curr_node = Node(curr_node.bset, false_branch_node=new_false_branch_node,
                                     true_branch_node=new_true_branch_node)
                old_to_new_nodes_dict[curr_node] = new_curr_node
            if curr_node is self.root_node:
                self.root_node = old_to_new_nodes_dict[curr_node]
            return old_to_new_nodes_dict[curr_node]

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

    def __get_reachable_subDAG_as_dict(self, target):
        reachable_dict = {}
        self.__add_reachable_subDAG_into_dict(target=target, curr_node=self.root_node, reachable_dict=reachable_dict)
        return reachable_dict

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
                reachable_dict = self.__prune_equal_children_node(curr_node)
            return reachable_dict

    def __are_nodes_equal(self, node1, node2):
        return node1.bset == node2.bset

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
        self.in_node = Node(bset="TERMINAL", node_type=Node.TERMINAL)
        self.out_node = Node(bset="TERMINAL", node_type=Node.TERMINAL)
        self.root_node = None
        self.space = None

        if basic_set is not None:
            constraints = [isl.BasicSet.from_constraint(constraint) for constraint in basic_set.get_constraints()]
            if len(constraints) is not 0:
                self.root_node = Node(bset=constraints[0], false_branch_node=self.out_node,
                                      true_branch_node=self.__add_node(constraints=constraints, i=1))
                self.space = self.root_node.bset.get_space()

    def __add_node(self, constraints, i):
        if i is len(constraints):
            return self.in_node
        else:
            return Node(bset=constraints[i], false_branch_node=self.out_node,
                        true_branch_node=self.__add_node(constraints=constraints, i=i + 1))
