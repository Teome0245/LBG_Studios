# Watch-AvatarBridge.ps1 - smoke SSE avatar (poste .10)
# ASCII-only for Windows PowerShell 5.1 via SMB.
# Usage: powershell -ExecutionPolicy Bypass -File .\adapters\Watch-AvatarBridge.ps1

param(
  [string]$BaseUrl = "http://127.0.0.1:8765",
  [int]$RetrySec = 3
)

$ErrorActionPreference = "Stop"
$stateUrl = "$BaseUrl/avatar/state"
$streamUrl = "$BaseUrl/avatar/stream"

Write-Host "Avatar bridge smoke -> $BaseUrl"
try {
  $st = Invoke-RestMethod -Uri $stateUrl -TimeoutSec 3
  Write-Host ("STATE ok={0} event={1} mood={2}" -f $st.ok, $st.state.event, $st.state.mood)
} catch {
  Write-Host "FAIL: bridge injoignable. Activer avatarBridge.enabled puis relancer Compagnon Desktop."
  Write-Host $_.Exception.Message
  exit 1
}

Write-Host "Listening SSE (Ctrl+C pour quitter)..."
while ($true) {
  $reader = $null
  $resp = $null
  try {
    $req = [System.Net.HttpWebRequest]::Create($streamUrl)
    $req.Method = "GET"
    $req.Accept = "text/event-stream"
    $req.Timeout = [int]::MaxValue
    $req.ReadWriteTimeout = [int]::MaxValue
    $resp = $req.GetResponse()
    $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
    while ($null -ne ($line = $reader.ReadLine())) {
      if ($line -like "data: *") {
        $json = $line.Substring(6)
        try {
          $ev = $json | ConvertFrom-Json
          Write-Host ("[{0}] {1} mood={2} talking={3} text={4}" -f `
            $ev.ts, $ev.event, $ev.mood, $ev.talking, $ev.text)
        } catch {
          Write-Host $json
        }
      }
    }
  } catch {
    Write-Host ("SSE disconnected: {0}" -f $_.Exception.Message)
  } finally {
    if ($reader) { try { $reader.Close() } catch {} }
    if ($resp) { try { $resp.Close() } catch {} }
  }
  Write-Host ("Reconnect in {0}s..." -f $RetrySec)
  Start-Sleep -Seconds $RetrySec
}
