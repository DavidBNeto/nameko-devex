function Get-File-Path($file) {
    try {
        $relativePath = $PSScriptRoot
        $filePath = Join-Path -Path $relativePath -ChildPath $file
        $filePath
    } catch {
        return null
    }
}

function Install($module) {
    try {
        $path = Get-File-Path $module
        Push-Location $path
        python setup.py install
        Pop-Location
    } catch {
        exit 1
    }
}

Install "\orders"
Install "\products"
Install "\gateway"
