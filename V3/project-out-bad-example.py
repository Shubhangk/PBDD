import islpy as isl
import V3.Quast as Q

# S_0 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_0 = 2x and a_0  = 5x }")
# S_1 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_1 = 2x and a_1  = 5x }")
# S_2 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_2 = 2x and a_2  = 5x }")
# S_3 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_3 = 2x and a_3  = 5x }")
# S_4 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_4 = 2x and a_4  = 5x }")
# S_5 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_5 = 2x and a_5  = 5x }")
# S_6 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_6 = 2x and a_6  = 5x }")
# S_7 = isl.Set("{[x, a_0, a_1, a_2, a_3, a_4, a_5, a_6, a_7]: a_7 = 2x and a_7  = 5x }")
#
# S = isl.Set.universe(S_0.get_space())
# sets = [S_0]
#
# for s in sets:
#     S = S.intersect(s.complement())
# quasts = [Q.Quast(S_i.complement()) for S_i in sets]
#
# T = Q.Quast.universe(S_0.get_space())
#
# for q in quasts:
#     T = T.intersect(q)

########################################################################

R = isl.Set("{[x, a1, a2, a3, a4, a5] : 10 > x > -10}")
r = Q.Quast(R)

S1 = isl.Set("{[x, a1, a2, a3, a4, a5] : a1 = 2x}")
S2 = isl.Set("{[x, a1, a2, a3, a4, a5] : a2 = 2x}")
S3 = isl.Set("{[x, a1, a2, a3, a4, a5] : a3 = 2x}")
S4 = isl.Set("{[x, a1, a2, a3, a4, a5] : a4 = 2x}")
S5 = isl.Set("{[x, a1, a2, a3, a4, a5] : a5 = 2x}")

s1 = Q.Quast(S1).complement()
s2 = Q.Quast(S2).complement()
s3 = Q.Quast(S3).complement()
s4 = Q.Quast(S4).complement()
s5 = Q.Quast(S5).complement()

T = r.intersect(s1).intersect(s2).union(s3).intersect(s4).union(s5)
print(T.compute_tree_size())
#T.visualize_tree()
T1 = T.project_out(isl.dim_type.set, 0, 1)
print(T1.compute_tree_size())
T1.visualize_tree()

t = R.intersect(S1.complement()).intersect(S2.complement()).union(S3.complement()).intersect(S4.complement()).union(S5.complement()).project_out(isl.dim_type.set, 0, 1)
print(len(t.get_basic_sets()))