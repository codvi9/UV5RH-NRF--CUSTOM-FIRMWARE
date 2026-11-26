#ifndef UART_H
#define UART_H

/* USART1 on PA9 (TX) / PA10 (RX), AF1, 115200 8N1.
   PA10 is shared with the PTT sense line: the pin stays readable through IDR,
   so PTT keeps working while the receiver is enabled. */
void uart_init(int clk48);
void uart_putc(char c);
void uart_puts(const char *s);
void uart_put_dec(unsigned int v);
void uart_put_hex(unsigned int v, int digits);

/* Non-blocking: returns -1 when no byte is waiting. */
int uart_getc(void);
int uart_rx_ready(void);

#endif
