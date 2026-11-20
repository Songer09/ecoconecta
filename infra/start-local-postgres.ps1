param([string]$StateDirectory = (Join-Path $env:LOCALAPPDATA 'EcoConecta\postgresql16'))
$ErrorActionPreference = 'Stop'
$pgBin = Join-Path $StateDirectory 'runtime\bin'
$pgData = Join-Path $StateDirectory 'data'
$credentialFile = Join-Path $StateDirectory 'credentials.xml'
if (!(Test-Path -LiteralPath (Join-Path $pgBin 'postgres.exe'))) {
    throw 'PostgreSQL 16 binaries are required in StateDirectory/runtime/bin; see db/README.md'
}
if (!(Test-Path -LiteralPath (Join-Path $StateDirectory 'tools\node_modules\pg'))) {
    throw 'Install pg@8.23.1 into StateDirectory/tools with npm first; see db/README.md'
}
New-Item -ItemType Directory -Force -Path $StateDirectory | Out-Null
if (Test-Path -LiteralPath $credentialFile) {
    $credentials = Import-Clixml -LiteralPath $credentialFile
} else {
    if (Test-Path -LiteralPath $pgData) { throw 'Existing data without credentials: refusing to reinitialize' }
    $credentials = @{}
    foreach ($name in @('Admin','Owner','App')) {
        $bytes = New-Object byte[] 32
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
        $password = [BitConverter]::ToString($bytes).Replace('-','')
        $securePassword = ConvertTo-SecureString $password -AsPlainText -Force
        $credentials[$name] = New-Object System.Management.Automation.PSCredential($name, $securePassword)
    }
    # Windows DPAPI encryption: readable only by this Windows identity on this PC.
    $credentials | Export-Clixml -LiteralPath $credentialFile
}
if (!(Test-Path -LiteralPath (Join-Path $pgData 'PG_VERSION'))) {
    $passwordFile = Join-Path $StateDirectory 'initdb-password.tmp'
    try {
        [IO.File]::WriteAllText($passwordFile, $credentials.Admin.GetNetworkCredential().Password)
        & (Join-Path $pgBin 'initdb.exe') -D $pgData -U postgres --auth-host=scram-sha-256 --auth-local=scram-sha-256 --encoding=UTF8 --no-locale --pwfile=$passwordFile
        if ($LASTEXITCODE -ne 0) { throw 'initdb failed' }
    } finally {
        if (Test-Path -LiteralPath $passwordFile) { Remove-Item -LiteralPath $passwordFile }
    }
}
& (Join-Path $pgBin 'pg_ctl.exe') -D $pgData status *> $null
if ($LASTEXITCODE -ne 0) {
    if (Get-NetTCPConnection -LocalPort 5432 -State Listen -ErrorAction SilentlyContinue) {
        throw 'Port 5432 already in use; not stopping or replacing another database'
    }
    $startArgs = @('-D', ('"' + $pgData + '"'), '-l', ('"' + (Join-Path $StateDirectory 'postgres.log') + '"'), '-o', '"-h 127.0.0.1 -p 5432"', '-w', 'start')
    $starter = Start-Process -FilePath (Join-Path $pgBin 'pg_ctl.exe') -ArgumentList $startArgs -WindowStyle Hidden -PassThru
    if (!$starter.WaitForExit(20000)) { throw 'PostgreSQL startup timed out; inspect the local log' }
    if ($starter.ExitCode -ne 0) { throw 'PostgreSQL failed to start; inspect the local log' }
}
$env:NODE_PATH = Join-Path $StateDirectory 'tools\node_modules'
try {
    $env:ECO_PG_ADMIN_PASSWORD = $credentials.Admin.GetNetworkCredential().Password
    $env:ECO_PG_OWNER_PASSWORD = $credentials.Owner.GetNetworkCredential().Password
    $env:ECO_PG_APP_PASSWORD = $credentials.App.GetNetworkCredential().Password
    node (Join-Path $PSScriptRoot 'provision-local-db.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Database provisioning failed; no existing tables were overwritten' }
} finally {
    Remove-Item Env:ECO_PG_ADMIN_PASSWORD,Env:ECO_PG_OWNER_PASSWORD,Env:ECO_PG_APP_PASSWORD -ErrorAction SilentlyContinue
}
