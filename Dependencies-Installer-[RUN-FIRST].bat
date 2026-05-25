@echo off
title AI Browser Dependency Installer

echo ================================
echo Installing AI Browser packages...
echo ================================
echo.

python -m pip install --upgrade pip

pip install ^
PyQt5==5.15.11 ^
PyQtWebEngine==5.15.7 ^
PyQt5-Qt5==5.15.2 ^
PyQt5-sip==12.17.1

echo.
echo ================================
echo Installation Complete!
echo ================================
pause