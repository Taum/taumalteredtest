$filePath = "C:\Users\taumx\Documents\GitHub\bga-altered\"
$tempPath = "C:\Users\taumx\Documents\GitHub\taumalteredtest\"
$include = @('*.php', '*.js') # adapt as needed

$excludes = @(".git",".vscode", "misc")


Get-ChildItem $filePath -Directory | 
    Where-Object{$_.Name -notin $excludes} | 
    Copy-Item -Destination $tempPath -Recurse -Force

Get-ChildItem $filePath -file | 
    Copy-Item -Destination $tempPath -Force


Get-ChildItem -File -Recurse $tempPath |
    Where-Object{ $_.Extension -in @('.php', '.js', '.css', '.tpl') } |
  Rename-Item -PassThru -Force -NewName { $_.Name -replace 'altered', 'taumalteredtest' } |
  ForEach-Object {
#     # NOTE: You may have to use an -Encoding argument here to ensure
#     #       the desired character encoding.
    ($_ | Get-Content -Raw) -replace 'altered', 'taumalteredtest' |
      Set-Content -NoNewLine -LiteralPath $_.FullName
 }
Read-Host "pause"
