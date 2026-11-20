# Dot-source this file to set DATABASE_URL in the current PowerShell session.
param([ValidateSet('App','Owner')][string]$Role = 'App')
$credentialFile = Join-Path $env:LOCALAPPDATA 'EcoConecta\postgresql16\credentials.xml'
$dbCredentials = Import-Clixml -LiteralPath $credentialFile
$dbUser = if ($Role -eq 'Owner') { 'ecoconecta_owner' } else { 'ecoconecta_app' }
$dbPassword = [Uri]::EscapeDataString($dbCredentials[$Role].GetNetworkCredential().Password)
$env:DATABASE_URL = "postgresql://${dbUser}:${dbPassword}@127.0.0.1:5432/ecoconecta"
Remove-Variable dbPassword,dbCredentials
Write-Host "DATABASE_URL configured for $dbUser (value hidden)."
