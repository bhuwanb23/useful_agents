# Manual Prisma Engine Download Script
# Use this if automatic download fails due to proxy/SSL issues

Write-Host "🔧 Manual Prisma Engine Download" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Get Prisma version
$packageJson = Get-Content "package.json" | ConvertFrom-Json
$prismaVersion = $packageJson.devDependencies.'@prisma/client'
if (-not $prismaVersion) {
    $prismaVersion = $packageJson.dependencies.'@prisma/client'
}

Write-Host "📦 Detected Prisma version: $prismaVersion" -ForegroundColor Green
Write-Host ""

# Prisma engine commit hash (update this for specific versions)
# This is for Prisma 5.x - check https://github.com/prisma/prisma-engines/releases
$engineVersion = "605197351a3c8bdd595af2d2a9bc3025bca48ea2"

Write-Host "🔍 Engine version: $engineVersion" -ForegroundColor Yellow
Write-Host ""

# Create engines directory
$enginesDir = "$env:USERPROFILE\.cache\prisma\binaries\engines\$engineVersion"
New-Item -ItemType Directory -Force -Path $enginesDir | Out-Null

# Download URLs
$baseUrl = "https://binaries.prisma.sh/all_commits/$engineVersion/windows"
$engines = @(
    "schema-engine.exe.gz",
    "query-engine.exe.gz",
    "introspection-engine.exe.gz",
    "migration-engine.exe.gz",
    "prisma-fmt.exe.gz"
)

Write-Host "📥 Downloading engines..." -ForegroundColor Green
Write-Host ""

# Configure web client for proxy
$webClient = New-Object System.Net.WebClient

# Try to use system proxy
$proxy = [System.Net.WebRequest]::GetSystemWebProxy()
$proxy.Credentials = [System.Net.CredentialCache]::DefaultNetworkCredentials
$webClient.Proxy = $proxy

# Disable SSL verification (for corporate proxy)
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12

foreach ($engine in $engines) {
    $url = "$baseUrl/$engine"
    $outputPath = "$enginesDir\$engine"
    
    Write-Host "  Downloading: $engine" -ForegroundColor Yellow
    
    try {
        $webClient.DownloadFile($url, $outputPath)
        
        # Extract .gz file
        $extractedPath = $outputPath -replace '\.gz$', ''
        
        # Simple GZ extraction (requires 7-Zip or expand-archive)
        if (Get-Command 7z -ErrorAction SilentlyContinue) {
            7z x $outputPath -o"$enginesDir" -y | Out-Null
            Remove-Item $outputPath
        } else {
            Write-Host "    ⚠️  Install 7-Zip to auto-extract, or manually extract $engine" -ForegroundColor Yellow
        }
        
        Write-Host "    ✅ Downloaded" -ForegroundColor Green
    } catch {
        Write-Host "    ❌ Failed: $_" -ForegroundColor Red
        Write-Host "    Manual download: $url" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Download complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next step: Run 'npx prisma generate'" -ForegroundColor Yellow
Write-Host ""
