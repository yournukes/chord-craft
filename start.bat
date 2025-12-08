@echo off
setlocal

rem 実行ディレクトリをスクリプト配置場所に変更
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

set "VENV_DIR=.venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "ACTIVATE=%VENV_DIR%\Scripts\activate.bat"

rem 仮想環境がなければ作成
if not exist "%PYTHON%" (
    echo 仮想環境を作成しています...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
)

rem 仮想環境を有効化
call "%ACTIVATE%"
if errorlevel 1 goto :error

rem 依存関係をインストール
echo 依存関係をインストールしています...
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo サーバーを起動します...
rem 再読み目的のウォッチャが仮想環境下を監視して
rem pip アップグレードなどで無限再読みが発生するのを防ぐ
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude ".venv/*"
if errorlevel 1 goto :error

goto :eof

:error
echo.
echo エラーが発生しました。ログを確認してください。
exit /b 1
