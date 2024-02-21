import chipwhisperer as CW
from mupq import platforms
import matplotlib.pyplot as plt

cw = platforms.ChipWhisperer()

cw.scope.arm()
cw.target.simpleserial_write('p', bytearray([0]*16))

cw.run("firm.hex", expiterations=10)

print(cw.scope.capture())
power_trace = cw.scope.get_last_trace()

print(len(power_trace))
plt.plot(power_trace)
plt.show()
