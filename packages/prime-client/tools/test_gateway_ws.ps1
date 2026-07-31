# Test rapide depuis Windows : TCP 50000 + HTTP M11 (gateway 246)
param(
    [string]$HttpBase = "http://192.168.0.246:8765",
    [string]$WsHost = "192.168.0.246",
    [int]$WsPort = 50000,
    [string]$User = "Teome",
    [string]$Pass = "dev"
)

$ErrorActionPreference = "Stop"
$tcpLabel = "{0}:{1}" -f $WsHost, $WsPort
Write-Host ("=== TCP {0} ===" -f $tcpLabel)

$t = Test-NetConnection -ComputerName $WsHost -Port $WsPort -WarningAction SilentlyContinue
if (-not $t.TcpTestSucceeded) {
    Write-Host "ECHEC TCP - ouvrir le port $WsPort vers $WsHost (pare-feu) ou verifier la gateway."
    exit 1
}
Write-Host "TCP OK"

Write-Host ("=== HTTP login {0} ===" -f $HttpBase)
$body = @{ type = "login"; username = $User; password = $Pass } | ConvertTo-Json -Compress
$login = Invoke-RestMethod -Method Post -Uri ($HttpBase + "/v1/auth/login") -ContentType "application/json" -Body $body
$token = $login.session_token
$charId = $login.characters[0].id
Write-Host ("token ok char={0}" -f $charId)

$headers = @{ Authorization = ("Bearer " + $token) }
$selBody = (@{ character_id = $charId } | ConvertTo-Json -Compress)
Invoke-RestMethod -Method Post -Uri ($HttpBase + "/v1/auth/select_character") -ContentType "application/json" -Headers $headers -Body $selBody | Out-Null
Invoke-RestMethod -Method Post -Uri ($HttpBase + "/v1/auth/enter_zone") -ContentType "application/json" -Headers $headers -Body '{"zone":"tatooine"}' | Out-Null
Write-Host "HTTP enter_zone OK"
Write-Host "Si Godot reste sur WS..., verifier la console Godot ([LbgWs] state=...) ou relancer F5 apres sync scripts."
