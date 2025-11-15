@echo off
chcp 65001 >nul
echo ================================================================
echo    FakeMan - 基于欲望驱动的自主智能体
echo    快速启动脚本
echo ================================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查.env文件
if not exist .env (
    echo [错误] 未找到.env文件
    echo 请创建.env文件并添加: DEEPSEEK_API_KEY=你的API密钥
    pause
    exit /b 1
)

echo [1] 交互模式（推荐）
echo [2] 持续运行模式
echo [3] 测试运行（5个周期）
echo [4] 退出
echo.

set /p choice="请选择启动模式 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 启动交互模式...
    echo.
    python run_fakeman.py
) else if "%choice%"=="2" (
    echo.
    echo 启动持续运行模式...
    echo 按 Ctrl+C 可以安全退出
    echo.
    python main.py
) else if "%choice%"=="3" (
    echo.
    echo 启动测试模式...
    echo.
    python main_refactored.py
) else if "%choice%"=="4" (
    exit /b 0
) else (
    echo 无效的选择
    pause
    exit /b 1
)

pause

