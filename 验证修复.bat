@echo off
chcp 65001 >nul
echo ================================================================
echo    FakeMan 系统修复验证
echo ================================================================
echo.

echo 正在测试DeepSeek API连接...
echo.

REM 创建临时测试脚本
echo import sys > temp_test.py
echo if sys.platform == 'win32': >> temp_test.py
echo     try: >> temp_test.py
echo         sys.stdout.reconfigure(encoding='utf-8') >> temp_test.py
echo         sys.stderr.reconfigure(encoding='utf-8') >> temp_test.py
echo     except: pass >> temp_test.py
echo. >> temp_test.py
echo import os >> temp_test.py
echo from dotenv import load_dotenv >> temp_test.py
echo load_dotenv() >> temp_test.py
echo. >> temp_test.py
echo if not os.getenv('DEEPSEEK_API_KEY'): >> temp_test.py
echo     print('❌ 未找到 DEEPSEEK_API_KEY') >> temp_test.py
echo     exit(1) >> temp_test.py
echo. >> temp_test.py
echo try: >> temp_test.py
echo     from utils.config import Config >> temp_test.py
echo     from action_model.llm_client import LLMClient >> temp_test.py
echo     config = Config() >> temp_test.py
echo     client = LLMClient(config) >> temp_test.py
echo     response = client.generate('测试', max_tokens=10) >> temp_test.py
echo     print('✅ DeepSeek API 连接正常') >> temp_test.py
echo     print(f'响应: {response[:50]}...') >> temp_test.py
echo except Exception as e: >> temp_test.py
echo     print(f'❌ 错误: {e}') >> temp_test.py
echo     exit(1) >> temp_test.py

python temp_test.py

if errorlevel 1 (
    echo.
    echo ================================================================
    echo    测试失败，请检查：
    echo    1. .env 文件中的 DEEPSEEK_API_KEY 是否正确
    echo    2. 网络连接是否正常
    echo    3. 依赖是否已安装: pip install -r requirements.txt
    echo ================================================================
    del temp_test.py
    pause
    exit /b 1
)

echo.
echo ================================================================
echo    ✅ 所有测试通过！
echo    系统已修复，可以正常运行
echo.
echo    使用以下方式启动系统：
echo    - 双击运行: 快速启动.bat
echo    - 命令行: python run_fakeman.py
echo ================================================================

REM 清理临时文件
del temp_test.py

pause

