# KyberCPA

## Prerequisites
Make a python venv (for example named venv), for example with:
```sh
mkdir venv
python -m venv .
source venv/bin/activate
```

Fetch `mupq` and `pqclean` git submodules with the command `git submodule update --init <name_submodule>`.

## How to build firmware
Compile needed implementations with `make -j7 PLATFORM=cw308t-stm32f3`, then run `python build_everything.py --platform=cw308t-stm32f3 --only=kyber512`

The binary we're using in this test is the `mupq_pqclean_crypto_kem_kyber512_clean_test` hex.

