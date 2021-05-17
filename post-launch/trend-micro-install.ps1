set-itemproperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' -name ProxyEnable -value 0

$scriptPath = split-path -parent $MyInvocation.MyCommand.Definition

$BasePath="c:\temp"
$unziploc = "$BasePath\GoldenAMI\trend"
$filename = "Agent-Windows-Latest.zip"
$software = "Trend Micro Deep Security Agent"

$bucket = "cascadesinstallationsourcesrepoprod"
$bucketpath = "GoldenAMI"

$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

$endpoint = aws.exe ec2 describe-vpc-endpoints --region ca-central-1 --filters '[{\"Name\": \"vpc-endpoint-type\", \"Values\": [\"Interface\"]}, {\"Name\": \"service-name\", \"Values\": [\"com.amazonaws.ca-central-1.s3\"]}]' --query VpcEndpoints[*].DnsEntries[0].DnsName --output text
$endpointurl = "http://"+$endpoint.remove(0,2)

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

aws.exe s3 cp "s3://$bucket/$bucketpath/$filename" "$BasePath\$filename" --endpoint-url "$endpointurl" --region ca-central-1

Expand-ZIPFile "$BasePath\$filename" $unziploc
Start-Sleep -Seconds 60
$msiFile = dir "$unziploc\agent*"|select name -ExpandProperty name


If ($msiFile -Notlike "*$TrendVersion*")
{
	if ( test-path "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control.cmd") {
		Invoke-Expression -Command:'cmd.exe /C "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control.cmd" -r'
	}
	start-process -filepath msiexec.exe -argumentlist "/i $unziploc\$msiFile /qn"
	Start-Sleep -Seconds 180
	start-process "C:\Program Files\Trend Micro\Deep Security Agent\dsa_control.cmd" -Args "-a dsm://dsm-aws.cascades.com:4120"
	cd c:\
	exit 3010
}
remove-item -recurse "$BasePath\$filename"
remove-item -recurse $unziploc
