# Cria o atalho na area de trabalho e/ou copia o app solto para la.
# Chamado pelo area-de-trabalho.bat

param([string]$Modo = "atalho")

$raiz = Split-Path -Parent $PSScriptRoot
$mesa = [Environment]::GetFolderPath('Desktop')

if (-not (Test-Path $mesa)) {
  Write-Host "Nao encontrei a area de trabalho neste usuario."
  exit 1
}

if ($Modo -eq "atalho" -or $Modo -eq "ambos") {
  $alvo = Join-Path $raiz 'iniciar.bat'
  if (-not (Test-Path $alvo)) {
    Write-Host "Nao achei o iniciar.bat. Rode este arquivo de dentro da pasta do projeto."
    exit 1
  }
  $w = New-Object -ComObject WScript.Shell
  $lnk = $w.CreateShortcut((Join-Path $mesa 'Consulta de Estoque.lnk'))
  $lnk.TargetPath       = $alvo
  $lnk.WorkingDirectory = $raiz
  $lnk.Description      = 'Abre a consulta de estoque no navegador'
  $ico = Join-Path $raiz 'app\icone.ico'
  if (Test-Path $ico) { $lnk.IconLocation = $ico }
  $lnk.Save()
  Write-Host "  Atalho criado: $mesa\Consulta de Estoque.lnk"
}

if ($Modo -eq "copia" -or $Modo -eq "ambos") {
  $origem = $null
  foreach ($lugar in @('index.html','docs\index.html','dist\index.html')) {
    $tentativa = Join-Path $raiz $lugar
    if (Test-Path $tentativa) { $origem = $tentativa; break }
  }
  if (-not $origem) {
    Write-Host "  O app ainda nao foi gerado. Rode o build antes."
    exit 1
  }
  $destino = Join-Path $mesa 'Consulta de Estoque.html'
  Copy-Item $origem $destino -Force
  $mb = [math]::Round((Get-Item $destino).Length / 1MB, 1)
  Write-Host "  Copia solta criada: $destino  ($mb MB)"
}
