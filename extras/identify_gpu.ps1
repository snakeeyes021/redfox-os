# RedFoxOS graphics check (Windows PowerShell).
#
#   irm https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/extras/identify_gpu.ps1 | iex
#
# Lists this computer's graphics and says which RedFoxOS download to get,
# by the name on its card on the download page. It reads only each display
# adapter's PCI vendor and device id, downloads RedFoxOS's graphics rules
# (files/system/usr/share/redfox/gpu-rules.json, the same rules the download
# page and RedFox Hub's image picker use) and decides here: nothing about
# this computer is sent anywhere. identify_gpu.sh does the same on Linux,
# with the same output.
#
# For tests: $env:RFX_DEVICES = "8086:46a6 10de:1c03" stands in for the
# computer's adapters, and $env:RFX_RULES_FILE = path reads the rules from a file.

$page = 'https://redfoxlabs.tech/download/'
$rulesUrls = @(
    'https://raw.githubusercontent.com/snakeeyes021/redfox-os/main/files/system/usr/share/redfox/gpu-rules.json',
    'https://raw.githubusercontent.com/snakeeyes021/redfox-os/unstable/files/system/usr/share/redfox/gpu-rules.json'
)

# Prints text in lines of up to 76 characters, indented by two spaces, the
# same way identify_gpu.sh wraps it.
function Write-Wrapped([string]$text) {
    $line = ''
    foreach ($word in ($text -split '\s+' | Where-Object { $_ })) {
        if ($line -eq '') {
            $line = $word
        } elseif ($line.Length + 1 + $word.Length -le 76) {
            $line = $line + ' ' + $word
        } else {
            Write-Output ('  ' + $line)
            $line = $word
        }
    }
    if ($line -ne '') { Write-Output ('  ' + $line) }
}

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

Write-Output 'RedFoxOS graphics check'
Write-Output ''
if ($ids.Count -eq 0) {
    Write-Output 'No graphics found.'
} else {
    Write-Output 'Graphics found:'
    foreach ($id in $ids) {
        if ($names[$id]) { Write-Output ('  {0} ({1})' -f $names[$id], $id) } else { Write-Output ('  ' + $id) }
    }
}
Write-Output ''

$rules = $null
if ($env:RFX_RULES_FILE) {
    try { $rules = Get-Content -Raw -Path $env:RFX_RULES_FILE -ErrorAction Stop | ConvertFrom-Json } catch { $rules = $null }
} else {
    foreach ($url in $rulesUrls) {
        try { $rules = Invoke-RestMethod -Uri $url -TimeoutSec 15 -ErrorAction Stop; break } catch { $rules = $null }
    }
}

if ($null -eq $rules) {
    Write-Output 'Couldn''t download RedFoxOS''s graphics rules (is this computer online?),'
    Write-Output 'so it can''t say which download to get. Choose by your graphics at'
    Write-Output ('  ' + $page)
    Write-Output ''
    Write-Output 'Nothing about this computer has been sent anywhere.'
    return
}

# The decision, the same way the download page and Hub make it: each adapter
# gets the first class it matches, then the first rule whose classes all fit wins.
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

# The name and label on the download's card on the page
$downloads = @{
    'redfox-os' = 'RedFoxOS (AMD & Intel graphics)'
    'redfox-os-nvidia' = 'RedFoxOS NVIDIA (NVIDIA GTX 16xx, RTX 20xx and newer)'
    'redfox-os-nvidia-legacy' = 'RedFoxOS NVIDIA Legacy (NVIDIA GTX 10xx, 9xx and 750)'
}
$download = if ($rule.image) { $downloads[$rule.image] } else { $null }
if ($download) {
    Write-Output 'The download to get:'
    Write-Output ('  ' + $download)
    Write-Output ''
    Write-Output 'Why:'
    Write-Wrapped ('This computer has ' + $rule.why + '.')
} else {
    Write-Output 'No single download works best on your machine:'
    Write-Wrapped ('It has ' + $rule.why + '. Choose the download for the graphics you want to use.')
}
if ($rule.hybrid) {
    Write-Output ''
    Write-Output 'Two graphics chips:'
    Write-Wrapped ('This computer has built-in graphics next to its NVIDIA card, like most laptops with NVIDIA. The NVIDIA download drives the card with NVIDIA''s driver, and the built-in graphics keep working. If the screen stays black when the USB stick starts, choose "Start RedFoxOS (basic graphics)" in its menu.')
}
Write-Output ''
if ($download) { Write-Output 'Get it at:' } else { Write-Output 'The downloads are at:' }
Write-Output ('  ' + $page)
Write-Output ''
Write-Output 'Nothing about this computer has been sent anywhere.'
