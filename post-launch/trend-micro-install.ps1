
$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition

$BasePath="c:\temp"
$unziploc = "$BasePath\GoldenAMI\trend"
$output = "Agent-Windows-Latest.zip"
$software = "Trend Micro Deep Security Agent"

$bucket = "cascadesinstallationsourcesrepoprod"
$filename = "GoldenAMI/Agent-Windows-Latest.zip"

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")


$Trend = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | select-Object DisplayName, DisplayVersion | Where { $_.DisplayName -eq $software }
$TrendVersion="not_installed"
if ( $Trend -ne $null ) {
	$TrendVersion = $Trend.DisplayVersion.Substring($Trend.DisplayVersion.Length - 3)
}


mkdir $unziploc
cd $BasePath

function Expand-ZIPFile($file, $destination)
{
	$shell = new-object -com shell.application
	$zip = $shell.NameSpace($file)
	foreach($item in $zip.items())
	{
		$shell.Namespace($destination).copyhere($item)
	}
}

aws.exe s3 cp "s3://$bucket/$filename" "$BasePath\$output"

Expand-ZIPFile "$BasePath\$output" $unziploc
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
	exit 3010
}
remove-item -recurse "$BasePath\$output"
remove-item -recurse $unziploc