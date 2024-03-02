#ifndef GPIO_TRIGGER_H
#define GPIO_TRIGGER_H

#include "hal.h"
#include <libopencm3/stm32/f3/memorymap.h>
#include <libopencm3/cm3/common.h>
#include <libopencm3/stm32/f3/rcc.h>
#include <libopencm3/stm32/f3/gpio.h>
#include <libopencm3/stm32/f3/syscfg.h>
#include <libopencm3/stm32/f3/exti.h>

#define GPIO_MODE             (0x00000003U)
#define EXTI_MODE             (0x10000000U)
#define GPIO_MODE_IT          (0x00010000U)
#define GPIO_MODE_EVT         (0x00020000U)
#define RISING_EDGE           (0x00100000U)
#define FALLING_EDGE          (0x00200000U)
#define GPIO_OUTPUT_TYPE      (0x00000010U)

typedef enum 
{
  RESET = 0, 
  SET = !RESET
} FlagStatus, ITStatus;

void trigger_setup();
void trigger_high();
void trigger_low();

#endif