@echo off
chcp 65001 >nul
setlocal
if "%~1"=="" (
  echo 用法：把电子书 txt 文件拖到本 bat 上，或命令行执行
  echo   flash_ebook.bat 你的书.txt
  echo   flash_ebook.bat 你的书.txt --port COM10
  pause
  exit /b 1
)
python "%~dp0flash_ebook.py" %*
echo.
pause
