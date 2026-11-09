# RedFoxOS graphics check (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.ps1 | iex
#
# Lists this computer's display adapters and says which RedFoxOS download
# works best on it, with a link to it. It reads only each adapter's PCI vendor and
# device id. It downloads RedFoxOS's graphics rules
# (files/system/usr/share/redfox/gpu-rules.json, the same rules the download
# page and RedFox Hub's image picker use) and decides here; nothing about
# this computer is sent anywhere. The link carries the ids after a "#", which
# browsers keep to themselves, so opening it doesn't send them either.
# If the rules can't be downloaded, it prints a code to paste into the
# download page instead. The Linux version is identify_gpu.sh.
#
# For tests: $env:RFX_DEVICES = "8086:46a6 10de:1c03" stands in for the
# computer's adapters, and $env:RFX_RULES_FILE = path reads the rules from a file.

$page = 'https://redfoxlabs.tech/download/'
$rulesUrls = @(
    'https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/files/system/usr/share/redfox/gpu-rules.json',
    'https://raw.githubusercontent.com/snakeeyes021/redfox-os/unstable/files/system/usr/share/redfox/gpu-rules.json'
)

$ids = @()
$names = @{}
if ($null -ne $env:RFX_DEVICES) {
    $ids = @($env:RFX_DEVICES -split '\s+' | Where-Object { $_ })
} else {
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
}

if ($ids.Count -eq 0) {
    Write-Host 'No graphics device found.'
} else {
    Write-Host 'Graphics found:'
    foreach ($id in $ids) { Write-Host (('  {0}  {1}' -f $id, $names[$id]).TrimEnd()) }
}
Write-Host ''

$code = if ($ids.Count -gt 0) { 'RFX1 ' + ($ids -join ' ') } else { 'RFX1 none' }
$link = $page + '#gpu=' + ($code -replace ' ', '+')

$rules = $null
if ($env:RFX_RULES_FILE) {
    try { $rules = Get-Content -Raw -Path $env:RFX_RULES_FILE -ErrorAction Stop | ConvertFrom-Json } catch { $rules = $null }
} else {
    foreach ($url in $rulesUrls) {
        try { $rules = Invoke-RestMethod -Uri $url -TimeoutSec 15 -ErrorAction Stop; break } catch { $rules = $null }
    }
}

if ($null -eq $rules) {
    # No rules (offline?): the page can decide from the code.
    Write-Host 'Couldn''t decide here. Your code for the download page:'
    Write-Host ''
    Write-Host ('    ' + $code)
    Write-Host ''
    Write-Host ('Paste it at ' + $page + ' to see which RedFoxOS works best on your machine,')
    Write-Host 'or open this link, which shows the same:'
    Write-Host ('    ' + $link)
    try { Set-Clipboard -Value $code; Write-Host '(The code is on the clipboard too.)' } catch { }
    return
}

# The decision, the same way the download page makes it: each adapter gets the
# first class it matches, then the first rule whose classes all fit wins.
$have = @{}
foreach ($id in $ids) {
    $vendor, $device = $id.ToLower().Split(':')
    $class = 'other'
    foreach ($c in $rules.classes) {
        $fromOk = ($null -eq $c.device_from) -or ([Convert]::ToInt32($device, 16) -ge [Convert]::ToInt32($c.device_from, 16))
        if (($c.vendors -contains $vendor) -and $fromOk) { $class = $c.id; break }
    }
    $have[$class] = $true
}
$rule = $null
foreach ($r in $rules.rules) {
    $allOk = @($r.all | Where-Object { -not $have.ContainsKey($_) }).Count -eq 0
    $noneOk = @($r.none | Where-Object { $_ -and $have.ContainsKey($_) }).Count -eq 0
    if ($allOk -and $noneOk) { $rule = $r; break }
}

$titles = @{
    'redfox-os' = 'RedFoxOS (Intel & AMD)'
    'redfox-os-nvidia' = 'RedFoxOS NVIDIA'
    'redfox-os-nvidia-legacy' = 'RedFoxOS NVIDIA Legacy'
}
$title = if ($rule.image) { $titles[$rule.image] } else { $null }
if ($title) {
    Write-Host ('Works best on your machine: ' + $title)
    Write-Host ('  It has ' + $rule.why + '.')
} else {
    Write-Host ('No single download works best on your machine: it has ' + $rule.why + '.')
    Write-Host '  Pick the one for the graphics you want to use.'
}
if ($rule.hybrid) {
    Write-Host ''
    Write-Host 'Two graphics chips: this computer has built-in graphics next to its NVIDIA card,'
    Write-Host 'like most laptops with NVIDIA. The NVIDIA download drives the card with NVIDIA''s'
    Write-Host 'driver, and the built-in graphics keep working. If the screen stays black when the'
    Write-Host 'USB stick starts, choose "Start RedFoxOS (basic graphics)" in its menu.'
}
Write-Host ''
if ($title) {
    Write-Host 'Download it here (the page opens with it picked):'
} else {
    Write-Host 'The downloads (the page opens with this computer''s graphics checked):'
}
Write-Host ('    ' + $link)
Write-Host ''
Write-Host ('Nothing about this computer has been sent anywhere. Code, if you''d rather paste it: ' + $code)
try { Set-Clipboard -Value $link; Write-Host '(The link is on the clipboard.)' } catch { }
