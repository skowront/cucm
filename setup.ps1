$currentDirectory = (Get-Location).Path
$confPath = $currentDirectory+"\conf"

function Create-Config {
	
	## URL Checker
	$valid = $false
    while (-not $valid) {
    $url = Read-Host "Please enter the URL to CUCM"
	Write-Host "$url"
	if ($url -match '(http|https):\/\/(.*):(\d+)') {
		$protocol = $matches[1]
		$domain = $matches[2]
		$port = $matches[3]
		Write-Host "Protocol: $protocol"
		Write-Host "Domain: $domain"
		Write-Host "Port: $port"
		$response = Read-Host "Is this correct? (Yes/Y)"
		if ($response -ieq "Y" -or $response -ieq "Yes") {
			$valid = $true
			}
		}
	else {
		Write-Host "Invalid URL format: '$url'. Please enter a valid URL including the protocol, domain, and port (e.g., https://example.com:8443)."
		}
    }
	
	## Check URL to keep in https://xxx:port/ format
	$lastChar = $url[$url.Length - 1]
	if ($lastChar -ne "/") {
		$url = $url+"/"
		}
	
	## User Details
    $username = Read-Host "Please enter the username to CUCM"
    $encryptedpass = Read-Host -Prompt "Enter the password:" -AsSecureString
    # Convert the password from SecureString to BSTR and then to a plain text string
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($encryptedpass)
    $pass = [Runtime.InteropServices.Marshal]::PtrToStringAuto($ptr)
    # Clean up the BSTR pointer
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
	
	## Convert to Base64
    $encrypt = [string]::Join(":", $username, $pass)
    $encrypted = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($encrypt))
    Write-Host "Encoded Text: $encrypted"
	
	## Servers Checker
    $valid = $false
    while (-not $valid) {
        $serverListInput = Read-Host "Please list all the CUCM servers (separated by commas)"
        $serverArray = $serverListInput.Split(',') | ForEach-Object { $_.Trim() }
        Write-Host "List of servers:"
        $serverArray
        $response = Read-Host "Is this correct? (Yes/Y)"
            if ($response -ieq "Y" -or $response -ieq "Yes") {
                $valid = $true
                }
    }
	
	## Convert from List to Array
	$outputserver = '[' + ($serverArray -join ', ') + ']'
	
	## Create Config File
	Write-Host "Creating configuration..."
	Copy-Item -Path $confPath"\config.ini.tmp" -Destination $confPath"\config.ini"
	
	$config = Get-Content $confPath"\config.ini"
	Write-Host "Writing Hostname..."
	$cucmhost = $config -replace "url:", "url: $url"
	Set-Content -Path $confPath"\config.ini" -Value $cucmhost
	
	$config = Get-Content $confPath"\config.ini"
	Write-Host "Writing secret..."
	$secret = $config -replace "secret:", "secret: $encrypted"
	Set-Content -Path $confPath"\config.ini" -Value $secret
	
	$config = Get-Content $confPath"\config.ini"
	Write-Host "Writing list of servers..."
	$servers = $config -replace "hosts:", "hosts: $outputserver"
	Set-Content -Path $confPath"\config.ini" -Value $servers
}

if (Test-Path $confPath"\config.ini" -PathType Leaf) {
	## Override
    $response = Read-Host "The file exists. Do you want to create a new configuration?"
	if ($response -ieq "Y" -or $response -ieq "Yes") {
		Write-Host "Deleting current configuration..."
		Remove-Item -Path $confPath"\config.ini"
		Create-Config
		}
}
else {
	Create-Config
}

Read-Host "Done.  Please hit <enter> to exit" 