#include "font.h"
#include "rf.h"
#include "uart.h"
#include "ebook.h"
typedef unsigned int u32; typedef unsigned char u8; typedef unsigned short u16;
#define R(a) (*(volatile u32*)(a))
#define CRM 0x40021000u
#define GPIOA 0x48000000u
#define GPIOB 0x48000400u
#define GPIOC 0x48000800u
#define GPIOF 0x48001400u
#define SPI2 0x40003800u
#define CS_BIT (1u<<2)
#define RST_BIT (1u<<12)
#define DC_BIT (1u<<14)
#define BLACK 0x0000
#define WHITE 0xFFFF
#define RED 0xF800
#define GREEN 0x07E0
#define BLUE 0x001F
#define YELLOW 0xFFE0
#define GREY 0x8410

static void spin(u32 n){ while(n--) __asm volatile("nop"); }
static int sys_fast=0;   /* 1 = 48 MHz (PLL), 0 = 8 MHz (HICK) */
static void delay_ms(u32 ms){ spin(ms*(sys_fast?12000u:2000u)); }
static void pin_mode(u32 g,int pin,u32 m){ volatile u32*c=(volatile u32*)g; u32 sh=2u*(u32)pin; *c=(*c&~(3u<<sh))|(m<<sh); }
static void pin_af(u32 g,int pin,u32 af){ if(pin>=8){ volatile u32*v=(volatile u32*)(g+0x24u); *v=(*v&~(0xFu<<((pin-8)*4)))|(af<<((pin-8)*4)); } else { volatile u32*v=(volatile u32*)(g+0x20u); *v=(*v&~(0xFu<<(pin*4)))|(af<<(pin*4)); } }
static void spi_byte(u8 b){ while(!(R(SPI2+0x08)&(1u<<1))); R(SPI2+0x0C)=b; }
static void spi_drain(void){ while(R(SPI2+0x08)&(1u<<7)); }
static void lcd_cmd(u8 c){ R(GPIOB+0x28)=DC_BIT; R(GPIOB+0x28)=CS_BIT; spi_byte(c); spi_drain(); R(GPIOB+0x18)=CS_BIT; }
static void lcd_data(const u8*d,int n){ R(GPIOB+0x18)=DC_BIT; R(GPIOB+0x28)=CS_BIT; for(int i=0;i<n;i++) spi_byte(d[i]); spi_drain(); R(GPIOB+0x18)=CS_BIT; }
static void lcd_cd(u8 c,const u8*d,int n){ lcd_cmd(c); if(n) lcd_data(d,n); }
static void lcd_init(void){
  R(GPIOB+0x18)=RST_BIT; delay_ms(10); R(GPIOB+0x28)=RST_BIT; delay_ms(10); R(GPIOB+0x18)=RST_BIT; delay_ms(120);
  lcd_cmd(0x11); delay_ms(120);
  { u8 a[]={0x05,0x3A,0x3A}; lcd_cd(0xB1,a,3); }
  { u8 a[]={0x05,0x3A,0x3A}; lcd_cd(0xB2,a,3); }
  { u8 a[]={0x05,0x3A,0x3A,0x05,0x3A,0x3A}; lcd_cd(0xB3,a,6); }
  { u8 a[]={0x03}; lcd_cd(0xB4,a,1); }
  { u8 a[]={0x62,0x02,0x04}; lcd_cd(0xC0,a,3); }
  { u8 a[]={0xC0}; lcd_cd(0xC1,a,1); }
  { u8 a[]={0x0D,0x00}; lcd_cd(0xC2,a,2); }
  { u8 a[]={0x8D,0x6A}; lcd_cd(0xC3,a,2); }
  { u8 a[]={0x8D,0xEE}; lcd_cd(0xC4,a,2); }
  { u8 a[]={0x12}; lcd_cd(0xC5,a,1); }
  { u8 a[]={0x03,0x1B,0x12,0x11,0x3F,0x3A,0x32,0x34,0x2F,0x2B,0x30,0x3A,0x00,0x00,0x01,0x05}; lcd_cd(0xE0,a,16); }
  { u8 a[]={0x03,0x1B,0x12,0x11,0x32,0x2F,0x2A,0x2F,0x2E,0x2C,0x35,0x3F,0x00,0x00,0x01,0x05}; lcd_cd(0xE1,a,16); }
  { u8 a[]={0x8C}; lcd_cd(0xFC,a,1); }
  { u8 a[]={0x60}; lcd_cd(0x36,a,1); }
  { u8 a[]={0x05}; lcd_cd(0x3A,a,1); }
  delay_ms(10); lcd_cmd(0x29);
}
static void set_win(u16 x0,u16 y0,u16 x1,u16 y1){ u8 c[4]={(u8)(x0>>8),(u8)x0,(u8)(x1>>8),(u8)x1}; u8 r[4]={(u8)(y0>>8),(u8)y0,(u8)(y1>>8),(u8)y1}; lcd_cd(0x2A,c,4); lcd_cd(0x2B,r,4); lcd_cmd(0x2C); }
static void fill_rect(u16 x,u16 y,u16 w,u16 h,u16 col){ if(!w||!h) return; set_win(x,y,(u16)(x+w-1),(u16)(y+h-1)); R(GPIOB+0x18)=DC_BIT; R(GPIOB+0x28)=CS_BIT; for(u32 i=0;i<(u32)w*h;i++){ spi_byte((u8)(col>>8)); spi_byte((u8)col);} spi_drain(); R(GPIOB+0x18)=CS_BIT; }
static const u8* glyph(char ch){ for(int i=0;FONT_MAP[i];i++) if(FONT_MAP[i]==ch) return FONT_5X7[i]; return FONT_5X7[0]; }
static void draw_char(u16 x,u16 y,char ch,u16 fg,u16 bg,u8 sc){
  const u8*g=glyph(ch);
  if(sc==1){ set_win(x,y,(u16)(x+5),(u16)(y+7)); R(GPIOB+0x18)=DC_BIT; R(GPIOB+0x28)=CS_BIT;
    for(int r=0;r<8;r++) for(int c=0;c<6;c++){ u16 v=(c<5&&r<7&&(g[c]&(1u<<r)))?fg:bg; spi_byte((u8)(v>>8)); spi_byte((u8)v);} spi_drain(); R(GPIOB+0x18)=CS_BIT; return; }
  for(int r=0;r<8;r++) for(int c=0;c<6;c++){ u16 v=(c<5&&r<7&&(g[c]&(1u<<r)))?fg:bg; fill_rect((u16)(x+c*sc),(u16)(y+r*sc),sc,sc,v); }
}
static void draw_text(u16 x,u16 y,const char*s,u16 fg,u16 bg,u8 sc){ while(*s){ draw_char(x,y,*s++,fg,bg,sc); x=(u16)(x+6*sc);} }

