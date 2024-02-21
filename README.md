# KyberCPA

## How to build firmware
The binary we're using in this test is the `mupq_pqclean_crypto_kem_kyber512_clean_test` elf.

To convert the binary to hex:
`arm-none-eabi-objcopy -O ihex <path_to_binary>.elf <path_to_new_hex>.hex`

