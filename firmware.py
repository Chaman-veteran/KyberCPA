PATH_TO_FIRMWARE = 'bin/mupq_pqclean_crypto_kem_kyber512_clean_test.hex'

from mupq import platforms
import matplotlib.pyplot as plt

cw = platforms.ChipWhisperer()

cw.scope.adc.samples = 1000
cw.scope.adc.basic_mode = "low"

cw.scope.arm()

print(cw.run(PATH_TO_FIRMWARE))

print(cw.scope.capture())
power_trace = cw.scope.get_last_trace()

plt.plot(power_trace)
plt.show()

cw.scope.dis()
cw.target.dis()
