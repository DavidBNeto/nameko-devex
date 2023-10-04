# Define a function to check if a port is open
function Test-Port ($TestHost, $Port){
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($TestHost, $Port)
        $tcpClient.Close()
        $true
    } catch {
        $false
    }
}

function Get-Run-File {
    try {
        $relativePath = $PSScriptRoot
        $filePath = Join-Path -Path $relativePath -ChildPath "run.ps1"
        $filePath
    } catch {
        return null
    }
}

# Check if RabbitMQ is up and running before starting the service
do {
    Write-Host "$(Get-Date) - waiting for RabbitMQ..."
    Start-Sleep -Seconds 2
} until (Test-Port 'localhost' 5672)

# Check if Redis is up and running before starting the service
do {
    Write-Host "$(Get-Date) - waiting for Redis..."
    Start-Sleep -Seconds 2
} until (Test-Port 'localhost' 6379)

# Check if PostgreSQL is up and running before starting the service
do {
    Write-Host "$(Get-Date) - waiting for PostgreSQL..."
    Start-Sleep -Seconds 2
} until (Test-Port 'localhost' 5432)

# Create the 'orders' database locally
python create_db.py

# Setting up local environment variables
$env:AMQP_URI = "amqp://guest:guest@localhost:5672"
$env:POSTGRES_URI = "postgresql://postgres:postgres@localhost:5432/orders"
$env:REDIS_URI = "redis://:password@127.0.0.1:6379/7"

# Start the service using run.ps1
$runFile = Get-Run-File
& $runFile $args
