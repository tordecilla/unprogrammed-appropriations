$ErrorActionPreference = 'Stop'
$repo = 'tordecilla/unprogrammed-appropriations'
$groups = @('documents', 'advice-pages', 'agency-expenditure-pages', 'debt-pages', 'listing-pages', 'process-pages', 'project-pages', 'revenue-pages', 'road-fund-pages', 'status-pages')
$annexes = (Get-Content 'site/data/annexes.json' -Raw | ConvertFrom-Json).records
$sets = @(@{ tag = 'pdfs-annex-v1'; names = @($annexes | ForEach-Object { $_.file }) })
foreach ($group in $groups) {
  $sets += @{ tag = "pdfs-$group-v1"; names = @(Get-ChildItem -LiteralPath (Join-Path 'site' $group) -Filter '*.pdf' -File | ForEach-Object { $_.Name }) }
}
$total = 0
foreach ($set in $sets) {
  $assets = @(gh release view $set.tag --repo $repo --json assets --jq '.assets[].name')
  if ($LASTEXITCODE -ne 0) { throw "Cannot read release $($set.tag)" }
  $missing = @($set.names | Where-Object { $_ -notin $assets })
  $extra = @($assets | Where-Object { $_ -notin $set.names })
  if ($missing.Count -or $extra.Count) { throw "$($set.tag): $($missing.Count) missing, $($extra.Count) unexpected" }
  $total += $assets.Count
  Write-Host "$($set.tag): $($assets.Count) of $($set.names.Count) verified"
}
Write-Host "Verified $total individual PDFs across $($sets.Count) releases."
