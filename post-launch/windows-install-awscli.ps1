
#Set the system to support TLS 1.2
$p = [Enum]::ToObject([System.Net.SecurityProtocolType], 3072);
[System.Net.ServicePointManager]::SecurityProtocol = $p;


$Link =  "https://awscli.amazonaws.com/AWSCLIV2.msi"
$AWSCliPath="C:\Program Files\Amazon\AWSCLIV2"
$AWSCliInstallFile="c:\temp\awscli2.msi"
#Use the webclient api and disable the proxy to download the file
if (!(test-path "c:\temp")) {
		mkdir c:\temp
}
	
if (test-path "$AWSCliPath\aws.exe") {
	new-item "c:\temp\aws_already_installed.lock" -type file
} else {
	$WebClient = New-Object System.Net.WebClient
	$WebClient.proxy=$null
	$WebClient.DownloadFile("$Link",$AWSCliInstallFile);

	$MsiexecArgs=@(
		"/norestart",
		"/i $AWSCliInstallFile",
		"/passive"
	)
	$MsiexecArgs
	$process=(Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait)


}
