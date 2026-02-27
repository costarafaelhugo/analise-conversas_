# Script para ativar GitHub Pages via API
$owner = "OmniChat"
$repo = "analise-conversas-after-sales"
$apiUrl = "https://api.github.com/repos/$owner/$repo/pages"

# Solicitar token do usuário
Write-Host "Para ativar o GitHub Pages via API, preciso de um Personal Access Token do GitHub." -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Crie um token em: https://github.com/settings/tokens" -ForegroundColor Cyan
Write-Host "2. Dê as permissões: 'repo' e 'admin:repo_hook'" -ForegroundColor Cyan
Write-Host "3. Cole o token abaixo:" -ForegroundColor Cyan
Write-Host ""

$token = Read-Host "Token do GitHub (ou pressione Enter para pular)"

if ([string]::IsNullOrWhiteSpace($token)) {
    Write-Host ""
    Write-Host "Token não fornecido. Ativando manualmente..." -ForegroundColor Yellow
    Write-Host "Acesse: https://github.com/$owner/$repo/settings/pages" -ForegroundColor Cyan
    Start-Process "https://github.com/$owner/$repo/settings/pages"
    exit
}

$headers = @{
    "Accept" = "application/vnd.github+json"
    "Authorization" = "Bearer $token"
    "X-GitHub-Api-Version" = "2022-11-28"
}

$body = @{
    source = @{
        branch = "main"
        path = "/"
    }
} | ConvertTo-Json

try {
    # Verificar status atual
    Write-Host "Verificando status atual do GitHub Pages..." -ForegroundColor Cyan
    $response = Invoke-RestMethod -Uri $apiUrl -Method Get -Headers $headers -ErrorAction Stop
    
    Write-Host "✅ GitHub Pages já está ativado!" -ForegroundColor Green
    Write-Host "Status: $($response.status)" -ForegroundColor White
    Write-Host "URL: $($response.html_url)" -ForegroundColor White
    exit
}
catch {
    if ($_.Exception.Response.StatusCode -eq 404) {
        Write-Host "GitHub Pages não está ativado. Ativando agora..." -ForegroundColor Yellow
        
        try {
            $response = Invoke-RestMethod -Uri $apiUrl -Method Put -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
            
            Write-Host "✅ GitHub Pages ativado com sucesso!" -ForegroundColor Green
            Write-Host "URL do site: https://$owner.github.io/$repo/" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Aguarde alguns minutos para o site ser publicado..." -ForegroundColor Yellow
        }
        catch {
            Write-Host "❌ Erro ao ativar GitHub Pages:" -ForegroundColor Red
            Write-Host $_.Exception.Message -ForegroundColor Red
            Write-Host ""
            Write-Host "Tente ativar manualmente em:" -ForegroundColor Yellow
            Write-Host "https://github.com/$owner/$repo/settings/pages" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "❌ Erro ao verificar status:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
}




