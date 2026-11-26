# 逆向分析脚本（可选）

这些是开发过程中写的一次性脚本，原样保留，方便追溯结论是怎么来的。

**注意**：多数脚本依赖仓库里**没有**的数据，比如：

- `dump/fw/*.bin`（原厂固件镜像）
- `dump/stock.asm`（反汇编）
- `_repo/Baofeng-UV-5RM-5RH-RE-main/.../dumped_btldr.bin`（bootloader dump）

没有这些数据时脚本会因找不到文件而报错，属正常现象。需要复现分析的话，请先按上游
`amoxu/Baofeng-UV-5RM-5RH-RE` 的方式自己解包对应版本的 `.BF`。

编译和刷写**不需要**这个目录，可以直接删掉。
