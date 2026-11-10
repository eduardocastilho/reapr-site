@echo off
setlocal
chcp 65001 >nul
title REAPR Labs - site local
cd /d "%~dp0"

echo.
echo  REAPR Labs - rodando o site localmente
echo  ======================================
echo.

rem 1. Encontrar o Python 3
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
  python --version >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo  Python 3 nao encontrado. Instalando com o winget...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  if errorlevel 1 (
    echo.
    echo  Nao consegui instalar o Python automaticamente.
    echo  Instale pelo site python.org ^(marque "Add python.exe to PATH"^) e rode este arquivo de novo.
    pause
    exit /b 1
  )
  echo.
  echo  Python instalado. Feche esta janela e rode o rodar-local.bat de novo.
  pause
  exit /b 0
)
echo  Python: 
%PY% --version

rem 2. Ambiente virtual e dependencias
if not exist ".venv\Scripts\python.exe" (
  echo  Criando ambiente virtual em .venv ...
  %PY% -m venv .venv || (echo  Falha ao criar o .venv & pause & exit /b 1)
)
echo  Instalando dependencias ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt || (echo  Falha ao instalar dependencias & pause & exit /b 1)

rem 3. Gerar o site (inclui rascunhos para voce revisar)
echo  Gerando o site ...
".venv\Scripts\python.exe" build.py --drafts || (echo  O build falhou. Leia a mensagem acima. & pause & exit /b 1)

rem 4. Servir e abrir no navegador
echo.
echo  Site rodando em http://localhost:8000
echo  Para parar, feche esta janela ^(ou Ctrl+C^).
echo  Depois de editar algum .md, rode este arquivo de novo.
echo.
start "" http://localhost:8000
".venv\Scripts\python.exe" -m http.server 8000 --bind 127.0.0.1 -d dist
