# to ensure if 1 command fails.. build fail

# ensure prefix is passed in
if ($args.Length -lt 1) {
    Write-Host "nex-bzt.ps1 needs prefix"
    Write-Host "eg: nex-bzt.ps1 local|url"
    Write-Host "eg: nex-bzt.ps1 local numOfuser hold_time ramp_up"
    Write-Host "eg: nex-bzt.ps1 local 10 2h 3m"
    Write-Host "      means 10 users, run for 2 hours and use 3 min to ramp up"
    exit
}

$PREFIX = $args[0]

if ($PREFIX -ne "local") {
    Write-Host "Production Performance Test in CF"
    $STD_APP_URL = $PREFIX
}
else {
    Write-Host "Local Performance Test"
    $STD_APP_URL = "http://localhost:8000"
}

if ($args.Length -lt 2) {
    $NO_USERS = 3
}
else {
    $NO_USERS = [int]$args[1]
}

if ($args.Length -lt 3) {
    $HOLD = "3m"
}
else {
    $HOLD = $args[2]
}

if ($args.Length -lt 4) {
    $RAMP_UP = "1m"
}
else {
    $RAMP_UP = $args[3]
}

$DATA_SRC = "./nex-users.csv"

Write-Host "Starting with $NO_USERS user(s) in $RAMP_UP min, will run for $HOLD"
bzt -report -o scenarios.nex.default-address=$STD_APP_URL `
    -o scenarios.nex.variables.apigee_client_id=client_id `
    -o scenarios.nex.variables.apigee_client_secret=client_secret `
    -o scenarios.nex.data-sources.0=$DATA_SRC `
    -o execution.0.concurrency=$NO_USERS `
    -o execution.0.hold-for=$HOLD `
    -o execution.0.ramp-up=$RAMP_UP `
    -o modules.console.disable=$true `
    -o settings.artifacts-dir="./perf-test-results" `
    ./nex-bzt.yml
