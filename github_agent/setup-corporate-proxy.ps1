# Corporate Proxy Setup Script for Windows PowerShell
# Run this script to configure your development environment for corporate proxy

Write-Host "🔧 Corporate Proxy Configuration Script" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Function to test if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "⚠️  Warning: Not running as Administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host "   Consider running: Right-click PowerShell -> Run as Administrator" -ForegroundColor Yellow
    Write-Host ""
}

# Detect proxy settings
Write-Host "🔍 Step 1: Detecting Proxy Settings..." -ForegroundColor Green

$proxyServer = ""
$proxyPort = ""

# Try to get proxy from system settings
$proxySettings = Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -ErrorAction SilentlyContinue
if ($proxySettings.ProxyEnable -eq 1) {
    $proxyFull = $proxySettings.ProxyServer
    if ($proxyFull -match '(.+):(\d+)') {
        $proxyServer = $matches[1]
        $proxyPort = $matches[2]
    } else {
        $proxyServer = $proxyFull
        $proxyPort = "8080"
    }
}

# Try to get from environment variables
if (-not $proxyServer -and $env:HTTP_PROXY) {
    if ($env:HTTP_PROXY -match 'https?://(.+):(\d+)') {
        $proxyServer = $matches[1]
        $proxyPort = $matches[2]
    }
}

# Manual input if not detected
if (-not $proxyServer) {
    Write-Host "❌ Could not auto-detect proxy settings." -ForegroundColor Yellow
    Write-Host ""
    $proxyServer = Read-Host "Enter your proxy server (e.g., proxy.company.com)"
    $proxyPort = Read-Host "Enter proxy port (default: 8080)"
    if (-not $proxyPort) { $proxyPort = "8080" }
}

$proxyUrl = "http://${proxyServer}:${proxyPort}"
Write-Host "✅ Using proxy: $proxyUrl" -ForegroundColor Green
Write-Host ""

# Configure npm
Write-Host "🔧 Step 2: Configuring npm..." -ForegroundColor Green
npm config set proxy $proxyUrl
npm config set https-proxy $proxyUrl
npm config set strict-ssl false
npm config set registry http://registry.npmjs.org/
Write-Host "✅ npm configured" -ForegroundColor Green
Write-Host ""

# Configure git
Write-Host "🔧 Step 3: Configuring git..." -ForegroundColor Green
git config --global http.proxy $proxyUrl
git config --global https.proxy $proxyUrl
git config --global http.sslVerify false
Write-Host "✅ git configured" -ForegroundColor Green
Write-Host ""

# Set environment variables for current session
Write-Host "🔧 Step 4: Setting environment variables..." -ForegroundColor Green
$env:HTTP_PROXY = $proxyUrl
$env:HTTPS_PROXY = $proxyUrl
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
Write-Host "✅ Environment variables set for current session" -ForegroundColor Green
Write-Host ""

# Create .env file for Prisma
Write-Host "🔧 Step 5: Configuring Prisma..." -ForegroundColor Green

$prismaEnv = @"
# Prisma Proxy Configuration
HTTP_PROXY=$proxyUrl
HTTPS_PROXY=$proxyUrl
NODE_TLS_REJECT_UNAUTHORIZED=0
PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1
"@

$prismaEnv | Out-File -FilePath ".env.proxy" -Encoding UTF8
Write-Host "✅ Created .env.proxy file" -ForegroundColor Green
Write-Host ""

# Create permanent environment variable script
Write-Host "🔧 Step 6: Creating permanent configuration..." -ForegroundColor Green

$permanentScript = @"
# Run this to set PERMANENT environment variables (requires restart)
# Right-click PowerShell -> Run as Administrator, then run this script

[System.Environment]::SetEnvironmentVariable('HTTP_PROXY', '$proxyUrl', 'User')
[System.Environment]::SetEnvironmentVariable('HTTPS_PROXY', '$proxyUrl', 'User')
[System.Environment]::SetEnvironmentVariable('NODE_TLS_REJECT_UNAUTHORIZED', '0', 'User')

Write-Host "✅ Permanent environment variables set!" -ForegroundColor Green
Write-Host "⚠️  Please RESTART your terminal for changes to take effect" -ForegroundColor Yellow
"@

