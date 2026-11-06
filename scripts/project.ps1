param([ValidateSet('acquire','build','analyse','test','powerbi','all')][string]$Task='all')
Set-Location D:\SupplyScope
$ErrorActionPreference='Stop'
if ($Task -in @('acquire','all')) { & .\.venv\Scripts\python.exe -m pipelines.acquire; if($LASTEXITCODE){exit $LASTEXITCODE} }
if ($Task -in @('build','all')) { & .\.venv\Scripts\python.exe -m pipelines.build; if($LASTEXITCODE){exit $LASTEXITCODE} }
if ($Task -in @('analyse','all')) { & .\.venv\Scripts\python.exe -m pipelines.analyse; if($LASTEXITCODE){exit $LASTEXITCODE} }
if ($Task -in @('powerbi','all')) { & .\.venv\Scripts\python.exe -m scripts.powerbi_package; if($LASTEXITCODE){exit $LASTEXITCODE} }
if ($Task -eq 'test') { & .\.venv\Scripts\python.exe -m pytest tests -q; if($LASTEXITCODE){exit $LASTEXITCODE}; npm.cmd run build --prefix frontend; exit $LASTEXITCODE }
