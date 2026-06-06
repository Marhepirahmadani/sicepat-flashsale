Write-Host "Monitoring SiCepat Flash Sale Infrastructure" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

Write-Host "Pilih tampilan:" -ForegroundColor Yellow
Write-Host "1. Docker Stats (resource usage)"
Write-Host "2. Log Server Checkout"
Write-Host "3. Log Server Katalog"
Write-Host "4. Log Server Cart"
Write-Host "5. Log Nginx (load balancer)"

$choice = Read-Host "Masukkan pilihan (1-5)"

switch ($choice) {
    "1" { docker stats }
    "2" { docker-compose logs -f backend-checkout }
    "3" { docker-compose logs -f backend-katalog }
    "4" { docker-compose logs -f backend-cart }
    "5" { docker-compose logs -f nginx }
    default { Write-Host "Pilihan tidak valid" -ForegroundColor Red }
}