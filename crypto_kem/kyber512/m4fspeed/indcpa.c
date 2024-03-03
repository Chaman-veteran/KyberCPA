#include "indcpa.h"
#include "ntt.h"
#include "poly.h"
#include "polyvec.h"
#include "randombytes.h"
#include "symmetric.h"
#include "matacc.h"

#include <string.h>
#include <stdint.h>


// https://github.com/newaetech/chipwhisperer/blob/develop/hardware/victims/firmware/hal/stm32f3/stm32f3_hal_lowlevel.c#L661
// https://github.com/libopencm3/libopencm3/blob/9545471e4861090a77f79c4458eb19ec771e23d9/include/libopencm3/stm32/common/gpio_common_f234.h#L63

// Mappings foireux entre la lib CW et libopencm3
#define GPIO_MODER_MODER0 GPIO_MODE_ANALOG
#define GPIO_OSPEEDER_OSPEEDR0 GPIO_OSPEED_2MHZ
#define GPIO_OTYPER_OT_0 GPIO_OTYPE_PP
#define GPIO_PUPDR_PUPDR0 GPIO_PUPD_NONE
#define GPIO_GET_INDEX(__GPIOx__)    (((__GPIOx__) == (GPIOA))? 0U :\
                                      ((__GPIOx__) == (GPIOB))? 1U :\
                                      ((__GPIOx__) == (GPIOC))? 2U :\
                                      ((__GPIOx__) == (GPIOD))? 3U : 5U)

void HAL_GPIO_Init(uint32_t gpio, uint16_t gpiopin, uint32_t gpiospeed, uint32_t gpiopull, uint32_t gpiomode) {
    uint32_t position = 0x00U;
    uint32_t iocurrent = 0x00U;
    uint32_t temp = 0x00U;
    /* Configure the port pins */
    while ((gpiopin >> position) != RESET) {
        /* Get current io position */
        iocurrent = gpiopin & (1U << position);
        if(iocurrent) {
            /*--------------------- GPIO Mode Configuration ------------------------*/
            /* TODO: In case of Alternate function mode selection */
            // if(gpiomode == GPIO_MODE_AF) {
            //     // /* Check the Alternate function parameters */
            //     // assert_param(IS_GPIO_AF_INSTANCE(GPIOx));
            //     // assert_param(IS_GPIO_AF(GPIO_Init->Alternate));
                
            //     /* Configure Alternate function mapped with the current IO */
            //     temp = GPIOx->AFR[position >> 3];
            //     temp &= ~(0xFU << ((uint32_t)(position & 0x07U) * 4U)) ;
            //     temp |= ((uint32_t)(GPIO_Init->Alternate) << (((uint32_t)position & 0x07U) * 4U));
            //     GPIOx->AFR[position >> 3] = temp;
            // }

            /* Configure IO Direction mode (Input, Output, Alternate or Analog) */
            temp = GPIO_MODER(gpio);
            temp &= ~(GPIO_MODER_MODER0 << (position * 2U));
            temp |= ((gpiomode & GPIO_MODE) << (position * 2U));
            GPIO_MODER(gpio) = temp;

            /* In case of Output or Alternate function mode selection */
            if((gpiomode == GPIO_MODE_OUTPUT) || (gpiomode == GPIO_MODE_AF)) {
                // /* Check the Speed parameter */
                // assert_param(IS_GPIO_SPEED(gpiospeed));

                /* Configure the IO Speed */
                temp = GPIO_OSPEEDR(gpio);
                temp &= ~(GPIO_OSPEEDER_OSPEEDR0 << (position * 2U));
                temp |= (gpiospeed << (position * 2U));
                GPIO_OSPEEDR(gpio) = temp;

                /* Configure the IO Output Type */
                temp = GPIO_OTYPER(gpio);
                temp &= ~(GPIO_OTYPER_OT_0 << position) ;
                temp |= (((gpiomode & GPIO_OUTPUT_TYPE) >> 4U) << position);
                GPIO_OTYPER(gpio) = temp;
            }

            /* Activate the Pull-up or Pull down resistor for the current IO */
            temp = GPIO_PUPDR(gpio);
            temp &= ~(GPIO_PUPDR_PUPDR0 << (position * 2U));
            temp |= ((gpiopull) << (position * 2U));
            GPIO_PUPDR(gpio) = temp;

            /*--------------------- EXTI Mode Configuration ------------------------*/
            /* Configure the External Interrupt or event for the current IO */
            if((gpiomode & EXTI_MODE) == EXTI_MODE) {
                /* Enable SYSCFG Clock */
                //__HAL_RCC_SYSCFG_CLK_ENABLE(); // ça marche de laisser ça comme ça ???????

                temp = SYSCFG_EXTICR(position >> 2);
                temp &= ~((0x0FU) << (4U * (position & 0x03U)));
                temp |= (GPIO_GET_INDEX(gpio) << (4U * (position & 0x03U)));
                SYSCFG_EXTICR(position >> 2) = temp;

                /* Clear EXTI line configuration */
                temp = EXTI_IMR;
                temp &= ~((uint32_t)iocurrent);
                if((gpiomode & GPIO_MODE_IT) == GPIO_MODE_IT) {
                    temp |= iocurrent;
                }
                EXTI_IMR = temp;

                temp = EXTI_EMR;
                temp &= ~((uint32_t)iocurrent);
                if((gpiomode & GPIO_MODE_EVT) == GPIO_MODE_EVT) {
                    temp |= iocurrent;
                }
                EXTI_EMR = temp;

                /* Clear Rising Falling edge configuration */
                temp = EXTI_RTSR;
                temp &= ~((uint32_t)iocurrent);
                if((gpiomode & RISING_EDGE) == RISING_EDGE) {
                    temp |= iocurrent;
                }
                EXTI_RTSR = temp;

                temp = EXTI_FTSR;
                temp &= ~((uint32_t)iocurrent);
                if((gpiomode & FALLING_EDGE) == FALLING_EDGE) {
                    temp |= iocurrent;
                }
                EXTI_FTSR = temp;
            }
        }
    position++;
    }
}

