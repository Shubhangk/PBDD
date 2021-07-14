import islpy as isl

def print_dim_types(isl_object):
    print("Printing number of each dimension types for " + str(isl_object))
    print("out: " + str(isl_object.dim(isl.dim_type.out)))
    print("set: " + str(isl_object.dim(isl.dim_type.set)))
    print("in_: " + str(isl_object.dim(isl.dim_type.in_)))
    print("param: " + str(isl_object.dim(isl.dim_type.param)))
    print("div: " + str(isl_object.dim(isl.dim_type.div)))
    print("all: " + str(isl_object.dim(isl.dim_type.all)))
    print()

def print_set_info(bset):
    print("------------------------------------------------------------")
    print("Set: " + str(bset))
    print()
    print("----- Basic information -----")
    print("Is empty: " + str(bset.is_empty()))
    constraints = bset.get_constraints()
    print("constraints : " + str(constraints))
    space = bset.get_space()
    print("space : " + str(space))
    lspace = bset.get_local_space()
    print("local space : " + str(lspace))
    print()
    print("----- Dimension information -----")
    print_dim_types(bset)
    num_divs = bset.dim(isl.dim_type.div)
    if num_divs > 0:
        print("Affine expressions [get_div]")
        for i in range(num_divs):
            print(bset.get_div(i))
        print()
    print("----- Internal dictionaries -----")
    print("id dict: " + str(bset.get_id_dict()))
    print("var dict: " + str(bset.get_var_dict()))
    print()


def print_constraint_info(constraint):
    print("------------------------------------------------------------")
    print("Constraint: " + str(constraint))
    print()
    print("------ Basic Information ------")
    print("Is equality: " + str(constraint.is_equality()))
    print("Is div: " + str(constraint.is_div_constraint()))
    print("Coefficients: " + str(constraint.get_coefficients_by_name()))
    print("Constant: " + str(constraint.get_constant_val()))
    print()
    print("------ Dimension information ------")
    print_dim_types(constraint)
    num_divs = constraint.dim(isl.dim_type.div)
    # if num_divs > 0:
    #     print("Affine expressions [get_div]")
    #     for i in range(num_divs):
    #         print(constraint.get_div(i))
    #     print()
    # print("Aff [get_aff]: ")
    # print(constraint.get_aff())
    # print()
    print("------ Space Information ------")
    space = constraint.get_space()
    print("space : " + str(space))
    print()
    lspace = constraint.get_local_space()
    print_local_space_info(lspace)
    print()
    print("----- Internal dictionaries -----")
    print("id dict: " + str(constraint.get_id_dict()))
    print("var dict: " + str(constraint.get_var_dict()))
    print()

def print_local_space_info(lspace):
    print("local space : " + str(lspace))
    print("----- Dimension information -----")
    print_dim_types(lspace)
    num_divs = lspace.dim(isl.dim_type.div)
    # if num_divs > 0:
    #     print("Affine expressions [get_div]")
    #     for i in range(num_divs):
    #         print(lspace.get_div(i))
    #     print()
    print()
    print("----- Internal dictionaries -----")
    print("id dict: " + str(lspace.get_id_dict()))
    print("var dict: " + str(lspace.get_var_dict()))
    print()



# A = isl.BasicSet("{[x, y, z]: (z) mod 2 = 0 and x = 2z and x = 3y and (y) mod 3 = 0 and y + z >= 9}")
# # for i in range(len(A.get_constraints())):
# #     print("CONSTRAINT " + str(i))
# #     constraint = A.get_constraints()[i]
# #     print_constraint_info(constraint)
# C = isl.BasicSet("{[x, y, z]: (z) mod 2 = 0 and x = 2z and x = 3y and (y) mod 3 = 0 and y + z >= 9 and exists e : y = 4e}")
# B = C.compute_divs()
# print(C)
# print(B)
