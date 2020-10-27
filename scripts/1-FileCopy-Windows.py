from __future__ import print_function
import sys
import argparse
import requests
import json
import subprocess
import getpass

with open('FactoryEndpoints.json') as json_file:
    endpoints = json.load(json_file)

serverendpoint = '/prod/user/servers'
appendpoint = '/prod/user/apps'

def Factorylogin(username, password, LoginHOST):
    login_data = {'username': username, 'password': password}
    r = requests.post(LoginHOST + '/prod/login',
                  data=json.dumps(login_data))
    if r.status_code == 200:
        print("Migration Factory : You have successfully logged in")
        print("")
        token = str(json.loads(r.text))
        return token
    if r.status_code == 502:
        print("ERROR: Incorrect username or password....")
        sys.exit(1)
    else:
        print(r.text)
        sys.exit(2)

def ServerList(waveid, token, UserHOST):
# Get all Apps and servers from migration factory
    auth = {"Authorization": token}
    servers = json.loads(requests.get(UserHOST + serverendpoint, headers=auth).text)
    #print(servers)
    apps = json.loads(requests.get(UserHOST + appendpoint, headers=auth).text)
    #print(apps)
    
    # Get App list
    applist = []
    for app in apps:
        if 'wave_id' in app:
            if str(app['wave_id']) == str(waveid):
                applist.append(app['app_id'])
    
    # Get Server List
    serverlist = []
    for app in applist:
        for server in servers:
            if app == server['app_id']:
                        if 'server_os' in server:
                                if 'server_fqdn' in server:
                                    if server['server_os'].lower() == "windows":
                                        serverlist.append(server['server_fqdn'])
                                else:
                                    print("ERROR: server_fqdn for server: " + server['server_name'] + " doesn't exist")
                                    sys.exit(4)
                        else:
                            print ('server_os attribute does not exist for server: ' + server['server_name'] + ", please update this attribute")
                            sys.exit(2)
                
    if len(serverlist) == 0:
        print("ERROR: Serverlist for wave: " + waveid + " is empty....")
        print("")
    else:
        print("successfully retrived server list")
        for s in serverlist:
            print(s)
        return serverlist

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--Waveid', required=True)
    parser.add_argument('--Source', required=True)
    parser.add_argument('--WindowsUser', default="")
    args = parser.parse_args(arguments)
    LoginHOST = endpoints['LoginApiUrl']
    UserHOST = endpoints['UserApiUrl']
    Domain_User = args.WindowsUser
    print("")
    print("****************************")
    print("*Login to Migration factory*")
    print("****************************")
    token = Factorylogin(input("Factory Username: ") , getpass.getpass('Factory Password: '), LoginHOST)

    print("****************************")
    print("*Getting Server List*")
    print("****************************")
    Servers = ServerList(args.Waveid, token, UserHOST)

    print("")
    print("*************************************")
    print("*Copying files to post_launch folder*")
    print("*************************************")

    if Domain_User != "":
        Domain_Password = getpass.getpass("Windows User Password: ")
    dest_path = "c:\\Program Files (x86)\\CloudEndure\\post_launch"
    for server in Servers:
        command1 = "Invoke-Command -ComputerName " + server + " -ScriptBlock {if (!(Test-path \"" + dest_path + "\")) {New-Item -Path \"" + dest_path + "\"  -ItemType directory}}"
        command2 = "Copy-Item \""+ args.Source  +"/*\" \"" + dest_path + "\" -ToSession (New-PSSession -ComputerName '"+ server  +"')"
        if Domain_User != "":
            command1 += " -Credential (New-Object System.Management.Automation.PSCredential('" + Domain_User + "', (ConvertTo-SecureString '" + Domain_Password + "' -AsPlainText -Force))) -Authentication Negotiate"
            command2 = "Copy-Item \""+ args.Source  +"/*\" \"" + dest_path + "\" -ToSession (New-PSSession -ComputerName '"+ server  +"'  -Authentication Negotiate -Credential (New-Object System.Management.Automation.PSCredential('" + Domain_User + "', (ConvertTo-SecureString '" + Domain_Password + "' -AsPlainText -Force))))"
        print("Copying files to server: " + server)
        p1 = subprocess.Popen(["pwsh", "-Command", command1], stdout=sys.stdout)
        p1.communicate()
        p2 = subprocess.Popen(["pwsh", "-Command", command2], stdout=sys.stdout)
        p2.communicate()

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
