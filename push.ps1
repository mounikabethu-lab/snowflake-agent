Write-Host "Git Push with Confirmation"
Write-Host "==========================="
Write-Host ""

git status
Write-Host ""

$message = Read-Host "Enter commit message"
if ([string]::IsNullOrWhiteSpace($message)) {
    $message = "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}

Write-Host ""
Write-Host "Commit message: $message"
Write-Host ""

$confirm = Read-Host "Push to GitHub? (yes/no)"

if ($confirm -eq "yes" -or $confirm -eq "y") {
    Write-Host "Adding files..."
    git add .
    
    Write-Host "Committing..."
    git commit -m "$message"
    
    Write-Host "Pushing to GitHub..."
    git push
    
    Write-Host "Success!"
} else {
    Write-Host "Cancelled."
}