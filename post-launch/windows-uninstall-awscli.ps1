
$AWSCliPath="C:\Program Files\Amazon\AWSCLIV2"
$AWSCliInstallFile="C:\PROGRA~2\CloudEndure\post_launch\awscliv2.msi"

if ( -not (test-path "C:\PROGRA~2\CloudEndure\post_launch\aws_already_installed.lock") ) {

	$MsiexecArgs=@(
		"/norestart",
		"/x $AWSCliInstallFile",
		"/passive"
	)
	$MsiexecArgs
	$process=(Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait)
	$process
}
