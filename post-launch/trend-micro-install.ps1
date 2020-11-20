
$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition


$filename = "GoldenAMI/Agent-Windows-Latest.zip"
$unziploc = "c:\install\GoldenAMI\trend"
$output = "$scriptPath\Agent-Windows-Latest.zip"
$software = "Trend Micro Deep Security Agent"


$Trend = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | select-Object DisplayName, DisplayVersion | Where { $_.DisplayName -eq $software }
$TrendVersion="not_installed"
if ( $Trend -ne $null ) {
	$TrendVersion = $Trend.DisplayVersion.Substring($Trend.DisplayVersion.Length - 3)
}


mkdir $unziploc
cd c:\install

function Expand-ZIPFile($file, $destination)
{
	$shell = new-object -com shell.application
	$zip = $shell.NameSpace($file)
	foreach($item in $zip.items())
	{
		$shell.Namespace($destination).copyhere($item)
	}
}



Expand-ZIPFile $output $unziploc
Start-Sleep -Seconds 60
$msiFile = dir "$unziploc\agent*"|select name -ExpandProperty name


If ($msiFile -Notlike "*$TrendVersion*")
{
	if ( test-path "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control") {
		Invoke-Expression -Command:'cmd.exe /C "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control" -r'
		Start-Sleep -Seconds 15
	}
	start-process -filepath msiexec.exe -argumentlist "/i $unziploc\$msiFile /qn"
	Start-Sleep -Seconds 180
	Invoke-Expression -Command:'cmd.exe /C "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control" -a dsm://dsm-aws.cascades.com:4120'
	cd c:\
	remove-item -path c:\install\ -recurse -force
	exit 3010
}