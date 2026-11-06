# Match the project path and server invocation; never stop unrelated listeners.
$all = @(Get-CimInstance Win32_Process)
$servers = @($all | Where-Object {
 $_.Name -in @('python.exe','node.exe') -and
 $_.CommandLine -like '*D:\SupplyScope*' -and
 ($_.CommandLine -match 'uvicorn|vite[\\/]bin[\\/]vite')
})
foreach ($server in $servers) {
 foreach ($child in @($all | Where-Object { $_.ParentProcessId -eq $server.ProcessId })) {
  if ($child.Name -in @('python.exe','node.exe')) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
 }
 Stop-Process -Id $server.ProcessId -ErrorAction SilentlyContinue
}
