# Stop containers
docker rm -f devRabbit
docker rm -f devPostgres 
docker rm -f devRedis

# Display message
Write-Host "All services stopped and removed"
