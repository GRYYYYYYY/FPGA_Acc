$tools = @("g++","python","java","javac","vpr","rapidwright","vitis_hls","v++","vivado","xbutil")
$rows = foreach ($name in $tools) {
  $command = Get-Command $name -ErrorAction SilentlyContinue
  [pscustomobject]@{ Tool=$name; Available=[bool]$command; Path=if($command){$command.Source}else{""} }
}
$rows | Format-Table -AutoSize
if (-not ($rows | Where-Object {$_.Tool -eq "vitis_hls" -and $_.Available})) {
  Write-Host "Vitis HLS synthesis/cosim: PENDING"
}
if (-not ($rows | Where-Object {$_.Tool -eq "rapidwright" -and $_.Available})) {
  Write-Host "RapidWright real DCP/FPGAIF round-trip: PENDING"
}
if (-not ($rows | Where-Object {$_.Tool -eq "vivado" -and $_.Available})) {
  Write-Host "Vivado legality/timing/power validation: PENDING"
}
