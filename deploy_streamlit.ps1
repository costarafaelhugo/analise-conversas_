# Script para abrir a página de deploy do Streamlit Cloud
$streamlitUrl = "https://share.streamlit.io/"

Write-Host "Abrindo Streamlit Cloud para deploy da aplicacao..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Instrucoes:" -ForegroundColor Green
Write-Host "1. Faca login com sua conta GitHub" -ForegroundColor White
Write-Host "2. Clique em New app" -ForegroundColor White
Write-Host "3. Repository: OmniChat/analise-conversas-after-sales" -ForegroundColor White
Write-Host "4. Branch: main" -ForegroundColor White
Write-Host "5. Main file path: app.py" -ForegroundColor White
Write-Host "6. Clique em Deploy" -ForegroundColor White
Write-Host ""

Start-Process $streamlitUrl