void trigger_setup() {
    rcc_periph_clock_enable(RCC_AHBENR);
    HAL_GPIO_Init(GPIOA, GPIO12, GPIO_OSPEED_100MHZ, GPIO_PUPD_NONE, GPIO_MODE_OUTPUT);
    trigger_low();
}

void trigger_high() {
    gpio_set(GPIOA, GPIO12);
    // gpio_toggle(GPIOA, GPIO12);
    // gpio_port_write(GPIOA, GPIO12);
}

void trigger_low() {
    gpio_clear(GPIOA, GPIO12);
}


/*************************************************
* Name:        indcpa_keypair
*
* Description: Generates public and private key for the CPA-secure
*              public-key encryption scheme underlying Kyber
*
* Arguments:   - unsigned char *pk: pointer to output public key (of length KYBER_INDCPA_PUBLICKEYBYTES bytes)
*              - unsigned char *sk: pointer to output private key (of length KYBER_INDCPA_SECRETKEYBYTES bytes)
**************************************************/
void indcpa_keypair(unsigned char *pk, unsigned char *sk) {
    polyvec skpv, skpv_prime;
    poly pkp;
    unsigned char buf[2 * KYBER_SYMBYTES];
    unsigned char *publicseed = buf;
    unsigned char *noiseseed = buf + KYBER_SYMBYTES;
    int i;
    unsigned char nonce = 0;

    randombytes(buf, KYBER_SYMBYTES);
    hash_g(buf, buf, KYBER_SYMBYTES);

    for (i = 0; i < KYBER_K; i++)
        poly_getnoise_eta1(skpv.vec + i, noiseseed, nonce++);

    polyvec_ntt(&skpv);
    
    // i = 0
    matacc_cache32(&pkp, &skpv, &skpv_prime, 0, publicseed, 0);
    poly_invntt(&pkp);

    poly_addnoise_eta1(&pkp, noiseseed, nonce++);
    poly_ntt(&pkp);

    poly_tobytes(pk, &pkp);
    for (i = 1; i < KYBER_K; i++) {
        matacc_opt32(&pkp, &skpv, &skpv_prime, i, publicseed, 0);
        poly_invntt(&pkp);

        poly_addnoise_eta1(&pkp, noiseseed, nonce++);
        poly_ntt(&pkp);

        poly_tobytes(pk+i*KYBER_POLYBYTES, &pkp);
    }

    polyvec_tobytes(sk, &skpv);
    memcpy(pk + KYBER_POLYVECBYTES, publicseed, KYBER_SYMBYTES); // Pack the public seed in the public key
}

