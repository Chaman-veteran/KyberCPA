"""
get_traces.py

Module to capture and optionaly save power traces from the ARM Cortex-M4.
To use it for capture only: python get_traces.py
To save the capture: python get_traces.py --save-traces y >> ciphertexts 
"""

from mupq import platforms
import matplotlib.pyplot as plt
from json import dumps
from argparse import ArgumentParser

PATH_TO_FIRMWARE = 'bin/crypto_kem_kyber512_m4fspeed_test.hex'

"""
As we are using the segment mode of the CW, we let this note copied from CW documentation when using the segment mode:
#IMPORTANT - we now need to generate enough triggers such that scope.adc.samples * NUM_TRIGGERS > max_fifo_size
#            If not the HW won't exit capture mode. In this example code we weill just call the function so
#            many times.
For more information, see: https://github.com/newaetech/chipwhisperer-jupyter/blob/84a9feabcfe5f1b76e31c4ac7d96d00f2577685c/demos/Using%20Segmented%20Memory%20for%20Hardware%20AES%20(STM32F4).ipynb#L185
In our case (with a CW-Lite), max_fifo_size = 24400
"""

parser = ArgumentParser(description="Get traces from kyber512 implementation")
parser.add_argument(
        "--save-traces",
        dest='save_traces',
        default=False,
    )
parser.parse_args()
args = vars(parser.parse_args())
save_traces = bool(args.get('save_traces'))

cw = platforms.ChipWhisperer()

cw.scope.adc.samples = 1000 #200
cw.scope.adc.basic_mode = "rising_edge"
cw.scope.adc.fifo_fill_mode = "segment"

print(cw.run(PATH_TO_FIRMWARE))

cw.scope.capture_segmented()
power_traces = cw.scope.get_last_trace_segmented()

print(f'Captured {len(power_traces)} segments of {len(power_traces[0])} points each.')

plt.plot(power_traces[0])
plt.xlabel('Sample')
plt.ylabel('Power consumption')
plt.show()

cw.scope.dis()
cw.target.dis()

if save_traces:
    with open('traces.log', 'a+') as f:
        f.write(dumps(power_traces.tolist()))
        f.write('\n')
