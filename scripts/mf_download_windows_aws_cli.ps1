#Set the system to support TLS 1.2
$p = [Enum]::ToObject([System.Net.SecurityProtocolType], 3072);
[System.Net.ServicePointManager]::SecurityProtocol = $p;


$Link =  "https://awscli.amazonaws.com/AWSCLIV2.msi"
$AWSCliInstallFile="C:\PROGRA~2\CloudEndure\post_launch\AWSCLIV2.msi"

#Use the webclient api and disable the proxy to download the file
if (!(test-path "C:\PROGRA~2\CloudEndure\post_launch")) {
		mkdir C:\PROGRA~2\CloudEndure\post_launch
}

if (test-path "$AWSCliPath\aws.exe") {
	new-item "C:\PROGRA~2\CloudEndure\post_launch\aws_already_installed.lock" -type file
} else {
	$WebClient = New-Object System.Net.WebClient
	$WebClient.proxy=$null
	$WebClient.DownloadFile("$Link",$AWSCliInstallFile);
}
