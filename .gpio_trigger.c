#include "gpio_trigger.h"

// https://github.com/newaetech/chipwhisperer/blob/develop/hardware/victims/firmware/hal/stm32f3/stm32f3_hal_lowlevel.c#L661
// https://github.com/libopencm3/libopencm3/blob/9545471e4861090a77f79c4458eb19ec771e23d9/include/libopencm3/stm32/common/gpio_common_f234.h#L63

// Mappings foireux entre la lib CW et libopencm3
#define GPIO_MODER_MODER0 GPIO_MODE_ANALOG
#define GPIO_OSPEEDER_OSPEEDR0 GPIO_OSPEED_2MHZ
#define GPIO_OTYPER_OT_0 GPIO_OTYPE_PP
#define GPIO_PUPDR_PUPDR0 GPIO_PUPD_NONE

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
                __HAL_RCC_SYSCFG_CLK_ENABLE(); // ça marche de laisser ça comme ça ???????

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
