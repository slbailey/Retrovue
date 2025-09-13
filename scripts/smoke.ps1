$ErrorActionPreference = 'Stop'
$python = $env:PYTHON; if (-not $python) { $python = 'python' }
$cli = 'cli.plex_sync'

function Assert-Help {
  param([string[]]$Args)
  $out = & $python -m $cli @Args 2>$null
  if (-not ($out | Select-String -Quiet '(Usage:|Options:|Subcommands:|Command Groups:)'))) {
  throw "Help indicators not found for: $($Args -join ' ')"
}
}

function Run-CLI {
  param([string[]]$Args, [switch]$ExpectFail, [string]$StdinJson)
  if ($StdinJson) {
    $StdinJson | & $python -m $cli @Args | Out-Null
    $code = $LASTEXITCODE
  }
  else {
    & $python -m $cli @Args | Out-Null
    $code = $LASTEXITCODE
  }
  if ($ExpectFail) { if ($code -eq 0) { throw "Expected non-zero exit code" } }
  else { if ($code -ne 0) { throw "Exit code $code" } }
}

# Examples (expand as needed)
Assert-Help @('--help')
Assert-Help @('servers', '--help')
Run-CLI @('servers', 'list')
# stdin example:
$json = '{"title":"Test Movie","type":"movie","duration":7200000,"contentRating":"PG-13","ratingKey":"12345"}' + "`n"
Run-CLI @('items', 'map', '--from-stdin') -StdinJson $json
Write-Host "✅ smoke.ps1 finished"

