"""
arm.py

Module reproducing some ARM instruction set used in Kyber.
"""

def smultt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    """
        Signed Multiply, with 16-bit operands and a 32-bit result.
        Particular case of the SMULxy instruction.
        smultt multiplies top halves of bytes_1 and bytes_2. 
    """
    return (int.from_bytes(bytes_1[2:4], signed=True) * int.from_bytes(bytes_2[2:4], signed=True)).to_bytes(4, signed=True)

def smulbb(bytes_1: bytes, bytes_2: bytes) -> bytes:
    """
        Signed Multiply, with 16-bit operands and a 32-bit result.
        Particular case of the SMULxy instruction.
        smulbb multiplies bottom halves of bytes_1 and bytes_2. 
    """
    return (int.from_bytes(bytes_1[0:2], signed=True) * int.from_bytes(bytes_2[0:2], signed=True)).to_bytes(4, signed=True)

def smulbt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    """
        Signed Multiply, with 16-bit operands and a 32-bit result.
        Particular case of the SMULxy instruction.
        smulbb multiplies the bottom half of bytes_1 with the top half of bytes_2. 
    """
    return (int.from_bytes(bytes_1[0:2], signed=True) * int.from_bytes(bytes_2[2:4], signed=True)).to_bytes(4, signed=True)

def smadd(bytes_1 : bytes, bytes_2 : bytes) -> bytes:
    """
        Instruction outside of ARM instruction set.
        Adds two bytes.
        Precondition: bytes_1 + bytes_2 should not hold any carry.
    """
    return (int.from_bytes(bytes_1, signed=True) + int.from_bytes(bytes_2, signed=True)).to_bytes(4, signed=True)

def smlabb(bytes_1 : bytes, bytes_2 : bytes, bytes_3 : bytes) -> bytes:
    """
        Signed Multiply Accumulate, with 16-bit operands and a 32-bit result and accumulator.
        Particular case of the SMLAxy instruction.
        smlabb multiplies bottom halves of bytes_1 and bytes_2. The result it then added to bytes_3. 
    """
    return smadd(smulbb(bytes_1, bytes_2), bytes_3)

def smlabt(bytes_1: bytes, bytes_2: bytes, bytes_3: bytes) -> bytes:
    """
        Signed Multiply Accumulate, with 16-bit operands and a 32-bit result and accumulator.
        Particular case of the SMLAxy instruction.
        smlabb multiplies the bottom half of bytes_1 with the top half of bytes_2. The result it then added to bytes_3. 
    """
    return smadd(smulbt(bytes_1, bytes_2), bytes_3)

def smulwt(bytes_1: bytes, bytes_2: bytes) -> bytes:
    """
        Signed Multiply Wide, with one 32-bit and one 16-bit operand, providing the top 32 bits of the result.
        Particular case of the SMULWy instruction.
        smulwt multiplies bytes_1 with the top half of bytes_2. The output it then the top 32 bits result.
    """
    return ((int.from_bytes(bytes_1, signed=True) * int.from_bytes(bytes_2[2:4], signed=True)) >> 16).to_bytes(4, signed=True)

def smuadx(bytes_1: bytes, bytes_2: bytes) -> bytes:
    """
        Dual 16-bit Signed Multiply with Addition of products, and optional exchange of operand halves.
        Particular case of the SMUAD instruction.
        smuadx exchanges the two halves of bytes_2 and then multiplies it by the bottom half of bytes_1.
        Pre-condition: The multiplication should not hold any carry.
    """
    bytes_2 = bytes_2[2:4] + bytes_2[0:2]
    return int.from_bytes(bytes_1[0:2], signed=True) * int.from_bytes(bytes_2, signed=True).to_bytes(4, signed=True)
