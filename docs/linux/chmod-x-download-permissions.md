# 下载文件为什么有时需要 `chmod +x`

是否需要 `chmod +x`，本质取决于传输或打包格式有没有保存并恢复可执行权限：Git 通过 index 保存 executable bit，tar/部分 zip 通过 metadata 保存权限；而 wget、curl、浏览器直接下载裸文件时，HTTP 不携带 Unix 权限信息，所以通常需要手动 `chmod +x`。
