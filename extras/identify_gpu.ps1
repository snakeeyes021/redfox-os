# RedFoxOS graphics check (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.ps1 | iex
#
# Lists this computer's display adapters and prints a short code to paste into
# the download page (https://redfoxlabs.tech/download/), which shows the
# RedFoxOS image that suits them. The code is just each adapter's PCI vendor
# and device id, e.g. "RFX1 8086:46a6 10de:1c03"; nothing else is read and
# nothing is sent anywhere. The page decides with the same rules as RedFox
# Hub's "(Recommended)" (files/system/usr/share/redfox/gpu-rules.json).
# The Linux version is identify_gpu.sh.

$ids = @()
$names = @{}
# Every display adapter Windows knows, including one that's switched off
# (the NVIDIA card in a hybrid laptop can be).
$adapters = Get-CimInstance -ClassName Win32_PnPEntity -Filter "PNPClass = 'Display'" -ErrorAction SilentlyContinue
foreach ($adapter in $adapters) {
    if ($adapter.PNPDeviceID -match '^PCI\\VEN_([0-9A-Fa-f]{4})&DEV_([0-9A-Fa-f]{4})') {
        $id = ('{0}:{1}' -f $Matches[1], $Matches[2]).ToLower()
        if ($ids -notcontains $id) {
            $ids += $id
            $names[$id] = $adapter.Name
        }
    }
}

if ($ids.Count -eq 0) {
    Write-Host 'No graphics device found.'
} else {
    Write-Host 'Graphics found:'
    foreach ($id in $ids) { Write-Host ('  {0}  {1}' -f $id, $names[$id]) }
}
$code = if ($ids.Count -gt 0) { 'RFX1 ' + ($ids -join ' ') } else { 'RFX1 none' }
Write-Host ''
Write-Host 'Your code for the download page:'
Write-Host ''
Write-Host ('    ' + $code)
Write-Host ''
Write-Host 'Paste it at https://redfoxlabs.tech/download/ to see which RedFoxOS suits this computer.'
try { Set-Clipboard -Value $code; Write-Host '(It''s on the clipboard too.)' } catch { }
