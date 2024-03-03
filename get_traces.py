PATH_TO_FIRMWARE = 'bin/crypto_kem_kyber512_m4fspeed_test.hex'

from mupq import platforms
import matplotlib.pyplot as plt
from json import dumps

"""
Note copied from CW documentation when using the segment mode:
#IMPORTANT - we now need to generate enough triggers such that scope.adc.samples * NUM_TRIGGERS > max_fifo_size
#            If not the HW won't exit capture mode. In this example code we weill just call the function so
#            many times.
For more information, see: https://github.com/newaetech/chipwhisperer-jupyter/blob/84a9feabcfe5f1b76e31c4ac7d96d00f2577685c/demos/Using%20Segmented%20Memory%20for%20Hardware%20AES%20(STM32F4).ipynb#L185
In our case (with a CW-Lite), max_fifo_size = 24400
"""

cw = platforms.ChipWhisperer()

cw.scope.adc.samples = 1000 #200
cw.scope.adc.basic_mode = "rising_edge"
cw.scope.adc.fifo_fill_mode = "segment"

print(cw.run(PATH_TO_FIRMWARE))

# print(cw.scope.capture())
# power_trace = cw.scope.get_last_trace()
cw.scope.capture_segmented()
power_traces = cw.scope.get_last_trace_segmented()

print(f'Captured {len(power_traces)} segments of {len(power_traces[0])} points each.')

plt.plot(power_traces[-1])
plt.show()

cw.scope.dis()
cw.target.dis()

with open('traces.log', 'a+') as f:
    f.write(dumps(power_traces.tolist()))
