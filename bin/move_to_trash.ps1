param (
    [string]$targetDir
)

# Moves all files from the target directory to the trash
Get-ChildItem -Path $targetDir | ForEach-Object { $_ | Remove-Item -Recurse -Confirm:$false -WhatIf }
