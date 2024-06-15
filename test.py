# from itertools import permutations, combinations_with_replacement, combinations, batched
# import random
# import threading

def generate_combinations(length):
    total_combinations = 2 ** length
    return ([int(bit) for bit in format(i, f'0{length}b')] for i in range(total_combinations))

length = 20
combinations = generate_combinations(length)

for combo in combinations:
    print(combo)
# amt = 10

# # comb_w_r = list(combinations_with_replacement(range(2), amt))
# # print(comb_w_r)


# def l_func(amt, l):
#     sub_l = [random.randint(0, 1) for _ in range(amt)]
#     if sub_l in l:
#         l_func(amt, l)
#     return sub_l

# l = []
# def l2_func(amt, amt2):
#     for _ in range(amt):
#         s_l = l_func(amt2, l)
#         l.append(s_l)

# # print(l)
# for lists in list(batched([1 for _ in range(2**amt)], 100)):
#     t = threading.Thread(target=lambda: l2_func(sum(lists), amt))
#     t.daemon = True
#     t.start()

# l.sort()
# for r in l:
#     print(r)