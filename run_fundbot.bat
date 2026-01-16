@echo off
setlocal

echo =========================================
echo   GoFundBot 一键启动 (conda: fundbot)
echo =========================================

REM 检查 conda 是否可用
where conda >nul 2>nul
if %errorlevel% neq 0 (
  echo [ERROR] 未找到 conda，请先在系统 PATH 中配置 conda。
  echo        可以先在 Anaconda Prompt 中运行此脚本。
  pause
  exit /b 1
)

REM 启动后端 (新窗口)
start "GoFundBot Backend" cmd /k "call conda activate fundbot && python Backend\app.py"

REM 启动前端 (新窗口)
start "GoFundBot Frontend" cmd /k "cd Frontend && npm run dev"

echo [OK] 已启动后端与前端。
echo     后端: http://127.0.0.1:5000
echo     前端: http://127.0.0.1:5173
pause