/*************************************************
* Name:        indcpa_enc
*
* Description: Encryption function of the CPA-secure
*              public-key encryption scheme underlying Kyber.
*
* Arguments:   - unsigned char *c:          pointer to output ciphertext (of length KYBER_INDCPA_BYTES bytes)
*              - const unsigned char *m:    pointer to input message (of length KYBER_INDCPA_MSGBYTES bytes)
*              - const unsigned char *pk:   pointer to input public key (of length KYBER_INDCPA_PUBLICKEYBYTES bytes)
*              - const unsigned char *coin: pointer to input random coins used as seed (of length KYBER_SYMBYTES bytes)
*                                           to deterministically generate all randomness
**************************************************/
void indcpa_enc(unsigned char *c,
               const unsigned char *m,
               const unsigned char *pk,
               const unsigned char *coins) {
    polyvec sp, sp_prime;
    poly bp;
    poly *pkp = &bp;
    poly *k = &bp;
    poly *v = &sp.vec[0];
    const unsigned char *seed = pk+KYBER_POLYVECBYTES;
    int i;
    unsigned char nonce = 0;

    for (i = 0; i < KYBER_K; i++)
        poly_getnoise_eta1(sp.vec + i, coins, nonce++);

    polyvec_ntt(&sp);

    // i = 0
    matacc_cache32(&bp, &sp, &sp_prime, 0, seed, 1);
    poly_invntt(&bp);
    poly_addnoise_eta2(&bp, coins, nonce++);
    poly_reduce(&bp);
    poly_packcompress(c, &bp, 0);
    for (i = 1; i < KYBER_K; i++) {
        matacc_opt32(&bp, &sp, &sp_prime, i, seed, 1);
        poly_invntt(&bp);

        poly_addnoise_eta2(&bp, coins, nonce++);
        poly_reduce(&bp);

        poly_packcompress(c, &bp, i);
    }

    poly_frombytes(pkp, pk);
    int32_t v_tmp[KYBER_N];
    poly_basemul_opt_16_32(v_tmp, &sp.vec[0], pkp, &sp_prime.vec[0]);

    for (i = 1; i < KYBER_K - 1; i++) {
        poly_frombytes(pkp, pk + i*KYBER_POLYBYTES);
        poly_basemul_acc_opt_32_32(v_tmp, &sp.vec[i], pkp, &sp_prime.vec[i]);
    }
    poly_frombytes(pkp, pk + i*KYBER_POLYBYTES);
    poly_basemul_acc_opt_32_16(v, &sp.vec[i], pkp, &sp_prime.vec[i], v_tmp);

    poly_invntt(v);

    poly_addnoise_eta2(v, coins, nonce++);

    poly_frommsg(k, m);
    poly_add(v, v, k);
    poly_reduce(v);

    poly_compress(c + KYBER_POLYVECCOMPRESSEDBYTES, v);
}

