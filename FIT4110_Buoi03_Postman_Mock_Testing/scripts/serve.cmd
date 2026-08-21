@echo off
REM Run AI Vision service or side mocks on Windows.
REM Usage: scripts\serve.cmd <service>
REM   service = vision | camera-mock | core-mock
setlocal

if "%~1"=="" (
  set SERVICE=vision
) else (
  set SERVICE=%~1
)

if "%SERVICE%"=="vision" (
  set APP=ai_vision_service.main:app
  set PORT=8000
) else if "%SERVICE%"=="camera-mock" (
  set APP=side_mocks.camera_stream:app
  set PORT=4014
) else if "%SERVICE%"=="core-mock" (
  set APP=side_mocks.core_business:app
  set PORT=4012
) else (
  echo Unknown service: %SERVICE%
  exit /b 1
)

set PYTHONPATH=src
python -m uvicorn %APP% --host 127.0.0.1 --port %PORT% --log-level warning
