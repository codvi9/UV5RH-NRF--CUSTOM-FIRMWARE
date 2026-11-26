# BF-UV5RH 第三方固件 — 交接文档（2026-11-25）

当前固件：baofeng-uv5rh-fw/fw/fw.BF（9076 字节，已刷入实机）
固件名：FEATURE OS ALPHA 01

---

## 1. 硬件

| 项 | 值 |
|---|---|
| 机型 | BF-UV5RH（板号 5RHNRF，M 标，HW V01，原厂 V0.21 已丢失） |
| MCU | AT32F421C8T7（64KB Flash / 16KB RAM） |
| 应用区 | 0x08001000 – 0x0800FFFF（60KB） |
| 射频 | FD6818B（三线总线） |
| 外部 Flash | 25QH16（2MB SPI NOR，不可 XIP） |
| 广播芯片 | TEA5767（I²C 0x60，固定 5 字节帧，32.768 kHz 晶振） |
| 屏幕 | ST7735 160x128 |

### 引脚
LCD：SCLK PB13、MOSI PB15、CS PB2、RST PB12、DC PB14、BL PA4
键盘：列 PB8–PB11、行 PB3–PB6
PTT PA10、侧键 PA15（静噪开关）、收发切换 PB7（高=喇叭/低=麦克风）
LED：TX PA13、RX PA14；电源锁存 PF6；旋钮 PB0（1=关）
RF：LE PC13、SCK PA2、SDA PA3；Flash：PA5/PA6/PA7/PA8；I2C：SCL PC15、SDA PA3

### 键盘原始值
1 FFFE 2 FFFD 3 FFFB 4 FFEF 5 FFDF 6 FFBF 7 FEFF 8 FDFF 9 FBFF 0 FF7F
* FFF7 # F7FF 上 EFFF 下 DFFF 左下绿(MENU) BFFF 右上红(EXIT) 7FFF
A/B EEEE VFO/MR DDDD SCAN BBBB SOS 7777

---

## 2. 刷机

进模式：旋钮关 → 按住两侧键 → 旋钮开（黑屏即成功）
串口：COM10，115200
编译：python baofeng-uv5rh-fw/tools/build.py
刷写：cd baofeng-uv5rh-fw && python -c "import sys; sys.path.insert(0,'libs'); sys.argv=['f','COM10','fw/fw.BF','--go']; exec(compile(open('tools/flash.py').read(),'fl','exec'))"
Bootloader 未动（0x08000000–0x0FFF），永远可救

---

## 3. 当前固件功能

- 开机：蓝底 + 黄 FEATURE OS + 白 ALPHA 01，约 2.3 秒，无提示音
- 主界面：蓝顶栏（H-0001 / FM H / RX-TX / SQ1 / 99%）、黄 3 倍字号频率、B 频点、RSSI 数字+条（>400 红）+ RW 原始值、底部提示
- 按键：上下 ±25k（18M–1300M）、数字键输入（ENT + MENU 确认）、MENU、EXIT、A/B、VFO/MR、侧键静噪
- 静噪：REG_0C bit1 或 RSSI>=300（回差 290，600ms 防抖），写 0x78=0x4A48
- 菜单：SQL / MOD / DUAL(残留) / SPEC(频谱) / FM(实验) / ABOUT / EXIT
- 发射：PTT 防抖 80ms，PB7 切麦克风，已写入原厂音频链寄存器
- 频谱：32 点 ±0.8MHz，刻度 140–500，底部频率刻度 + 右上最强信号频率
- UART：PA9/PA10 USART1 115200，详见第 7 节
- 时钟：运行时识别 48MHz(PLL) / 8MHz(HICK)，UART 分频与 delay_ms 自动匹配
- 菜单：SQL/STEP/TXP/MOD/BEEP/ROGER/SPEC/FM/BOOK/ABOUT/EXIT（11 项，每行独立重绘）
- 电子书：NOR 存书 + GB2312 字库，支持中英混排、自动换行、翻页，详见第 6b 节

---

## 4. 原厂固件分析（已完成）

对象：dump/fw/5RH_NRF_V0.13（59392 + 1296 = 59.3KB，几乎占满 60KB）
反汇编：dump/stock.asm（24059 行）

