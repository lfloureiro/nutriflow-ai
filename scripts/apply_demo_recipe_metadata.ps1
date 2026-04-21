param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Format-Text {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    return $Value.Trim()
}

$recipeMetadataMap = @{
    "Esparguete à bolonhesa" = @{
        categoria_alimentar = "carne"
        proteina_principal = "vaca"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Strogonoff de frango" = @{
        categoria_alimentar = "carne"
        proteina_principal = "frango"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Massa com atum e tomate" = @{
        categoria_alimentar = "peixe"
        proteina_principal = "peixe"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Salmão no forno com legumes" = @{
        categoria_alimentar = "peixe"
        proteina_principal = "peixe"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Bacalhau com natas" = @{
        categoria_alimentar = "peixe"
        proteina_principal = "peixe"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Frango assado com batatas" = @{
        categoria_alimentar = "carne"
        proteina_principal = "frango"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Caril suave de frango" = @{
        categoria_alimentar = "carne"
        proteina_principal = "frango"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Arroz de frango no forno" = @{
        categoria_alimentar = "carne"
        proteina_principal = "frango"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Salada de grão com atum" = @{
        categoria_alimentar = "peixe"
        proteina_principal = "peixe"
        adequado_refeicao = "almoco"
        auto_plan_enabled = $true
    }
    "Fajitas de frango" = @{
        categoria_alimentar = "carne"
        proteina_principal = "frango"
        adequado_refeicao = "jantar"
        auto_plan_enabled = $true
    }
    "Lasanha de carne" = @{
        categoria_alimentar = "carne"
        proteina_principal = "vaca"
        adequado_refeicao = "jantar"
        auto_plan_enabled = $true
    }
    "Almôndegas com molho de tomate" = @{
        categoria_alimentar = "carne"
        proteina_principal = "vaca"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Shakshuka" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "ovos"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Arroz de legumes com ovo" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "ovos"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Quiche de espinafres e cogumelos" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "ovos"
        adequado_refeicao = "jantar"
        auto_plan_enabled = $true
    }
    "Chili con carne" = @{
    categoria_alimentar = "carne"
    proteina_principal = "vaca"
    adequado_refeicao = "ambos"
    auto_plan_enabled = $true
    }
    "Chili vegetariano" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "leguminosas"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Jardineira de vitela" = @{
        categoria_alimentar = "carne"
        proteina_principal = "vaca"
        adequado_refeicao = "ambos"
        auto_plan_enabled = $true
    }
    "Sopa de lentilhas e legumes" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "leguminosas"
        adequado_refeicao = "jantar"
        auto_plan_enabled = $true
    }
    "Tarte de legumes e feta" = @{
        categoria_alimentar = "vegetariano_leguminosas"
        proteina_principal = "queijo_lacticinios"
        adequado_refeicao = "jantar"
        auto_plan_enabled = $true
    }
}

Write-Host ""
Write-Host "==> A obter receitas de $BaseUrl/recipes/" -ForegroundColor Cyan
$recipes = Invoke-RestMethod -Method Get -Uri "$BaseUrl/recipes/"

$updatedCount = 0
$skippedCount = 0
$unmapped = @()

foreach ($recipe in $recipes) {
    $recipeName = Format-Text $recipe.name

    if (-not $recipeMetadataMap.ContainsKey($recipeName)) {
        $skippedCount++
        $unmapped += $recipeName
        continue
    }

    $payload = $recipeMetadataMap[$recipeName] | ConvertTo-Json -Depth 5

    if ($DryRun) {
        Write-Host "[DRY RUN] Atualizaria: $recipeName" -ForegroundColor Yellow
        Write-Host "          $payload"
        $updatedCount++
        continue
    }

    Invoke-RestMethod `
        -Method Patch `
        -Uri "$BaseUrl/recipes/$($recipe.id)" `
        -ContentType "application/json" `
        -Body $payload | Out-Null

    Write-Host "Atualizada: $recipeName" -ForegroundColor Green
    $updatedCount++
}

Write-Host ""
Write-Host "==> Resumo" -ForegroundColor Cyan
Write-Host "Atualizadas: $updatedCount"
Write-Host "Sem mapeamento: $skippedCount"

if ($unmapped.Count -gt 0) {
    Write-Host ""
    Write-Host "==> Receitas sem mapeamento" -ForegroundColor Yellow
    $unmapped | Sort-Object -Unique | ForEach-Object { Write-Host " - $_" }
}