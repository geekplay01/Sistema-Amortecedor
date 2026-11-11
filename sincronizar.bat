@echo off
rem PERFECT Shock Data - sincronizacao diaria com o servidor (somente leitura).
rem Chamado pela tarefa agendada do Windows "PERFECT Shock Data - sincronizacao diaria" (06:30).
rem Funciona com o app fechado. Se o app ja sincronizou hoje, nao repete. Se o app estiver sincronizando, desiste (trava).
rem Log: data\sincronizacao_log.txt (as ultimas execucoes ficam no fim do arquivo).
setlocal
cd /d "%~dp0"
set "PYTHONIOENCODING=utf-8"
set "PSD_SCHEDULER=off"
set "LOG=%~dp0data\sincronizacao_log.txt"
if not exist "%~dp0data" mkdir "%~dp0data"
if not exist ".venv\Scripts\python.exe" (
  echo [%date% %time%] ERRO: .venv nao encontrado. Abra o iniciar.bat uma vez para criar o ambiente. >> "%LOG%"
  exit /b 2
)
echo === %date% %time% === >> "%LOG%"
".venv\Scripts\python.exe" data_pipeline.py diaria >> "%LOG%" 2>&1
set "RC=%ERRORLEVEL%"
echo === fim (codigo %RC%) === >> "%LOG%"
exit /b %RC%
