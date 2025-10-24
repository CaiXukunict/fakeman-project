@echo off
chcp 65001 >nul
title FakeMan 图形聊天界面

echo ================================================
echo    FakeMan 图形聊天界面
echo ================================================
echo.
echo 正在启动...
echo.
echo 💡 提示：请确保 main.py 已在另一个终端运行
echo.

python chat_gui.py

if errorlevel 1 (
    echo.
    echo ❌ 启动失败！
    echo 请检查：
    echo   1. Python 是否已安装
    echo   2. 依赖是否已安装 ^(pip install -r requirements.txt^)
    echo.
    pause
)

