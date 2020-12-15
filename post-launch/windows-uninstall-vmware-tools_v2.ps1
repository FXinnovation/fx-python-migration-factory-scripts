
$VarDebug=$true
$LogFileEnabled=$true
$LogFileLocation="c:\temp\"
$LogFilePrintNotFound=$false

#Do not modify bellow this script unless you know what you are doing
$scriptName = $MyInvocation.MyCommand.Name
$Logfile = $LogFileLocation + ($scriptName).Replace("ps1","log")
$RegBaseKey="HKEY_CLASSES_ROOT\CLSID"
if (!(test-path HKCR:)) {
	New-PSDrive -PSProvider registry -Root HKEY_CLASSES_ROOT -Name HKCR
}
if (!(test-path $LogFileLocation)) {
    mkdir $LogFileLocation
}

function com_registeredpath()
{  
    param([string]$guid)

    $key = Get-Item "HKCR:\CLSID\$guid\InprocServer32"
    $values = Get-ItemProperty $key.PSPath

    [string] $defaultValue = [string] $values."(default)"
    #write-host ">>>: $defaultValue" # returns a value like: c:\somefolder\somefile.dll

    return $defaultValue
}
function com_registeredProgID()
{  
    param([string]$guid)

    $key = Get-Item "HKCR:\CLSID\$guid\ProgID"
    $values = Get-ItemProperty $key.PSPath

    [string] $defaultValue = [string] $values."(default)"
    #write-host ">>>: $defaultValue" # returns a value like: c:\somefolder\somefile.dll

    return $defaultValue
}
#com_registeredpath "{C73DA087-EDDB-4a7c-B216-8EF8A3B92C7B}"

function com_registeredAppID()
{  
    param([string]$guid)

    $key = Get-Item "HKCR:\CLSID\$guid\"
    $values = Get-ItemProperty $key.PSPath

    [string] $defaultValue = [string] $values."AppID"
    #write-host ">>>: $defaultValue" # returns a value like: c:\somefolder\somefile.dll

    return $defaultValue
}

Function LogWrite
{

   Param ([string]$logstring)
   if ($LogFileEnabled -eq $true)  {
    Add-content $Logfile -value $logstring
   }
}

