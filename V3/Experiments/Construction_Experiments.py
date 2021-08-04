import islpy as isl
import V3.Quast as Q
from timeit import default_timer as timer
import matplotlib.pyplot as plt


def construct_set(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)
        p = []
        for i in range(num_non_equalities):
            p_i = '[p_'+str(i)+'] -> {[i0] : i0 = p_' + str(i) + ' }'
            p.append(isl.Set(p_i))

        set_ = isl.Set.universe(space)
        for p_i in p:
            set_ = set_.intersect(p_i.complement())
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments


def set_is_subset(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)
        p = []
        for i in range(num_non_equalities):
            p_i = '[p_'+str(i)+'] -> {[i0] : i0 = p_' + str(i) + ' }'
            p.append(isl.Set(p_i))

        set_ = isl.Set.universe(space)
        for p_i in p:
            set_ = set_.intersect(p_i.complement())
        set1587 = isl.Set("[p_0, p_1, p_2, p_3, p_4, p_5, p_6] -> { [i0] : (p_1 < 0 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_1 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_2 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_3 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_4 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) }")
        #print(set_.is_subset(set1587))
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments


def construct_quast(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)
        q = []
        for i in range(num_non_equalities):
            q_i = '[p_' + str(i) + '] -> {[i0] : i0 = p_' + str(i) + ' }'
            q.append(Q.Quast(isl.Set(q_i)))
        quast = Q.Quast(isl.Set.universe(space))
        for q_i in q:
            quast = quast.intersect(q_i.complement())
            quast.prune_redundant_branches()
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments


def quast_is_subset(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)
        q = []
        for i in range(num_non_equalities):
            q_i = '[p_' + str(i) + '] -> {[i0] : i0 = p_' + str(i) + ' }'
            q.append(Q.Quast(isl.Set(q_i)))
        quast = Q.Quast(isl.Set.universe(space))
        for q_i in q:
            quast = quast.intersect(q_i.complement())
            quast.prune_redundant_branches()
        quast1587 = Q.Quast(isl.Set("[p_0, p_1, p_2, p_3, p_4, p_5, p_6] -> { [i0] : (p_1 < 0 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_1 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_1 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_1 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_2 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_2 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_2 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_3 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_3 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_3 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_4 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_4 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_4 < 0 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_1 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_2 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_3 and i0 > p_4 and i0 >= 0 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_3 and i0 >= 0 and i0 < p_4 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 > p_4 and i0 >= 0 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) or (p_5 < 0 and i0 >= 0 and i0 < p_4 and i0 < p_3 and i0 < p_2 and i0 < p_1 and i0 < p_0) }"))
        #print(quast.is_subset(quast1587))
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments


def set_project_out(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)

        param_dims = ''
        for j in range(num_non_equalities):
            param_dims = param_dims + 'p_' + str(j) + (', ' if j < num_non_equalities - 1 else '')
        param_dims = '[' + param_dims + ']'

        p = []
        for i in range(num_non_equalities):
            p_i = param_dims + ' -> {[i0] : i0 = p_' + str(i) + ' }'
            p.append(isl.Set(p_i))

        set_ = isl.Set.universe(p[0].get_space())
        for p_i in p:
            set_ = set_.subtract(p_i)
            #set_ = set_.intersect(p_i.complement())
        project_out_set = set_.project_out(isl.dim_type.param, 1, 3)
        project_out_set.is_empty()
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments, project_out_set


def quast_project_out(num_non_equalities, num_experiments):
    total_time = 0
    for _ in range(num_experiments):
        start = timer()
        ctx = isl.DEFAULT_CONTEXT
        space = isl.Space.set_alloc(ctx, 0, 1)

        param_dims = ''
        for j in range(num_non_equalities):
            param_dims = param_dims + 'p_' + str(j) + (', ' if j < num_non_equalities - 1 else '')
        param_dims = '[' + param_dims + ']'

        q = []
        for i in range(num_non_equalities):
            q_i = param_dims + '-> {[i0] : i0 = p_' + str(i) + ' }'
            q.append(Q.Quast(isl.Set(q_i)))

        quast = Q.Quast(isl.Set.universe(q[0].get_space()))
        for q_i in q:
            quast = quast.subtract(q_i)
            #quast = quast.intersect(q_i.complement())
        project_out_quast = quast.project_out(isl.dim_type.param, 1, 3)
        project_out_quast.is_empty()
        end = timer()
        total_time = total_time + end - start
    return total_time / num_experiments, project_out_quast


if __name__ == "__main__":
    NUM_NON_EQUALITIES = 11
    quast_outputs = [0] * NUM_NON_EQUALITIES
    quast_times = [0] * NUM_NON_EQUALITIES
    set_outputs = [0] * NUM_NON_EQUALITIES
    set_times = [0] * NUM_NON_EQUALITIES
    for i in range(6, NUM_NON_EQUALITIES):
        set_times[i], set_outputs[i] = set_project_out(i, 1)#construct_set(i, 1) #set_is_subset(i, 1)
        quast_times[i], quast_outputs[i] = quast_project_out(i, 1)#construct_quast(i, 1)#quast_is_subset(i, 1)
        print("number of non-equalities = " + str(i))
        print("quast: " + str(quast_times[i]))
        print("set: " + str(set_times[i]))
        print("-------------------------------------")
    x_axis = [i for i in range(NUM_NON_EQUALITIES)]
    plt.plot(x_axis, quast_times, 'r--', x_axis, set_times, 'b--')
    #plt.savefig('/Users/shubhangkulkarni/PycharmProjects/ANLSummer21/V3/Experiments/Plots/construction_times_plot.pdf')
    #plt.show()
    for j in range(6, NUM_NON_EQUALITIES):
        assert quast_outputs[j].reconstruct_set() == set_outputs[j]