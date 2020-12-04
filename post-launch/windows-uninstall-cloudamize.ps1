
$CloudAmizeInfo=get-wmiobject Win32_Product -Filter "Name LIKE 'Cloudamize Windows Agent'"

if ($CloudAmizeInfo.IdentifyingNumber -ne $null) { 
	$MsiexecArgs=@(
		"/norestart",
		"/x " + $CloudAmizeInfo.IdentifyingNumber,
		"/passive"
       	)
	$MsiexecArgs
	Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait
 }
