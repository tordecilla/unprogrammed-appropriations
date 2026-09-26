$ErrorActionPreference = 'Stop'
$repo = 'tordecilla/unprogrammed-appropriations'
$groups = @(
  'documents', 'advice-pages', 'agency-expenditure-pages', 'debt-pages',
  'listing-pages', 'process-pages', 'project-pages', 'revenue-pages',
  'road-fund-pages', 'status-pages'
)
$existingTags = @(gh release list --repo $repo --limit 100 --json tagName | ConvertFrom-Json | ForEach-Object { $_.tagName })
if ($LASTEXITCODE -ne 0) { throw 'Could not list existing releases' }

foreach ($group in $groups) {
  $tag = "pdfs-$group-v1"
  if ($tag -notin $existingTags) {
    gh release create $tag --repo $repo --target main --title "$group source PDFs" --notes "Individual source PDFs for the $group group of the published SARO index."
    if ($LASTEXITCODE -ne 0) { throw "Could not create $tag" }
  }
  $existing = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
  @(gh release view $tag --repo $repo --json assets --jq '.assets[].name') | ForEach-Object { if ($_ -and $_.Trim()) { [void]$existing.Add($_.Trim()) } }
  if ($LASTEXITCODE -ne 0) { throw "Could not read assets for $tag" }
  $files = @(Get-ChildItem -LiteralPath (Join-Path 'site' $group) -Filter '*.pdf' -File | Sort-Object Name | Where-Object { -not $existing.Contains($_.Name) })
  Write-Host "$tag : $($files.Count) PDFs remaining"
  for ($start = 0; $start -lt $files.Count; $start += 40) {
    $last = [Math]::Min($start + 39, $files.Count - 1)
    $batch = @($files[$start..$last] | ForEach-Object { $_.FullName })
    gh release upload $tag @batch --repo $repo
    if ($LASTEXITCODE -ne 0) { throw "Upload failed for $tag, batch $start..$last; rerun to resume" }
    Write-Host "$tag : uploaded $($last + 1)/$($files.Count)"
  }
}
