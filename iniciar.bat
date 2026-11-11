@echo off
setlocal
cd /d "%~dp0"
title PERFECT Shock Data
set "LOG=%~dp0iniciar_log.txt"
echo === %date% %time% === > "%LOG%"
echo Pasta: %cd% >> "%LOG%"
if exist "VERSAO.txt" type "VERSAO.txt"
if not exist "app.py" goto sem_pasta

rem --- 1) acha o Python (nenhum acesso de administrador e nenhum driver do sistema e necessario) ---
set "PY="
py -3 --version >> "%LOG%" 2>&1
if not errorlevel 1 set "PY=py -3"
if defined PY goto achou
python --version >> "%LOG%" 2>&1
if not errorlevel 1 set "PY=python"
if defined PY goto achou
goto sem_python

:achou
echo Python encontrado: %PY%
if exist ".venv\Scripts\python.exe" goto venv_ok
echo Criando ambiente portatil (.venv) nesta pasta...
%PY% -m venv .venv >> "%LOG%" 2>&1
if not exist ".venv\Scripts\python.exe" goto erro_venv

:venv_ok
set "VPY=.venv\Scripts\python.exe"
set "HAVEENV="
if exist ".env" set "HAVEENV=1"
if exist "%USERPROFILE%\.perfect_shock_data\.env" set "HAVEENV=1"
if exist "..\.env" set "HAVEENV=1"
for /d %%D in ("..\*") do if exist "%%~fD\.env" set "HAVEENV=1"
if not defined HAVEENV if exist ".env.example" (
  copy /y ".env.example" ".env" >nul
  echo.
  echo  ATENCAO: criei o arquivo .env. Abra-o no Bloco de Notas e preencha DEV_DB_PASSWORD
  echo  para o sistema sincronizar com o servidor. Depois feche e abra este arquivo de novo.
  echo.
)

rem --- 2) dependencias: tenta tudo de uma vez; se algum pacote falhar, instala um a um e segue ---
echo Instalando/verificando dependencias (na 1a vez precisa de internet)...
"%VPY%" -m pip install --disable-pip-version-check --prefer-binary -r requirements.txt >> "%LOG%" 2>&1
if not errorlevel 1 goto deps_ok
echo Alguns pacotes falharam; instalando um por um...
for /f "usebackq eol=# tokens=*" %%L in ("requirements.txt") do (
  "%VPY%" -m pip install --disable-pip-version-check --prefer-binary "%%L" >> "%LOG%" 2>&1
)
:deps_ok
"%VPY%" -c "import flask,pandas,openpyxl" >> "%LOG%" 2>&1
if errorlevel 1 goto erro_pip
for /f "delims=" %%D in ('"%VPY%" -c "import data_pipeline as d; print(', '.join(d.available_drivers()) or 'NENHUM')"') do set "DRV=%%D"
echo Drivers do SQL Server disponiveis: %DRV%
echo Drivers: %DRV% >> "%LOG%"

echo.
echo Abrindo http://127.0.0.1:5000  (feche esta janela para encerrar o sistema)
start "" /min cmd /c "ping -n 4 127.0.0.1 >nul & start http://127.0.0.1:5000"
"%VPY%" app.py
echo.
echo O sistema parou. Leia a mensagem acima.
pause
exit /b 0

:sem_pasta
echo Execute este arquivo dentro da pasta do projeto (onde esta o app.py).
pause
exit /b 1
:sem_python
echo Python 3 nao encontrado. Instale o Python (marque "Add to PATH"; nao precisa de administrador: "Install for me only").
pause
exit /b 1
:erro_venv
echo Nao foi possivel criar o ambiente .venv. Veja iniciar_log.txt
pause
exit /b 1
:erro_pip
echo Nao foi possivel instalar as dependencias basicas. Confira a internet/proxy e veja iniciar_log.txt
pause
exit /b 1