/* ---- battery: PA1 = ADC_IN1 ---- */
#define ADC1 0x40012400u
static u8 bat_pct=0; static u16 bat_mv=0;
static void bat_init(void){
  R(CRM+0x18)|=(1u<<9); (void)R(CRM+0x18);
  pin_mode(GPIOA,1,3);                                  /* analog */
  R(ADC1+0x10)=(R(ADC1+0x10)&~(7u<<3))|(7u<<3);         /* SPT2 ch1: 239.5 cycles */
  R(ADC1+0x34)=0x00000001u;                             /* OSQ3: osn1 = ch1 */
  R(ADC1+0x2C)=0x00000000u;                             /* oclen = 0 */
  R(ADC1+0x08)=1u;                                      /* adcen */
  delay_ms(3);
  R(ADC1+0x08)|=(1u<<3);                                /* calibration init */
  for(int i=0;i<20000 && (R(ADC1+0x08)&(1u<<3));i++);
  R(ADC1+0x08)|=(1u<<2);                                /* calibration start */
  for(int i=0;i<20000 && (R(ADC1+0x08)&(1u<<2));i++);
}
static u16 bat_raw(void){
  R(ADC1+0x08)=(R(ADC1+0x08)&~(7u<<17))|(7u<<17);       /* software trigger */
  R(ADC1+0x08)|=(1u<<20);                               /* octen */
  R(ADC1+0x08)|=(1u<<22);                               /* ocswtrg */
  for(volatile int i=0;i<40000;i++){ if(R(ADC1+0x00)&2u) break; }
  u16 v=(u16)(R(ADC1+0x4C)&0x0FFFu);
  R(ADC1+0x00)&=~2u;
  return v;
}
/* divider 1:2 assumed (Vbat -> PA1). 3300 mV = 0 %, 4200 mV = 100 %. */
static void bat_update(void){
  u32 acc=0; for(int i=0;i<4;i++) acc+=bat_raw();
  u32 raw=(acc+2u)/4u;
  bat_mv=(u16)((raw*3300u*2u)/4095u);
  int p=(int)(((int)bat_mv-3300)*100/900);
  if(p<0) p=0; if(p>100) p=100;
  bat_pct=(u8)p;
}

static u16 g_matrix=0;
static void kbd_init(void){ pin_mode(GPIOB,8,1); pin_mode(GPIOB,9,1); pin_mode(GPIOB,10,1); pin_mode(GPIOB,11,1); pin_mode(GPIOB,3,0); pin_mode(GPIOB,4,0); pin_mode(GPIOB,5,0); pin_mode(GPIOB,6,0); R(GPIOB+0x0C)=(R(GPIOB+0x0C)&~(0xFFu<<6))|(0x55u<<6); R(GPIOB+0x18)=0xFu<<8; }
static void kbd_scan(void){ g_matrix=0; for(int c=0;c<4;c++){ R(GPIOB+0x18)=0xFu<<8; R(GPIOB+0x28)=1u<<(8+c); spin(200); u32 idt=(R(GPIOB+0x10)>>3)&0xF; g_matrix|=(u16)(idt<<(c*4)); R(GPIOB+0x18)=0xFu<<8; } }
/* round0: all columns released high, PB3..PB6 read the direct keys
   (AB / VM / SCAN / side-2 = FM radio). */
static int side2_pressed(void){
  R(GPIOB+0x18)=0xFu<<8;
  spin(300);
  return ((R(GPIOB+0x10)>>6)&1u)==0u;
}
enum { K_NONE=0,K_1=1,K_2,K_3,K_4,K_5,K_6,K_7,K_8,K_9,K_0,K_STAR,K_HASH,K_UP,K_DN,K_MENU,K_EXIT,K_AB,K_MR,K_SCANK,K_SOS };
static int key_id(void){
  switch(g_matrix){
    case 0xFFFE:return K_1; case 0xFFFD:return K_2; case 0xFFFB:return K_3;
    case 0xFFEF:return K_4; case 0xFFDF:return K_5; case 0xFFBF:return K_6;
    case 0xFEFF:return K_7; case 0xFDFF:return K_8; case 0xFBFF:return K_9;
    case 0xFF7F:return K_0; case 0xFFF7:return K_STAR; case 0xF7FF:return K_HASH;
    case 0xEFFF:return K_UP; case 0xDFFF:return K_DN;
    case 0xBFFF:return K_MENU; case 0x7FFF:return K_EXIT;
    case 0xEEEE:return K_AB; case 0xDDDD:return K_MR; case 0xBBBB:return K_SCANK; case 0x7777:return K_SOS;
  }
  return K_NONE;
}
static u32 freq[2]={438500000u,145000000u};
static int band=0, mr=0, chan=1, sq_on=1, f_latch=0, locked=0, tx=0, mod=0;
static u32 step_khz10=250;         /* 25.0 kHz, in units of 0.1 kHz */
static const u16 step_tbl[4]={25,50,125,250};
static int step_i=3;
/* TX power: 0x37 has only two valid values (0x1D00 low / 0x1D0F high, per
   stock 0x08008F68). The ramp in 0x36[15:8] is the usable knob - stock uses
   100 for full power. Keep 0x37 at 0x1D0F so every step still transmits. */
static const u8 pwr_ramp[5]={20,40,60,80,100};
static int tx_i=4;                 /* index into pwr_ramp */
static int beep_on=1;
static int roger_on=1;             /* roger beep at end of TX */
static int dw=0, dw_b=0; static u32 dw_t=0;
static int menu_on=0, menu_sel=0, sq_open=1;
static u32 sq_th=0, sq_low=0;
static char msg[14]={0}; static u32 msg_t=0;

