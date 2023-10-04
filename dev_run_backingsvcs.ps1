docker rm -f devRabbit ; docker run -d --name devRabbit -p 5672:5672 -p 5673:5673 -p 15672:15672 rabbitmq:3-management
docker rm -f devPostgres ; docker run -d --name devPostgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
docker rm -f devRedis ; docker run -d --name devRedis -p 6379:6379 redis docker-entrypoint.sh --requirepass password

Write-Host "all services started"