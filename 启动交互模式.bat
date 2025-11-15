@echo off
chcp 65001 >nul
title FakeMan 交互模式

echo.
echo ================================================================
echo    FakeMan 交互式系统启动
echo    直接输入模式 + 实时仪表盘
echo ================================================================
echo.

python run_interactive.py

pause

