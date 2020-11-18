


    function add-member {
        param($type, $name, $value, $input)
        $note = "system.management.automation.psnoteproperty"
        $member = new-object $note $name,$value
        $metaInfoObj.psobject.members.add($member)
        return $metaInfoObj
    }


    function emitMetaInfoObject($path) {
        [string]$path = (resolve-path $path).path
        [string]$dir  = split-path $path
        [string]$file = split-path $path -leaf
        write-output $file
        $shellApp = new-object -com shell.application
        $myFolder = $shellApp.Namespace($dir)
        $fileobj = $myFolder.Items().Item($file)

        $metaInfoObj = new-object psobject
        $metaInfoObj.psobject.typenames[0] = "Custom.IO.File.Metadata"
        $metaInfoObj = add-member noteproperty Path $path -input $metaInfoObj


        for ( $i=0 ; $i -lt 40; $i++) {
            $n = $myFolder.GetDetailsOf($null, $i)


            if ($n) {
              $v = $myFolder.GetDetailsOf($fileobj,$i)
              if ($v) {
                  $metaInfoObj = add-member noteproperty $n $v -input $metaInfoObj
              }
            }
        }
        write-output $metaInfoObj
    }

 




function UninstallVmToolsFromClassesDefinition() {
$UninstallRegKeyLocation = Get-ChildItem HKLM:\SOFTWARE\Classes\Installer\Products\ 


#foreach ($Index in $UninstallRegKey.Name) {
#    $Index
#}

    $UninstallRegKeyLocation | ForEach-Object {
        $UninstallRegKeyItem = Get-ItemProperty $_.pspath
        $UninstallRegKeyItem | ForEach-Object {
            $UninstallRegKeyDetail = $_
            if ( $UninstallRegKeyDetail.ProductName -contains "Vmware Tools") {
                $UninstallRegKeyDetail.ProductName
                $UninstallRegKeyDetail.PackageCode
                $UninstallRegKeyDetail
            }
        }
    
    }

}
function UninstallVmToolsFromAddRemoveSoftware() {

    $UninstallStringFound=$false
    $UninstallString=""

    $UninstallRegKeyLocation = Get-ChildItem HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall
    foreach ($UninstallRegKeyItems in $UninstallRegKeyLocation ) {
        $UninstallRegKeyItem = Get-ItemProperty $UninstallRegKeyItems.pspath
        foreach ( $UninstallProductKey in $UninstallRegKeyItem ) {
            $UninstallRegKeyDetail = $UninstallProductKey
            if ( $UninstallRegKeyDetail.DisplayName -contains "Vmware Tools") {

                $UninstallString=$UninstallRegKeyDetail.UninstallString -replace 'MsiExec.exe /I',''

                $UninstallStringFound=$true
            }
            if ($UninstallStringFound -eq $true) { break }
        }
        if ($UninstallStringFound -eq $true) { break }

    }
    if ($UninstallStringFound -eq $true) {
    $UninstallString
       return (UninstallPackages $UninstallString)

    } else { 
        "Vmware Tools not found"
        return $true
    }
}

function UninstallVmToolsFromCacheFolder() {
    $CacheFolderLocation = "C:\Windows\Installer"
    $VmwareFileName=""
    $MSIPackageFound=$false

    $InstallerFolderContent = (get-childitem -path $CacheFolderLocation -Filter "*.msi" -file ).Name
    foreach ($MsiFile in $InstallerFolderContent) {
        $MsiInfo=emitMetaInfoObject "$($CacheFolderLocation)\$($MsiFile)"
        if ( $MsiInfo.Subject -like "*Vmware Tools*") {
            $MsiInfo.Path
            $MSIPackageFound=$true
            $VmwareFileName=$MsiInfo.Path
        }
        if ($MSIPackageFound -eq $true) { break }
    }
   
   if ($MSIPackageFound -eq $true) {
        return (UninstallPackages $VmwareFileName)

   } else {
        return $false
   }

}
function UninstallPackages ($UninstallKey) {
        try {
            $MsiexecArgs=@(
                "/norestart",
                "/x $($UninstallKey)",
                "/passive"
             )
             $MsiexecArgs
            $process=(Start-Process -filepath "C:\Windows\System32\msiexec.exe" -ArgumentList $MsiexecArgs -passthru -wait)
            Write-Host "Process finished with return code: " $process.ExitCode
            if ($process.ExitCode -eq 3010 -or $process.ExitCode -eq 0) {
                return $true
            } else { 
                return $false

            }
            #3010 (reboot requireD)

        } catch {
            Write-Output "Msiexec crashed"
            return $false
        }

}
#UninstallVmToolsFromAddRemoveSoftware
#UninstallVmToolsFromCacheFolder
if ( UninstallVmToolsFromAddRemoveSoftware -eq $false ) { UninstallVmToolsFromCacheFolder }
#UninstallVmToolsFromClassesDefinition;