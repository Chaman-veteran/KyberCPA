from scipy.stats import pearsonr

part_key_1 = 2**16
part_key_2 = 2**16

# max_pearson_corr: ceiling (discriminant) on Pearson's correlation coefficient
max_pearson_corr = 0.6

# number of traces
n = 200 

# number of samples per traces
m = 200

# trace_matrix: matrix of M_{n,m} of acquired traces
trace_matrix = [[0 for _ in range(m)] for _ in range(n)]

# hammingWeight: gives the hamming weight of a byte
def hammingWeight(byte: bytes):
    return bin(int.from_bytes(byte, byteorder='big')).count('1')

# 3. Repeat step 1-2 for all possibilities of k2k3 and keep a sample S = {k2k3 such that P CCk2k3 > x}, x being the chosen discriminant.
# For example, x = 0.6,
candidates_k2k3 = list()
for k in range(part_key_2):
    # 1. Make a guess for k2k3 (216 possibilities) and compute the result rst = [rst0, ..., rst200]
    # where rsti is the Hamming weight of the operation smultt on line 25 of doublebasemul using the ith ciphertext.
    # TODO: remplacer par la vraie valeur de smultt_result
    smultt_result_smultt = bytearray(b'\x00' * m) # smultt_result = smultt(ciphertext, k2k3)
    rst = [hammingWeight(x) for x in smultt_result_smultt]

    # 2. Compute Pearson correlation coefficient between Ti and rst for all i and keep the biggest value in absolute PCCk2k3.
    # Rq: y'a un intérêt à faire tout ce tatouin de construire tmp pour faire un if plutôt que de break quand on a trouvé une bonne valeur ?
    tmp = [abs(pearsonr(captured_trace, rst)[1]) for captured_trace in trace_matrix]

    if max(tmp) > max_pearson_corr:
        candidates_k2k3.append(k)


# 4. Fix k2k3 ∈ S, make a guess for k0k1 and compute the result rst′ of pkhtb for all of the ciphertexts. Then compute Pearson correlation between rst′ and the power traces, keep the largest value in absolute P CCk0k1k2k3 .
candidates_k0k1k2k3 = list()
for k2k3 in candidates_k2k3:
    # 5. Redo step 4 for all the k0k1 ∈ S.
    for k in range(part_key_2):
        # TODO: remplacer par la vraie valeur de smultt_result
        smultt_result_pkhtb = bytearray(b'\x00' * m) # smultt_result_pkhtb = smultt_result_pkhtb(ciphertext, k0k1k2k3)
        rst = [hammingWeight(x) for x in smultt_result_pkhtb]

        # Même remarque qu'avant...
        tmp = [abs(pearsonr(captured_trace, rst)[1]) for captured_trace in trace_matrix]
        
        t_max = max(tmp)
        if t_max > max_pearson_corr:
            candidates_k0k1k2k3.append((k, t_max))


# 6. The part of the key k0k1k2k3 with the largest P CCk0k1k2k3 is the correct guess.
key = max(candidates_k0k1k2k3, key=lambda x: x[1])

