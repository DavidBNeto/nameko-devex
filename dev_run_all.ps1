function Get-Run-File {
    try {
        $relativePath = $PSScriptRoot
        $filePath = Join-Path -Path $relativePath -ChildPath "dev_run.ps1"
        $filePath
    } catch {
        return null
    }
}

$runFile = Get-Run-File
& $runFile gateway.service
& $runFile orders.service
& $runFile products.service
