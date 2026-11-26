# FEATURE OS ALPHA 01 · UV-5RH 
第三方固件 非官方、与宝锋无关、仅供持照业余频段使用、禁止在 76–108/108–136 等频段发射、改机后不可出售

# 警告！！！ 刷机前请按住数字8开机查看版本 如版本为UV5RH NRL即可刷入 或确认主控及射频与下文所述一致
# 且目前为测试版本 FM功能不可用 其他功能正在完善 仅做交流 不建议作为主力使用







> 从零手写的裸机固件，跑在 Baofeng **UV-5RH（5RHNRF 板，AT32F421 + FD6818）** 上。
> 60KB 应用区里塞下了完整 UI、串口控制台、中文电子书和 5 档发射功率 —— 当前仅 **14.5KB**。

**English**: A from-scratch bare-metal firmware for the Baofeng UV-5RH (AT32F421 MCU + FD6818
transceiver), featuring a runtime-detected clock, a UART shell, battery ADC, a 11-item menu,
5-step TX power, a GB2312 Chinese ebook reader with resume, and a spectrum view — in 14.5 KB.

---

## 亮点速览

| | |
|---|---|
| 🕹 **运行时时钟自适应** | 开机读 `CRM_CFG[3:2]` 判定 48MHz(PLL) / 8MHz(HICK)，UART 分频与 `delay_ms` 自动换算，不再依赖 bootloader 残留状态 |
| 📟 **11 项可用菜单** | SQL / STEP / TXP / MOD / BEEP / ROGER / SPEC / FM / BOOK / ABOUT / EXIT，逐行局部重绘，无闪烁无残影 |
| 📶 **5 档发射功率** | PA 固定 `0x1D0F`，功率斜坡 `0x36[15:8]` = 20/40/60/80/100，顶栏显示 L/M/H |
| 🔋 **真实电量** | PA1 的 ADC1 通道 1 + 开机校准，1:2 分压按 3.3V 基准换算，实测 4.05V → 83% |
| 🔊 **提示音 + 可发射尾音** | 本地音用 TIM1_CH4 PWM(PA11)；尾音走原厂射频音频链（`0x24/0x70/0x3F`），**对端能听到** |
| 📚 **中文电子书** | 2MB SPI NOR 里放 GB2312 16×16 字库 + 最长 1.80MB 书；中英混排自动换行，退出自动记页 |
| 📈 **频谱** | 32 点 ±0.8MHz，标注最强信号频率 |
| 💻 **串口控制台** | 115200 8N1，命令直接读写电台状态，可全程无屏幕调试 |
| 🧯 **刷不坏** | 只写应用区 `0x08001000–0x0800FFFF`，原厂 bootloader 永远可救 |

## 硬件

| 项目 | 参数 |
|---|---|
| MCU | AT32F421C8T7（丝印 CNHT9-001，Cortex-M4，64KB Flash / 16KB SRAM） |
| 射频 | FD6818（"NRF" 变体），PA 为 HTL7006 U/V 各一片 |
| 音频 | TDA2822 功放 + LM2904B 麦克风/VOX 放大 |
| FM 调谐 | RDA5807M（I²C 0x10/0x11，SOP-8） |
| 显示 | ST7735 SPI TFT 160×128 |
| 存储 | GD25Q16 2MB SPI NOR（JEDEC `C4 60 15`） |
| Flash 布局 | `0x08000000–0x08000FFF` 原厂 bootloader；`0x08001000–0x0800FFFF` 应用区（60KB） |

<details>
<summary><b>引脚表（实测）</b></summary>

| 功能 | 引脚 |
|---|---|
| LCD SCLK / MOSI / CS / RST / DC / BL | PB13 / PB15 / PB2 / PB12 / PB14 / PA4 |
| 键盘 列(输出) / 行(输入上拉) | PB8–PB11 / PB3–PB6 |
| 功放使能 | PB7（高=开） |
| 电源自锁 / 旋钮检测 | PF6（高=保持） / PB0 |
| FD6818 三线总线 | LE=PC13, SCK=PA2, SDA=PA3 |
| RDA5807M I²C | SCL=PC15, SDA=PA3（与射频 SDA 共用） |
| SPI NOR | SCK/MISO/MOSI/CS = PA5/PA6/PA7/PA8 |
| 串口 | TX=PA9, RX=PA10（PA10 兼 PTT） |
| 电池 ADC / VOX ADC | PA1 / PA0 |
| 提示音 PWM | PA11（TIM1_CH4） |
| 指示灯 | TX=PA13, RX=PA14 |

</details>

<details>
<summary><b>键盘矩阵（原始值）</b></summary>

矩阵值 16 位，每 4 位一列，某位为 0 表示该行被拉低。

