# Security Check Script - Verify no secrets are exposed
# Windows PowerShell version

Write-Host "`n🔍 Checking for exposed secrets in code...`n" -ForegroundColor Cyan

# Check for exposed API keys in JavaScript files
Write-Host "1. Checking for exposed API keys (sk-or-v1-)..." -ForegroundColor Yellow
try {
    $jsFiles = Get-ChildItem -Path ".\static\js\*.js" -Recurse -ErrorAction SilentlyContinue
    $foundKeys = $false
    foreach ($file in $jsFiles) {
        $content = Get-Content $file.FullName -Raw
        if ($content -match "sk-or-v1-[a-zA-Z0-9]{60,}") {
            Write-Host "   ❌ WARNING: Exposed API key in $($file.Name)" -ForegroundColor Red
            $foundKeys = $true
        }
    }
    if (-not $foundKeys) {
        Write-Host "   ✅ No exposed API keys found in JavaScript files" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Could not check JavaScript files" -ForegroundColor Yellow
}

Write-Host ""

# Check .gitignore coverage
Write-Host "2. Checking .gitignore coverage..." -ForegroundColor Yellow
if (Test-Path .gitignore) {
    $gitignore = Get-Content .gitignore -Raw
    
    if ($gitignore -match "\.env") {
        Write-Host "   ✅ .env is in .gitignore" -ForegroundColor Green
    } else {
        Write-Host "   ❌ WARNING: .env not in .gitignore!" -ForegroundColor Red
    }
    
    if ($gitignore -match "\.db|\.sqlite|plansphere\.db") {
        Write-Host "   ✅ Database files are in .gitignore" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Database files might not be ignored" -ForegroundColor Yellow
    }
    
    if ($gitignore -match "\.log|server\.log") {
        Write-Host "   ✅ Log files are in .gitignore" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Log files might not be ignored" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ .gitignore file not found!" -ForegroundColor Red
}

Write-Host ""

# Check if .env exists and is not tracked
Write-Host "3. Checking .env file status..." -ForegroundColor Yellow
if (Test-Path .env) {
    Write-Host "   ✅ .env file exists" -ForegroundColor Green
    try {
        git ls-files --error-unmatch .env 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ❌ CRITICAL: .env is tracked by Git! Run: git rm --cached .env" -ForegroundColor Red
        } else {
            Write-Host "   ✅ .env is not tracked by Git" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ✅ .env is not tracked by Git" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  .env file doesn't exist (create from .env.example)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🎉 Security Check Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. ⚠️  REVOKE the old API key at https://openrouter.ai/" -ForegroundColor Yellow
Write-Host "2. 📝 Create .env from .env.example and add your NEW key" -ForegroundColor White
Write-Host "3. 📦 Install dependency: pip install httpx" -ForegroundColor White
Write-Host "4. ✅ Verify everything works, then push to GitHub!" -ForegroundColor Green
Write-Host ""