/*************************************************
* Name:        indcpa_enc_cmp
*
* Description: Re-encryption function.
*              Compares the re-encypted ciphertext with the original ciphertext byte per byte.
*              The comparison is performed in a constant time manner.
*
*
* Arguments:   - unsigned char *ct:         pointer to input ciphertext to compare the new ciphertext with (of length KYBER_INDCPA_BYTES bytes)
*              - const unsigned char *m:    pointer to input message (of length KYBER_INDCPA_MSGBYTES bytes)
*              - const unsigned char *pk:   pointer to input public key (of length KYBER_INDCPA_PUBLICKEYBYTES bytes)
*              - const unsigned char *coin: pointer to input random coins used as seed (of length KYBER_SYMBYTES bytes)
*                                           to deterministically generate all randomness
* Returns:     - boolean byte indicating that re-encrypted ciphertext is NOT equal to the original ciphertext
**************************************************/
unsigned char indcpa_enc_cmp(const unsigned char *c,
                             const unsigned char *m,
                             const unsigned char *pk,
                             const unsigned char *coins) {
    uint64_t rc = 0;
    polyvec sp, sp_prime;
    poly bp;
    poly *pkp = &bp;
    poly *k = &bp;
    poly *v = &sp.vec[0];
    const unsigned char *seed = pk+KYBER_POLYVECBYTES;
    int i;
    unsigned char nonce = 0;

    for (i = 0; i < KYBER_K; i++)
        poly_getnoise_eta1(sp.vec + i, coins, nonce++);

    polyvec_ntt(&sp);
    // i = 0
    matacc_cache32(&bp, &sp, &sp_prime, 0, seed, 1);
    poly_invntt(&bp);
    poly_addnoise_eta2(&bp, coins, nonce++);
    poly_reduce(&bp);
    rc |= cmp_poly_packcompress(c, &bp, 0);
    for (i = 1; i < KYBER_K; i++) {
        matacc_opt32(&bp, &sp, &sp_prime, i, seed, 1);
        poly_invntt(&bp);

        poly_addnoise_eta2(&bp, coins, nonce++);
        poly_reduce(&bp);

        rc |= cmp_poly_packcompress(c, &bp, i);
    }

    poly_frombytes(pkp, pk);
    int32_t v_tmp[KYBER_N];
    
    poly_basemul_opt_16_32(v_tmp, &sp.vec[0], pkp, &sp_prime.vec[0]);
    for (i = 1; i < KYBER_K - 1; i++) {
        poly_frombytes(pkp, pk + i*KYBER_POLYBYTES);
        poly_basemul_acc_opt_32_32(v_tmp, &sp.vec[i], pkp, &sp_prime.vec[i]);
    }
    poly_frombytes(pkp, pk + i*KYBER_POLYBYTES);
    poly_basemul_acc_opt_32_16(v, &sp.vec[i], pkp, &sp_prime.vec[i], v_tmp);

    poly_invntt(v);

    poly_addnoise_eta2(v, coins, nonce++);
    poly_frommsg(k, m);
    poly_add(v, v, k);
    poly_reduce(v);

    rc |= cmp_poly_compress(c + KYBER_POLYVECCOMPRESSEDBYTES, v);

    rc = ~rc + 1;
    rc >>= 63;
    return (unsigned char)rc;
}

/*************************************************
* Name:        indcpa_dec
*
* Description: Decryption function of the CPA-secure
*              public-key encryption scheme underlying Kyber.
*
* Arguments:   - unsigned char *m:        pointer to output decrypted message (of length KYBER_INDCPA_MSGBYTES)
*              - const unsigned char *c:  pointer to input ciphertext (of length KYBER_INDCPA_BYTES)
*              - const unsigned char *sk: pointer to input secret key (of length KYBER_INDCPA_SECRETKEYBYTES)
**************************************************/
void __attribute__ ((noinline)) indcpa_dec(unsigned char *m,
                                           const unsigned char *c,
                                           const unsigned char *sk) {
    poly mp, bp;
    poly *v = &bp;
    int32_t r_tmp[KYBER_N];
    int i;
    
    trigger_setup();
    trigger_high();
    poly_unpackdecompress(&mp, c, 0);
    poly_ntt(&mp);
    poly_frombytes_mul_16_32(r_tmp, &mp, sk);
    trigger_low();
    for(i = 1; i < KYBER_K - 1; i++) {
        poly_unpackdecompress(&bp, c, i);
        poly_ntt(&bp);
        poly_frombytes_mul_32_32(r_tmp, &bp, sk + i*KYBER_POLYBYTES);
    }
    poly_unpackdecompress(&bp, c, i);
    poly_ntt(&bp);
    poly_frombytes_mul_32_16(&mp, &bp, sk + i*KYBER_POLYBYTES, r_tmp);

    poly_invntt(&mp);
    poly_decompress(v, c+KYBER_POLYVECCOMPRESSEDBYTES);
    poly_sub(&mp, v, &mp);
    poly_reduce(&mp);

    poly_tomsg(m, &mp);
}
