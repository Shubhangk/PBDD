# Todo -- remove reference to main
from Quast import *
import islpy as isl
# from Quast import *

def Test1():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    Q = BasicQuast(A)
    Q.print_tree()

def Test2():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    print("Quast for A:")
    a.print_tree()
    B = isl.BasicSet("{[x,y]: x <= -1 and y <=5 }")
    b = BasicQuast(B)
    print("Quast for B:")
    b.print_tree()
    a.union(b)
    print("Union of quasts\n")
    a.print_tree()


def Test3():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    a.print_tree()
    print("\nComplement Tree\n")
    a.complement()
    a.print_tree()


def Test4():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    a = BasicQuast(A)
    a.complement()
    B = isl.BasicSet("{[x,y]: x <= -1 and y <=5 }")
    b = BasicQuast(B)
    a.union(b)
    a.print_tree()


def Test5():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 }")
    B = isl.BasicSet("{[x,y]: y >= 7 }")
    a = BasicQuast(A)
    b = BasicQuast(B)
    a.intersect(b)
    a.print_tree()

def Test6():
    A = isl.BasicSet("{[x,y]: x >= 0 and y >=8 and x < 20 and y <= 99}")
    Q = BasicQuast(A)
    print("Quast:\n")
    Q.print_tree()
    Q_clone = Q.deepclone()
    print("Clone Quast:\n")
    Q_clone.print_tree()