function ParseCLSID () {
	
	$RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\CLSID\" 
	
	$VmwareComDefinition=@{}

	$CLSID_Items = Get-childitem  $RegBaseKey
    foreach ($CLS_Entries in $CLSID_Items ) {
        $RegKeyInprocID = join-path $CLS_Entries.PSPath 'InprocServer32'
        if ( Test-Path $RegKeyInprocID ) {
            $ClassID = [string] $CLS_Entries.Name.Replace("HKEY_CLASSES_ROOT\CLSID\","")
            $ComDefaultValue = com_registeredpath $ClassID
            if ($ComDefaultValue -like "*vmware*") {
                #com_registeredProgID  $ClassID
                $ComDefaultValue 
                $ClassID
                $VmwareComDefinition[$ClassID]=@{}
                $VmwareComDefinition[$ClassID]["Prog"]=com_registeredProgID  $ClassID
                $VmwareComDefinition[$ClassID]["GUID"]=$ClassID
                $VmwareComDefinition[$ClassID]["DLL"]=$ComDefaultValue
                $VmwareComDefinition[$ClassID]["PSPATH"]=$CLS_Entries.PSPath
                $VmwareComDefinition[$ClassID]["AppID"]=com_registeredAppID  $ClassID
                $VmwareComDefinition[$ClassID]
                DeleteRegistryKeys $CLS_Entries.PSPath
                #break;
            }
        }
    }
    LocateClassKeys $VmwareComDefinition
    LocateClassAppIdsFromAppID $VmwareComDefinition
    LocateClassAppIdsFromGuid $VmwareComDefinition
}
function ParseTypeLibs () {
	
	$RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\TypeLib\" 
	
	$VmwareComDefinition=@{}

	$CLSID_Items = Get-childitem  $RegBaseKey
    foreach ($CLS_Entries in $CLSID_Items ) {
        $RegKeyInprocID = join-path $CLS_Entries.PSPath '1.0\HELPDIR'
        if ( Test-Path $RegKeyInprocID ) {
            $key = Get-Item $RegKeyInprocID
            $values = Get-ItemProperty $key.PSPath
            [string] $defaultValue = [string] $values."(default)"
            if ($defaultValue -like "*vmware*") {
                $defaultValue
                $CLS_Entries.PSPath
                $ClassID = [string] $CLS_Entries.Name.Replace("HKEY_CLASSES_ROOT\TypeLib\","")
                DeleteRegistryKeys  $CLS_Entries.PSPath
            }
        }
    }
    #LocateClassKeys $VmwareComDefinition
    #LocateClassAppIdsFromAppID $VmwareComDefinition
    #LocateClassAppIdsFromGuid $VmwareComDefinition
}

function ParseTypeLibsWow6432 () {
		$RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\Wow6432Node\TypeLib\" 
	
	$VmwareComDefinition=@{}

	$CLSID_Items = Get-childitem  $RegBaseKey
    foreach ($CLS_Entries in $CLSID_Items ) {
        $RegKeyInprocID = join-path $CLS_Entries.PSPath '1.0\HELPDIR'
        if ( Test-Path $RegKeyInprocID ) {
            $key = Get-Item $RegKeyInprocID
            $values = Get-ItemProperty $key.PSPath
            [string] $defaultValue = [string] $values."(default)"
            if ($defaultValue -like "*vmware*") {
                $defaultValue
                $CLS_Entries.PSPath
                $ClassID = [string] $CLS_Entries.Name.Replace("HKEY_CLASSES_ROOT\Wow6432Node\TypeLib\","")

            }
        }
    }
    #LocateClassKeys $VmwareComDefinition
    #LocateClassAppIdsFromAppID $VmwareComDefinition
    #LocateClassAppIdsFromGuid $VmwareComDefinition
}
function LocateClassKeys ($ClassArray ) {
    
    $ClassArray
    $RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\" 
    $CLSID_Items = Get-childitem  $RegBaseKey
    foreach ($CLS_Entries in $CLSID_Items ) {
        $RegKeyInCLSID = join-path $CLS_Entries.PSPath 'CLSID'
        if ( Test-Path $RegKeyInCLSID ) {
            $ClassID = [string] $CLS_Entries.Name.Replace("HKEY_CLASSES_ROOT\","")
            $key = Get-Item "HKCR:\$ClassID\CLSID"
            $values = Get-ItemProperty $key.PSPath
            #$values


          [string] $defaultValue = [string] $values."(default)"
            if ($ClassArray[$defaultValue] -ne $null) {
            #$RegKeyInCLSID
            DeleteRegistryKeys $CLS_Entries.PSPath
            }
         }
        
    }
}

function LocateClassAppIdsFromAppID ($ClassAppArray ) {
    $ClassAppArray.Keys
    #$ClassAppArray
    $RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\AppID" 
    $CLSID_Items = Get-childitem  $RegBaseKey
    foreach ($CLS_Entries in $CLSID_Items ) {
            $key = Get-Item $CLS_Entries.PSPath
            $values = Get-ItemProperty $key.PSPath
            [string] $defaultValue = [string] $values."AppID"
          if ($defaultValue -ne "") {
            foreach ($ClassAppArrayInfo in $ClassAppArray.Keys) {
               if ($ClassAppArray[$ClassAppArrayInfo]["AppID"] -eq $defaultValue) {
                      $defaultValue

                $CLS_Entries.PSPath
               # defaultValue
               # DeleteRegistryKeys $CLS_Entries.PSPath
                }
            }
         }
    }
}
function LocateClassAppIdsFromGuid ($ClassAppArray ) {
    #$ClassAppArray.Keys

    $RegBaseKey="REGISTRY::HKEY_CLASSES_ROOT\AppID" 
    $CLSID_Items = Get-childitem  $RegBaseKey
#    $CLSID_Items
    foreach ($ClassAppArrayInfo in $ClassAppArray.Keys) {
        $AppGuid=$ClassAppArray[$ClassAppArrayInfo]["AppID"]
        "App: $AppGuid"
        if ( $AppGuid -ne "" ) {
            $RegKeyInAppGuid = join-path $RegBaseKey $AppGuid
            "AppGuid: $RegKeyInAppGuid"
            if ( Test-Path $RegKeyInAppGuid  ) {
                "Found Guid"
                $ClassAppArrayInfo
                $RegKeyInAppGuid
                ""
                DeleteRegistryKeys $RegKeyInAppGuid
            }
        }
    }
}


function DeleteRegistryKeys ($RegistryPath) {
   
   if ($VarDebug -eq $true) {
        $RegistryPath
    }
    if ( Test-Path $RegistryPath ) {
        LogWrite "Registry Key found - Deleting $RegistryPath"
        Remove-Item $RegistryPath -Recurse    
    } else {
        if ($LogFilePrintNotFound -eq $true) {
            LogWrite "Registry Key Not found, Skipping - $RegistryPath"
        }
    }

}
function DeleteVmFiles ($VarFilePath) {

   if ($VarDebug -eq $true) {
        $VarFilePath
    }
    if ( Test-Path  $VarFilePath ) {
        LogWrite "File found - Deleting $VarFilePath"
        Remove-Item -path $VarFilePath -Recurse -force
    } else {
    if ($LogFilePrintNotFound -eq $true) {
            LogWrite "File Not found, Skipping - $VarFilePath"
        }
    }

}
function DeleteRegistryProperties ($RegistryPath,$RegistryItem) {
   
   if ($VarDebug -eq $true) {
    "Path: $RegistryPath , Name: $RegistryItem"
   }
    if ( Get-ItemProperty -Path $RegistryPath -name $RegistryItem -ErrorAction SilentlyContinue ) {
        LogWrite "Registry Entry found - Deleting Path: $RegistryPath - Name: $RegistryItem"
        Remove-ItemProperty -Path $RegistryPath -Name $RegistryItem
    } else {
        if ($LogFilePrintNotFound -eq $true) {
            LogWrite "Registry Entry Not found, Skipping - $RegistryPath"
        }
    }
}


function UnregisterDLL () {
    
    regsvr32 /u "C:\Program Files\VMware\VMware Tools\vmStatsProvider\win32\vmStatsProvider.dll" /s
    regsvr32 /u "C:\Program Files\VMware\VMware Tools\vmStatsProvider\win64\vmStatsProvider.dll" /s
    regsvr32 /u "C:\Program Files\Common Files\VMware\Drivers\vss\VCBSnapshotProvider.dll" /s
}



function RemoveSoftwareFromAddRemoveSoftware($RegKey) {
   $UninstallStringFound=$false
    $UninstallPath=$null
        $UninstallRegKeyLocation = Get-ChildItem $RegKey
    foreach ($UninstallRegKeyItems in $UninstallRegKeyLocation ) {
        $UninstallRegKeyItem = Get-ItemProperty $UninstallRegKeyItems.pspath
        foreach ( $UninstallProductKey in $UninstallRegKeyItem ) {
            $UninstallRegKeyDetail = $UninstallProductKey
            if ( $UninstallRegKeyDetail.ProductName -like "*Vmware Tools*" -OR  $UninstallRegKeyDetail.DisplayName -like "*Vmware Tools*") {
                $UninstallPath=$UninstallRegKeyDetail.PSPath
                $UninstallStringFound=$true
            }
            if ($UninstallStringFound -eq $true) { break }
        }
        if ($UninstallStringFound -eq $true) { break }

    }
    if ($UninstallStringFound -eq $true) {
       return $UninstallPath
    } else { 
        return $null
    }
}

function RemoveVmwareRegistryEntries() {
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\efifw"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\pvscsi"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\svga_wddm"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VGAuthService"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vm3dmp"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vm3dmp-debug"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vm3dmp-stats"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vm3dmp_loader"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmci"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmmemctl"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmmouse"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VMTools"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmusbmouse"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmvss"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VMwareCAFCommAmqpListener"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VMwareCAFManagementAgentHost"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmxnet3"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vsock"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vsockDll"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vsockSys"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VM3DService"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\VMRawDsk"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmwefifw"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmxnet3ndis6"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vmhgfs"
	DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\vsepflt"
	
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\vmStatsProvider"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\vmtools"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\VMUpgradeHelper"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\VMware Tools"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\System\vmci"
    DeleteRegistryKeys "HKLM:\SYSTEM\CurrentControlSet\Services\EventLog\Application\VGAuth"


    DeleteRegistryKeys "HKLM:\SOFTWARE\VMware, Inc."
    DeleteRegistryProperties "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "VMware User Process"
    DeleteRegistryProperties "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "VMware VM3DService Process"

    $RegPath1=RemoveSoftwareFromAddRemoveSoftware "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    if ($RegPath1 -ne $null) { 
        $RegPath1
       DeleteRegistryKeys $RegPath1 
    }
    $RegPath2=RemoveSoftwareFromAddRemoveSoftware "REGISTRY::HKEY_CLASSES_ROOT\Installer\Products"
    #$RegPath2
    if ($RegPath2 -ne $null) { 
        $VmProductID=(get-itemproperty $RegPath2).PSChildName
        DeleteRegistryKeys "REGISTRY::HKEY_CLASSES_ROOT\Installer\Features\$VmProductID"
        DeleteRegistryKeys "REGISTRY::HKEY_CLASSES_ROOT\Installer\Products\$VmProductID"

    }
}
function DeleteServicesViaSC() {
	$VmServiceList=@(
	"efifw" ,"pvscsi" ,"svga_wddm" ,"VGAuthService" ,"vm3dmp" ,"vm3dmp-debug" ,"vm3dmp-stats" ,"vm3dmp_loader"
   ,"vmci" ,"vmmemctl" ,"vmmouse" ,"VMTools" ,"vmusbmouse" ,"vmvss" ,"VMwareCAFCommAmqpListener" ,"VMwareCAFManagementAgentHost" ,"vmxnet3"
    ,"vsock" ,"vsockDll" ,"vsockSys", "VM3DService", "GISvc", "giappdef", "VMRawDsk", "vmwefifw", "vmxnet3ndis6", "vsepflt"
	)
	foreach ($ServicesID in $VmServiceList) {
		sc.exe delete $ServicesID
	}
}
function RemoveVmwareFiles() {
    TerminateVmProcess

    DeleteVmFiles "C:\Program Files\VMware"
    DeleteVmFiles "C:\Program Files\Common Files\VMware"
    DeleteVmFiles "c:\programdata\Microsoft\Windows\Start Menu\Programs\VMware"
    DeleteVmFiles "C:\ProgramData\VMware"

    DeleteVmFiles "C:\Windows\System32\vm3ddevapi64-debug.dll"
	DeleteVmFiles "C:\Windows\System32\vm3ddevapi64-release.dll"
	DeleteVmFiles "C:\Windows\System32\vm3ddevapi64-stats.dll"
    DeleteVmFiles "C:\Windows\System32\vm3ddevapi64.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dgl64.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dglhelper64.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64-debug.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64-stats.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64_10-debug.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64_10-stats.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64_10.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dum64_loader.dll"
    DeleteVmFiles "C:\Windows\System32\vmGuestLibJava.dll"
    DeleteVmFiles "C:\Windows\System32\vmGuestLib.dll"
    DeleteVmFiles "C:\Windows\System32\vsocklib.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dco.dll"
    DeleteVmFiles "C:\Windows\System32\vm3dservice.exe"
	DeleteVmFiles "C:\Windows\System32\vmhgfs.sys"
	DeleteVmFiles "C:\Windows\System32\VMWSU.DLL"
	
	DeleteVmFiles "C:\Windows\System32\Drivers\vm3dmp.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vm3dmp_loader.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vm3dmp-debug.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vm3dmp-stats.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmusbmouse.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmmouse.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmmemctl.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmci.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vsock.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmxnet3.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmxnet3n61x64.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\GIAppDef.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\glxgi.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vsepflt.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmhgfs.sys"
	DeleteVmFiles "C:\Windows\System32\Drivers\vmrawdsk.sys"
	
	
	

    DeleteVmFiles "C:\Windows\SysWOW64\vm3ddevapi.dll"
	DeleteVmFiles "C:\Windows\SysWOW64\vm3ddevapi-debug.dll"
	DeleteVmFiles "C:\Windows\SysWOW64\vm3ddevapi-release.dll"
	DeleteVmFiles "C:\Windows\SysWOW64\vm3ddevapi-stats.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dgl.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dglhelper.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum-debug.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum-stats.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum_10-debug.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum_10-stats.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum_10.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vm3dum_loader.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vmGuestLibJava.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vmGuestLib.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vsocklib.dll"
	DeleteVmFiles "C:\Windows\SysWOW64\vmGuestLib.dll"
    DeleteVmFiles "C:\Windows\SysWOW64\vsocklib.dll"
	DeleteVmFiles "C:\Windows\SysWOW64\vmhgfs.sys"
	

    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\pvscsi.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\efifw.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\vm3d.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\vmci.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\vmmouse.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\vmusbmouse.inf*"
    DeleteVmFiles "C:\Windows\System32\DriverStore\FileRepository\vmxnet3.inf*"
	


}

function TerminateVmProcess() {

    stop-process -name "vm3dservice" -Force
    stop-process -name "vmtoolsd" -Force
    

}


function CheckVmToolsStatus() {

    $scriptNewLocation=Join-Path $LogFileLocation $scriptName
    $scriptNewLocation


    $VmToolsInfo=get-wmiobject Win32_Product -Filter "Name LIKE 'VMware Tools'"
    if ($VmToolsInfo -ne $null) {
        "Initializing vmware tools cleanup process"
        LogWrite "Vmware Tools found installed. Executing uninstall process"
        if ($scriptNewLocation -ne $MyInvocation.PSCommandPath) {
            LogWrite "Copying cleanup script to $LogFileLocation"
            Copy-Item  $MyInvocation.PSCommandPath -Destination $LogFileLocation
        }
        if ( Test-Path -Path $scriptNewLocation) {
            "Script found configuring runonce"
            #Set-ItemProperty "HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce" -Name 'VmToolsUninstall' -Value "c:\WINDOWS\system32\WindowsPowerShell\v1.0\powershell.exe -file $scriptNewLocation"
            $TaskTrigger = (New-ScheduledTaskTrigger -atstartup)
            $TaskAction = New-ScheduledTaskAction -Execute Powershell.exe -argument "-ExecutionPolicy Bypass -File $scriptNewLocation"
            $TaskUserID = New-ScheduledTaskPrincipal -UserId System -RunLevel Highest -LogonType ServiceAccount
            Register-ScheduledTask -Force -TaskName HeadlessRestartTask -Action $TaskAction -Principal $TaskUserID -Trigger $TaskTrigger

        }
        ExecuteCleanup
    }
    if ($MyInvocation.PSCommandPath -eq $scriptNewLocation) {
        "Script running in temp folder"
        if(!(Test-Path -Path "$scriptNewLocation.Run0")) {
            out-file -FilePath "$scriptNewLocation.Run0"
            ExecuteCleanup
            Unregister-ScheduledTask -TaskName "HeadlessRestartTask" -Confirm:$false
            DeleteVmFiles $MyInvocation.PSCommandPath
			LogWrite "$(get-date) Cleanup Process Completed - Restarting computer"
            Restart-Computer -force
        }
    }
}

function ExecuteCleanup () {
    UnregisterDLL
    ParseCLSID
    ParseTypeLibs
    ParseTypeLibsWow6432
    DeleteServicesViaSC
    RemoveVmwareRegistryEntries
    RemoveVmwareFiles
}
LogWrite "$(get-date) Starting Cleanup Process"
CheckVmToolsStatus
LogWrite "$(get-date) Cleanup Process Completed"