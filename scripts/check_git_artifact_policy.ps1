$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

$status = git status --porcelain

$localOnlyPatterns = @(
  "^(\?\?| M|M |A |AM|MM) release/",
  "^(\?\?| M|M |A |AM|MM) frontend/public/vendor/supermap3d/",
  "^(\?\?| M|M |A |AM|MM) \.tmp/",
  "^(\?\?| M|M |A |AM|MM) tmp_iobjectspy_probe",
  "^(\?\?| M|M |A |AM|MM) .*\.log$",
  "^(\?\?| M|M |A |AM|MM) supermap_file_root/.*\.(smwu|udb|udd|udbx)$",
  "^(\?\?| M|M |A |AM|MM) docs/delivery/screenshots/QQ.*\.png$",
  "^(\?\?| M|M |A |AM|MM) docs/delivery/screenshots/compat_cbd/"
)

$unexpected = @()
foreach ($line in $status) {
  foreach ($pattern in $localOnlyPatterns) {
    if ($line -match $pattern) {
      $unexpected += $line
      break
    }
  }
}

if ($unexpected.Count -gt 0) {
  Write-Host "[FAIL] Local-only/generated artifacts are visible to Git:"
  $unexpected | ForEach-Object { Write-Host "  $_" }
  Write-Host ""
  Write-Host "Check .gitignore or move these artifacts before creating a stable commit point."
  exit 1
}

Write-Host "[PASS] Git artifact policy check passed. No local-only generated artifacts are visible in git status."