关键事实：
1. 原厂调 ROM Bootloader IAP（0x1FFFE4xx/0x1FFFE5xx，40 处），自己不写 Flash 驱动
2. 菜单标签表在 0x0800F000–0x0800F600，共 70 条（SQL/STEP/TXP/W-N/RPT-RL/TDR/BEEP/TOT/CTCSS/DCS/SC-REV/VOX...）
3. 14 个镜像里没有任何 FM 广播代码（无 FM/RADIO/87.5 字符串，无 RDA 初始化常量）
4. RSSI：0x08008D70 = read(0x67) & 0x1FF（0–511）
5. 静噪：0x08008D80 = read(REG_0C) bit1 芯片判决 + 写 0x78 门限
6. 原厂 TX 音频链（0x08008C22）：0x40=(old&0xF000)|0x04D2、0x74=0xFA02、0x44=0x8F88、0x45=0x3201、0x7D=0xE952、0x48=0xB3BF、0x1F=0x5454、0x3E=0xA037、0x77=0x88EF、0x4F=0x3732、0x26=0x13A0、0x30=0、0x37=0x1D00/0x1D0F
7. GPIO 层：0x08006300 gpio_config、0x080063B2 gpio_set、0x08009B20 读寄存器、0x08009FF4 写寄存器
8. 原厂用 USART1（基址出现在 0x0800C63C）
9. 中文靠外部字库索引

详见 STOCK_ANALYSIS.md、STOCK_VS_OURS.md

---

## 5. FM 收音机（RDA5807M，调谐可用 / 音频未通）

**芯片是 TEA5767，I²C 地址 0x60** —— 之前的"RDA5807 未工作"结论是协议错误。

错在哪：
- RDA5807 有寄存器寻址；0x60 这颗对任何地址都返回同一组状态字节，这就是"16 个寄存器全 0x013F"的原因
- 0x10 / 0x11 的 ACK 是假象：真正读回全是 `FF FF FF FF FF`（只有上拉，没有器件）
- 对 0x10 按 RDA 协议写 `0x02=0xC011` 之类，芯片根本没收到

正确协议：
- 写：固定 5 字节帧 `{PLL>>8, PLL&0xFF, 0x00, 0x10, 0x00}`
- PLL = 4 × (f + 225000) / 32768（32.768 kHz 晶振）
- 读：5 字节状态，`byte0 bit7 = READY`，`byte2 bit7 = STEREO`

实测 100.000 MHz：写 PLL=0x2FCB，回读 `AF CB 02 00 00`；
90.1 MHz：PLL=0x2B12，回读 `AB 12 02 00 00`。

**回读是写入的回显，不是真状态**：`byte0 = 0x80 | PLL高字节`，`byte1 = PLL低字节`，两个频点精确吻合。
真 TEA5767 返回的是 IF 计数/立体声/电平，不会回显 PLL。所以 **READY 位不可信**，
界面上的 TUNED 只代表命令写进去了，不代表锁到台。

音频实测（FM 页按 1 循环 A1–A4，PB7 × FD6818 AF 静音位）：
- A1/A3（PB7 高=喇叭）：只有功放底噪，扫台无电台声
- A2/A4（PB7 低=麦克风）：完全无声 → 确认 PB7 就是喇叭/麦克风切换，高电平接喇叭

## 5b. 板上芯片清单（实测丝印，2026-11-26）

| 丝印 | 封装 | 型号 | 功能 |
|---|---|---|---|
| CNHT9-001 | QFP-44/48 | 定制 MCU（AT32F421 内核） | 主控 |
| FD6818 | QFN-32/40 | FD6818 | V/U 双段收发解调 |
| HTL7006S011P / HTL7006S0xxP | QFN | PA | UHF / VHF 功放 |
| **5807M / TN141** | **SOP-8L** | **RDA5807M（或 TN141 兼容片）** | **FM 收音调谐器** |
| LM2904B / BA0S | SOP-8 | 3PEAK 双运放 | 麦克风放大 + VOX |
| TDA2822 / DAWV30 | SOP-8 | TDA2822 | 双通道音频功放 |
| 516A / 56A-UGLI | SOP-8 ×2 | DC-DC | 3.3V / 功放供电 |
| YL260 Ad22 | 2.2µH | 电感 | Buck 储能 |
| R390 ×3 | 2512 | 0.39Ω | 发射电流检测 |
| A1SHB / 24 | SOT-23 | NPN | 静音/开关驱动 |

