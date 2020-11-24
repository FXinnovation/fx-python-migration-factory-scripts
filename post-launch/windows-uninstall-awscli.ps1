
$AWSCliPath="C:\Program Files\Amazon\AWSCLIV2"
$AWSCliInstallFile="c:\temp\awscli2.msi"
#Use the webclient api and disable the proxy to download the file

if ( -not (test-path "c:\temp\aws_already_installed.lock") ) {

	$MsiexecArgs=@(
		"/norestart",
		"/x $AWSCliInstallFile",
		"/passive"
	)
	$MsiexecArgs
	$process=(Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait)
}
