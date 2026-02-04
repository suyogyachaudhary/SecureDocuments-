param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
# Shim for typo 'pyhton' -> 'python'
try {
    & python @Args
} catch {
    Write-Host ""
    Write-Host "Python execution failed or 'python' not found. Try:"
    Write-Host " - Ensure Python is installed and available in PATH."
    Write-Host " - Run: python <script>"
    Write-Host " - Or: py <script>"
}
