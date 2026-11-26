#ifndef EBOOK_H
#define EBOOK_H

/* 25QH16 SPI NOR on SPI1: PA5 SCK, PA6 MISO, PA7 MOSI, PA8 CS.
   Book region starts at BOOK_BASE, header = "FEBO" + u32 length. */
#define FONT_BASE 0x000000u          /* GB2312 16x16 bitmap font, 282752 B */
#define BOOK_BASE 0x046000u          /* sector-aligned, right after the font */
#define BOOK_DATA (BOOK_BASE+256u)   /* 256-byte aligned: page-program safe */
#define FONT_BYTES 282752u
#define BM_BASE   0x1FF000u          /* last 4K sector: reading position */
#define BOOK_MAX  0x1B7F00u          /* exactly stops at BM_BASE (no overlap) */

void nor_init(void);
unsigned int nor_id(void);
void nor_read(unsigned int addr, void *buf, unsigned int len);
void nor_erase_4k(unsigned int addr);
void nor_write_page(unsigned int addr, const void *buf, unsigned int len);

#endif