static void led_tx(int on){ if(on) R(GPIOA+0x18)=(1u<<13); else R(GPIOA+0x28)=(1u<<13); }
static void led_rx(int on){ if(on) R(GPIOA+0x18)=(1u<<14); else R(GPIOA+0x28)=(1u<<14); }
static void draw_status(void){
  fill_rect(0,112,160,16,BLACK);
  if(msg[0]) draw_text(2,114,msg,GREY,BLACK,1);
  else if(f_latch) draw_text(2,114,"F",YELLOW,BLACK,1);
  else if(locked) draw_text(2,114,"LOCK",RED,BLACK,1);
  else draw_text(2,114,"MENU  EXIT",GREY,BLACK,1);
  draw_text(96,114,"A/B",WHITE,BLACK,1);
}
static u8 bat_shown=255;
static void draw_bat(void){
  char p[5]; int v=bat_pct;
  p[0]=(char)('0'+(v/100)%10); p[1]=(char)('0'+(v/10)%10); p[2]=(char)('0'+v%10); p[3]='%'; p[4]=0;
  fill_rect(120,4,40,9,BLUE);
  draw_text(122,4,(v>=100)?p:(p+1),YELLOW,BLUE,1);
  bat_shown=bat_pct;
}
static void draw_top(void){
  fill_rect(0,0,160,15,BLUE);
  char c[8]; c[0]='H'; c[1]='-';
  c[2]=(char)('0'+(chan/1000)%10); c[3]=(char)('0'+(chan/100)%10); c[4]=(char)('0'+(chan/10)%10); c[5]=(char)('0'+chan%10); c[6]=0;
  draw_text(3,4,c,WHITE,BLUE,1);
  { char m[5]; m[0]=mod?'A':'F'; m[1]='M'; m[2]=' ';
    m[3]=(char)(tx_i<=1?'L':(tx_i<=3?'M':'H')); m[4]=0;
    draw_text(52,4,m,WHITE,BLUE,1); }
  if(tx) draw_text(78,4,"TX",RED,BLUE,1); else if(sq_open) draw_text(78,4,"RX",GREEN,BLUE,1);
  { char b[4]; b[0]='S'; b[1]='Q'; b[2]=sq_on?'1':'0'; b[3]=0; fill_rect(96,4,24,9,BLUE); draw_text(98,4,b,WHITE,BLUE,1); }
  draw_bat();
}
static void draw_a(void){
  fill_rect(0,16,160,48,BLACK);
  draw_text(2,18, band?"B":"A", YELLOW,BLACK,2);
  draw_text(2,38, mr?"MR":"VFO", WHITE,BLACK,1);
  { u32 hz=freq[band]; u32 mhz=hz/1000000u, k=hz%1000000u/1000u; char f[8];
    f[0]=(char)('0'+(mhz/100)%10); f[1]=(char)('0'+(mhz/10)%10); f[2]=(char)('0'+mhz%10); f[3]='.';
    f[4]=(char)('0'+(k/100)%10); f[5]=(char)('0'+(k/10)%10); f[6]=(char)('0'+k%10); f[7]=0;
    draw_text(32,18,f,YELLOW,BLACK,3); }
  { const char*L[4]={"2.5K","5K","12.5K","25K"}; draw_text(2,50,L[step_i],GREY,BLACK,1); }
}
static void draw_b(void){
  fill_rect(0,60,160,16,BLACK);
  { u32 hz=freq[band^1]; u32 mhz=hz/1000000u, fr=(hz/100u)%10000u; char f[10];
    f[0]=(char)('0'+(mhz/100)%10); f[1]=(char)('0'+(mhz/10)%10); f[2]=(char)('0'+mhz%10); f[3]='.';
    f[4]=(char)('0'+(fr/1000)%10); f[5]=(char)('0'+(fr/100)%10); f[6]=(char)('0'+(fr/10)%10); f[7]=(char)('0'+fr%10); f[8]=0;
    draw_text(3,61,f,WHITE,BLACK,1); }
  draw_text(110,61,"FM H",WHITE,BLACK,1);
}
static void draw_meter(u16 r){
  fill_rect(0,80,160,30,BLACK);
  draw_text(2,81,"RSSI",GREY,BLACK,1);
  { char b[4]; b[0]=(char)('0'+(r/100)%10); b[1]=(char)('0'+(r/10)%10); b[2]=(char)('0'+r%10); b[3]=0; draw_text(30,81,b,YELLOW,BLACK,1); }
  { u16 w=(u16)((u32)r*150u/511u); if(w>150) w=150;
    u16 w200=(u16)((u32)400u*150u/511u);
    fill_rect(2,90,150,7,0x2104);
    if(w<=w200){ fill_rect(2,90,w,7,WHITE); }
    else { fill_rect(2,90,w200,7,WHITE); fill_rect((u16)(2+w200),90,(u16)(w-w200),7,RED); } }
  { u16 raw=rf_read(0x67); const char *H="0123456789ABCDEF"; char x[7]; x[0]='R'; x[1]='W'; x[2]=':'; x[3]=H[(raw>>8)&15]; x[4]=H[(raw>>4)&15]; x[5]=H[raw&15]; x[6]=0; draw_text(2,100,x,GREY,BLACK,1); }
}
static void retune(void);
static void apply_sq(void);
static u16 spec_buf[32];
static void about_page(void){
  for(int w=0; w<100; w++){ kbd_scan(); if(!key_id()) break; delay_ms(20); }
  fill_rect(0,16,160,112,BLACK);
  draw_text(12,40,"FEATURE",YELLOW,BLACK,3);
  draw_text(58,66,"OS",YELLOW,BLACK,3);
  draw_text(44,92,"By CODVI9",WHITE,BLACK,1);
  { char v[10]; v[0]='B'; v[1]='A'; v[2]='T'; v[3]=' ';
    v[4]=(char)('0'+(bat_mv/1000)%10); v[5]='.';
    v[6]=(char)('0'+(bat_mv/100)%10); v[7]=(char)('0'+(bat_mv/10)%10); v[8]='V'; v[9]=0;
    draw_text(44,104,v,GREY,BLACK,1); }
  for(int i=0;i<600;i++){ kbd_scan(); if(key_id()){ while(1){ kbd_scan(); if(!key_id()) break; delay_ms(20);} break; } delay_ms(20); }
  fill_rect(0,16,160,112,BLACK);
}
static void i2cd(void){ for(volatile int i=0;i<40;i++); }
static u32 g_sclp=GPIOC; static int g_scln=15;
static u32 g_sdap=GPIOA; static int g_sdan=3;
static void scl(int h){ if(h) R(g_sclp+0x18)=(1u<<g_scln); else R(g_sclp+0x28)=(1u<<g_scln); }
static void sdao(int h){ if(h) R(g_sdap+0x18)=(1u<<g_sdan); else R(g_sdap+0x28)=(1u<<g_sdan); }
static void sdain(void){ u32 sh=2u*(u32)g_sdan; R(g_sdap)=(R(g_sdap)&~(3u<<sh)); R(g_sdap+0x0C)=(R(g_sdap+0x0C)&~(3u<<sh))|(1u<<sh); }
static void sdaout(void){ u32 sh=2u*(u32)g_sdan; R(g_sdap)=(R(g_sdap)&~(3u<<sh))|(1u<<sh); R(g_sdap+0x0C)&=~(3u<<sh); }
static void i2c_pins(u32 sp,int sn,u32 dp,int dn){
  /* PA3 is shared with the FD6818 3-wire SDA; deselect it (LE low) so the
     RF chip releases the line before we talk I2C. */
  R(GPIOC+0x28)=(1u<<13);
  g_sclp=sp; g_scln=sn; g_sdap=dp; g_sdan=dn;
  pin_mode(sp,sn,1); R(sp+0x18)=(1u<<sn);
  pin_mode(dp,dn,1); R(dp+0x18)=(1u<<dn);
  i2cd();
}
static void i2c_start(void){ sdaout(); sdao(1); scl(1); i2cd(); sdao(0); i2cd(); scl(0); i2cd(); }
static void i2c_stop(void){ sdaout(); sdao(0); scl(1); i2cd(); sdao(1); i2cd(); }
static void i2c_byte(u8 b){ for(int i=0;i<8;i++){ sdao((b&0x80)?1:0); b<<=1; i2cd(); scl(1); i2cd(); scl(0); i2cd(); }
  sdain(); i2cd(); scl(1); i2cd(); scl(0); i2cd(); sdaout(); }
static int i2c_ack_byte(u8 b){ for(int i=0;i<8;i++){ sdao((b&0x80)?1:0); b<<=1; i2cd(); scl(1); i2cd(); scl(0); i2cd(); }
  sdain(); i2cd(); scl(1); i2cd(); int ack=(R(GPIOA+0x10)&(1u<<3))?0:1; scl(0); i2cd(); sdaout(); return ack; }
static int i2c_probe(u8 addr){ i2c_start(); int ack=i2c_ack_byte((u8)(addr<<1)); i2c_stop(); return ack; }
static u8 i2c_rb(int ack){
  u8 v=0; sdain();
  for(int i=0;i<8;i++){ i2cd(); scl(1); i2cd();
    v=(u8)((v<<1) | ((R(GPIOA+0x10)&(1u<<3))?1:0)); scl(0); i2cd(); }
  sdaout(); sdao(ack?0:1); i2cd(); scl(1); i2cd(); scl(0); i2cd(); sdao(1);
  return v;
}
static u32 fm_khz=98000;
static u16 fm_status=0; static int fm_stc=0;
/* RDA5807M at I2C 0x10 (write) / 0x11 (read), 2-byte registers:
   write = {reg, hi, lo}; a read returns the 0x0A status word,
   bit15 = STC (tune complete), bit14 = SF (seek fail). */