**FM 调谐器是 RDA5807M（SOP-8，I²C 0x10/0x11），不是 TEA5767。**
之前按 0x60/TEA5767 折腾的全是错的，0x60 是板上别的器件。

### 与原厂镜像的矛盾（未解决）

- 手上 14 个镜像（V0.11–V0.14，含 AT1846S/BK/NRF 三种）**全部没有 FM 代码**：
  菜单标签表里无 FM 条目，也搜不到 RDA 的 `0xC001` 初始化常量
- 但规格页写明 5RH 支持 **FM 收音 76–108 MHz**，且板上有 RDA5807M
- 结论：**带 FM 的是更新版本固件（原厂 V0.21，已丢失）**，这批 dump 都早于它

### GPIO 实测用途（2026-11-26）

| 引脚 | 用途 |
|---|---|
| PA0 | ADC_IN0，VOX / 麦克风电平检测 |
| PA1 | ADC_IN1，电池电压 |
| PA2 | FD6818 时钟 SCLK |
| PA3 | 双向数据，FD6818 SDIO 与 RDA5807 SDA 共用 |
| PA4 | LCD 背光使能（高有效） |
| PA5/6/7/8 | SPI Flash（SCK/MISO/MOSI/CS） |
| PA9 / PA10 | USART1 TX / RX（PA10 兼 PTT，编程线复用） |
| PA11 | TMR1_CH4 PWM，喇叭/语音播放（DMA 搬运） |
| PA12 | 未使用 |
| PA13 / PA14 | TX 红灯 / RX 绿灯 |
| PA15 | 侧键1（手电筒） |
| PB0 | 电源开关检测 |
| PB2 | LCD CS |
| PB3–PB6 | 键盘行；round0 时 PB3=AB、PB4=VM、PB5=SCAN、**PB6=侧键2(FM)**；col4 拉低时 PB3=UP、PB4=DOWN、PB5=MENU、PB6=EXIT |
| **PB7** | **音频功放使能（高有效）** |
| PB8–PB11 | 键盘列 |
| PB12/13/14/15 | LCD RESET / SCK / DC / MOSI |
| PC13 | FD6818 使能/锁存 LE |
| PC15 | RDA5807M SCL |
| PF6 | 电源自锁（关机拉低） |
| PF7 | 手电筒 |
| PC14 | 开机拉高后无动作（用途未明） |
| PB1 | 输入上拉（用途未明） |

重要推论：**引脚表里没有任何音频切换 GPIO** → FM 音频应是硬连接（RDA 输出并到功放输入，或经 LM2904B 进 FD6818 MICP/MICN）。

### 当前状态（2026-11-26）

**调谐器是工作的。** 实测在 97.0–97.3 MHz 会出现 TUNED、状态字随之变化 —— 说明 I²C 写入、
PLL、STC 都正常。之前"状态恒为 0x013F"是因为没有台/未锁定，不是通讯失败。

修掉的第二个真 bug：**寄存器 0x05 音量**
- 原代码（以及所有历史版本）写 `0x05 = 0x8880`，低 4 位是 VOLUME，**0x0 = 0 级 = 静音**
- 已改为 `0x888F`（音量 15）

仍缺的一环：**音频通路**
- FM 页已确认 PB7 高=喇叭接通；A1–A6（FD6818 0x47/0x48 组合）与 G1–G6（候选 GPIO 扫描）均未出声
- 按 G 扫描时能听到"咔哒"声 → 说明确实有 GPIO 在控制音频开关，但尚未找到能让电台声通过的那一组

