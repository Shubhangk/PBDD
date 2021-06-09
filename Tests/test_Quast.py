import unittest
import Quast as Q
import islpy as isl


class MyTestCase(unittest.TestCase):
    def are_constraints_equal(self, constraint1, constraint2):
        return constraint1.get_space().is_equal(constraint2.get_space()) and (
                    constraint1.get_coefficients_by_name() == constraint2.get_coefficients_by_name())

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
            self.are_constraints_equal(isl.Constraint.ineq_from_names(space, {1: 4, "x": 1}), test_node.false_branch_node.constraint))
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


if __name__ == '__main__':
    unittest.main()