static void rda_write(u8 reg,u16 v){
  i2c_start();
  if(i2c_ack_byte(0x20)){ i2c_byte(reg); i2c_byte((u8)(v>>8)); i2c_byte((u8)v); }
  i2c_stop();
}
static void rda_read(void){
  fm_status=0xFFFF;
  i2c_start();
  if(i2c_ack_byte(0x21)){ u8 h=i2c_rb(1), l=i2c_rb(0); fm_status=(u16)(((u16)h<<8)|l); }
  i2c_stop();
}
static int fm_clk=0;   /* CLK_MODE[1:0]: 0=32.768k 1=12M 2=24M 3=13M */
static void fm_init(void){
  i2c_pins(GPIOC,15,GPIOA,3);
  rda_write(0x02,(u16)(0xC001|((u16)fm_clk<<6)));  /* DHIZ|DMUTE|ENABLE + CLK_MODE */
  delay_ms(60);
  rda_write(0x03,0x0000);
  rda_write(0x04,0x0400);        /* 50 us de-emphasis */
  rda_write(0x05,0x888F);        /* INT_MODE, VOLUME=15 (0x8880 = volume 0 = silent!) */
  rda_write(0x06,0x0000);
  rda_write(0x07,0x0000);
  rda_write(0x02,(u16)(0xC001|((u16)fm_clk<<6)));
  delay_ms(20);
}
static void fm_tune(void){
  u16 ch=(u16)((fm_khz-87000u)/100u);
  rda_write(0x03,(u16)((ch<<6)|0x0010u));   /* CHAN | TUNE, 100 kHz, 87-108 */
  fm_stc=0;
  for(int i=0;i<40;i++){ delay_ms(10); rda_read(); if(fm_status&0xC000u){ fm_stc=(fm_status&0x8000u)?1:0; break; } }
}
static void fm_show(void){
  draw_text(2,18,"FM RADIO",YELLOW,BLACK,1);
  { char b[8]; u32 m=fm_khz/1000u, t=(fm_khz/100u)%10;
    b[0]=(char)('0'+(m/100)%10); b[1]=(char)('0'+(m/10)%10); b[2]=(char)('0'+m%10); b[3]='.';
    b[4]=(char)('0'+t); b[5]='0'; b[6]=0;
    draw_text(10,40,b,YELLOW,BLACK,3); }
  draw_text(2,58,"RDA5807M  ",GREY,BLACK,1);
  draw_text(2,70, fm_stc?"TUNED ":"TUNING", fm_stc?GREEN:RED, BLACK,1);
  { const char*H="0123456789ABCDEF"; char x[8];
    x[0]='S'; x[1]='T'; x[2]=':';
    x[3]=H[(fm_status>>12)&15]; x[4]=H[(fm_status>>8)&15];
    x[5]=H[(fm_status>>4)&15]; x[6]=H[fm_status&15]; x[7]=0;
    draw_text(60,70,x,GREY,BLACK,1); }
  draw_text(2,84,"1=clk mode  EXIT",GREY,BLACK,1);
  { char m[6]; m[0]='C'; m[1]='L'; m[2]='K'; m[3]=(char)('0'+fm_clk); m[4]=0;
    draw_text(140,84,m,YELLOW,BLACK,1); }
}
static void fm_page(void){
  for(int w=0; w<100; w++){ kbd_scan(); if(!key_id()) break; delay_ms(20); }
  fill_rect(0,16,160,112,BLACK);
  rf_idle(); rf_write(0x47,0x6040);   /* mute the FM demod AF; RDA drives audio */
  R(GPIOB+0x18)=(1u<<7);              /* PB7 high = speaker connected */
  fm_init(); fm_tune(); fm_show();
  for(;;){
    kbd_scan(); int k=key_id();
    if(k==K_UP){ if(fm_khz<108000) fm_khz+=100; fm_tune(); fm_show(); }
    else if(k==K_DN){ if(fm_khz>87000) fm_khz-=100; fm_tune(); fm_show(); }
    else if(k==K_1){ fm_clk=(fm_clk+1)&3; fm_init(); fm_tune(); fm_show(); }
    else if(k==K_5){ rda_read(); fm_show(); }
    else if(k==K_EXIT||k==K_MENU){ while(1){ kbd_scan(); if(!key_id()) break; delay_ms(20);} break; }
    delay_ms(60);
  }
  fill_rect(0,16,160,112,BLACK);
  rf_init_pins(); retune(); apply_sq(); draw_top();
}

static void screen_a(void){ draw_a(); draw_b(); draw_meter(0); draw_status(); }
static void spec_run(void){
  u32 base0 = freq[band] - 800000u;
  for(int w=0; w<100; w++){ kbd_scan(); if(!key_id()) break; delay_ms(20); }
  for(;;){
    kbd_scan();
    int k=key_id();
    if(k){ while(1){ kbd_scan(); if(!key_id()) break; delay_ms(20); } break; }
    for(int i=0;i<32;i++){
      rf_set_freq(base0 + (u32)i*50000u);
      rf_write(0x30,0x0200); rf_write(0x30,0xBFF1);
      for(volatile int j=0;j<16000;j++);
      (void)rf_rssi();
      for(volatile int j=0;j<4000;j++);
      spec_buf[i]=rf_rssi();
    }
    fill_rect(0,16,160,96,BLACK);
    draw_text(2,17,"SPECTRUM",YELLOW,BLACK,1);
    { u16 mn=spec_buf[0], mx=spec_buf[0];
      for(int i=1;i<32;i++){ if(spec_buf[i]<mn) mn=spec_buf[i]; if(spec_buf[i]>mx) mx=spec_buf[i]; }
      if(mx<=mn) mx=(u16)(mn+1);
      for(int i=0;i<32;i++){
        u16 d = (spec_buf[i] > 140) ? (u16)(spec_buf[i]-140) : 0;
        u16 h=(u16)((u32)d * 74u / 360u);
        if(h>74) h=74;
        if(h<1) h=1;
        u16 col=(i%8==0)?YELLOW:WHITE;
        fill_rect((u16)(2+i*5),(u16)(88-h),4,h,col);
      } }
    { int pk=0; for(int i=1;i<32;i++) if(spec_buf[i]>spec_buf[pk]) pk=i;
      u32 pf=base0+(u32)pk*50000u; u32 pm=pf/1000000u, pt=(pf/1000u)%1000u;
      char pb[12]; pb[0]='P'; pb[1]=' ';
      pb[2]=(char)('0'+(pm/100)%10); pb[3]=(char)('0'+(pm/10)%10); pb[4]=(char)('0'+pm%10); pb[5]='.';
      pb[6]=(char)('0'+(pt/100)%10); pb[7]=(char)('0'+(pt/10)%10); pb[8]=(char)('0'+pt%10); pb[9]=0;
      fill_rect(78,18,82,10,BLACK);
      draw_text(80,19,pb,YELLOW,BLACK,1); }
    for(int i=0;i<5;i++){
      u16 x=(u16)(2+i*40); if(x>156) x=156;
      fill_rect(x,88,1,4,WHITE);
      u32 f=base0+(u32)i*400000u; u32 m=f/1000000u, t=(f/100000u)%10;
      char b[8]; b[0]=(char)('0'+(m/100)%10); b[1]=(char)('0'+(m/10)%10); b[2]=(char)('0'+m%10);
      b[3]='.'; b[4]=(char)('0'+t); b[5]=0;
      draw_text((u16)(x>140?140:x),92,b,GREY,BLACK,1);
    }
  }
  retune();
  fill_rect(0,16,160,112,BLACK);
  screen_a();
}
static const char* menu_item[11]={"SQL","STEP","TXP","MOD","BEEP","ROGER","SPEC","FM","BOOK","ABOUT","EXIT"};
#define MENU_N 11
static void menu_val(int i,char*b){
  b[0]=0;
  if(i==0){ b[0]='O'; b[1]='N'; b[2]=0; if(!sq_on){ b[1]='F'; b[2]='F'; b[3]=0; } }
  else if(i==1){ const char*L[4]={"2.5K","5K","12.5K","25K"}; const char*s=L[step_i]; int k=0; while(s[k]){ b[k]=s[k]; k++; } b[k]=0; }
  else if(i==2){ b[0]='P'; b[1]=(char)('1'+tx_i); b[2]=':';
    u8 r=pwr_ramp[tx_i];
    if(r>=100){ b[3]='1'; b[4]='0'; b[5]='0'; b[6]=0; }
    else { b[3]=(char)('0'+r/10); b[4]=(char)('0'+r%10); b[5]=0; } }
  else if(i==3){ b[0]='F'; b[1]='M'; b[2]=0; if(mod){ b[1]='A'; } }
  else if(i==4){ b[0]='O'; b[1]='N'; b[2]=0; if(!beep_on){ b[1]='F'; b[2]='F'; b[3]=0; } }
  else if(i==5){ b[0]='O'; b[1]='N'; b[2]=0; if(!roger_on){ b[1]='F'; b[2]='F'; b[3]=0; } }
}
static void menu_row(int i,int sel){
  u16 y=(u16)(22+i*9);
  u16 bg = sel ? 0x0010 : BLACK;
  fill_rect(0,y,160,9,bg);
  draw_text(6,(u16)(y+1),menu_item[i], sel?YELLOW:WHITE, bg,1);
  char v[8]; menu_val(i,v);
  if(v[0]) draw_text(104,(u16)(y+1),v, sel?YELLOW:GREY, bg,1);
}
static void draw_menu(void){
  fill_rect(0,16,160,112,BLACK);
  draw_text(4,18,"MENU",YELLOW,BLACK,1);
  for(int i=0;i<MENU_N;i++) menu_row(i, i==menu_sel);
}
/* Beeper is MCU-generated: TIM1_CH4 PWM on PA11 (amp enabled by PB7).
   TIM1 register block is the usual STM32 layout. */
