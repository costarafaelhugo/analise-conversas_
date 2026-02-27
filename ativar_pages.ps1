# Script para abrir a página de configurações do GitHub Pages
$repo = "OmniChat/analise-conversas-after-sales"
$url = "https://github.com/$repo/settings/pages"

Write-Host "Abrindo página de configurações do GitHub Pages..." -ForegroundColor Cyan
Write-Host "URL: $url" -ForegroundColor Yellow
Write-Host ""
Write-Host "Instruções:" -ForegroundColor Green
Write-Host "1. Na seção 'Source', selecione 'Deploy from a branch'" -ForegroundColor White
Write-Host "2. Escolha a branch 'main'" -ForegroundColor White
Write-Host "3. Escolha a pasta '/ (root)'" -ForegroundColor White
Write-Host "4. Clique em 'Save'" -ForegroundColor White
Write-Host ""
Write-Host "Após salvar, aguarde alguns minutos e acesse:" -ForegroundColor Cyan
Write-Host "https://OmniChat.github.io/analise-conversas-after-sales/" -ForegroundColor Yellow

Start-Process $url




