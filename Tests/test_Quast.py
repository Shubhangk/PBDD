import unittest
import Quast as Q
import islpy as isl


class TestQuast(unittest.TestCase):
    # Description: Function that checks whether two constraints (affine inequalities) are equal by comparing their space
    # and co-efficients.
    # @TODO Should be replaced by islpy.Constraint.is_equal() in the future.
    def are_constraints_equal(self, constraint1, constraint2):
        return constraint1.get_space() == constraint2.get_space() and (
                constraint1.get_coefficients_by_name() == constraint2.get_coefficients_by_name())

    # Description: Constructs a Quast.Quast from an islpy.Set that is the union of two polyhedra. Traverses the
    # constructed Quast (in a depth-first manner) and checks that each node has the expected constraint.
    def test_Quast(self):
        A = isl.Set("{[x,y]: (x >= 0 and y >=8) or (-5 < x < 1 and y < 3)}")
        T = Q.Quast(A)
        space = isl.Space.create_from_names(isl.DEFAULT_CONTEXT, set=["x", "y"])
        test_node = T.root_node
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: 0, "x": 1}), test_node.constraint))
        test_node = test_node.true_branch_node
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: -8, "y": 1}), test_node.constraint))
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: 4, "x": 1}),
                                       test_node.false_branch_node.constraint))
        test_node = test_node.true_branch_node
        self.assertTrue(test_node is T.in_node)
        test_node = T.root_node.false_branch_node
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: 4, "x": 1}), test_node.constraint))
        self.assertTrue(test_node.false_branch_node is T.out_node)
        test_node = test_node.true_branch_node
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {"x": -1}), test_node.constraint))
        self.assertTrue(test_node.false_branch_node is T.out_node)
        test_node = test_node.true_branch_node
        self.assertTrue(
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: 2, "y": -1}), test_node.constraint))
        self.assertTrue(test_node.false_branch_node is T.out_node)
        self.assertTrue(test_node.true_branch_node is T.in_node)

    # Description: Constructs a Quast.Quast from an isl.Set, converts back to the isl.Set representation and checks
    # whether same as initial set
    def test_reconstruct_set__0(self):
        A = isl.Set("{[x]: x >= 0}")
        T = Q.Quast(A)
        self.assertTrue(T.reconstruct_set() == A)

    # Description: Constructs a Quast.Quast from an isl.Set, converts back to the isl.Set representation and checks
    # whether same as initial set
    def test_reconstruct_set__1(self):
        A = isl.Set("{[x,y]: (x > 0 and y > 4) or (x < -1)}")
        T = Q.Quast(A)
        self.assertTrue(T.reconstruct_set() == A)

    # Description: Constructs a Quast.Quast from an isl.Set, converts back to the isl.Set representation and checks
    # whether same as initial set
    def test_reconstruct_set__2(self):
        A = isl.Set("{[w,x,y,z]: (x > 0 and 2 > w > 9) or (x < -1 and y >= 20) or (x + y > 9 and x + 2z + 3w <= 4)}")
        T = Q.Quast(A)
        self.assertTrue(T.reconstruct_set() == A)

    def test_reconstruct_set__3(self):
        A = isl.Set("{[x]: x >= 0}")
        B = isl.Set("{[x]: x < 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = a.intersect(b)
        c.prune_redundant_branches()
        self.assertTrue(c.reconstruct_set() == A.intersect(B))

    # Description: Constructs a Quast.Quast from an isl.Set, complements the Quast using Quast.complement(),
    # converts back to isl.Set and checks whether complement of initial set
    def test_complement__0(self):
        A = isl.Set("{[x]: x >= 0}")
        T = Q.Quast(A)
        T_compl = T.complement()
        self.assertTrue(T_compl.reconstruct_set() == A.complement())

    # Description: Constructs a Quast.Quast from an isl.Set, complements the Quast using Quast.complement(),
    # converts back to isl.Set and checks whether complement of initial set
    def test_complement__1(self):
        A = isl.Set("{[x,y]: x >= 0 and y <= 9}")
        T = Q.Quast(A)
        T_compl = T.complement()
        self.assertTrue(T_compl.reconstruct_set() == A.complement())

    # Description: Constructs a Quast.Quast from an isl.Set, complements the Quast using Quast.complement(),
    # converts back to isl.Set and checks whether complement of initial set
    def test_complement__2(self):
        A = isl.Set("{[w,x,y,z]: (x >= 0 and y <= 9) or (x + y + z < 7 and x + w > 5 and y - w <= 0) or (w - z >= 20)}")
        T = Q.Quast(A)
        T_compl = T.complement()
        self.assertTrue(T_compl.reconstruct_set() == A.complement())

    def test_intersect__0(self):
        A = isl.Set("{[x, y]: x >= 0}")
        B = isl.Set("{[x, y]: y >= 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        intersection_quast = a.intersect(b)
        self.assertTrue(intersection_quast.reconstruct_set() == A.intersect(B))

    def test_intersect__1(self):
        A = isl.Set("{[x, y, z]: x >= 0 and y <= 9 or (x + z <= 8 and y + z >= 9)}")
        B = isl.Set("{[x, y, z]: y >= 0 and x + y + z <= 10}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        intersection_quast = a.intersect(b)
        self.assertTrue(intersection_quast.reconstruct_set() == A.intersect(B))

    def test_union__0(self):
        A = isl.Set("{[x, y]: x >= 0}")
        B = isl.Set("{[x, y]: y >= 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        union_quast = a.union(b)
        self.assertTrue(union_quast.reconstruct_set() == A.union(B))

    def test_union__1(self):
        A = isl.Set("{[x, y, z]: x >= 0 and y <= 9 or (x + z <= 8 and y + z >= 9)}")
        B = isl.Set("{[x, y, z]: y >= 0 and x + y + z <= 10}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        union_quast = a.union(b)
        self.assertTrue(union_quast.reconstruct_set() == A.union(B))

    def test_prune_empty_branches__0(self):
        A = isl.Set("{[x]: x <= -2 or (x > 0)}")
        B = isl.Set("{[x]: x < 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = a.intersect(b)
        c.prune_emptyset_branches()
        self.assertTrue(c.reconstruct_set() == A.intersect(B))

    def test_prune_empty_branches__1(self):
        A = isl.Set("{[x,y]: x <= -2 or (x > 0) or (x + y <= 3 and x - y >= 9) or x>= 5}")
        B = isl.Set("{[x, y]: x < 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = a.intersect(b)
        c.prune_emptyset_branches()
        self.assertTrue(c.reconstruct_set() == A.intersect(B))

    def test_prune_same_constraint_nodes__0(self):
        A1 = isl.Set("{[x,y]: x >= 0}")
        A2 = isl.Set("{[x,y]: x >= 0}")
        A3 = isl.Set("{[x,y]: x >= 0}")
        A4 = isl.Set("{[x,y]: x >= 0}")
        A5 = isl.Set("{[x,y]: x >= 0}")
        c = Q.Quast(A1).intersect(Q.Quast(A2)).intersect(Q.Quast(A3)).intersect(Q.Quast(A4)).intersect(Q.Quast(A5))
        c.prune_redundant_branches()
        self.assertTrue(c.reconstruct_set() == A1)

    def test_prune_same_constraint_nodes__1(self):
        A1 = isl.Set("{[x,y]: x >= 0 or ( x + y <= 0)}")
        A2 = isl.Set("{[x,y]: x + y > 0}")
        c = Q.Quast(A1).intersect(Q.Quast(A2))
        c.prune_redundant_branches()
        self.assertTrue(c.reconstruct_set() == A1.intersect(A2))

    def test_is_equal__0(self):
        A1 = isl.Set("{[x,y]: x >= 0 or ( x + y <= 0)}")
        A2 = isl.Set("{[x,y]: x < 0}")
        A3 = isl.Set("{[x,y]: x + y <= 0}")
        a1 = Q.Quast(A1)
        a23 = Q.Quast(A2).complement().union(Q.Quast(A3))
        self.assertTrue(a1.is_equal(a23))

    def test_is_empty__0(self):
        A1 = isl.Set("{[x,y]: x >= 0}")
        A2 = isl.Set("{[x,y]: x < 0}")
        a1 = Q.Quast(A1)
        a2 = Q.Quast(A2)
        self.assertTrue(a1.intersect(a2).is_empty())

    def test_prune_equal_children_node__0(self):
        A = isl.BasicSet("{[x]: x > 0}")
        B = isl.BasicSet("{[x]: x < 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = a.intersect(b)
        c.prune_emptyset_branches()
        c.prune_equal_children_node()
        self.assertTrue(c.reconstruct_set().is_empty())

    def test_prune_empty_branches_AND_equal_children_node(self):
        A = isl.BasicSet("{[x, y]: y <= 0 and x >=0}")
        B = isl.BasicSet("{[x,y]:x < 0}")
        C = isl.BasicSet("{[x,y]:y > 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = Q.Quast(C)
        d = a.intersect(b)
        e = d.union(c)
        e.prune_emptyset_branches()
        e.prune_equal_children_node()
        self.assertTrue(e.reconstruct_set() == A.intersect(B).union(C))
        space = A.get_space()
        self.assertTrue(self.are_constraints_equal(e.root_node.constraint, isl.Constraint.ineq_from_names(space, {1: 0, "y": -1})))
        self.assertTrue(e.root_node.true_branch_node.node_type == e.root_node.true_branch_node.OUT_NODE)
        self.assertTrue(e.root_node.false_branch_node.node_type == e.root_node.true_branch_node.IN_NODE)

    def test_prune_isomorphic_subtrees__0(self):
        A = isl.BasicSet("{[x, y]: y >= 0 and x >=0}")
        B = isl.BasicSet("{[x,y]:x >= 0}")
        a = Q.Quast(A)
        b = Q.Quast(B)
        c = a.union(b)
        c.prune_emptyset_branches()
        c.prune_isomorphic_subtrees()
        self.assertTrue(c.reconstruct_set() == A.union(B))
        space = A.get_space()
        self.assertTrue(self.are_constraints_equal(c.root_node.constraint, isl.Constraint.ineq_from_names(space, {"y": 1})))
        self.assertTrue(c.root_node.true_branch_node is c.root_node.false_branch_node)
        self.assertTrue(self.are_constraints_equal(c.root_node.true_branch_node.constraint, isl.Constraint.ineq_from_names(space, {"x": 1})))
        self.assertTrue(c.root_node.true_branch_node.true_branch_node.node_type == c.root_node.IN_NODE)
        self.assertTrue(c.root_node.false_branch_node.false_branch_node.node_type == c.root_node.OUT_NODE)
        c.prune_equal_children_node()
        self.assertTrue(self.are_constraints_equal(c.root_node.constraint,
                                                   isl.Constraint.ineq_from_names(space, {"x": 1})))
        self.assertTrue(c.root_node.true_branch_node.node_type == c.root_node.IN_NODE)
        self.assertTrue(c.root_node.false_branch_node.node_type == c.root_node.OUT_NODE)

if __name__ == '__main__':
    unittest.main()