#define TIM1 0x40012C00u
/* Stock beep path: 0x24=0x8A7F, 0x70=0xE0E0, 0x3F=0x0800. It goes through the
   RF audio chain, so it is transmitted while keyed (used for the roger beep). */
static void rf_beep_on(void){
  rf_write(0x24,0x8A7Fu);
  rf_write(0x70,0xE0E0u);
  rf_write(0x3F,0x0800u);
}
static void rf_beep_off(void){
  u16 v=rf_read(0x24);
  rf_write(0x24,(u16)(v&~0x0020u));
  rf_write(0x70,0x0000u);
}
static void tone(u16 hz,u16 ms){
  if(!hz) hz=2000;
  int pb7=(int)((R(GPIOB+0x14)>>7)&1u);   /* remember amp state */
  if(!tx) rf_af_mute();                   /* keep demod noise out of the beep */
  R(CRM+0x18)|=(1u<<11); (void)R(CRM+0x18);
  if(!pb7) R(GPIOB+0x18)=(1u<<7);         /* amp on only while we sound */
  pin_mode(GPIOA,11,2); pin_af(GPIOA,11,2);
  u32 arr=48000000u/(u32)hz; if(arr<2) arr=2; arr-=1u;
  R(TIM1+0x28)=0u;                       /* PSC */
  R(TIM1+0x2C)=arr;                      /* ARR */
  R(TIM1+0x40)=arr/2u;                   /* CCR4 = 50% */
  R(TIM1+0x1C)=(R(TIM1+0x1C)&~(7u<<12))|(6u<<12);   /* CH4 PWM mode 1 */
  R(TIM1+0x20)|=(1u<<12);                /* CC4E */
  R(TIM1+0x44)|=(1u<<15);                /* MOE */
  R(TIM1+0x14)|=1u;                      /* UG */
  R(TIM1+0x00)|=1u;                      /* CEN */
  delay_ms(ms);
  R(TIM1+0x00)&=~1u;
  R(TIM1+0x20)&=~(1u<<12);
  R(TIM1+0x44)&=~(1u<<15);
  pin_mode(GPIOA,11,0);
  if(!pb7) R(GPIOB+0x28)=(1u<<7);         /* restore amp state */
  if(!tx) rf_af_rx(25);
}
static void beep(void){
  if(!beep_on) return;
  tone(2000,45);
}
static void say(const char*s){ int i=0; while(s[i]&&i<12){ msg[i]=s[i]; i++; } msg[i]=0; msg_t=1500; draw_status(); }
static void apply_sq(void){
  rf_write(0x28,0x0B40);
  rf_write(0x78, sq_on ? 0x4A48 : 0x0000);
  sq_open=1; sq_low=0; R(GPIOB+0x18)=(1u<<7);
}
static void apply_mod(void){
  if(mod){ rf_write(0x3D,0x0000); rf_write(0x73,(u16)(rf_read(0x73)|0x0010)); rf_write(0x47,0x6740); rf_write(0x48,0xB3AA); }
  else { rf_write(0x3D,0x2AAB); rf_write(0x73,(u16)(rf_read(0x73)&~0x0010)); rf_af_rx(25); }
}
static void retune(void){ rf_idle(); for(volatile int i=0;i<20000;i++); rf_set_freq(freq[band]); for(volatile int i=0;i<20000;i++); rf_rx_on(freq[band]>=300000000u?1:0); apply_mod(); }
static void enter_tx(void){
  R(GPIOB+0x28)=(1u<<7); rf_tx_band(freq[band]>=300000000u?1:0);
  rf_write(0x50,0x3B20);
  rf_write(0x40,(u16)((rf_read(0x40)&0xF000u)|0x04D2u));
  rf_write(0x74,0xFA02); rf_write(0x44,0x8F88); rf_write(0x45,0x3201);
  rf_write(0x7D,0xE952); rf_write(0x48,0xB3BF);
  rf_write(0x1F,0x5454); rf_write(0x3E,0xA037);
  rf_write(0x77,0x88EF); rf_write(0x4F,0x3732);
  rf_write(0x47,0x6040); rf_write(0x30,0x0200); rf_write(0x30,0xC1FE);
  rf_write(0x36,(u16)(((u16)pwr_ramp[tx_i]<<8)|0x00A2u));
  rf_write(0x37,0x1D0Fu);
  tx=1; led_tx(1); led_rx(0); draw_top();
}
static void exit_tx(void){
  if(roger_on){ rf_beep_on(); delay_ms(110); rf_beep_off(); }  /* transmitted roger */
  rf_write(0x36,0x0022); rf_idle(); for(volatile int i=0;i<40000;i++);
  rf_set_freq(freq[band]); rf_write(0x43,0x3028); rf_rx_on(freq[band]>=300000000u?1:0); rf_af_rx(25);
  R(GPIOB+0x18)=(1u<<7); tx=0; led_tx(0); apply_sq(); draw_top();
}
static void step(int d){
  u32 f=freq[band];
  u32 lo = 18000000u;
  u32 hi = 1300000000u;
  u32 s = (u32)step_tbl[step_i]*100u;
  if(d>0){ if(f<hi) f+=s; } else { if(f>lo) f-=s; }
  if(f<lo) f=lo; if(f>hi) f=hi;
  freq[band]=f; retune(); draw_a(); draw_b();
}
static char dig[8]; static int dig_n=0;
static void show_ent(void){
  fill_rect(0,44,160,12,BLACK);
  char b[12]; b[0]='E'; b[1]='N'; b[2]='T'; b[3]=' ';
  int i=0; for(;i<dig_n;i++) b[4+i]=dig[i]; b[4+i]=0;
  draw_text(2,46,b,YELLOW,BLACK,1);
}
static int uget(u32 to){ for(u32 i=0;i<to;i++){ int c=uart_getc(); if(c>=0) return c; } return -1; }
/* font=1: raw glyph blob to FONT_BASE; font=0: book with FEBO header */
static void ebook_upload(int font){
  uart_puts("\nREADY\n");
  u8 h[16];
  for(int i=0;i<4;i++){ int c=uget(6000000u); if(c<0){ uart_puts("ERR\n"); return; } h[i]=(u8)c; }
  u32 len=(u32)h[0]|((u32)h[1]<<8)|((u32)h[2]<<16)|((u32)h[3]<<24);
  if(len==0u||len>BOOK_MAX){ uart_puts("ERR\n"); return; }
  u32 base   = font ? FONT_BASE : BOOK_BASE;
  u32 dataoff= font ? 0u : 256u;
  uart_puts("ERASE\n");
  for(u32 a=0;a<dataoff+len;a+=4096u) nor_erase_4k(base+a);
  if(!font){
    h[0]='F';h[1]='E';h[2]='B';h[3]='O';
    h[4]=(u8)len; h[5]=(u8)(len>>8); h[6]=(u8)(len>>16); h[7]=(u8)(len>>24);
    for(int i=8;i<16;i++) h[i]=0;
    nor_write_page(base,h,16);
  }
  u8 buf[256];
  u32 addr=base+dataoff, done=0;
  uart_puts("OK\n");                 /* erase finished, safe to stream */
  while(done<len){
    u32 n=len-done; if(n>256u) n=256u;
    for(u32 i=0;i<n;i++){ int c=uget(6000000u); if(c<0){ uart_puts("ERR\n"); return; } buf[i]=(u8)c; }
    nor_write_page(addr,buf,n);
    addr+=n; done+=n;
    uart_putc('.');
  }
  uart_puts("DONE\n");
}
static void blit16(u16 x,u16 y,const u8*g){
  set_win(x,y,(u16)(x+15),(u16)(y+15));
  R(GPIOB+0x18)=DC_BIT; R(GPIOB+0x28)=CS_BIT;
  for(int yy=0;yy<16;yy++){
    u16 bits=(u16)(((u16)g[yy*2]<<8)|g[yy*2+1]);
    for(int xx=0;xx<16;xx++){
      u16 v=(bits&(0x8000u>>xx))?WHITE:BLACK;
      spi_byte((u8)(v>>8)); spi_byte((u8)v);
    }
  }
  spi_drain(); R(GPIOB+0x18)=CS_BIT;
}
/* Render one screenful starting at byte offset off; returns the next offset. */
static u32 book_draw(u32 off,u32 len){
  u8 g[32];
  int x=0,row=0;
  fill_rect(0,16,160,112,BLACK);
  while(row<7 && off<len){
    u8 c; nor_read(BOOK_DATA+off,&c,1); off++;
    if(c=='\n'||c=='\r'){ x=0; row++; continue; }
    if(c>=0x81u && off<len){
      u8 c2; nor_read(BOOK_DATA+off,&c2,1); off++;
      if(x+16>160){ x=0; row++; if(row>=7) break; }
      if(c>=0xA1u&&c<=0xF7u&&c2>=0xA1u&&c2<=0xFEu){
        u32 idx=(u32)(c-0xA1u)*94u+(u32)(c2-0xA1u);
        nor_read(FONT_BASE+idx*32u,g,32);
        blit16((u16)x,(u16)(16+row*16),g);
      }
      x+=16;
    } else {
      if(x+8>160){ x=0; row++; if(row>=7) break; }
      char s[2]={(c>=0x20u&&c<0x7Fu)?(char)c:' ',0};
      draw_char((u16)x,(u16)(16+row*16+4),s[0],WHITE,BLACK,1);
      x+=8;
    }
  }
  while(off<len){ u8 c; nor_read(BOOK_DATA+off,&c,1); if(c!='\n'&&c!='\r') break; off++; }
  return off;
}
/* reading position lives in the last NOR sector: "FBK" + u32 offset */
static u32 book_pos_load(void){
  u8 b[8]; nor_read(BM_BASE,b,8);
  if(b[0]=='F'&&b[1]=='B'&&b[2]=='K')
    return (u32)b[4]|((u32)b[5]<<8)|((u32)b[6]<<16)|((u32)b[7]<<24);
  return 0u;
}
static void book_pos_save(u32 off){
  u8 b[8]={'F','B','K',0,0,0,0,0};
  b[4]=(u8)off; b[5]=(u8)(off>>8); b[6]=(u8)(off>>16); b[7]=(u8)(off>>24);
  nor_erase_4k(BM_BASE);
  nor_write_page(BM_BASE,b,8);
}
static void book_page(void){
  u8 h[16]; nor_read(BOOK_BASE,h,16);
  if(h[0]!='F'||h[1]!='E'||h[2]!='B'||h[3]!='O'){ say("NO BOOK"); delay_ms(700); return; }
  u32 len=(u32)h[4]|((u32)h[5]<<8)|((u32)h[6]<<16)|((u32)h[7]<<24);
  if(!len){ say("NO BOOK"); delay_ms(700); return; }
  for(int w=0;w<100;w++){ kbd_scan(); if(!key_id()) break; delay_ms(20); }
  u32 hist[24]; int hn=0;
  u32 start=book_pos_load();
  if(start>=len) start=0;
  u32 off=start;
  u32 next=book_draw(off,len);
  for(;;){
    kbd_scan(); int k=key_id();
    if(k==K_DN && next<len){ if(hn<24) hist[hn++]=off; off=next; next=book_draw(off,len); }
    else if(k==K_UP && hn>0){ next=off; off=hist[--hn]; book_draw(off,len); }
    else if(k==K_EXIT||k==K_MENU){ while(1){ kbd_scan(); if(!key_id()) break; delay_ms(20);} break; }
    delay_ms(140);
  }
  if(off!=start) book_pos_save(off);
  fill_rect(0,16,160,112,BLACK);
}
static void act(int k,int lng){
  if(menu_on){
    if(k==K_UP||k==K_DN){
      int old=menu_sel;
      menu_sel = (k==K_UP) ? (menu_sel+MENU_N-1)%MENU_N : (menu_sel+1)%MENU_N;
      menu_row(old,0); menu_row(menu_sel,1);
      return;
    }
    if(k==K_EXIT){ menu_on=0; fill_rect(0,16,160,112,BLACK); draw_top(); screen_a(); return; }
    if(k==K_MENU){
      switch(menu_sel){
        case 0: sq_on^=1; apply_sq(); draw_top(); beep(); break;
        case 1: step_i=(step_i+1)&3; beep(); break;
        case 2: tx_i=(tx_i+1)%5; beep(); break;
        case 3: mod^=1; retune(); draw_top(); beep(); break;
        case 4: beep_on^=1; if(beep_on) beep(); break;
        case 5: roger_on^=1; if(roger_on) tone(1800,90); break;
        case 6: menu_on=0; spec_run(); return;
        case 7: fm_page(); menu_on=1; draw_menu(); return;
        case 8: menu_on=0; book_page(); menu_on=1; draw_menu(); return;
        case 9: about_page(); draw_menu(); return;
        default: menu_on=0; fill_rect(0,16,160,112,BLACK); draw_top(); screen_a(); return;
      }
      menu_row(menu_sel,1);
      return;
    }
    return;
  }
  (void)lng;
  if(k>=K_1 && k<=K_0){
    int d = (k==K_0) ? 0 : k;
    if(dig_n<6){ dig[dig_n++]=(char)('0'+d); show_ent(); }
    return;
  }
  if(k==K_UP){ step(1); return; }
  if(k==K_DN){ step(-1); return; }
  if(k==K_AB){ band^=1; retune(); draw_a(); draw_b(); draw_top(); return; }
  if(k==K_MR){ mr^=1; draw_a(); draw_b(); return; }
  if(k==K_MENU){
    if(dig_n>0){
      if(dig_n==6){ u32 v=0; for(int i=0;i<6;i++) v=v*10u+(u32)(dig[i]-'0'); freq[band]=v*1000u; retune(); }
      dig_n=0; draw_a(); draw_b(); return;
    }
    menu_on=1; menu_sel=0; draw_menu(); return;
  }
  if(k==K_EXIT){ dig_n=0; draw_a(); say("EXIT"); return; }
  if(f_latch){ f_latch=0; draw_status(); lng=1; }
  if(!lng) return;
  if(k==K_1){ freq[band]=(freq[band]>=400000000u)?145000000u:438500000u; retune(); draw_a(); draw_b(); }
  else if(k==K_2){ band^=1; retune(); draw_a(); draw_b(); draw_top(); }
  else if(k==K_3){ mr^=1; draw_a(); draw_b(); }
  else if(k==K_4||k==K_STAR){ say("SCAN"); }
  else if(k==K_6){ say("POWER"); }
  else if(k==K_8){ say("REV"); }
  else if(k==K_0){ say("FM RADIO"); }
}
static void fm_diag(void){
  rf_idle(); rf_write(0x47,0x6040); rf_af_mute();
  i2c_pins(GPIOC,15,GPIOA,3);
  uart_puts("\n[FM] plain:"); rda_read(); uart_put_hex(fm_status,4);
  { static const u8 regs[4]={0x00,0x02,0x0A,0x0B};
    for(int r=0;r<4;r++){
      u16 v=0xFFFF; int a1, a2;
      i2c_start(); a1=i2c_ack_byte(0x20);
      if(a1) i2c_byte(regs[r]);
      i2c_start(); a2=i2c_ack_byte(0x21);
      if(a2){ u8 h=i2c_rb(1), l=i2c_rb(0); v=(u16)(((u16)h<<8)|l); }
      i2c_stop();
      uart_puts("\n[FM] reg"); uart_put_hex(regs[r],2);
      uart_puts("="); uart_put_hex(v,4);
      uart_puts(" a:"); uart_put_dec((u32)a1); uart_put_dec((u32)a2);
    } }
  rda_write(0x02,0x0000); delay_ms(50); rda_read();
  uart_puts("\n[FM] off:"); uart_put_hex(fm_status,4);
  rda_write(0x02,0xC001); delay_ms(80); rda_read();
  uart_puts(" on:"); uart_put_hex(fm_status,4);
  uart_puts("\n[FM] done\n");
  rf_init_pins(); retune();
}
static void i2c_bus_scan(void){
  const u32 sclp[5]={GPIOC,GPIOA,GPIOC,GPIOB,GPIOA};
  const int  scln[5]={15,    2,    14,    1,    1};
  const u32 sdap[5]={GPIOA,GPIOA,GPIOC,GPIOA,GPIOA};
  const int  sdan[5]={3,    3,    15,    0,    12};
  for(int k=0;k<5;k++){
    i2c_pins(sclp[k],scln[k],sdap[k],sdan[k]);
    uart_puts("\n[I2C] scl="); uart_put_dec(sclp[k]==GPIOC?2:0); uart_puts(".");
    uart_put_dec((u32)scln[k]); uart_puts(" sda="); uart_put_dec(sdap[k]==GPIOC?2:0); uart_puts(".");
    uart_put_dec((u32)sdan[k]); uart_puts(" a10=");
    uart_put_dec((u32)i2c_probe(0x10));
    uart_puts(" a60="); uart_put_dec((u32)i2c_probe(0x60));
  }
  i2c_pins(GPIOC,15,GPIOA,3);
  uart_puts("\n");
}
static void uart_freq(void){
  u32 hz=freq[band], f=hz%1000000u;
  uart_put_dec(hz/1000000u); uart_putc('.');
  char b[6];
  for(int i=5;i>=0;i--){ b[i]=(char)('0'+f%10u); f/=10u; }
  for(int i=0;i<6;i++) uart_putc(b[i]);
}
static void uart_shell(void){
  int c, n=0;
  while(n++<32 && (c=uart_getc())>=0){
    if(c=='\r'||c=='\n'){ uart_puts("\n> "); continue; }
    if(c=='?'){ uart_puts("\ncmds: v version  r status  s squelch  m mod  b band  p ping  f fm-diag\n"); continue; }
    if(c=='v'){ uart_puts("\nFEATURE OS ALPHA 01 - BF-UV5RH (AT32F421) "); uart_puts(sys_fast?"48M":"8M"); uart_puts("\n"); continue; }
    if(c=='p'){ uart_puts("\nPONG\n"); continue; }
    if(c=='f'){ fm_diag(); continue; }
    if(c=='e'){ ebook_upload(0); continue; }
    if(c=='F'){ ebook_upload(1); continue; }
    if(c=='k'){ u8 h[16]; nor_read(BOOK_BASE,h,16);
      uart_puts("\nBOOK magic="); uart_put_hex(h[0],2); uart_put_hex(h[1],2);
      uart_puts(" len="); uart_put_dec((u32)h[4]|((u32)h[5]<<8)|((u32)h[6]<<16)|((u32)h[7]<<24));
      uart_puts("\n"); continue; }
    if(c=='n'){ nor_init(); u32 id=nor_id(); uart_puts("\nNOR "); uart_put_hex(id,6); uart_puts("\n"); continue; }
    if(c=='i'){ i2c_bus_scan(); continue; }
    if(c=='g'){
      rf_idle(); rf_write(0x47,0x6040); rf_af_mute();
      pin_mode(GPIOC,15,1); R(GPIOC+0x18)=(1u<<15);
      pin_mode(GPIOA,3,1); R(GPIOA+0x18)=(1u<<3);
      fm_tune();
      uart_puts("\n[FM] f="); uart_put_dec(fm_khz);
      uart_puts(" stc="); uart_put_dec((u32)fm_stc);
      uart_puts(" st="); uart_put_hex(fm_status,4);
      uart_puts("\n");
      rf_init_pins(); retune();
      continue;
    }
    if(c=='r'){
      uart_puts("\nF="); uart_freq();
      uart_puts(" RX="); uart_put_dec(rf_rssi());
      uart_puts(" SQ="); uart_put_dec((u32)sq_on);
      uart_puts(" TX="); uart_put_dec((u32)tx);
      uart_puts(" MOD="); uart_puts(mod?"AM":"FM");
      uart_puts(" BAND="); uart_put_dec((u32)band);
      uart_puts("\n"); continue;
    }
    if(c=='s'){ sq_on^=1; apply_sq(); draw_top(); uart_puts(sq_on?"\nSQ ON\n":"\nSQ OFF\n"); continue; }
    if(c=='m'){ mod^=1; retune(); draw_top(); uart_puts(mod?"\nAM\n":"\nFM\n"); continue; }
    if(c=='B'){ bat_update(); uart_puts("\nBAT "); uart_put_dec(bat_pct); uart_puts("% ");
      uart_put_dec(bat_mv); uart_puts("mV raw="); uart_put_dec(bat_raw()); uart_puts("\n"); continue; }
    if(c=='q'){ u16 r0=rf_read(0x0C); uart_puts("\nSQ reg0C="); uart_put_hex(r0,4);
      uart_puts(" bit1="); uart_put_dec((u32)((r0>>1)&1u));
      uart_puts(" rssi="); uart_put_dec(rf_rssi());
      uart_puts(" open="); uart_put_dec((u32)sq_open); uart_puts("\n"); continue; }
    if(c=='b'){ band^=1; retune(); draw_a(); draw_b(); draw_top(); uart_puts("\nband\n"); continue; }
    if(c>=' '&&c<0x7F) uart_putc((char)c);
  }
}
/* Decide the clock from CRM_CFG[3:2]: 0 = HICK 8 MHz, 2 = PLL. The stock
   bootloader leaves the PLL at 48 MHz when it jumps into the app, so we
   follow whatever it set instead of fighting it. */
