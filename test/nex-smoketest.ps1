# Ensure prefix is passed in
if ($args.Length -lt 1) {
    Write-Host "NEX smoketest needs a prefix"
    Write-Host "nex-smoketest.ps1 acceptance"
    exit
}

$prefix = $args[0]

# Check if doing a local smoke test
if ($prefix -ne "local") {
    Write-Host "Remote Smoke Test in CF"
    $stdAppUrl = $prefix
} else {
    Write-Host "Local Smoke Test"
    $stdAppUrl = "http://localhost:8000"
}

Write-Host "STD_APP_URL=$stdAppUrl"

# Test: test connections
Write-Host "=== Test connections ==="
try {
    Invoke-RestMethod -Uri "$stdAppUrl/test" -Method Get
    Write-Host "Basic infrastructure working"
} catch {
    Write-Error "!!! FAILED TO CONNECT TO REQUIRED BASIC INFRASTRUCTURE !!!"
    exit 1
}

# Test: Create Products
Write-Host "=== Creating a product id: the_odyssey ==="
Invoke-RestMethod -Uri "$stdAppUrl/products" -Method Post -Headers @{"accept"="application/json"; "Content-Type"="application/json"} -Body '{
    "id": "the_odyssey",
    "title": "The Odyssey",
    "passenger_capacity": 101,
    "maximum_speed": 5,
    "in_stock": 10
}'
Write-Host

# Test: Get Product
Write-Host "=== Getting product id: the_odyssey ==="
Invoke-RestMethod -Uri "$stdAppUrl/products/the_odyssey" | ConvertTo-Json
Write-Host

# Test: Create Order
Write-Host "=== Creating Order ==="
$orderDetails = @(
    @{
        "product_id" = "the_odyssey"
        "price" = "100000.99"
        "quantity" = 1
    }
)
$orderBody = @{
    "order_details" = $orderDetails
} | ConvertTo-Json

$orderResponse = Invoke-RestMethod -Uri "$stdAppUrl/orders" -Method Post -Headers @{"accept"="application/json"; "Content-Type"="application/json"} -Body $orderBody
$orderResponseId = $orderResponse.id
Write-Host $orderResponseId

# Test: Get Order back
Write-Host "=== Getting Order ==="
Invoke-RestMethod -Uri "$stdAppUrl/orders/$orderResponseId" | ConvertTo-Json

# Test: List Orders
Write-Host "=== Listing Orders ==="
Invoke-RestMethod -Uri "$stdAppUrl/orders" -Method Get | ConvertTo-Json

# Test: Delete Product
Write-Host "=== Deleting Product ==="
Invoke-RestMethod -Uri "$stdAppUrl/products/the_odyssey" -Method Delete