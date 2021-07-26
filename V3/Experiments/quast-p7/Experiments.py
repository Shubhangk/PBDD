import islpy as isl
import V3.Quast as Q
from timeit import default_timer as timer
import matplotlib.pyplot as plt

def construct_set():
    ctx = isl.DEFAULT_CONTEXT
    space = isl.Space.set_alloc(ctx, 0, 1)

    p_0 = isl.Set("[p_0] -> {[i0] : i0 = p_0 }")
    p_1 = isl.Set("[p_1] -> {[i0] : i0 = p_1 }")
    p_2 = isl.Set("[p_2] -> {[i0] : i0 = p_2 }")
    p_3 = isl.Set("[p_3] -> {[i0] : i0 = p_3 }")
    p_4 = isl.Set("[p_4] -> {[i0] : i0 = p_4 }")
    p_5 = isl.Set("[p_5] -> {[i0] : i0 = p_5 }")
    p_6 = isl.Set("[p_6] -> {[i0] : i0 = p_6 }")
    p_7 = isl.Set("[p_7] -> {[i0] : i0 = p_7 }")
    p_8 = isl.Set("[p_8] -> {[i0] : i0 = p_8 }")
    p_9 = isl.Set("[p_9] -> {[i0] : i0 = p_9 }")
    p_10 = isl.Set("[p_10] -> {[i0] : i0 = p_10 }")
    p_11 = isl.Set("[p_11] -> {[i0] : i0 = p_11 }")

    p = [p_0, p_1, p_2, p_3, p_4, p_5, p_6, p_7, p_8, p_9, p_10, p_11]


    num_experiments = 3
    time = [0] * (len(p) + 1)
    for num_non_equality_constraints in range(1, len(p)+1):
        constraints = p[0:num_non_equality_constraints]
        for _ in range(num_experiments):
            set_ = isl.Set.universe(space)
            start = timer()
            for p_i in constraints:
                set_to_subtract = set_.intersect(p_i)
                set_ = set_.subtract(set_to_subtract)
                set_ = set_.coalesce()
            end = timer()
            time[num_non_equality_constraints] = time[num_non_equality_constraints] + end - start
        time[num_non_equality_constraints] = time[num_non_equality_constraints] / num_experiments
    return time
    # t.start()
    # for p_i in p:
    #     set_to_subtract = set_.intersect(p_i)
    #     set_ = set_.subtract(set_to_subtract)
    # t.stop()
    # return set_


def construct_quast():
    ctx = isl.DEFAULT_CONTEXT
    space = isl.Space.set_alloc(ctx, 0, 1)

    p_0 = isl.Set("[p_0] -> {[i0] : i0 = p_0 }")
    p_1 = isl.Set("[p_1] -> {[i0] : i0 = p_1 }")
    p_2 = isl.Set("[p_2] -> {[i0] : i0 = p_2 }")
    p_3 = isl.Set("[p_3] -> {[i0] : i0 = p_3 }")
    p_4 = isl.Set("[p_4] -> {[i0] : i0 = p_4 }")
    p_5 = isl.Set("[p_5] -> {[i0] : i0 = p_5 }")
    p_6 = isl.Set("[p_6] -> {[i0] : i0 = p_6 }")
    p_7 = isl.Set("[p_7] -> {[i0] : i0 = p_7 }")
    p_8 = isl.Set("[p_8] -> {[i0] : i0 = p_8 }")
    p_9 = isl.Set("[p_9] -> {[i0] : i0 = p_9 }")
    p_10 = isl.Set("[p_10] -> {[i0] : i0 = p_10 }")
    p_11 = isl.Set("[p_11] -> {[i0] : i0 = p_11 }")
    p_12 = isl.Set("[p_12] -> {[i0] : i0 = p_12 }")
    p_13 = isl.Set("[p_13] -> {[i0] : i0 = p_13 }")
    p_14 = isl.Set("[p_14] -> {[i0] : i0 = p_14 }")
    p_15 = isl.Set("[p_15] -> {[i0] : i0 = p_15 }")

    p = [p_0, p_1, p_2, p_3, p_4, p_5, p_6, p_7, p_8, p_9, p_10, p_11, p_12, p_13, p_14, p_15]
    q = [Q.Quast(p_i) for p_i in p]

    num_experiments = 1
    time = [0] * (len(p) + 1)
    for num_non_equality_constraints in range(1, len(q) + 1):
        constraints = q[0:num_non_equality_constraints]
        for _ in range(num_experiments):
            quast = Q.Quast(isl.Set.universe(space))
            start = timer()
            for q_i in constraints:
                quast_to_subtract = q_i.intersect(quast)
                quast = quast.subtract(quast_to_subtract)
                #quast.prune_emptyset_branches
                quast.prune_redundant_branches()
            end = timer()
            time[num_non_equality_constraints] = time[num_non_equality_constraints] + end - start
        time[num_non_equality_constraints] = time[num_non_equality_constraints] / num_experiments
        if num_non_equality_constraints == 11:
            quast.visualize_tree()
    return time

    # q = [Q.Quast(p_i) for p_i in p]
    # quast = Q.Quast(isl.Set.universe(space))
    # #t.start()
    # for q_i in q:
    #     quast_to_subtract = quast.intersect(q_i)
    #     quast = quast.subtract(quast_to_subtract)
    #     #quast.prune_redundant_nodes()
    #     quast.prune_emptyset_branches()
    # #t.stop()
    # return quast


if __name__ == "__main__":
    # t = Timer()
    # set_ = construct_set(t)
    # quast = construct_quast(t)
    # quast.visualize_tree()

    quast_times = construct_quast()
    print(quast_times)
    # set_times = construct_set()
    # print(set_times)
    # x_axis = [i for i in range(len(quast_times))]
    # plt.plot(x_axis, quast_times, 'r--', x_axis, set_times, 'b--')
    # plt.savefig('/Users/shubhangkulkarni/PycharmProjects/ANLSummer21/V3/plot.pdf')
    # plt.show()