已知事实汇总：
- RDA5807M @ 0x10/0x11，总线 PC15(SCL)/PA3(SDA)（引脚扫描确认，其余组合无应答）
- 板上**没有 32.768 kHz 晶振**；CLK_MODE 四档（32.768k/12M/24M/13M）需逐档试，其中某档能锁定
- FD6818 9 脚 AFOUT 直接驱动 TDA2822；11/12 脚 MICP/MICN 接 LM2904B 麦克风放大
  → FM 音频若走 MICP/MICN，需要 FD6818 处于"麦克风直通"状态，这一配置尚未找到

### 有用的旁证

- FD6818 引脚（[专利公开](https://www.jigao616.com/zhuanlijieshao_34353271.aspx)）：2=SCL 3=SDA 7=BUSM 8=SCN 9=AFOUT 11=MICP 12=MICN 15=RFIN 18=RFOUT 25–32=CPIO0–7
  → **AFOUT 直接驱动功放**，所以 FM 音频若要出声，要么直接并到功放输入，要么从 MICP/MICN 进 FD6818 再出来
- 主界面 VFO 调到 98.000 MHz 完全无声 → 广播频段不是主射频芯片收的
- 0x60 器件：写 5 字节后回读近似回显（写 `5A`→读 `1A`，bit6 被清），**不是调谐器**

### 已废弃的结论（留作记录，避免重犯）

- "板上是 TEA5767@0x60" —— 错，芯片清单证实是 RDA5807M
- "原厂没有 FM、芯片只是共板残留" —— 错，原厂更新版本固件支持 FM，只是我们没拿到那份镜像
- "音频没接、硬件无解" —— 未证实，暂不下结论

---

## 6. 菜单 / 电池 / 功率 / 提示音（2026-11-26）

### 菜单（9 项 → 现为 10 项）
`SQL / STEP / TXP / MOD / BEEP / ROGER / SPEC / FM / ABOUT / EXIT`
- 每行独立重绘（选中行深蓝底），不再整屏擦写，消除闪烁与残影
- 旧的"值错行"bug 已修：原来 SQL 的值画在 y=36、MOD 在 54，与条目 y=28/41/54 对不上

### 电池
- PA1 = ADC_IN1；AT32F421 ADC：`STS`0x00 / `CTRL1`0x04 / `CTRL2`0x08 / `SPT2`0x10 / `OSQ3`0x34 / `ODT`0x4C
- 采样通道 1、239.5 周期、软件触发；开机做一次校准
- 分压按 1:2、基准 3.3V：`mV = raw*3300*2/4095`，3300mV=0%，4200mV=100%
- 实测 4.05V / 83%，与锂电相符；若与实际电压有偏差改 `bat_update()` 的 2 倍系数
- 只在百分比变化时才刷那一小块，避免顶栏闪烁

### 发射功率
- **`0x37` 只有两个有效值**：`0x1D00`（低）/ `0x1D0F`（高）——原厂 `0x08008F68` 就是二选一，
  中间值会让 PA 不出功率（实测 P1–P14 全无声）
- 现在固定 `0x37=0x1D0F`，用 **`0x36` 高字节做功率斜坡**：20/40/60/80/100 五档（原厂满功率用 100）
- 顶栏显示 L/M/H，菜单显示 `P几:斜坡值`；真实 mW 需功率计标定

### 提示音与尾音
- 本地提示音：**MCU 的 TIM1_CH4 PWM（PA11，AF2）**，2kHz、50% 占空比；播放时临时开功放（PB7）并静噪射频 AF，结束后恢复
- **尾音（可发射）**：原厂路径 `0x24=0x8A7F` → `0x70=0xE0E0` → `0x3F=0x0800`，停止为清 `0x24` bit5 且 `0x70=0`
  在 `exit_tx()` 里于**停止发射前**播放 110ms，对端可听到（已实测）

---

## 6b. 电子书（2026-11-26 完成）

### NOR 布局（GD25Q16，实测 JEDEC `C4 60 15`，2MB）

| 区域 | 用途 |
|---|---|
| 0x000000–0x045080 | GB2312 16×16 点阵字库（282,752 B，7445 字形） |
| 0x046000 | 书头：`FEBO` + u32 长度（扇区对齐，紧接字库之后） |
| 0x046100 | 正文（GBK 编码），最大 `0x1B7F00` ≈ 1.80MB |
| 0x1FF000–0x1FFFFF | 阅读位置书签扇区：`FBK` + u32 偏移 |

> 书区上限 `0x1B7F00` 是精确算出来的：`0x1FF000 - 0x046100`，正好停在书签扇区之前。
> 之前用 0x1B8900 会让书末 2.5KB 落进书签扇区，退出保存书签时被擦掉。

### 驱动
`fw/ebook.c`：SPI1（PA5 SCK / PA6 MISO / PA7 MOSI / PA8 CS，AF0，时钟 12MHz）
- `nor_id / nor_read / nor_erase_4k / nor_write_page`（0x9F / 0x03 / 0x20 / 0x02，含 WIP 轮询）
- 页编程按 256 字节对齐，正文起点 0x080100 保证不跨页

### 上传协议（串口 115200）
`e`=书 / `F`=字库 → `READY` → 4 字节小端长度 → `ERASE` →（擦除完）→ `OK`
→ 每 256 字节一块，每块回 `.` → 全部写完回 `DONE`

电脑端：`python tools/ebook_put.py COM10 book.txt`（自动 UTF-8→GBK）
　　　　`python tools/ebook_put.py COM10 --font fw/font_cn.bin`

### 渲染
- 变宽排版：汉字 16×16（从 NOR 逐字形取 32 字节），ASCII 8px 宽走 5×7 字库
- 每屏 7 行，自动换行；`\n`/`\r` 换行；页尾按实际渲染位置衔接，不丢字
- `book_draw(off)` 返回下一页起点；UP 用 24 层历史栈回退
- 只在翻页时重绘（旧版每 130ms 无条件重绘导致闪屏，已修）

### 字库生成
`python tools/make_font_cn.py` → `fw/font_cn.bin`
用 `C:\Windows\Fonts\simhei.ttf` 渲染，94×94 网格，索引 `(b0-0xA1)*94+(b1-0xA1)`，
每字形 32 字节（每行 2 字节，MSB 在左）。

限制：只覆盖 GB2312 字符集（GBK 扩展字显示为空白）；书最大 ≈1.80MB。

### 阅读位置记忆
- 退出 BOOK 页时若位置有变化，擦写 `0x1FF000` 扇区，写入 `"FBK"` + u32 字节偏移
- 再次进入先读书签；无 `FBK` 标记或偏移越界则从 0 开始
- 只在位置改变时写一次，避免无谓磨损

---

## 7. UART 串口（已完成 2026-11-25）

- 引脚：PA9 = TX、PA10 = RX，AF1，115200 8N1。已由 bootloader 反汇编证实：0x08000E20 把 GPIOA bit9(0x200)/bit10(0x400) 配成 AF，先开 APB2EN bit14，再用 115200 算 BAUDR
- PA10 与 PTT 共用：AF 模式下 IDR 仍反映引脚电平，PTT 逻辑无需改；PA10 内部上拉保持空闲高电平
- 实现：fw/uart.c、fw/uart.h（uart_init / putc / puts / put_dec / put_hex / getc / rx_ready），已加入 tools/build.py
- 时钟：main() 开头 `clk_8mhz()` 强制 HICK 8MHz。**bootloader 用 48MHz PLL 跳进应用时不复位时钟**，不钉死会让波特率和所有 delay_ms 差 6 倍
- BAUDR：AT32F421 是 Artery 新版 USART，BAUDR@0x08、CTRL1@0x0C、CTRL2@0x10、CTRL3@0x14；PCLK2=8MHz → DIV=0x45（115,942 baud，-0.6%）
- 自检：上电打印 `FEATURE OS ALPHA 01 UART1 115200 8N1 ready`
- 命令（主循环内非阻塞 uart_shell）：v 版本／r 状态／s 静噪开关／m 调制／b 波段／p ping／? 帮助
- PC 侧：`python tools/uart_mon.py COM10 monitor 6` 监听；`... probe` 探测是否在刷机模式；`... send "r"` 发命令

---

## 8. 待办

| 优先级 | 事项 |
|---|---|
| 高 | 菜单继续向原厂 70 项靠（已完成 SQL/STEP/TXP/MOD/BEEP/ROGER 六项可调） |
| 中 | 功率挡位实测标定（需要功率计，把斜坡值换算成 mW） |
| 中 | 频谱 5 次/秒 |
| 低 | 电子书：GBK 扩展字补全 / 书签 / 字号切换 |
| 挂起 | FM 音频通路（调谐正常、无声，需量 RDA 音频走线） |
| 挂起 | 原厂按键表 |
| 已完成 | ~~UART 115200~~、~~电量 ADC~~、~~提示音/尾音~~、~~发射功率多档~~、~~电子书（含中文）~~ |

---

## 9. 踩坑记录

1. .data 未复制/.bss 未清零 → 全局变量初值全 0
2. step(u32) 传 -1u 溢出 → 下键变上加，参数必须 int
3. fm_khz 用 u16 → 87500 溢出
4. 调频必须 idle → 写频率 → 重进接收
5. 进页面时按键未松开会秒退（FM/ABOUT/SPEC 需先等松手）
6. 菜单打开时主循环仍重画 RSSI → 加 !menu_on 判断
7. 发射后静噪失效 → exit_tx 要调用 apply_sq() 重写 0x78
8. 大段替换 main.c 易花括号失配导致文件截断 → 整文件重写
9. 工作区外路径（桌面）写入需 danger-full-access 审批
10. GitHub raw 路径不确定会 404；API 会限流 403
11. ops SDK 会重置，需重新 ops_load_sdk
12. bootloader 跳转进应用时主频是 48MHz（PLL 未复位）→ 冷启动 8MHz、刷完直接跳 48MHz，同一固件两种时序。已在 main() 开头 clk_8mhz() 钉死
13. 波特率错表现为"收到乱码"而不是"收不到"；用固定字符串 + 多档 BRR 扫描（69/139/208/417…）一次定位主频
14. AT32F421 的 USART 不是 STM32F0 布局：BAUDR 在 0x08、CTRL1 在 0x0C，别照搬 F0 的 0x0C/0x00
15. 电台不在刷机模式时 flash.py 会卡在 handshake（cmd 0x1 timeout）；先用 uart_mon.py probe 确认
16. FM 芯片是 TEA5767@0x60，不是 RDA5807@0x10；0x10/0x11 的 ACK 是上拉假象（读回全 FF）
17. 判断"I²C 器件不存在"要看**读回数据**，不能只看 ACK —— 假 ACK 会把排查带偏一整天
18. "回读值正好等于刚才写进去的值"= 回显，不是状态寄存器；READY 之类的位要先验证再信
19. 主频不要硬钉：48 MHz(PLL) 和 8 MHz(HICK) 都要支持。`sys_fast` 由 `CRM_CFG[3:2]` 判定，UART 分频与 delay_ms 都跟着走
20. 局部刷新不要整块 `fill_rect` 擦黑再重画 —— 会先黑一下。用带背景色的 draw_text 原地覆盖，动态字符串补空格等长

---

## 10. 文件索引

| 路径 | 内容 |
|---|---|
| fw/main.c | 主固件 |
| fw/uart.c / uart.h | USART1 驱动（PA9/PA10 115200） |
| fw/rf.c / rf.h | FD6818 驱动 |
| fw/rf_init.h | 39 条射频初始化表 |
| fw/font.h | 5x7 字库 44 字符 |
| tools/build.py / flash.py / bf_tool.py | 编译/刷写/打包 |
| tools/uart_mon.py | PC 侧串口监视/探测/发命令 |
| tools/uart_probe.py、btldr_pins.py、btldr_dump.py | 反汇编定位 UART 引脚与寄存器 |
| dump/stock.asm | 原厂反汇编 |
| dump/fw/*.bin | 14 个解包镜像 |
| STOCK_ANALYSIS.md | 原厂解包分析 |
| STOCK_VS_OURS.md | 原厂 vs 我们比对 |
| FM_AUDIO_CHECK.md | FM 排查指南 |
| _mod/UV-5RM-Radio-Mod-main/ | Rust 驱动 |
| _repo/Baofeng-UV-5RM-5RH-RE-main/ | 原厂镜像/工具 |

工具链：baofeng-uv5rh-fw/tools/xpack-arm-none-eabi-gcc-13.2.1-1.1/bin/
