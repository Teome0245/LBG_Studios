#Requires -RunAsAdministrator
# Expose WSL OpenSSH (2222) sur le LAN 192.168.0.10 + autorise la clé VM 140 (OpenSSH Windows admin).
param(
    [string]$LanHost = $(if ($env:LBG_LAN_HOST_DESKTOP) { $env:LBG_LAN_HOST_DESKTOP } else { "192.168.0.10" }),
    [int]$ListenPort = $(if ($env:LBG_INFOGRAPHISTE_WSL_SSH_PORT) { [int]$env:LBG_INFOGRAPHISTE_WSL_SSH_PORT } else { 2222 }),
    [int]$WslPort = $(if ($env:LBG_INFOGRAPHISTE_WSL_SSH_PORT) { [int]$env:LBG_INFOGRAPHISTE_WSL_SSH_PORT } else { 2222 }),
    [string]$Vm140PubKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMCdFbGmk9456QK9CHqrtYwbE3seiCmumT0vwpeACVA8 lbg@vm140-lbg-ia-mmorpg"
)

$ErrorActionPreference = "Stop"
$wslIp = (wsl.exe -e hostname -I).Trim().Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)[0]
if (-not $wslIp) { throw "IP WSL introuvable" }

Write-Host "WSL IP: $wslIp"
Write-Host "Portproxy ${LanHost}:${ListenPort} -> ${wslIp}:${WslPort}"

netsh interface portproxy delete v4tov4 listenaddress=$LanHost listenport=$ListenPort 2>$null | Out-Null
netsh interface portproxy add v4tov4 listenaddress=$LanHost listenport=$ListenPort connectaddress=$wslIp connectport=$WslPort | Out-Null

$ruleName = "WSL SSH LoRA Train $ListenPort"
netsh advfirewall firewall delete rule name=$ruleName 2>$null | Out-Null
netsh advfirewall firewall add rule name=$ruleName dir=in action=allow protocol=TCP localport=$ListenPort | Out-Null

$adminKeys = "$env:ProgramData\ssh\administrators_authorized_keys"
if (-not (Test-Path $adminKeys)) {
    New-Item -Path $adminKeys -ItemType File -Force | Out-Null
}
$content = Get-Content $adminKeys -Raw -ErrorAction SilentlyContinue
if ($content -notmatch [regex]::Escape("lbg@vm140-lbg-ia-mmorpg")) {
    Add-Content -Path $adminKeys -Value $Vm140PubKey
    Write-Host "Cle VM 140 ajoutee: $adminKeys"
} else {
    Write-Host "Cle VM 140 deja presente"
}
icacls $adminKeys /inheritance:r | Out-Null
icacls $adminKeys /grant "Administrators:F" | Out-Null
icacls $adminKeys /grant "SYSTEM:F" | Out-Null

Restart-Service sshd -ErrorAction SilentlyContinue
netsh interface portproxy show all
Write-Host "OK - test depuis 140 (user lbg): ssh -p $ListenPort sdesh@${LanHost} hostname"
