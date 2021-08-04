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
            T = None
            for basic_set in set_.get_basic_sets():
                bquast = BasicQuast(basic_set)
                if T is None:
                    T = bquast
                else:
                    T = bquast.union(T)
            self.update_num_nodes(T.get_tree_size())
            self.root_node = T.root_node
            self.in_node = T.in_node
            self.out_node = T.out_node
            self.set_space(T.get_space())
        # initialize when isl.Set is not provided (also by super.__init__() call from BasicQuast)
        else:
            if space is None:
                raise Exception("Cannot initialize Quast with Space None")
            self.in_node = Node(bset="TERMINAL", node_type=Node.TERMINAL) if in_node is None else in_node
            self.out_node = Node(bset="TERMINAL", node_type=Node.TERMINAL) if out_node is None else out_node
            self.set_space(space)
            self.root_node = None

    ################################################################
    # Quast API for set operations
    ################################################################
    @staticmethod
    def from_basic_set(bset):
        return Quast(bset)

    @staticmethod
    def empty(space):
        quast = Quast(space=space)
        quast.root_node = quast.out_node
        return quast

    @staticmethod
    def universe(space):
        quast = Quast(space=space)
        quast.root_node = quast.in_node
        return quast

    def add_dims(self, type, n):
        new_quast = Quast(space=self.get_space(), out_node=self.out_node, in_node=self.in_node)
        new_quast.root_node = self.__apply_callback_to_every_node(self.root_node, {}, self.__isl_add_dims, type, n)
        new_quast.set_space(new_quast.root_node.bset.get_space())
        return new_quast

    def remove_dims(self, type, first, n):
        new_quast = Quast(space=self.get_space(), out_node=self.out_node, in_node=self.in_node)
        new_quast.root_node = self.__apply_callback_to_every_node(self.root_node, {}, self.__isl_remove_dims, type, first, n)
        new_quast.set_space(new_quast.root_node.bset.get_space())
        return new_quast

    def insert_dims(self, type, pos, n):
        new_quast = Quast(space=self.get_space(), out_node=self.out_node, in_node=self.in_node)
        new_quast.root_node = self.__apply_callback_to_every_node(self.root_node, {}, self.__isl_insert_dims, type, pos, n)
        new_quast.set_space(new_quast.root_node.bset.get_space())
        return new_quast

    def align_params(self, model):
        new_quast = Quast(space=self.get_space(), out_node=self.out_node, in_node=self.in_node)
        new_quast.root_node = self.__apply_callback_to_every_node(self.root_node, {}, self.__isl_align_params, model)
        new_quast.set_space(new_quast.root_node.bset.get_space())
        return new_quast

    def apply(self, map_):
        new_quast = Quast(space=self.get_space(), out_node=self.out_node, in_node=self.in_node)
        new_quast.root_node = self.__apply_callback_to_every_node(self.root_node, {}, self.__isl_apply, map_)
        new_quast.set_space(new_quast.root_node.bset.get_space())
        return new_quast

    def params(self):
        return isl.Set.universe(self.get_space()).params()

    def union(self, quast):
        # if self.get_space() != quast.get_space():
        #     raise Exception("spaces don't match")
        if not self.root_node.is_terminal():
            union_space = self.root_node.bset.union(quast.root_node.bset).get_space()
        else:
            union_space = self.get_space()
        union_quast = Quast(space=union_space, in_node=quast.in_node, out_node=quast.out_node)
        memo = {self.in_node: union_quast.in_node, self.out_node: quast.root_node}
        union_quast.root_node = self.__union(self.root_node, memo)
        union_quast.set_tree_size(self.get_tree_size() + quast.get_tree_size())
        union_quast.prune_redundant_branches()
        union_quast.simplify()
        return union_quast

    def intersect(self, quast):
        # if self.get_space() != quast.get_space():
        #     raise Exception("spaces don't match")
        if not self.root_node.is_terminal():
            intersection_space = self.root_node.bset.intersect(quast.root_node.bset).get_space()
        else:
            intersection_space = self.get_space()
        intersection_quast = Quast(space=intersection_space, in_node=quast.in_node, out_node=quast.out_node)
        memo = {self.in_node: quast.root_node, self.out_node: intersection_quast.out_node}
        intersection_quast.root_node = self.__intersect(self.root_node, memo)
        intersection_quast.set_tree_size(self.get_tree_size() + quast.get_tree_size())
        intersection_quast.prune_redundant_branches()
        intersection_quast.simplify()
        return intersection_quast

    def complement(self):
        complement_quast = Quast(space=self.get_space(), in_node=self.out_node, out_node=self.in_node)
        complement_quast.root_node = self.root_node
        return complement_quast

    def is_empty(self):
        return self.__is_empty(self.root_node, isl.Set.universe(self.get_space()), isl.Set.empty(self.get_space()))

    def is_subset(self, quast):
        return self.intersect(quast.complement()).is_empty()

    def is_equal(self, quast):
        return self.reconstruct_set() == quast.reconstruct_set()

    def project_out(self, dim_type, first, n):
        # get the new projected out space
        projected_out_universe = isl.Set.universe(self.get_space()).project_out(dim_type, first, n)
        # create new projected out quast with the projected out space
        project_out_quast = Quast(space=projected_out_universe.get_space(), in_node=self.in_node, out_node=self.out_node)
        # construct the projected out quast
        project_out_quast.root_node = self.__project_out(self.root_node, project_out_quast, [], {}, projected_out_universe, dim_type, first, n)
        return project_out_quast

    def subtract(self, quast):
        return self.intersect(quast.complement())

    def copy(self):
        quast_copy = Quast(space=self.get_space(), in_node=self.in_node, out_node=self.out_node)
        quast_copy.root_node = self.root_node
        return quast_copy

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

    ################################################################
    # Wrappers for islpy.Set functions (for callbacks)
    ################################################################

    def __isl_apply(self, set_, map_):
        return set_.apply(map_)

    def __isl_align_params(self, set_, model):
        return set_.align_params(model)

    def __isl_add_dims(self, set_, type, n):
        return set_.add_dims(type, n)

    def __isl_remove_dims(self, set_, type, first, n):
        return set_.remove_dims(type, first, n)

    def __isl_insert_dims(self, set_, type, pos, n):
        return set_.insert_dims(type, pos, n)

    def __apply_callback_to_every_node(self, node, memo, callback, *args):
        if node.is_terminal():
            return node
        elif node in memo:
            return memo[node]
        else:
            new_true_branch = self.__apply_callback_to_every_node(node.true_branch_node, memo, callback, *args)
            new_false_branch = self.__apply_callback_to_every_node(node.false_branch_node, memo, callback, *args)
            new_node = Node(callback(node.bset, *args), false_branch_node=new_false_branch, true_branch_node=new_true_branch)
            memo[node] = new_node
            return new_node

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

    def update_num_nodes(self, num_additions):
        self.num_nodes = self.num_nodes + num_additions

    def reconstruct_set(self):
        memo = {}
        return self.__reconstruct_set(self.root_node, memo)

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

    ########################################################################
    # Internal implementation of set operations in quast representation
    ########################################################################

    # root_to_node_true_set: is an isl.BasicSet of all the TRUE constraints along root to node path
    # root_to_node_false_set: isl.Set (only or constraints) of all the FALSE constraints along the root to node path
    def __is_empty(self, curr_node, root_to_node_true_set, root_to_node_false_set):
        if curr_node is self.in_node:
            return root_to_node_true_set.is_subset(root_to_node_false_set) #isl.Set.is_subset()
        elif curr_node is self.out_node:
            return True
        else:
            new_root_to_node_true_set = root_to_node_true_set.intersect(curr_node.bset)
            is_true_branch_empty = self.__is_empty(curr_node.true_branch_node, new_root_to_node_true_set, root_to_node_false_set)
            if not is_true_branch_empty:
                return False
            new_root_to_node_false_set = root_to_node_false_set.union(curr_node.bset)
            is_false_branch_empty = self.__is_empty(curr_node.false_branch_node, root_to_node_true_set, new_root_to_node_false_set)
            return is_false_branch_empty

    # def __reconstruct_set_(self, curr_node):
    #     if curr_node is self.in_node:
    #         return isl.BasicSet.universe(self.get_space())
    #     elif curr_node is self.out_node:
    #         return isl.BasicSet.empty(self.get_space())
    #     else:
    #         true_branch_set = curr_node.bset.intersect(self.__reconstruct_set_(curr_node.true_branch_node))
    #         false_branch_set = self.__negate_bset(curr_node.bset).intersect(
    #             self.__reconstruct_set(curr_node.false_branch_node))
    #         return true_branch_set.union(false_branch_set)

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
            #bset = node.bset
            #return str(bset).split(":")[-1].split("}")[0]
            return str(node.bset)
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

    def __project_out(self, node, project_out_quast, root_to_node_set, memo, new_universe, dim_type, first, n):
        if node is self.in_node:
            if not root_to_node_set:
                return project_out_quast.in_node
            else:
                new_set = isl.Set.universe(project_out_quast.get_space())
                for bset in root_to_node_set:
                    new_set = new_set.intersect(bset)
                new_set = new_set.project_out(dim_type, first, n)
                next_true_branch_node = project_out_quast.in_node
                for bset_constraint in new_set.get_basic_sets():
                    new_node = Node(bset=bset_constraint, false_branch_node=project_out_quast.out_node,
                                true_branch_node=next_true_branch_node)
                    next_true_branch_node = new_node
                return next_true_branch_node
        elif node is self.out_node:
            return project_out_quast.out_node
        else:
            fset = frozenset(root_to_node_set)
            if node in memo:
                if fset in memo[node]:
                    return memo[node][fset]
            else:
                memo[node] = {}
            # if node has dimensions to be projected out
            if node.bset.involves_dims(dim_type, first, n):
                # add the constraint to the set of true constraints from root, recurse and then remove.
                root_to_node_set.append(node.bset)
                new_true_branch_node = self.__project_out(node.true_branch_node, project_out_quast, root_to_node_set, memo, new_universe, dim_type, first, n)
                root_to_node_set.pop()
                negated_set = self.__negate_bset(node.bset)
                root_to_node_set.append(negated_set)
                new_false_branch_node = self.__project_out(node.false_branch_node, project_out_quast, root_to_node_set, memo, new_universe, dim_type, first, n)
                root_to_node_set.pop()
                new_node = self.__union(new_true_branch_node, {project_out_quast.out_node: new_false_branch_node, project_out_quast.in_node: project_out_quast.in_node})
            # else dimensions do not have any dimensions to be projected out
            else:
                # Recurse on successors (post-order) without adding the node constraint to the root_to_node_set
                new_true_branch_node = self.__project_out(node.true_branch_node, project_out_quast, root_to_node_set, memo, new_universe, dim_type, first, n)
                new_false_branch_node = self.__project_out(node.false_branch_node, project_out_quast, root_to_node_set, memo, new_universe, dim_type, first, n)
                # Project out the dimensions from the space of the set.
                new_node = Node(node.bset.project_out(dim_type, first, n), false_branch_node=new_false_branch_node, true_branch_node=new_true_branch_node)

            memo[node][fset] = new_node
            return new_node

    ######################################################################
    # Quast API for optimizing tree representation of underlying sets
    ######################################################################

    def prune_redundant_branches(self):
        self.root_node, _ = self.__prune_redundant_branches(node=self.root_node, true_branch_ancestors=set(), false_branch_ancestors=set(), memo={})

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
        self.root_node, _ = self.__simplify(self.root_node, {})

    def merge_nodes(self):
        self.root_node, _ = self.__merge_nodes(self.root_node, {})

    ########################################################################
    # Internal implementation of quast optimization functions
    ########################################################################

    def __simplify(self, node, isomorphic_nodes_memo):
        if node.is_terminal():
            return node, False
        elif (node.bset, node.true_branch_node, node.false_branch_node) in isomorphic_nodes_memo:
            return isomorphic_nodes_memo[(node.bset, node.true_branch_node, node.false_branch_node)], True
        else:
            # post-order traversal
            new_true_branch_node, is_true_modified = self.__simplify(node.true_branch_node, isomorphic_nodes_memo)
            new_false_branch_node, is_false_modified = self.__simplify(node.false_branch_node, isomorphic_nodes_memo)

            # prune redundant checks
            if new_true_branch_node is new_false_branch_node:
                isomorphic_nodes_memo[(node.bset, node.true_branch_node, node.false_branch_node)] = new_true_branch_node
                return new_true_branch_node, True

            if (node.bset, new_true_branch_node, new_false_branch_node) in isomorphic_nodes_memo:
                return isomorphic_nodes_memo[(node.bset, new_true_branch_node, new_false_branch_node)], True

            # case where node or any subtrees not to be pruned
            elif not is_true_modified and not is_false_modified:
                isomorphic_nodes_memo[(node.bset, node.true_branch_node, node.false_branch_node)] = node
                return node, False
            # case where subtree has been pruned but node not to be pruned
            else:
                new_node = Node(bset=node.bset, true_branch_node=new_true_branch_node,
                                false_branch_node=new_false_branch_node)
                isomorphic_nodes_memo[(node.bset, new_true_branch_node, new_false_branch_node)] = new_node
                return new_node, True

    # merge two nodes containing the same set (constraint) and pointing to the same children nodes
    def __merge_nodes(self, node, memo):
        if node.is_terminal():
            return node, False
        elif (node.bset, node.true_branch_node, node.false_branch_node) in memo:
            return (node.bset, node.true_branch_node, node.false_branch_node), True
        else:
            new_true_branch_node, is_true_modified = self.__merge_nodes(node.true_branch_node, memo)
            new_false_branch_node, is_false_modified = self.__merge_nodes(node.false_branch_node, memo)

            if not is_true_modified and not is_false_modified:
                memo[(node.bset, node.true_branch_node, node.false_branch_node)] = node
                return node, False
            else:
                new_node = Node(bset=node.bset, true_branch_node=new_true_branch_node, false_branch_node=new_false_branch_node)
                memo[(node.bset, node.true_branch_node, node.false_branch_node)] = new_node
                return new_node, True

    # ancestors: maps set to true/false to indicate which branch was taken
    def __prune_redundant_branches(self, node, true_branch_ancestors, false_branch_ancestors, memo):
        if node.is_terminal():
            return node, False
        fset_true_ancestors = frozenset(true_branch_ancestors)
        fset_false_ancestors = frozenset(false_branch_ancestors)
        if node not in memo:
            memo[node] = {}
        if fset_true_ancestors not in memo[node]:
            memo[node][fset_true_ancestors] = {}
        if fset_false_ancestors in memo[node][fset_true_ancestors]:
            return memo[node][fset_true_ancestors][fset_false_ancestors]

        if node.bset in true_branch_ancestors:
            new_true_branch_node, _ = self.__prune_redundant_branches(node.true_branch_node,
                                                                      true_branch_ancestors,
                                                                      false_branch_ancestors, memo)
            memo[node][fset_true_ancestors][fset_false_ancestors] = new_true_branch_node, True
            return new_true_branch_node, True
        elif node.bset in false_branch_ancestors:
            new_false_branch_node, _ = self.__prune_redundant_branches(node.false_branch_node,
                                                                       true_branch_ancestors,
                                                                       false_branch_ancestors, memo)
            memo[node][fset_true_ancestors][fset_false_ancestors] = new_false_branch_node, True
            return new_false_branch_node, True
        else:
            true_branch_ancestors.add(node.bset)
            new_true_branch_node, is_true_modified = self.__prune_redundant_branches(node.true_branch_node, true_branch_ancestors, false_branch_ancestors, memo)
            true_branch_ancestors.remove(node.bset)

            false_branch_ancestors.add(node.bset)
            new_false_branch_node, is_false_modified = self.__prune_redundant_branches(node.false_branch_node, true_branch_ancestors, false_branch_ancestors, memo)
            false_branch_ancestors.remove(node.bset)
            if not is_false_modified and not is_true_modified:
                memo[node][fset_true_ancestors][fset_false_ancestors] = node, False
                return node, False
            else:
                new_node = Node(bset=node.bset, false_branch_node=new_false_branch_node, true_branch_node=new_true_branch_node)
                memo[node][fset_true_ancestors][fset_false_ancestors] = new_node, True
                return new_node, True

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

    ########################################################################
    # Other internal functions
    ########################################################################

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
