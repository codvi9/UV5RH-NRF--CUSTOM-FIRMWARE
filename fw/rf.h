#pragma once
#include <stdint.h>
void rf_init_pins(void);
void rf_write(uint8_t addr, uint16_t val);
uint16_t rf_read(uint8_t addr);
void rf_power_init(void);
void rf_set_freq(uint32_t hz);
void rf_rx_on(int uhf);
void rf_tx_band(int uhf);
void rf_af_rx(uint8_t vol);
void rf_af_mute(void);
void rf_idle(void);
uint16_t rf_rssi(void);
