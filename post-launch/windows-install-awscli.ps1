$AWSCliPath="C:\Program Files\Amazon\AWSCLIV2"
$AWSCliInstallFile="C:\PROGRA~2\CloudEndure\post_launch\AWSCLIV2.msi"

if (test-path "$AWSCliPath\aws.exe") {
	new-item "C:\PROGRA~2\CloudEndure\post_launch\aws_already_installed.lock" -type file
} else {

	$MsiexecArgs=@(
		"/norestart",
		"/i $AWSCliInstallFile",
		"/passive"
	)
	$MsiexecArgs
	$process=(Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait)
    $process
}
