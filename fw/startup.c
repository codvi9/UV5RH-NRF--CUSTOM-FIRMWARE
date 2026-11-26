extern int main(void);
extern unsigned int _sidata, _sdata, _edata, _sbss, _ebss;

void Reset_Handler(void);
void Default_Handler(void){ for(;;); }

__attribute__((section(".vectors"), used))
void (*const g_vectors[16])(void) = {
  (void (*)(void))0x20004000u,
  Reset_Handler,
  Default_Handler, Default_Handler, Default_Handler, Default_Handler,
  Default_Handler, Default_Handler, Default_Handler, Default_Handler,
  Default_Handler, Default_Handler, Default_Handler, Default_Handler,
  Default_Handler, Default_Handler,
};

void Reset_Handler(void)
{
  unsigned int *src = &_sidata;
  for(unsigned int *dst = &_sdata; dst < &_edata; ) *dst++ = *src++;
  for(unsigned int *dst = &_sbss; dst < &_ebss; ) *dst++ = 0u;
  main();
  for(;;);
}