$permanentScript | Out-File -FilePath "set-permanent-proxy.ps1" -Encoding UTF8
Write-Host "✅ Created set-permanent-proxy.ps1 (run as admin for permanent settings)" -ForegroundColor Green
Write-Host ""

# Create certificate helper
Write-Host "🔧 Step 7: Handling SSL Certificates..." -ForegroundColor Green

$certPath = "C:\certs\corp-root.pem"
if (Test-Path $certPath) {
    $env:NODE_EXTRA_CA_CERTS = $certPath
    Write-Host "✅ Found corporate certificate at $certPath" -ForegroundColor Green
    
    # Add to npm config
    npm config set cafile $certPath
    Write-Host "✅ Configured npm to use corporate certificate" -ForegroundColor Green
} else {
    Write-Host "⚠️  No certificate found at $certPath" -ForegroundColor Yellow
    Write-Host "   If you have SSL issues, ask IT for the root certificate" -ForegroundColor Yellow
}
Write-Host ""

# Create helper batch file for Prisma
Write-Host "🔧 Step 8: Creating Prisma helper scripts..." -ForegroundColor Green

$prismaBatch = @"
@echo off
REM Prisma commands with proxy configuration
set HTTP_PROXY=$proxyUrl
set HTTPS_PROXY=$proxyUrl
set NODE_TLS_REJECT_UNAUTHORIZED=0
set PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING=1

if "%1"=="generate" (
    echo Running: prisma generate
    npx prisma generate
) else if "%1"=="migrate" (
    echo Running: prisma migrate dev
    npx prisma migrate dev
) else if "%1"=="studio" (
    echo Running: prisma studio
    npx prisma studio
) else if "%1"=="push" (
    echo Running: prisma db push
    npx prisma db push
) else (
    echo Usage: prisma-proxy.bat [generate^|migrate^|studio^|push]
    echo.
    echo Examples:
    echo   prisma-proxy.bat generate
    echo   prisma-proxy.bat migrate
    echo   prisma-proxy.bat studio
)
"@

$prismaBatch | Out-File -FilePath "prisma-proxy.bat" -Encoding ASCII
Write-Host "✅ Created prisma-proxy.bat helper script" -ForegroundColor Green
Write-Host ""

# Create npm helper
$npmBatch = @"
@echo off
REM npm commands with proxy configuration
set HTTP_PROXY=$proxyUrl
set HTTPS_PROXY=$proxyUrl
set NODE_TLS_REJECT_UNAUTHORIZED=0

npm %*
"@

$npmBatch | Out-File -FilePath "npm-proxy.bat" -Encoding ASCII
Write-Host "✅ Created npm-proxy.bat helper script" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Corporate Proxy Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Summary:" -ForegroundColor Yellow
Write-Host "  ✅ npm configured with proxy: $proxyUrl" -ForegroundColor White
Write-Host "  ✅ git configured with proxy" -ForegroundColor White
Write-Host "  ✅ Environment variables set (current session)" -ForegroundColor White
Write-Host "  ✅ Created helper scripts" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Try Prisma generation now:" -ForegroundColor Cyan
Write-Host "   prisma-proxy.bat generate" -ForegroundColor White
Write-Host ""
Write-Host "2️⃣  Install npm packages:" -ForegroundColor Cyan
Write-Host "   npm-proxy.bat install" -ForegroundColor White
Write-Host ""
Write-Host "3️⃣  For PERMANENT configuration (requires admin + restart):" -ForegroundColor Cyan
Write-Host "   Right-click PowerShell -> Run as Administrator" -ForegroundColor White
Write-Host "   .\set-permanent-proxy.ps1" -ForegroundColor White
Write-Host ""
Write-Host "📝 Helper Scripts Created:" -ForegroundColor Yellow
Write-Host "   - prisma-proxy.bat   (Run Prisma commands with proxy)" -ForegroundColor White
Write-Host "   - npm-proxy.bat      (Run npm commands with proxy)" -ForegroundColor White
Write-Host "   - set-permanent-proxy.ps1 (Set permanent env vars)" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  If still having issues:" -ForegroundColor Yellow
Write-Host "   - Ensure proxy URL is correct" -ForegroundColor White
Write-Host "   - Check if proxy requires authentication" -ForegroundColor White
Write-Host "   - Contact IT for root certificate if SSL errors persist" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
