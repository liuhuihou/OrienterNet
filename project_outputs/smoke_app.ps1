$ErrorActionPreference = "Continue"

$root = "E:\code_file\robot_final_project\OrienterNet"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$stdout = Join-Path $root "project_outputs\smoke_stdout_$stamp.log"
$stderr = Join-Path $root "project_outputs\smoke_stderr_$stamp.log"

$process = Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "$root\project_outputs\run_app.ps1"
    ) `
    -WorkingDirectory $root `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden `
    -PassThru

Write-Output "started_pid=$($process.Id)"
Write-Output "stdout=$stdout"
Write-Output "stderr=$stderr"

$ok = $false
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    try {
        $response = Invoke-WebRequest `
            -Uri "http://127.0.0.1:7860" `
            -UseBasicParsing `
            -TimeoutSec 10
        Write-Output "http_status=$($response.StatusCode)"
        Write-Output "content_length=$($response.Content.Length)"
        $ok = $true
        break
    }
    catch {
        Write-Output "waiting $($i + 1): $($_.Exception.Message)"
    }
}

Write-Output "--- stdout tail ---"
Get-Content $stdout -Tail 80 -ErrorAction SilentlyContinue
Write-Output "--- stderr tail ---"
Get-Content $stderr -Tail 160 -ErrorAction SilentlyContinue

if (-not $ok) {
    exit 1
}