| 键 | 值 | 键 | 值 |
|---|---|---|---|
| 1/2/3/* | FFFE FFFD FFFB FFF7 | 4/5/6/0 | FFEF FFDF FFBF FF7F |
| 7/8/9/# | FEFF FDFF FBFF F7FF | 上/下 | EFFF / DFFF |
| 绿(MENU)/红(EXIT) | BFFF / 7FFF | A/B | EEEE |
| VFO/MR | DDDD | 扫描 | BBBB |
| 求助 | 7777 | | |

功能键是整行拉低，会被扫成 13–16，必须用矩阵原始值判断。

</details>

## 编译与刷写

```bash
python tools/build.py                     # 输出 fw/fw.BF
cd baofeng-uv5rh-fw && python tools/flash.py COM10 fw/fw.BF --go
```

进刷机模式：**旋钮关 → 按住两个侧键 → 旋钮开**（屏幕保持全黑）。串口 115200 8N1。

刷前可先探测是否已在刷机模式：

```bash
python tools/uart_mon.py COM10 probe      # 收到 KDH 握手 ACK 即已就绪
```

## 电子书：一条命令

```bash
python tools/flash_ebook.py 你的书.txt
```

脚本会：自动找串口 → UTF-8/GBK 自动识别并转 GBK → 超长自动按行裁到 1.80MB → 显示进度与 ETA。
第一次运行会自动把字库一起传进去（之后跳过）。

Windows 上也可以直接 **把 txt 拖到 `tools/flash_ebook.bat` 上**。

细节：

| 项 | 说明 |
|---|---|
| NOR 布局 | `0x000000` 字库 / `0x046000` 书头 `FEBO`+长度 / `0x046100` 正文 / `0x1FF000` 阅读位置 |
| 上传协议 | `e`=书 `F`=字库 → `READY` → 4B 长度 → `ERASE` →（擦完）`OK` → 每 256B 回 `.` → `DONE` |
| 速度 | 1.8MB 约 190 秒（115200 波特率，含擦除） |
| 阅读位置 | 退出时写 `FBK`+偏移到最后一个扇区；再次进入自动续读，无记录从 0 开始 |
| 限制 | 字库只含 GB2312（6763 常用字），GBK 生僻字显示空白 |

## 串口控制台

连上串口敲单字母即可（回显 `>`）：

| 键 | 功能 | 键 | 功能 |
|---|---|---|---|
| `v` | 版本 + 当前主频 | `r` | 频率/RSSI/静噪/收发状态 |
| `s` | 静噪开关 | `m` | FM/AM |
| `b` | A/B 波段 | `B` | 电池百分比 + 电压 + 原始 ADC |
| `q` | FD6818 静噪判决位 | `n` | NOR JEDEC ID |
| `k` | 书头 magic + 长度 | `e`/`F` | 电子书/字库上传模式 |
| `p` | ping | `f` | FM 诊断 |

## 工具

| 脚本 | 用途 |
|---|---|
| `tools/build.py` | 编译 + 打包 `.BF` |
| `tools/flash.py` | 通过原厂 bootloader 刷写 |
| `tools/flash_ebook.py` | 一键刷电子书（推荐） |
| `tools/ebook_put.py` | 底层上传（书/字库分开传） |
| `tools/make_font_cn.py` | 用系统字体生成 GB2312 16×16 点阵 |
| `tools/uart_mon.py` | 串口监听/探测刷机模式/发命令 |
| `tools/bf_tool.py` | `.BF` 容器打包与解包 |

## 已知限制

- **发射功率没有 mW 标定**：只找到芯片的功率斜坡寄存器，实际瓦数需功率计实测。菜单显示 `P几:斜坡值`。
- **FM 只有调谐没有声音**：RDA5807M 已能 TUNED（97.0–97.3 实测锁定），但音频未到达功放，疑为经 FD6818 的 MICP/MICN 回放，尚无该芯片的音频切换寄存器资料。
- 菜单是 11 项可用功能，不是原厂 70 项的完整复刻。
- 电子书按顺序阅读，向上只回退 24 页。

## 技术笔记（踩过的坑）

1. **bootloader 会留下 48MHz PLL** 再跳进应用 —— 固件必须自己判定时钟，否则 UART 和所有延时都差 6 倍。
2. **`.data` 要自己拷、`.bss` 要自己清**，没有 C 运行时。
3. **调频必须 空闲 → 写频率 → 重进接收**，只写 0x38/0x39 不生效。
4. **PA3 是共享的**（FD6818 SDA + RDA5807 SDA），操作 I²C 前要把 LE 拉低让射频芯片释放总线。
5. **`0x37` 只有 `0x1D00`/`0x1D0F` 两个有效值**，中间值会让 PA 不出功率。
6. **提示音不是射频芯片的 `0x70`**，而是 MCU 的 TIM1_CH4 PWM(PA11)；但尾音要用射频链才能发出去。
7. **SPI NOR 页编程不能跨 256 字节边界**，正文起点固定 `0x046100`。
8. **书区上限要精确算**：`0x1FF000 - 0x046100 = 0x1B7F00`，多 1 字节就会压进书签扇区，保存书签时把书尾擦掉。
9. 插写频线等于插耳机，内部喇叭被机械断开，"没声音"是正常的。

## 致谢

- bootloader 协议与 `.BF` 容器：社区逆向项目 `amoxu/Baofeng-UV-5RM-5RH-RE`
- 原厂固件行为分析：本仓库 `dump/stock.asm`
- 参考实现：DualTachyon / Dondji 系列开源固件

---

*本项目为个人折腾产物，刷机有风险，请自行承担。原厂 bootloader 未被改动，刷坏可用 `fw/restore_nrf_v0.14.BF` 尝试恢复。*
