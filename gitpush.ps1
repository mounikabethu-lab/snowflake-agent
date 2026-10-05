# ============================================================================
# Push to GitHub Script (PowerShell)
# ============================================================================

# Load .env file
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^=]+)\s*=\s*(.+)\s*$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Variable -Name $key -Value $value -Scope Global
        }
    }
}

# Get git config
$branch = if ($env:GIT_BRANCH) { $env:GIT_BRANCH } else { "main" }
$message = if ($env:GIT_COMMIT_MESSAGE) { $env:GIT_COMMIT_MESSAGE } else { "Deploy Snowflake Native Agent" }

Write-Host ""
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host "GIT PUSH TO GITHUB" -ForegroundColor Magenta
Write-Host "================================================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "Branch:  " -NoNewline -ForegroundColor White
Write-Host $branch -ForegroundColor Green

Write-Host "Message: " -NoNewline -ForegroundColor White
Write-Host $message -ForegroundColor Green

Write-Host ""

# Ask for confirmation
$response = Read-Host "Push to GitHub? (yes/no)"

if ($response -ne "yes" -and $response -ne "y") {
    Write-Host ""
    Write-Host "❌ Push cancelled" -ForegroundColor Red
    Write-Host ""
    exit 0
}

# Execute git commands
Write-Host ""
Write-Host "Executing git commands..." -ForegroundColor White
Write-Host ""

try {
    # Add files
    Write-Host "  ▶️  git add sql/ .env"
    git add sql/ .env
    if ($LASTEXITCODE -eq 0) {
        Write-Host "     ✅ Files staged" -ForegroundColor Green
    } else {
        Write-Host "     ❌ Failed to stage files" -ForegroundColor Red
        exit 1
    }
    
    # Commit
    Write-Host "  ▶️  git commit -m `"$message`""
    git commit -m $message
    if ($LASTEXITCODE -eq 0) {
        Write-Host "     ✅ Committed" -ForegroundColor Green
    } else {
        Write-Host "     ❌ Failed to commit" -ForegroundColor Red
        exit 1
    }
    
    # Push
    Write-Host "  ▶️  git push origin $branch"
    git push origin $branch
    if ($LASTEXITCODE -eq 0) {
        Write-Host "     ✅ Pushed" -ForegroundColor Green
    } else {
        Write-Host "     ❌ Failed to push" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✅ Successfully pushed to GitHub!" -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}