#include "uart.h"

typedef unsigned int u32;

#define R(a) (*(volatile u32 *)(a))

#define CRM    0x40021000u
#define GPIOA  0x48000000u
#define USART1 0x40013800u

/* AT32F421 usart register offsets (Artery new USART IP) */
#define US_STS   0x00u
#define US_DT    0x04u
#define US_BAUDR 0x08u
#define US_CTRL1 0x0Cu
#define US_CTRL2 0x10u
#define US_CTRL3 0x14u

/* STS flags */
#define US_RDBF (1u << 5)
#define US_TDBE (1u << 7)

/* CTRL1 bits */
#define US_REN (1u << 2)
#define US_TEN (1u << 3)
#define US_UEN (1u << 13)

/* BAUDR is usartdiv in Q4. 115200: 8 MHz -> 8e6/(16*115200)=4.34 -> 0x45,
   48 MHz -> 26.04 -> 0x1A1. */
#define US_BAUD_8M  0x45u
#define US_BAUD_48M 0x1A1u

static void pin_mode(u32 g, int pin, u32 m)
{
  volatile u32 *c = (volatile u32 *)g;
  u32 sh = 2u * (u32)pin;
  *c = (*c & ~(3u << sh)) | (m << sh);
}

static void pin_pull(u32 g, int pin, u32 p)
{
  volatile u32 *c = (volatile u32 *)(g + 0x0Cu);
  u32 sh = 2u * (u32)pin;
  *c = (*c & ~(3u << sh)) | (p << sh);
}

static void pin_af(u32 g, int pin, u32 af)
{
  if (pin >= 8) {
    volatile u32 *v = (volatile u32 *)(g + 0x24u);
    *v = (*v & ~(0xFu << ((pin - 8) * 4))) | (af << ((pin - 8) * 4));
  } else {
    volatile u32 *v = (volatile u32 *)(g + 0x20u);
    *v = (*v & ~(0xFu << (pin * 4))) | (af << (pin * 4));
  }
}

void uart_init(int clk48)
{
  R(CRM + 0x14) |= (1u << 17);   /* GPIOA clock   */
  R(CRM + 0x18) |= (1u << 14);   /* USART1 clock (APB2) */
  (void)R(CRM + 0x18);

  pin_mode(GPIOA, 9, 2);         /* AF, push-pull (OTYPER default 0) */
  pin_af(GPIOA, 9, 1);           /* AF1 = USART1 */
  pin_mode(GPIOA, 10, 2);
  pin_af(GPIOA, 10, 1);
  pin_pull(GPIOA, 10, 1);        /* pull-up keeps PTT sense idle-high */

  R(USART1 + US_BAUDR) = clk48 ? US_BAUD_48M : US_BAUD_8M;
  R(USART1 + US_CTRL2) = 0;      /* 1 stop bit, no clock output */
  R(USART1 + US_CTRL3) = 0;      /* no flow control, no dma */
  R(USART1 + US_CTRL1) = US_UEN | US_TEN | US_REN;
  (void)R(USART1 + US_STS);
}

void uart_putc(char c)
{
  if (c == '\n') uart_putc('\r');
  while (!(R(USART1 + US_STS) & US_TDBE))
    ;
  R(USART1 + US_DT) = (u32)(unsigned char)c;
}

void uart_puts(const char *s)
{
  while (*s) uart_putc(*s++);
}

void uart_put_dec(unsigned int v)
{
  char b[11];
  int i = 0;
  if (!v) { uart_putc('0'); return; }
  while (v && i < 10) { b[i++] = (char)('0' + v % 10u); v /= 10u; }
  while (i) uart_putc(b[--i]);
}

void uart_put_hex(unsigned int v, int digits)
{
  static const char *H = "0123456789ABCDEF";
  for (int i = digits - 1; i >= 0; i--) uart_putc(H[(v >> (i * 4)) & 0xFu]);
}

/* Reading STS then DT clears a pending overrun/framing error. */
static void uart_drop_errors(void)
{
  (void)R(USART1 + US_STS);
  (void)R(USART1 + US_DT);
}

int uart_rx_ready(void)
{
  return (R(USART1 + US_STS) & US_RDBF) != 0;
}

int uart_getc(void)
{
  u32 st = R(USART1 + US_STS);
  if (!(st & US_RDBF)) {
    if (st & 0x0000000Fu) uart_drop_errors();   /* perr/ferr/nerr/roerr */
    return -1;
  }
  return (int)(R(USART1 + US_DT) & 0xFFu);
}
