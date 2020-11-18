
#Set the system to support TLS 1.2
$p = [Enum]::ToObject([System.Net.SecurityProtocolType], 3072);
[System.Net.ServicePointManager]::SecurityProtocol = $p;

#Get the proper utl
if ((Get-WmiObject win32_operatingsystem | select osarchitecture).osarchitecture -like "64*")
{
    $Link = "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe"
}
else
{
    $Link =  "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_386/AmazonSSMAgentSetup.exe"
}
#Use the webclient api and disable the proxy to download the file
$WebClient = New-Object System.Net.WebClient
$WebClient.proxy=$null
$WebClient.DownloadFile("$Link","$env:USERPROFILE\Desktop\SSMAgent_latest.exe");

Start-Process -FilePath $env:USERPROFILE\Desktop\SSMAgent_latest.exe -ArgumentList "/S" -wait -passthru

rm -Force $env:USERPROFILE\Desktop\SSMAgent_latest.exe
