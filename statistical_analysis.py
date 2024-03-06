from scipy.stats import pearsonr
from json import loads
from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np

ciphertexts = []

def parse_firmware_output(output):
    with open(output, 'r') as f:
        readingCT = False
        ciphertext = bytes()
        compteur = 0
        for line in map(lambda l: l.strip('\n'), f.readlines()):
            if '++++' == line:
                readingCT = not(readingCT)
                if readingCT == False:
                    if compteur % 25 != 0:
                        ciphertexts.append(ciphertext)
                    compteur += 1
                    ciphertext = bytes()
            if readingCT and line != '++++':
                ciphertext += int(line).to_bytes()

parse_firmware_output('ciphertexts')

part_key_length = 2**16

# max_pearson_corr: ceiling (discriminant) on Pearson's correlation coefficient
max_pearson_corr = 0.6

with open('traces.log', 'r') as f:
    trace_matrix = []
    for line in f.readlines():
        # trace_matrix: matrix of M_{n,m} of acquired traces
        trace_matrix += loads(line)

sample_matrix = np.asarray([np.asarray([trace_matrix[i][j] for i in range(len(trace_matrix))]) for j in range(len(trace_matrix[0]))])

# hammingWeight: gives the hamming weight of a byte
def hammingWeight(byte: bytes) -> int:
    return int.from_bytes(byte).bit_count()

def smultt(byte_1: bytes, byte_2: bytes) -> bytes:
    return (int.from_bytes(byte_1[3:1:-1]) * int.from_bytes(byte_2[3:1:-1])).to_bytes(4)

def pkhtb(byte_1: bytes, byte_2: bytes) -> bytes:
    return byte_1[3:1:-1] + byte_2[2:0:-1]

# 3. Repeat step 1-2 for all possibilities of k2k3 and keep a sample S = {k2k3 such that P CCk2k3 > x},
# x being the chosen discriminant.
# For example, x = 0.6,
candidates_k2k3 = []
print('Guessing k2k3...')
for k2k3 in map(lambda k: k.to_bytes(2), tqdm(range(1, part_key_length))):
    # 1. Make a guess for k2k3 (216 possibilities) and compute the result rst = [rst0, ..., rst200]
    # where rsti is the Hamming weight of the operation smultt on line 25 of doublebasemul using the ith ciphertext.
    k0k1k2k3 = bytes(2) + k2k3 # k0k1 will be thrown away in the smultt
    rst = np.asarray([hammingWeight(smultt(ciphertext, k0k1k2k3)) for ciphertext in ciphertexts])

    for sample_trace in sample_matrix:
        # # 2. Compute Pearson correlation coefficient between Ti and rst for all i and keep the biggest value in absolute PCCk2k3.
        pcc_k2k3 = abs(pearsonr(sample_trace, rst)[0])
        if pcc_k2k3 > max_pearson_corr:
            candidates_k2k3.append(k2k3)
            break

rst = np.asarray([hammingWeight(smultt(ciphertext, bytes(2) + candidates_k2k3[0])) for ciphertext in ciphertexts])
pearson_traces = [pearsonr(sample_trace, rst)[0] for sample_trace in sample_matrix]

plt.plot(pearson_traces)
plt.show()

exit()

# 4. Fix k2k3 ∈ S, make a guess for k0k1 and compute the result rst′ of pkhtb for all of the ciphertexts.
# Then compute Pearson correlation between rst′ and the power traces, keep the largest value in absolute PCCk0k1k2k3 .
candidates_k0k1k2k3 = []
print('Guessing k0k1k2k3...')
for k2k3 in tqdm(candidates_k2k3):
    # 5. Redo step 4 for all the k0k1 ∈ S.
    for k0k1 in range(2**5):#part_key_length)):
        k0k1k2k3 = k0k1.to_bytes(2) + k2k3
        rst = asarray([hammingWeight(pkhtb(ciphertext, k0k1k2k3)) for ciphertext in ciphertexts])
  
        pearson_traces = [abs(pearsonr(sample_trace, rst)[0]) for sample_trace in sample_matrix]
        max_pcc = max(pearson_traces)
        if max_pcc > max_pearson_corr:
            candidates_k0k1k2k3.append((k0k1k2k3, max_pcc))

# 6. The part of the key k0k1k2k3 with the largest PCCk0k1k2k3 is the correct guess.
key = max(candidates_k0k1k2k3, key=lambda x: x[1])

rst = [hammingWeight(pkhtb(ciphertext, key[0])) for ciphertext in ciphertexts]
pearson_traces = [pearsonr(sample_trace, rst)[0] for sample_trace in sample_matrix]
plt.plot(pearson_traces)
plt.show()

print("Key = ", key)

