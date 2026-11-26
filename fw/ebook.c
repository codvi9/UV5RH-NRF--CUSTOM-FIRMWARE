#include "ebook.h"

typedef unsigned int u32;
typedef unsigned char u8;
typedef unsigned short u16;

#define R(a) (*(volatile u32*)(a))

#define CRM   0x40021000u
#define GPIOA 0x48000000u
#define SPI1  0x40013000u

#define NOR_CS_HI  (R(GPIOA+0x18)=(1u<<8))
#define NOR_CS_LO  (R(GPIOA+0x28)=(1u<<8))

static void pin_mode(u32 g,int pin,u32 m){ volatile u32*c=(volatile u32*)g; u32 sh=2u*(u32)pin; *c=(*c&~(3u<<sh))|(m<<sh); }
static void pin_af(u32 g,int pin,u32 af){ if(pin>=8){ volatile u32*v=(volatile u32*)(g+0x24u); *v=(*v&~(0xFu<<((pin-8)*4)))|(af<<((pin-8)*4)); } else { volatile u32*v=(volatile u32*)(g+0x20u); *v=(*v&~(0xFu<<(pin*4)))|(af<<(pin*4)); } }

static u8 spi_xfer(u8 b){
  while(!(R(SPI1+0x08)&(1u<<1)));
  R(SPI1+0x0C)=b;
  while(!(R(SPI1+0x08)&1u));
  return (u8)R(SPI1+0x0C);
}

void nor_init(void){
  R(CRM+0x14)|=(1u<<17); (void)R(CRM+0x14);
  R(CRM+0x18)|=(1u<<12); (void)R(CRM+0x18);
  pin_mode(GPIOA,5,2); pin_af(GPIOA,5,0);
  pin_mode(GPIOA,6,2); pin_af(GPIOA,6,0);
  pin_mode(GPIOA,7,2); pin_af(GPIOA,7,0);
  pin_mode(GPIOA,8,1); NOR_CS_HI;
  R(SPI1+0x04)=0;
  R(SPI1)=(1u<<2)|(1u<<9)|(1u<<8)|(1u<<6)|(1u<<3);
}

u32 nor_id(void){
  u32 id=0;
  NOR_CS_LO; spi_xfer(0x9F);
  id=(id<<8)|spi_xfer(0); id=(id<<8)|spi_xfer(0); id=(id<<8)|spi_xfer(0);
  NOR_CS_HI;
  return id;
}

static void nor_wren(void){ NOR_CS_LO; spi_xfer(0x06); NOR_CS_HI; }

static void nor_wait(void){
  for(volatile u32 i=0;i<2000000u;i++){
    NOR_CS_LO; spi_xfer(0x05); u8 s=spi_xfer(0); NOR_CS_HI;
    if(!(s&1u)) return;
  }
}

void nor_read(u32 addr,void*buf,u32 len){
  u8*p=(u8*)buf;
  NOR_CS_LO;
  spi_xfer(0x03);
  spi_xfer((u8)(addr>>16)); spi_xfer((u8)(addr>>8)); spi_xfer((u8)addr);
  for(u32 i=0;i<len;i++) p[i]=spi_xfer(0);
  NOR_CS_HI;
}

void nor_erase_4k(u32 addr){
  nor_wren();
  NOR_CS_LO;
  spi_xfer(0x20);
  spi_xfer((u8)(addr>>16)); spi_xfer((u8)(addr>>8)); spi_xfer((u8)addr);
  NOR_CS_HI;
  nor_wait();
}

void nor_write_page(u32 addr,const void*buf,u32 len){
  const u8*p=(const u8*)buf;
  if(len>256u) len=256u;
  nor_wren();
  NOR_CS_LO;
  spi_xfer(0x02);
  spi_xfer((u8)(addr>>16)); spi_xfer((u8)(addr>>8)); spi_xfer((u8)addr);
  for(u32 i=0;i<len;i++) spi_xfer(p[i]);
  NOR_CS_HI;
  nor_wait();
}
