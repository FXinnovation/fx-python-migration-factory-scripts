param ($reinstall = "No",
       $API_Token,
       $Servername,
       $Username = "",
       $Password = ""
)

function agent-install {
  Param($key, $account, $Username, $Password)

  $ScriptPath = "c:\Scripts\"
  if ($account -ne "") {
    foreach ($machine in $account -split (',')) {
      if ($Username -ne "") {
        $s = New-PSSession -ComputerName $machine -Credential (New-Object System.Management.Automation.PSCredential($Username, (ConvertTo-SecureString $Password -AsPlainText -Force))) -Authentication Negotiate
      }
      else {
        $s = New-PSSession -ComputerName $machine
      }
      if ($reinstall -eq 'Yes' -or ($reinstall -eq 'No' -and (!(Invoke-Command -Session $s -ScriptBlock {Test-path "c:\Program Files (x86)\CloudEndure\dist\windows_service_wrapper.exe"})))) {
        write-host "--------------------------------------------------------"
        write-host "- Installing CloudEndure for:   $machine -" -BackgroundColor Blue
        write-host "--------------------------------------------------------"
        if (!(Invoke-Command -Session $s -ScriptBlock {Test-path "c:\Scripts\"})) {
          Invoke-Command -Session $s -ScriptBlock {New-Item -Path "c:\Scripts\" -ItemType directory}
        }

        Invoke-Command -Session $s -ScriptBlock {
          $p = [Enum]::ToObject([System.Net.SecurityProtocolType], 3072);
          [System.Net.ServicePointManager]::SecurityProtocol = $p;
          $WebClient = New-Object System.Net.WebClient
          $WebClient.proxy=$null
          $WebClient.DownloadFile("https://console.cloudendure.com/installer_win.exe","C:\Scripts\installer_win.exe")
        }

        $fileexist = Invoke-Command -Session $s -ScriptBlock {Test-path "c:\Scripts\installer_win.exe"}

        if ($fileexist -eq "true") {
          $message = "** Successfully downloaded CloudEndure for: " + $machine + " **"
          Write-Host $message
        }

        $device_ids = @()

        $boot_disk_index = Invoke-Command -Session $s -ScriptBlock {Get-WmiObject -class Win32_DiskPartition |Where-Object {$_.BootPartition -eq $True}| Select-Object -ExpandProperty DiskIndex}
        $boot_device_id = Invoke-Command -Session $s -ScriptBlock {Get-WmiObject -class Win32_DiskDrive |Where-Object {$_.Index -eq "$boot_disk_index"}| Select-Object -ExpandProperty DeviceID}
        $device_ids += $boot_device_id

        $no_boot_device_ids = Invoke-Command -Session $s -ScriptBlock {Get-WmiObject -class Win32_DiskDrive | Where-Object {$_.Index -ne "$boot_disk_index"}| Select -ExpandProperty DeviceID}
        $device_ids += $no_boot_device_ids

        $device_ids_flat = $device_ids -Join ','

        $command = $ScriptPath + "installer_win.exe -t " + $key + " --no-prompt" + " --skip-dotnet-check --force-volumes --drives=`"" + $device_ids_flat + "`" --no-auto-disk-detection"
        Write-Host $command
        $scriptblock2 = $executioncontext.invokecommand.NewScriptBlock($command)

        Invoke-Command -Session $s -ScriptBlock $scriptblock2
        write-host
        write-host "** CloudEndure installation finished for : $machine **"
        write-host
      }
      else {
       $message = "CloudEndure agent already installed for machine: " + $machine + " , please reinstall manually if required"
       write-host $message -BackgroundColor Red
      }
    }
  }
}

agent-install $API_Token $Servername $Username $Password
