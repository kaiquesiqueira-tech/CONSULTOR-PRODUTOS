# Liga, desliga e consulta o vigia que publica sozinho.
# Chamado pelo automatico.bat

param([string]$Acao = "estado")

$raiz  = Split-Path -Parent $PSScriptRoot
$script = Join-Path $raiz 'vigia.py'
$tarefa = 'Consulta de Estoque - publicar'

function Achar-Pythonw {
  foreach ($nome in @('pythonw.exe','pyw.exe')) {
    $c = Get-Command $nome -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
  }
  return $null
}

function Processos-Do-Vigia {
  Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*vigia.py*' }
}

switch ($Acao) {

  "iniciar" {
    if (Processos-Do-Vigia) { Write-Host "  O vigia ja esta rodando."; break }
    $pyw = Achar-Pythonw
    if (-not $pyw) { Write-Host "  Nao achei o Python (pythonw.exe). Instale o Python."; break }
    Start-Process -FilePath $pyw -ArgumentList "`"$script`"" -WorkingDirectory $raiz -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if (Processos-Do-Vigia) { Write-Host "  Vigia iniciado em segundo plano." }
    else { Write-Host "  Nao consegui iniciar. Rode 'python vigia.py' para ver o erro." }
  }

  "parar" {
    $ps = Processos-Do-Vigia
    if (-not $ps) { Write-Host "  O vigia nao estava rodando."; break }
    foreach ($p in $ps) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "  Vigia parado."
  }

  "instalar" {
    $pyw = Achar-Pythonw
    if (-not $pyw) { Write-Host "  Nao achei o Python (pythonw.exe). Instale o Python."; break }
    $acaoTarefa = New-ScheduledTaskAction -Execute $pyw -Argument "`"$script`"" -WorkingDirectory $raiz
    $gatilho    = New-ScheduledTaskTrigger -AtLogOn
    $opcoes     = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
                    -DontStopIfGoingOnBatteries -StartWhenAvailable `
                    -ExecutionTimeLimit ([TimeSpan]::Zero)
    try {
      Register-ScheduledTask -TaskName $tarefa -Action $acaoTarefa -Trigger $gatilho `
        -Settings $opcoes -Description 'Gera e publica a consulta de estoque sozinho' -Force | Out-Null
      Write-Host "  Instalado. A partir do proximo login do Windows ele sobe sozinho."
    } catch {
      Write-Host "  Nao consegui instalar: $($_.Exception.Message)"
    }
  }

  "remover" {
    try {
      Unregister-ScheduledTask -TaskName $tarefa -Confirm:$false -ErrorAction Stop
      Write-Host "  Removido do inicio do Windows."
    } catch {
      Write-Host "  Nao estava instalado no inicio do Windows."
    }
  }

  default {
    if (Processos-Do-Vigia) { Write-Host "  Vigia: RODANDO agora" }
    else { Write-Host "  Vigia: parado" }
    $t = Get-ScheduledTask -TaskName $tarefa -ErrorAction SilentlyContinue
    if ($t) { Write-Host "  Inicio com o Windows: instalado" }
    else { Write-Host "  Inicio com o Windows: nao instalado" }
  }
}
