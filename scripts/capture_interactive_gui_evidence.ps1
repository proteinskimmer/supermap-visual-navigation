param(
  [Parameter(Mandatory = $true)]
  [string]$Name,
  [string]$OutputDir = "E:\supermap_project\docs\delivery\screenshots",
  [int]$DelaySeconds = 5
)

$ErrorActionPreference = "Stop"

if ($Name -notmatch "\.png$") {
  $Name = "$Name.png"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$outputPath = Join-Path $OutputDir $Name

Write-Host "[INFO] Bring the target GUI window to the foreground."
Write-Host "[INFO] Capture starts in ${DelaySeconds}s and will save to: $outputPath"
for ($i = $DelaySeconds; $i -gt 0; $i--) {
  Write-Host "[CAPTURE] $i ..."
  Start-Sleep -Seconds 1
}

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$left = [int]$bounds.Left
$top = [int]$bounds.Top
$width = [int]$bounds.Width
$height = [int]$bounds.Height

Write-Host "[INFO] Virtual screen bounds: left=$left top=$top width=$width height=$height"
if ($width -le 0 -or $height -le 0) {
  throw "Invalid screen bounds: width=$width height=$height"
}

$bitmap = [System.Drawing.Bitmap]::new($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
try {
  $graphics.CopyFromScreen($left, $top, 0, 0, $bitmap.Size)
  $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
  $graphics.Dispose()
  $bitmap.Dispose()
}

$item = Get-Item -LiteralPath $outputPath
if ($item.Length -lt 20000) {
  Write-Warning "Screenshot file is small; it may be a blank or inaccessible desktop capture: $($item.Length) bytes"
}

Write-Host "[OK] saved => $($item.FullName)"
Write-Host "[OK] size  => $($item.Length) bytes"
