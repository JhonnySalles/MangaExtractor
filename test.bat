@echo off
chcp 65001
cd /d "%~dp0"
set PYTHONPATH=src
echo Rodando os testes...
.\.venv\Scripts\python.exe -m pytest tests/ --cov=src/manga_extractor --cov-report=term-missing
if %errorlevel% neq 0 (
    echo.
    echo Erro ao executar os testes!
    pause
) else (
    echo.
    echo Todos os testes passaram!
)
