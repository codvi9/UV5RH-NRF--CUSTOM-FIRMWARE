# 原厂固件解包分析（5RH_NRF V0.13 / FD6818 版）

分析对象：
- baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin（59,392 字节）
- baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-2.bin（1,296 字节）
- 源码 .BF：_repo/.../factory_firmware/NRF_FD6818/5RH_NRF_V0.13_231121.BF（60,704 字节）
- 反汇编：baofeng-uv5rh-fw/dump/stock.asm（24,059 行，arm-none-eabi-objdump -M force-thumb）

---

## 1. 镜像布局

| 项 | 值 |
|---|---|
| 加载地址 | 0x08001000 |
| region1 | 59,392 字节（0xE800） |
| region2 | 1,296 字节（0x510） |
| 合计 | 60,688 字节 ≈ 59.3KB |
| 结束地址 | 0x0800FD10 |

关键结论：**原厂固件几乎占满 60KB 应用区**（59.3/60KB，余量不到 800 字节）。
region2 不是配置区，而是应用的**后半段**（.BF 按 58KB 切分），其中带独立的菜单字符串。

### 向量表（前 0x80 字节）

    SP     = 0x20003DE0      （RAM 顶部附近）
    RESET  = 0x080010E1
    NMI    = 0x08007B59
    HARD   = 0x08006AA1
    ...    = 0x0800C7D5, 0x0800A193, 0x0800C045
    默认   = 0x080010FB（大量未用向量指向它）

---

## 2. 最重要的发现：原厂用 ROM Bootloader 的 IAP 例程

在 0x08001406 开始有一串 **跳板函数（thunk）**，形如：

    movw ip, #0xE401 / movt ip, #0x1FFF / bx ip   -> 跳到 0x1FFFE401
    movw ip, #0xE58D / movt ip, #0x1FFF / bx ip   -> 跳到 0x1FFFE58D
    movw ip, #0xE591 ... 0x1FFFE591
    movw ip, #0xE4D9 ... 0x1FFFE4D9
    movw ip, #0xE4E5 ... 0x1FFFE4E5
    movw ip, #0xE5B1 ... 0x1FFFE5B1
    movw ip, #0xE599 ... 0x1FFFE599
    movw ip, #0xE587 ... 0x1FFFE587
    movw ip, #0xE505 ... 0x1FFFE505

0x1FFFExxx 属于 **AT32 系统存储区（厂商 Bootloader ROM）**，共 40 处 0x1FFF 引用。
这批函数就是 Flash 解锁 / 擦除 / 编程 / 校验 / 跳转 等 IAP 接口。

含义：
- 原厂应用不需要自己写 FLASH 驱动，直接调 ROM 里的例程
- 升级、写频、备份都是通过这套接口完成的
- **我们的固件完全不需要它**（我们用 .BF 由 PC 端刷写，运行期不写内部 FLASH）

---

## 3. 字符串表：菜单标签全表（0x0800F000–0x0800F600 + region2）

从 region1 尾部提取到的完整标签序列（按地址顺序）：

    OFF / 1:1 / 1:2 / 1:4
    SEND SOUND / SEND CODE / ON SITE
    PTT / HIGH / LOW / Middle
    WIDE / NARROW
    10.0 K / 20.0 K / 50.0 K / 25.0 K / 5.0 K / 12.5 K / 2.5 K / 6.25 K
    NAME / FREQ
    DT+ANI / ANI-ST / DT-ST
    1000hz / 2100hz / 1450hz / 1750hz
    TONE1200 / BEEP
    MDF-A / MDF-B / SFT-D / PTT ID / AL-MOD
    POWER ON PWD / VOICE / S-CODE / CDCSS SAVE MODE / LANGUAGE
    SCRAMBLE / MENU EXIT TIME / TONE / RP-STE / STE / SAVE
    POWER ON MSG / DELCH / STOP WATCH / VOICEPRI / AUTOLOCK / BCL
    SQL / RPT-RL / W/N / VERSION / STEP / TXP / ABR / TDR / ROGER
    Scan DCS / R-DCS / T-DCS / Scan CTCSS / R-CTCSS / T-CTCSS
    RESET / OFFSET / PTT-LT / TOT / BEEP PROMPT / DTMFST / SC-REV
    VOX / VOX DELAY / DTMF / TONE

region2 中另有：BOTH / VOLTAGE / LOGO / MEMCH

这表明原厂菜单是**经典 UV-5R 菜单体系**（约 40 项），外加宝锋自己的扩展项（STOP WATCH、VOX DELAY、SCRAMBLE、LANGUAGE、POWER ON MSG、AUTOLOCK 等）。

