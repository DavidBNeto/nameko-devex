function Get-File-Path($file) {
    try {
        $relativePath = $PSScriptRoot
        $filePath = Join-Path -Path $relativePath -ChildPath $file
        $filePath
    } catch {
        return null
    }
}


# Check if at least 1 argument is passed
if ($args.Count -eq 0) {
    Write-Host "run.ps1 needs a service module package to run"
    Write-Host "e.g., run.ps1 gateway.service orders.service products.service"
    exit 1
}

# Set up the environment if not already available
$env:PYTHONPATH = ".\gateway;.\orders;.\products;.\gateapi"

# Check if required environment variables are set, exit on errors
$requiredEnvs = @("AMQP_URI", "POSTGRES_URI", "REDIS_URI")
$toExit = $false

foreach ($envName in $requiredEnvs) {
    if (-not [Environment]::GetEnvironmentVariable($envName, [System.EnvironmentVariableTarget]::Process) -or [Environment]::GetEnvironmentVariable($envName, [System.EnvironmentVariableTarget]::Process) -eq "null") {
        Write-Host "Required environment NOT initialized: $envName"
        $toExit = $true
    }
}

if ($toExit) {
    Write-Host "Above required environment(s) is not set properly. Crashing application deliberately"
    exit 1
}

# Run Migrations for Postgres DB for Orders' backing service
Push-Location (Get-File-Path "\orders")
$env:PYTHONPATH = "."
alembic revision --autogenerate -m "init"
alembic upgrade head
Pop-Location

function Cleanup {
    if ($null -ne $fastPid) {
        Stop-Process -Id $fastPid -Force
    }
}

Push-Location (Get-File-Path "")
if ($env:FASTAPI) {
    Write-Host "FastAPI gateway is enabled..."
    Start-Process -FilePath "python" -ArgumentList "gateapi\gateapi\main.py" -NoNewWindow
    $fastPid = $LastExitCode
    Register-ObjectEvent -InputObject ($fastPid) -EventName "Exited" -Action { Cleanup }
}

if ($env:DEBUG) {
    Write-Host "Nameko service in debug mode. Please connect to port 5678 to start service."
    $env:GEVENT_SUPPORT = "True"
    python -m debugpy --listen 5678 --wait-for-client run_nameko.py run --config config.yml $args
} else {
    python run_nameko.py run --config config.yml $args
}
