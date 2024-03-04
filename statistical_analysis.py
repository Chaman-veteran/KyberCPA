from scipy.stats import pearsonr
from json import loads

ciphertexts = list()

def parse_firmware_output(output):
    with open(output, 'r') as f:
        readingCT = False
        ciphertext = bytes()
        for line in map(lambda l: l.strip('\n'), f.readlines()):
            if '++++' == line:
                readingCT = not(readingCT)
                if readingCT == False:
                    ciphertexts.append(ciphertext)
                    ciphertext = bytes()
            if readingCT and line != '++++':
                ciphertext += int(line).to_bytes()

parse_firmware_output('ciphertexts')

part_key_1 = part_key_2 = 2**16

# max_pearson_corr: ceiling (discriminant) on Pearson's correlation coefficient
max_pearson_corr = 0.6

with open('traces.log', 'r') as f:
    trace_matrix = list()
    for line in f.readlines():
        # trace_matrix: matrix of M_{n,m} of acquired traces
        trace_matrix += loads(line)
# Rq: Les traces sont p-e fausses, on a 2 traces par ciphertext, et c'est peut-être "décalé"

# hammingWeight: gives the hamming weight of a byte
def hammingWeight(byte: bytes):
    return bin(int.from_bytes(byte, byteorder='big')).count('1')

def smultt(byte_1: bytes, byte_2: bytes):
    return int.to_bytes(int.from_bytes(byte_1[0:2])* int.from_bytes(byte_2[0:2]))

def pkhtb(byte_1: bytes, byte_2: bytes):
    return byte_1[3:2][::-1] + byte_2[3:2][::-1]

# 3. Repeat step 1-2 for all possibilities of k2k3 and keep a sample S = {k2k3 such that P CCk2k3 > x},
# x being the chosen discriminant.
# For example, x = 0.6,
candidates_k2k3 = list()
for k2k3 in range(part_key_2):
    rst = []
    for (i, captured_trace) in enumerate(trace_matrix):
        # 1. Make a guess for k2k3 (216 possibilities) and compute the result rst = [rst0, ..., rst200]
        # where rsti is the Hamming weight of the operation smultt on line 25 of doublebasemul using the ith ciphertext.
        smultt_result = smultt(ciphertexts[i], int.to_bytes(k2k3))
        rst.append(hammingWeight(smultt_result))

    # 2. Compute Pearson correlation coefficient between Ti and rst for all i and keep the biggest value in absolute PCCk2k3.
    print(len(captured_trace))
    print(len(rst))
    pcc_k2k3 = abs(pearsonr(captured_trace, rst)[1])
    if pcc_k2k3 > max_pearson_corr:
        candidates_k2k3.append(k2k3)
        break

# 4. Fix k2k3 ∈ S, make a guess for k0k1 and compute the result rst′ of pkhtb for all of the ciphertexts.
# Then compute Pearson correlation between rst′ and the power traces, keep the largest value in absolute PCCk0k1k2k3 .
candidates_k0k1k2k3 = list()
for k2k3 in candidates_k2k3:
    # 5. Redo step 4 for all the k0k1 ∈ S.
    for k0k1 in range(part_key_2):
        k0k1k2k3 = int.to_bytes(k0k1, 2) + int.to_bytes(k2k3, 2)
        rst = []
        for (i, captured_trace) in enumerate(trace_matrix):
            pkhtb_result = pkhtb(ciphertexts[i], None)
            rst.append(hammingWeight(pkhtb_result))

        pearson_traces = [abs(pearsonr(captured_trace, rst)[1]) for captured_trace in trace_matrix]
        
        max_pcc = max(pearson_traces)
        if max_pcc > max_pearson_corr:
            candidates_k0k1k2k3.append((k0k1, max_pcc))


# 6. The part of the key k0k1k2k3 with the largest PCCk0k1k2k3 is the correct guess.
key = max(candidates_k0k1k2k3, key=lambda x: x[1])

print("Key = ", key)