其它格式化字符串：
- 0x080035EE：`CH-%03d `   （信道显示格式）
- 0x0800363C：`VFO` / `%03d`

注意：**全镜像几乎没有中文**，说明中文信道名不是以文本存于固件，而是**字库点阵 + 索引**（与叮咚鸡同一思路），字库在外部 25QH16 中。

---

## 4. 频率与信道数据

在镜像中搜索 32 位与 16 位的常见频率常数（136000000/174000000/400000000/470000000/108000000/87500000/76000000，以及对应的 kHz 形式 136000/174000/400000/470000/108000/87500/76000）——**全部未命中**。

推断：
- 频率不是以 Hz 或 kHz 的裸常数存储，而是经**换算公式**（如乘以步进的定点数）或**信道结构体字段**处理
- 显示用 `CH-%03d` 和 `%03d`，说明信道号是 3 位十进制
- 需要进一步定位信道结构体（搜索 0x0800D8A8 附近对 `CH-%03d` 的引用）

---

## 5. 代码规模与结构特征

| 指标 | 值 |
|---|---|
| 反汇编总行数 | 24,059 |
| bl 指令数 | 1,828 |
| 0x1FFF（ROM IAP）引用 | 40 |
| ASCII 字符串段 | 663 处（多为代码误判，真实标签约 80 条） |

代码密度说明：59KB 里塞进了完整 UI + 菜单 + 双频 + 扫描 + DTMF + VOX + 加密扰频 + 中文显示框架，属于高度优化的小体积固件。

---

## 6. 与原厂行为的对照（结合此前实机观察）

| 行为 | 原厂实现（推断） | 我们的现状 |
|---|---|---|
| 双频守候 | `TDR` 菜单项，快速轮询 A/B | 已按用户要求删除；轮询方式与原厂一致（单芯片物理限制） |
| 静噪 | `SQL` 菜单 0–9 级，寄存器或固件判定 | 固件判定，门限固定 RSSI 150 |
| 中文信道名 | 字库索引，字库在外部 FLASH | 未实现（5x7 英文字库，44 字符） |
| 写频/升级 | 调 ROM IAP | 走 .BF + PC 刷写 |
| 菜单 | 约 40 项，经典 UV-5R 体系 | 7 项（SQL/MOD/DUAL/SPEC/FM/ABOUT/EXIT） |

---

## 7. 对开发的实际指导

1. **菜单结构照抄原厂顺序**：`SQL, STEP, TXP, W/N, TDR, BEEP, TOT, R-CTCSS, T-CTCSS, R-DCS, T-DCS, SC-REV, PTT-LT, ...` 这套是用户熟悉的心智模型
2. **不需要 ROM IAP**：我们的固件不在运行期写内部 FLASH，省掉这块
3. **中文必须走外部 FLASH 字库**：原厂同样如此，这印证了之前的判断
4. **频率存储要找结构体而不是常数**：下步可在 0x0800D8A8（`CH-%03d` 引用处）回溯信道读取函数
5. **代码体积参照**：原厂 59.3KB 做全套；我们 8KB 做基础功能，若要接近原厂需精简外设驱动、去掉浮点/字符串冗余

---

## 8. 还没挖到、需要继续的部分

| 目标 | 方法 |
|---|---|
| FD6818 三线写函数 | 搜 GPIO BSRR/ODR 写 + 短延时循环的三连模式（LE/SCK/SDA = PC13/PA2/PA3） |
| 静噪判定逻辑 | 从 0x67 RSSI 读取处回溯比较分支；确认原厂是否用 `0x78` |
| 双守（TDR）时序 | 找 TDR 菜单项的开关变量，回溯到定时切换频率的循环 |
| 按键映射表 | 搜键盘矩阵扫描函数（4 列输出 + 4 行读入），提取键值→动作表 |
| 信道结构体 | 从 `CH-%03d` 格式化调用回溯 |
| 中文显示 | 找字库读取（SPI 读 25QH16）与点阵绘制例程 |

---

## 9. 复现方法

    # 反汇编（已生成的 stock.asm）
    "baofeng-uv5rh-fw/tools/xpack-arm-none-eabi-gcc-13.2.1-1.1/bin/arm-none-eabi-objdump.exe" \
      -D -b binary -m armv7e-m -M force-thumb --adjust-vma=0x08001000 \
      baofeng-uv5rh-fw/dump/fw/5RH_NRF_V0.13_231121-1.bin > baofeng-uv5rh-fw/dump/stock.asm

    # 字符串提取
    python baofeng-uv5rh-fw/tools/an3.py

工具链：xpack arm-none-eabi-gcc 13.2.1（已下载在工作区）
