param ($reinstall = "No",
       $Servername,
       $Username = "",
       $Password = ""
)

function ssmagent-download {
  Param($account, $Username, $Password)

  if ($account -ne "") {
    foreach ($machine in $account -split (',')) {
      if ($Username -ne "") {
        $s = New-PSSession -ComputerName $machine -Credential (New-Object System.Management.Automation.PSCredential($Username, (ConvertTo-SecureString $Password -AsPlainText -Force))) -Authentication Negotiate
      }
      else {
        $s = New-PSSession -ComputerName $machine
      }
      if (!(Invoke-Command -Session $s -ScriptBlock {Test-path "C:\Program Files\Amazon\SSM"})) {
        write-host "--------------------------------------------------------"
        write-host "- Downloading SSM Agent for:   $machine -" -BackgroundColor Blue
        write-host "--------------------------------------------------------"
        if (!(Invoke-Command -Session $s -ScriptBlock {Test-path "C:\PROGRA~2\CloudEndure\post_launch"})) {
          Invoke-Command -Session $s -ScriptBlock {New-Item -Path "C:\PROGRA~2\CloudEndure\post_launch" -ItemType directory}
        }

        Invoke-Command -Session $s -ScriptBlock {
          $p = [Enum]::ToObject([System.Net.SecurityProtocolType], 3072);
          [System.Net.ServicePointManager]::SecurityProtocol = $p;
          $WebClient = New-Object System.Net.WebClient
          $WebClient.proxy=$null
          $WebClient.DownloadFile("https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/windows_amd64/AmazonSSMAgentSetup.exe")
        }

        $fileexist = Invoke-Command -Session $s -ScriptBlock {Test-path "C:\PROGRA~2\CloudEndure\post_launch\AmazonSSMAgentSetup.exe"}

        if ($fileexist -eq "true") {
          $message = "** Successfully downloaded SSM Agent for: " + $machine + " **"
          Write-Host $message
        }
      }
    }
  }
}

ssmagent-download $Servername $Username $Password
