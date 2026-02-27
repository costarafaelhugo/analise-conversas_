# Script para criar novo repositório no GitHub
$usuario = "costarafaelhugo"
$nomeRepo = "analista-conversas-qa"
$descricao = "Aplicacao web para analise automatizada de qualidade de atendimento de chatbots"

Write-Host "Criando novo repositorio no GitHub" -ForegroundColor Cyan
Write-Host ""
Write-Host "Usuario: $usuario" -ForegroundColor Yellow
Write-Host "Nome do repositorio: $nomeRepo" -ForegroundColor Yellow
Write-Host ""

Write-Host "Instrucoes:" -ForegroundColor Green
Write-Host "1. Acesse: https://github.com/new" -ForegroundColor White
Write-Host "2. Nome do repositorio: $nomeRepo" -ForegroundColor White
Write-Host "3. Descricao: $descricao" -ForegroundColor White
Write-Host "4. Escolha Publico ou Privado" -ForegroundColor White
Write-Host "5. NAO marque nenhuma opcao adicional (README, .gitignore, license)" -ForegroundColor Red
Write-Host "6. Clique em Create repository" -ForegroundColor White
Write-Host ""

Start-Process "https://github.com/new"

$continuar = Read-Host "Apos criar o repositorio, pressione Enter para continuar"

Write-Host ""
Write-Host "Configurando repositorio local..." -ForegroundColor Cyan

# Remover remote anterior se existir
git remote remove novo-origin 2>$null

# Adicionar novo remote
Write-Host "Adicionando novo remote..." -ForegroundColor Yellow
git remote add novo-origin "https://github.com/$usuario/$nomeRepo.git"

# Verificar
git remote -v

Write-Host ""
Write-Host "Configuracao concluida!" -ForegroundColor Green
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "Execute: .\fazer_push_novo_repo.ps1" -ForegroundColor White
