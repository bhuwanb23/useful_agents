@echo off
REM Quick Proxy Fix - Run this before any npm/prisma commands
REM Update proxy URL below with your actual proxy

echo.
echo =====================================================
echo    Quick Corporate Proxy Fix
echo =====================================================
echo.

REM ========================================
REM CONFIGURE YOUR PROXY HERE
REM ========================================
SET PROXY_HOST=proxy.company.com
SET PROXY_PORT=8080
REM ========================================

SET PROXY_URL=http://%PROXY_HOST%:%PROXY_PORT%

echo Using proxy: %PROXY_URL%
echo.

REM Set environment variables
echo Setting environment variables...
SET HTTP_PROXY=%PROXY_URL%
SET HTTPS_PROXY=%PROXY_URL%
SET NODE_TLS_REJECT_UNAUTHORIZED=0
SET PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1

REM Configure npm
echo Configuring npm...
call npm config set proxy %PROXY_URL%
call npm config set https-proxy %PROXY_URL%
call npm config set strict-ssl false
call npm config set registry http://registry.npmjs.org/

REM Configure git
echo Configuring git...
call git config --global http.proxy %PROXY_URL%
call git config --global https.proxy %PROXY_URL%
call git config --global http.sslVerify false

echo.
echo =====================================================
echo    Configuration Complete!
echo =====================================================
echo.
echo You can now run:
echo   - npm install
echo   - npm run db:generate
echo   - npm run db:migrate
echo   - npm run dev
echo.
echo Or use helper commands:
echo   - prisma-proxy.bat generate
echo   - npm-proxy.bat install
echo.
echo Press any key to exit...
pause >nul
