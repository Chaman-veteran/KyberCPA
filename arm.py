"""
Module reproducing some ARM instruction set used in Kyber.
"""

def smultt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    return (int.from_bytes(bytes_1[3:1:-1], signed=True) * int.from_bytes(bytes_2[3:1:-1], signed=True)).to_bytes(4, signed=True)

def smulbb(bytes_1: bytes, bytes_2: bytes) -> bytes:
    return (int.from_bytes(bytes_1[1:-1:-1], signed=True) * int.from_bytes(bytes_2[1:-1:-1], signed=True)).to_bytes(4, signed=True)

def smulbt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    return (int.from_bytes(bytes_1[1:-1:-1], signed=True) * int.from_bytes(bytes_2[3:1:-1], signed=True)).to_bytes(4, signed=True)

# vvvvvv : Name non official
def smadd(bytes_1 : bytes, bytes_2 : bytes) -> bytes:
    return (int.from_bytes(bytes_1, signed=True) + int.from_bytes(bytes_2, signed=True)).to_bytes(4, signed=True)

def smlabb(bytes_1 : bytes, bytes_2 : bytes, bytes_3 : bytes) -> bytes:
    return smadd(smulbb(bytes_1, bytes_2), bytes_3)

def smlabt(bytes_1: bytes, bytes_2: bytes, bytes_3: bytes) -> bytes:
    return smadd(smulbt(bytes_1, bytes_2), bytes_3)

def smulwt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    return ((int.from_bytes(bytes_1, signed=True) * int.from_bytes(bytes_2[2:4], signed=True)) >> 16).to_bytes(4, signed=True)

def smuadx(bytes_1: bytes, bytes_2: bytes) -> bytes:
    return int.from_bytes(bytes_1[0:2], signed=True) * int.from_bytes(bytes_2, signed=True).to_bytes(4, signed=True)
