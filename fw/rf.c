#include "rf.h"
#include "rf_init.h"

#define R(a) (*(volatile unsigned int*)(a))
#define GPIOA 0x48000000u
#define GPIOC 0x48000800u
#define CRM   0x40021000u

#define LE_BIT  (1u<<13)
#define SCK_BIT (1u<<2)
#define SDA_BIT (1u<<3)

static inline void spin(void){ __asm volatile("nop"); __asm volatile("nop"); __asm volatile("nop"); }

void rf_init_pins(void){
  R(CRM+0x14) |= (1u<<17)|(1u<<19);
  (void)R(CRM+0x14);
  R(GPIOA) = (R(GPIOA) & ~((3u<<4)|(3u<<6))) | (1u<<4) | (1u<<6);
  R(GPIOA+0x0C) &= ~((3u<<4)|(3u<<6));
  R(GPIOA+0x18) &= ~((1u<<2)|(1u<<3));
  R(GPIOC) = (R(GPIOC) & ~(3u<<26)) | (1u<<26);
  R(GPIOC+0x18) = LE_BIT;
}

static void sck(int high){ if(high) R(GPIOA+0x18)=SCK_BIT; else R(GPIOA+0x28)=SCK_BIT; }
static void sda(int high){ if(high) R(GPIOA+0x18)=SDA_BIT; else R(GPIOA+0x28)=SDA_BIT; }
static void le(int high){ if(high) R(GPIOC+0x18)=LE_BIT; else R(GPIOC+0x28)=LE_BIT; }

static void write_bits(uint8_t byte){
  for(uint8_t m=0x80; m; m>>=1){
    sck(0); sda((byte & m) ? 1 : 0); spin(); spin();
    sck(1); spin(); spin();
  }
}
static uint16_t read_bits(void){
  uint16_t d=0;
  for(int i=0;i<16;i++){
    d <<= 1;
    sck(1); spin();
    if(R(GPIOA+0x10) & SDA_BIT) d |= 1;
    spin(); sck(0); spin();
  }
  return d;
}

void rf_write(uint8_t addr, uint16_t val){
  le(0); spin();
  write_bits(addr & 0x7F);
  write_bits((uint8_t)(val>>8));
  write_bits((uint8_t)val);
  le(1); spin();
  sck(0);
}

uint16_t rf_read(uint8_t addr){
  le(0); spin();
  write_bits(addr | 0x80);
  sck(0); spin();
  R(GPIOA) = (R(GPIOA) & ~(3u<<6));
  R(GPIOA+0x0C) = (R(GPIOA+0x0C) & ~(3u<<6)) | (1u<<6);
  spin();
  uint16_t d = read_bits();
  R(GPIOA) = (R(GPIOA) & ~(3u<<6)) | (1u<<6);
  R(GPIOA+0x0C) &= ~(3u<<6);
  le(1); spin();
  sda(0); sck(0);
  return d;
}

static void gpio_bit(uint16_t bit, int high){
  uint16_t v = rf_read(0x33);
  v &= (uint16_t)~(bit << 8);
  if(high) v |= bit; else v &= (uint16_t)~bit;
  rf_write(0x33, v);
}

void rf_power_init(void){
  for(int i=0;i<RF_INIT_COUNT;i++) rf_write((uint8_t)RF_INIT_TBL[i][0], RF_INIT_TBL[i][1]);
  uint16_t sc = rf_read(0x31);
  rf_write(0x31, (uint16_t)(sc & ~0x0002));
  rf_write(0x43, 0x3028);   /* wide bandwidth */
}

void rf_set_freq(uint32_t hz){
  uint32_t word = hz / 10;
  rf_write(0x38, (uint16_t)word);
  rf_write(0x39, (uint16_t)(word >> 16));
}

void rf_rx_on(int uhf){
  rf_write(0x30, 0x0200);
  rf_write(0x30, 0xBFF1);
  rf_write(0x2B, 0x0300);
  gpio_bit(1u<<5, !uhf);
  gpio_bit(1u<<6, uhf);
}

void rf_af_rx(uint8_t vol){
  rf_write(0x47, 0x6040 | 0x0100);                       /* AF_OUT_BASE | RxAudio */
  rf_write(0x48, (uint16_t)(0x8000 | ((vol & 0x3F) << 4) | 15));
}

void rf_af_mute(void){
  rf_write(0x47, 0x6040);
}

void rf_tx_band(int uhf){
  gpio_bit(1u<<3, !uhf);
  gpio_bit(1u<<4, uhf);
}

void rf_idle(void){ rf_write(0x30, 0x0000); }

uint16_t rf_rssi(void){ return (uint16_t)(rf_read(0x67) & 0x01FF); }
