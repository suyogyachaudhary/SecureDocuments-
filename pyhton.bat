@echo off
REM Shim for common typo 'pyhton' -> 'python'
REM Usage: pyhton <args>  (works like python <args>)
python %*
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo Python execution failed or 'python' not found. Try:
  echo  - Ensure Python is installed and available in PATH.
  echo  - Run: python %*
  echo  - Or: py %*
)
