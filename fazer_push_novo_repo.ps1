# Script para fazer push para o novo repositório
$usuario = "costarafaelhugo"
$nomeRepo = "analista-conversas-qa"

Write-Host "📤 Enviando código para o novo repositório..." -ForegroundColor Cyan
Write-Host ""

# Verificar se o remote existe
$remotes = git remote
if ($remotes -notcontains "novo-origin") {
    Write-Host "❌ Remote 'novo-origin' não encontrado!" -ForegroundColor Red
    Write-Host "Execute primeiro: .\criar_novo_repositorio.ps1" -ForegroundColor Yellow
    exit 1
}

# Verificar status
Write-Host "Verificando status do repositório..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "Fazendo push para: https://github.com/$usuario/$nomeRepo.git" -ForegroundColor Cyan
Write-Host ""

# Fazer push
try {
    git push -u novo-origin main
    Write-Host ""
    Write-Host "✅ Push concluído com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Repositório disponível em:" -ForegroundColor Cyan
    Write-Host "https://github.com/$usuario/$nomeRepo" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🚀 Próximo passo: Deploy no Streamlit Cloud" -ForegroundColor Green
    Write-Host "Repository: $usuario/$nomeRepo" -ForegroundColor White
    Write-Host "Branch: main" -ForegroundColor White
    Write-Host "Main file path: app.py" -ForegroundColor White
}
catch {
    Write-Host ""
    Write-Host "❌ Erro ao fazer push:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Verifique se:" -ForegroundColor Yellow
    Write-Host "1. O repositório foi criado no GitHub" -ForegroundColor White
    Write-Host "2. Você tem permissão para fazer push" -ForegroundColor White
    Write-Host "3. Você está autenticado no GitHub" -ForegroundColor White
}




