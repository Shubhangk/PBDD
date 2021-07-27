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
        num_nodes:  Number of nodes in the Quast
    """

    def __init__(self, set_=None, space=None, in_node=None, out_node=None):
        self.num_nodes = 0

        # initialize when isl.Set is provided
        if set_ is not None:

            # normal quast construction. This is much faster than below, but does not simplify the final quast.
            T = None
            for basic_set in set_.get_basic_sets():
                bquast = BasicQuast(basic_set)
                if T is None:
                    T = bquast
                else:
                    T = bquast.union(T)
                    #T.prune_emptyset_branches()

            # # merge-sort-like round-based initialization with quast simplification. This is a slower quast construction,
            # # but simplifies the final quast heavily
            # quast_list = [BasicQuast(bset) for bset in set_.get_basic_sets()]
            # new_quast_list = []
            # offset = len(quast_list) % 2
            # while len(quast_list) > 1:
            #     for i in range(0, len(quast_list) - offset, 2):
            #         new_quast_list.append(quast_list[i].union(quast_list[i + 1]))
            #         new_quast_list[-1].simplify()
            #     if offset == 1:
            #         new_quast_list.append(quast_list[-1])
            #     offset = len(quast_list) % 2
            #     quast_list = new_quast_list
            #     new_quast_list = []
            # T = quast_list[0]

            # # Hybrid construction approach
            # quast_list = [BasicQuast(bset) for bset in set_.get_basic_sets()]
            # new_quast_list = []
            # offset = len(quast_list) % 2
            # rounds = 0
            # while len(quast_list) > 1 and rounds < 4:
            #     for i in range(0, len(quast_list) - offset, 2):
            #         new_quast_list.append(quast_list[i].union(quast_list[i + 1]))
            #         new_quast_list[-1].simplify()
            #     if offset == 1:
            #         new_quast_list.append(quast_list[-1])
            #     offset = len(quast_list) % 2
            #     quast_list = new_quast_list
            #     new_quast_list = []
            #     rounds = rounds + 1
            # T = quast_list[0]
            # if len(quast_list) != 1:
            #     for quast in quast_list:
            #         T = quast.union(T)

            self.update_num_nodes(T.get_tree_size())
            self.root_node = T.root_node
            self.in_node = T.in_node
            self.out_node = T.out_node
            self.set_space(T.get_space())
        # initialize when isl.Set is not provided (also from super.__init__() call from BasicQuast)
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

    def get_tree_size(self):
        return self.num_nodes

    def set_tree_size(self, tree_size):
        self.num_nodes = tree_size

    def compute_tree_size(self):
        return len(self.__get_node_set())

    def increment_tree_size(self):
        self.num_nodes = self.num_nodes + 1

    def __decrement_tree_size(self):
        self.num_nodes = self.num_nodes - 1

    def update_num_nodes(self, num_additions):
        self.num_nodes = self.num_nodes + num_additions

    ####################################
    # Quast API for set operations
    ####################################

    def union(self, quast):
        if self.get_space() != quast.get_space():
            raise Exception("spaces don't match")
        union_quast = Quast(space=quast.get_space(), in_node=quast.in_node, out_node=quast.out_node)
        memo = {self.in_node: union_quast.in_node, self.out_node: quast.root_node}
        union_quast.root_node = self.__union(self.root_node, memo)
        union_quast.set_tree_size(self.get_tree_size() + quast.get_tree_size())
        return union_quast

    def intersect(self, quast):
        # if self.get_space() != quast.get_space():
        #     raise Exception("spaces don't match")
        intersection_quast = Quast(space=self.get_space(), in_node=quast.in_node, out_node=quast.out_node)
        memo = {self.in_node: quast.root_node, self.out_node: intersection_quast.out_node}
        intersection_quast.root_node = self.__intersect(self.root_node, memo)
        intersection_quast.set_tree_size(self.get_tree_size() + quast.get_tree_size())
        return intersection_quast

    def reconstruct_set(self):
        memo = {}
        return self.__reconstruct_set(self.root_node, memo)

    def __reconstruct_set(self, curr_node, memo):
        # quast is a single node
        if curr_node is self.in_node:
            return isl.BasicSet.universe(self.get_space())
        elif curr_node is self.out_node:
            return isl.BasicSet.empty(self.get_space())
        # current node has already been memoized
        elif curr_node in memo:
            return memo[curr_node]
        # else compute memoization and memoize
        else:
            # true_branch_set = None
            # false_branch_set = None
            if curr_node.true_branch_node is self.in_node:
                true_branch_set = curr_node.bset
            elif curr_node.true_branch_node is self.out_node:
                true_branch_set = isl.BasicSet.empty(self.get_space())
            else:
                true_branch_set = curr_node.bset.intersect(self.__reconstruct_set(curr_node.true_branch_node, memo))

            if curr_node.false_branch_node is self.in_node:
                false_branch_set = self.__negate_bset(curr_node.bset)
            elif curr_node.false_branch_node is self.out_node:
                false_branch_set = isl.BasicSet.empty(self.get_space())
            else:
                false_branch_set = self.__negate_bset(curr_node.bset).intersect(self.__reconstruct_set(curr_node.false_branch_node, memo))

            curr_node_set = true_branch_set.union(false_branch_set)
            memo[curr_node] = curr_node_set
            return curr_node_set

    def complement(self):
        complement_quast = Quast(space=self.get_space(), in_node=self.out_node, out_node=self.in_node)
        complement_quast.root_node = self.root_node
        return complement_quast

    def visualize_tree(self, output_filename='quast'):
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
        #print(dot.source)
        dot.render('visualization-output/'+output_filename, view=True)

    def is_empty(self):
        memo = {self.in_node: isl.BasicSet.universe(self.get_space()), self.out_node: isl.BasicSet.empty(self.get_space())}
        is_empty, set_ = self.__is_empty(self.root_node, isl.BasicSet.universe(self.get_space()), memo)
        return is_empty

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

    def subtract(self, quast):
        return self.intersect(quast.complement())

    ########################################################################
    # Internal implementation of set operations in quast representation
    ########################################################################

    def __is_empty(self, curr_node, root_to_node_path_bset, memo):
        if curr_node in memo:
            curr_path_set = root_to_node_path_bset.intersect(memo[curr_node])
            return curr_path_set.is_empty(), memo[curr_node]
        elif root_to_node_path_bset.is_empty():
            return True, isl.BasicSet.universe(self.get_space())
        else:
            true_root_to_node_path_bset = root_to_node_path_bset.intersect(curr_node.bset)
            is_true_branch_empty, true_branch_set = self.__is_empty(curr_node.true_branch_node, true_root_to_node_path_bset, memo)
            if not is_true_branch_empty:
                return False, true_branch_set
            false_root_to_node_path_bset = root_to_node_path_bset.intersect(self.__negate_bset(curr_node.bset))
            is_false_branch_empty, false_branch_set = self.__is_empty(curr_node.false_branch_node, false_root_to_node_path_bset, memo)
            if not is_false_branch_empty:
                return False, false_branch_set
            subtree_set = curr_node.bset.intersect(true_branch_set).union(self.__negate_bset(curr_node.bset).intersect(false_branch_set))
            memo[curr_node] = subtree_set
            return True, subtree_set

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

    def __intersect(self, curr_node, memo):
        if curr_node in memo:
            return memo[curr_node]
        true_branch_node = self.__intersect(curr_node.true_branch_node, memo)
        false_branch_node = self.__intersect(curr_node.false_branch_node, memo)
        bset = curr_node.bset
        new_node = Node(bset=bset, false_branch_node=false_branch_node, true_branch_node=true_branch_node)
        memo[curr_node] = new_node
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

    def __negate_bset(self, bset):
        return bset.complement()

    def __visualize_tree(self, arcs, node):
        if node.is_terminal():
            return
        else:
            true_branch_arc = (node, node.true_branch_node, "T")
            if true_branch_arc not in arcs:
                arcs.add(true_branch_arc)
                self.__visualize_tree(arcs, node.true_branch_node)

            false_branch_arc = (node, node.false_branch_node, "F")
            if false_branch_arc not in arcs:
                arcs.add(false_branch_arc)
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
        self.root_node, _ = self.__prune_redundant_branches(node=self.root_node, ancestors={})

    def prune_emptyset_branches(self):
        self.root_node, _ = self.__prune_emptyset_branches(self.root_node, isl.Set.universe(self.get_space()))

    def prune_equal_children_nodes(self):
        self.root_node, _ = self.__prune_equal_children_nodes(node=self.root_node, new_nodes_map={})

    def prune_isomorphic_subtrees(self):
        MAX_MODIFICATIONS = 10
        num_modifications = 0
        modified = True
        while modified and num_modifications < MAX_MODIFICATIONS:
            modified = self.__detect_and_prune_isomorphic_subtrees()
            num_modifications = num_modifications + 1

    def simplify(self):
        #self.prune_redundant_branches()
        self.prune_emptyset_branches()
        self.prune_isomorphic_subtrees()
        #self.prune_equal_children_node()

    ########################################################################
    # Internal implementation of quast optimization functions
    ########################################################################

    # ancestors: maps set to true/false to indicate which branch was taken
    def __prune_redundant_branches(self, node, ancestors):
        if node.is_terminal():
            return node, False

        is_first_occurrence = node.bset not in ancestors
        if is_first_occurrence:
            ancestors[node.bset] = True
        new_true_branch_node, is_true_modified = self.__prune_redundant_branches(node.true_branch_node, ancestors)
        if is_first_occurrence:
            ancestors[node.bset] = False
        new_false_branch_node, is_false_modified = self.__prune_redundant_branches(node.false_branch_node,
                                                                                   ancestors)
        branch = ancestors[node.bset]
        if is_first_occurrence:
            del ancestors[node.bset]

        if not is_first_occurrence and node.bset in ancestors:
            return (new_true_branch_node if branch else new_false_branch_node), True
        elif not is_first_occurrence and self.__negate_bset(node.bset) in ancestors:
            return (new_false_branch_node if branch else new_true_branch_node), True
        elif not is_false_modified and not is_true_modified:
            return node, False
        else:
            return Node(bset=node.bset, false_branch_node=new_false_branch_node,
                        true_branch_node=new_true_branch_node), True

    def __prune_emptyset_branches(self, node, root_to_node_set):
        if node.is_terminal():
            return node, False

        root_to_true_node_set = root_to_node_set.intersect(node.bset)
        root_to_false_node_set = root_to_node_set.intersect(self.__negate_bset(node.bset))

        if root_to_true_node_set.is_empty():
            new_false_branch_node, is_false_modified = self.__prune_emptyset_branches(node.false_branch_node,
                                                                                      root_to_false_node_set)
            return new_false_branch_node, True
        elif root_to_false_node_set.is_empty():
            new_true_branch_node, is_true_modified = self.__prune_emptyset_branches(node.true_branch_node,
                                                                                    root_to_true_node_set)
            return new_true_branch_node, True
        else:
            new_false_branch_node, is_false_modified = self.__prune_emptyset_branches(node.false_branch_node,
                                                                                      root_to_false_node_set)
            new_true_branch_node, is_true_modified = self.__prune_emptyset_branches(node.true_branch_node,
                                                                                    root_to_true_node_set)
            if is_false_modified or is_true_modified:
                return Node(bset=node.bset, true_branch_node=new_true_branch_node, false_branch_node=new_false_branch_node), True
            else:
                return node, False

    def __prune_equal_children_nodes(self, node, new_nodes_map):
        if node.is_terminal():
            return node, False
        elif node in new_nodes_map:
            return new_nodes_map[node], new_nodes_map[node] is node
        elif node.true_branch_node is node.false_branch_node:
            next_node, is_subtree_modified = self.__prune_equal_children_nodes(node.true_branch_node, new_nodes_map)
            return next_node, True
        else:
            new_true_branch_node, is_true_branch_modified = self.__prune_equal_children_nodes(node.true_branch_node,
                                                                                              new_nodes_map)
            new_false_branch_node, is_false_branch_modified = self.__prune_equal_children_nodes(node.false_branch_node,
                                                                                                new_nodes_map)
            if is_true_branch_modified or is_false_branch_modified:
                new_node = Node(bset=node.bset, true_branch_node=new_true_branch_node, false_branch_node=new_false_branch_node)
                new_nodes_map[node] = new_node
                return new_node, True
            else:
                new_nodes_map[node] = node
                return node, False

    def __is_constraint_valid(self, bset, constraint_list):
        basic_set = isl.BasicSet.universe(self.get_space())
        for constraint in constraint_list:
            basic_set = basic_set.intersect(constraint)
        return basic_set.is_subset(bset)

    def __detect_and_prune_isomorphic_subtrees(self):
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
                    return True
        return False

    def __are_subtrees_isomorphic(self, root1, root2, memo_table):
        if not self.__are_nodes_equal(root1, root2):
            return False
        elif (root1, root2) in memo_table:
            return memo_table[(root1, root2)]
        elif (root2, root1) in memo_table:
            return memo_table[(root2, root1)]
        elif root1.is_terminal() or root2.is_terminal():
            return root1 is root2
        else:
            are_isomorphic = self.__are_subtrees_isomorphic(
                root1.true_branch_node, root2.true_branch_node, memo_table) and self.__are_subtrees_isomorphic(
                root1.false_branch_node, root2.false_branch_node, memo_table)
            memo_table[(root1, root2)] = are_isomorphic
            memo_table[(root2, root1)] = are_isomorphic
            return are_isomorphic

    def __are_nodes_equal(self, node1, node2):
        return node1.node_type == node2.node_type and node1.bset == node2.bset

    # Description: returns a set of all nodes in the current quast
    # Return: Python.set of Nodes
    def __get_node_set(self, node_set=None, curr_node=None):
        if node_set is None:
            node_set = set()
            curr_node = self.root_node
        if curr_node in node_set:
            return
        elif curr_node.is_terminal():
            node_set.add(curr_node)
        else:
            node_set.add(curr_node)
            self.__get_node_set(node_set=node_set, curr_node=curr_node.true_branch_node)
            self.__get_node_set(node_set=node_set, curr_node=curr_node.false_branch_node)
        if curr_node is self.root_node:
            return node_set


class BasicQuast(Quast):

    def __init__(self, bset=None, space=None):
        space = bset.get_space() if bset is not None else space
        super().__init__(set_=None, space=space)

        # construct tree from bset
        if bset is not None:
            next_true_branch_node = self.in_node
            constraints_as_bsets = [isl.Set.from_basic_set(isl.BasicSet.from_constraint(constraint)) for constraint in bset.get_constraints()]
            for bset_constraint in constraints_as_bsets:
                node = Node(bset=bset_constraint, false_branch_node=self.out_node, true_branch_node=next_true_branch_node)
                next_true_branch_node = node
            self.update_num_nodes(len(constraints_as_bsets))
            self.root_node = next_true_branch_node
