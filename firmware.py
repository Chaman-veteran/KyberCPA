PATH_TO_FIRMWARE = 'bin/mupq_pqclean_crypto_kem_kyber512_clean_test.hex'

# import chipwhisperer as CW
# import matplotlib.pyplot as plt

# scope = CW.scope()
# target = CW.target(scope)

# scope.default_setup()

# CW.program_target(scope, CW.programmers.STM32FProgrammer, PATH_TO_FIRMWARE)

# scope.arm()
# target.simpleserial_write('p', bytearray([0]*16))

# scope.capture()
# target.read()

# print(f'trig_count = {scope.adc.trig_count}')

# plt.plot(scope.get_last_trace())
# plt.show()

import chipwhisperer as CW
from mupq import platforms
import matplotlib.pyplot as plt

cw = platforms.ChipWhisperer()

cw.scope.gain.gain = 25
cw.scope.adc.samples = 1000
cw.scope.adc.basic_mode = "low"

cw.scope.arm()
cw.target.write(bytearray([0]*16))

print(cw.run(PATH_TO_FIRMWARE, expiterations=1))

print(cw.scope.capture())
power_trace = cw.scope.get_last_trace()
    
plt.plot(power_trace)
plt.show()

cw.scope.dis()
cw.target.dis()