static int clk_detect(void){
  return (((R(CRM+0x04)>>2)&3u)==2u) ? 1 : 0;
}
int main(void){
  sys_fast=clk_detect();
  R(CRM+0x14)|=(1u<<17)|(1u<<18)|(1u<<19)|(1u<<22); R(CRM+0x1C)|=(1u<<14); (void)R(CRM+0x14);
  pin_mode(GPIOF,6,1); R(GPIOF+0x18)=(1u<<6);
  pin_mode(GPIOB,2,1); pin_mode(GPIOB,12,1); pin_mode(GPIOB,14,1); R(GPIOB+0x18)=CS_BIT|RST_BIT;
  pin_mode(GPIOB,13,2); pin_mode(GPIOB,15,2); pin_af(GPIOB,13,0); pin_af(GPIOB,15,0);
  pin_mode(GPIOA,4,1); R(GPIOA+0x18)=(1u<<4);
  R(SPI2+0x04)=0; R(SPI2)=(1u<<2)|(2u<<3)|(1u<<6)|(1u<<8)|(1u<<9);
  lcd_init();
  fill_rect(0,0,160,128,BLUE);
  draw_text(20,44,"FEATURE OS",YELLOW,BLUE,2);
  draw_text(52,76,"ALPHA 01",WHITE,BLUE,1);
  for(int b=0;b<2;b++){
    rf_write(0x70,0x8000|40); rf_write(0x47,0x6240); rf_write(0x48,0xB8A2);
    delay_ms(110);
    rf_write(0x70,0); rf_write(0x47,0x6040);
    delay_ms(140);
  }
  delay_ms(1800);
  fill_rect(0,0,160,128,BLACK);
  pin_mode(GPIOA,13,1); pin_mode(GPIOA,14,1); R(GPIOA+0x28)=(1u<<13)|(1u<<14);
  kbd_init(); pin_mode(GPIOB,7,1); R(GPIOB+0x18)=(1u<<7);
  bat_init(); bat_update();
  nor_init();
  rf_init_pins(); rf_power_init(); rf_set_freq(freq[band]); rf_rx_on(1); rf_af_rx(25); apply_sq();
  pin_mode(GPIOA,10,0); R(GPIOA+0x0C)=(R(GPIOA+0x0C)&~(3u<<20))|(1u<<20);
  pin_mode(GPIOA,15,0); R(GPIOA+0x0C)=(R(GPIOA+0x0C)&~(3u<<30))|(1u<<30);
  uart_init(sys_fast);
  uart_puts("\n\nFEATURE OS ALPHA 01 UART1 115200 8N1 ready\n> ");
  delay_ms(150);
  int ptt_idle=(int)((R(GPIOA+0x10)>>10)&1u);
  pin_mode(GPIOB,0,0); R(GPIOB+0x0C)=(R(GPIOB+0x0C)&~3u)|1u;
  u32 hold=0; int cur=0, press=0, lfired=0; u32 tick=0; char bucket=0;
  draw_top(); draw_a(); draw_b(); draw_meter(0); draw_status();
  for(;;){
    if(R(GPIOB+0x10)&1u){ hold+=10; if(hold>300){ rf_af_mute(); rf_idle(); R(GPIOF+0x28)=(1u<<6); for(;;) __asm volatile("wfi"); } } else hold=0;
    { static int cnt=0; int p=(int)((R(GPIOA+0x10)>>10)&1u); int pressed=(p!=ptt_idle);
      if(pressed){ if(cnt<10) cnt++; } else { if(cnt>0) cnt--; }
      if(cnt>=8 && !tx) enter_tx(); else if(cnt<=2 && tx) exit_tx(); }
    { static u32 st=0; static int sp=1; int sk=(int)((R(GPIOA+0x10)>>15)&1u);
      /* side key PA15 is active low: toggle squelch on press only */
      if(sk==0 && sp==1 && (tick-st)>30){ st=tick; sq_on^=1; apply_sq(); draw_top(); }
      sp=sk; }
    kbd_scan(); int k=key_id();
    if(k && k!=cur) act(k,0);
    cur=k;
    { static int s2c=100;   /* starts disarmed: requires a release before first trigger */
      int now=(k==0 && !menu_on && dig_n==0 && side2_pressed()) ? 1 : 0;
      if(now){ if(s2c<100) s2c++; } else s2c=0;
      if(s2c==5){ fm_page(); screen_a(); draw_top(); s2c=6; } }
    if(msg_t){ msg_t-=10; if(!msg_t){ msg[0]=0; draw_status(); } }
    if(tick%50==0){ bat_update(); if(!menu_on && !tx && bat_pct!=bat_shown) draw_bat(); }
    if(++tick%20==0){
      u16 r=rf_rssi();      if(!menu_on && (char)(r>>2)!=bucket){ bucket=(char)(r>>2); draw_meter(r); }
      if(!tx && !menu_on){
        int open;
        u16 sqchip = rf_read(0x0C);
        /* FD6818 hardware squelch verdict (REG_0C bit1) is authoritative;
           the RSSI term is only a safety net on very strong signals. */
        if(!sq_on) open=1;
        else if((sqchip & 0x0002u) || r>=400u){ sq_low=0; open=1; }
        else if(r<380u) open=0;
        else open=sq_open;
        if(open!=sq_open){ sq_open=open; if(open){ R(GPIOB+0x18)=(1u<<7); led_rx(1);} else { R(GPIOB+0x28)=(1u<<7); led_rx(0);} draw_top(); }
      }
    }
    uart_shell();
    delay_ms(10);
  }
}