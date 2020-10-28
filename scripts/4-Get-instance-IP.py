from __future__ import print_function
import sys
import argparse
import requests
import json
import boto3
import getpass
import datetime
import csv
import os

HOST = 'https://console.cloudendure.com'
headers = {'Content-Type': 'application/json'}
session = {}
endpoint = '/api/latest/{}'

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
    else:
        print("ERROR: Incorrect username or password....")
        print("")
        sys.exit(1)

def CElogin(userapitoken, endpoint):
    login_data = {'userApiToken': userapitoken}
    r = requests.post(HOST + endpoint.format('login'),
                  data=json.dumps(login_data), headers=headers)
    if r.status_code == 200:
        print("CloudEndure : You have successfully logged in")
        print("")
    if r.status_code != 200 and r.status_code != 307:
        if r.status_code == 401 or r.status_code == 403:
            print('ERROR: The CloudEndure login credentials provided cannot be authenticated....')
        elif r.status_code == 402:
            print('ERROR: There is no active license configured for this CloudEndure account....')
        elif r.status_code == 429:
            print('ERROR: CloudEndure Authentication failure limit has been reached. The service will become available for additional requests after a timeout....')
    
    # check if need to use a different API entry point
    if r.history:
        endpoint = '/' + '/'.join(r.url.split('/')[3:-1]) + '/{}'
        r = requests.post(HOST + endpoint.format('login'),
                      data=json.dumps(login_data), headers=headers)
                      
    session['session'] = r.cookies['session']
    try:
       headers['X-XSRF-TOKEN'] = r.cookies['XSRF-TOKEN']
    except:
       pass

def GetCEProject(projectname, session, headers, endpoint, HOST):
    r = requests.get(HOST + endpoint.format('projects'), headers=headers, cookies=session)
    if r.status_code != 200:
        print("ERROR: Failed to fetch the project....")
        sys.exit(2)
    try:
        # Get Project ID
        project_id = ""
        projects = json.loads(r.text)["items"]
        project_exist = False
        for project in projects:
            if project["name"] == projectname:
               project_id = project["id"]
               project_exist = True
        if project_exist == False:
            print("ERROR: Project Name does not exist in CloudEndure....")
            sys.exit(3)
        return project_id
    except:
        print("ERROR: Failed to fetch the project....")
        sys.exit(4)

def GetRegion(project_id):
    rep = requests.get(HOST + endpoint.format('projects/{}/replicationConfigurations').format(project_id), headers=headers, cookies=session)
    region = requests.get(HOST + endpoint.format('cloudCredentials/{}/regions/{}').format(json.loads(rep.text)['items'][0]['cloudCredentials'], json.loads(rep.text)['items'][0]['region']), headers=headers, cookies=session)
    name = json.loads(region.text)['name']
    region_code = ""
    if "Northern Virginia" in name:
        region_code = 'us-east-1'
    elif "Frankfurt" in name:
        region_code = 'eu-central-1'
    elif "Paris" in name:
        region_code = 'eu-west-3'
    elif "Stockholm" in name:
        region_code = 'eu-north-1'
    elif "Northern California" in name:
        region_code = 'us-west-1'
    elif "Oregon" in name:
        region_code = 'us-west-2'
    elif "AWS GovCloud (US)" in name:
        region_code = 'us-gov-west-1'
    elif "Bahrain" in name:
        region_code = 'me-south-1'
    elif "Hong Kong" in name:
        region_code = 'ap-east-1'
    elif "Tokyo" in name:
        region_code = 'ap-northeast-1'
    elif "Singapore" in name:
        region_code = 'ap-southeast-1'
    elif "AWS GovCloud (US-East)" in name:
        region_code = 'us-gov-east-1'
    elif "Mumbai" in name:
        region_code = 'ap-south-1'
    elif "South America" in name:
        region_code = 'sa-east-1'
    elif "Sydney" in name:
        region_code = 'ap-southeast-2'
    elif "London" in name:
        region_code = 'eu-west-2'
    elif "Central" in name:
        region_code = 'ca-central-1'
    elif "Ireland" in name:
        region_code = 'eu-west-1'
    elif "Seoul" in name:
        region_code = 'ap-northeast-2'
    elif "Ohio" in name:
        region_code = 'us-east-2'
    else:
        print("Incorrect Region Name")
        sys.exit(7)
    return region_code

def GetServerList(projectname, waveid, token):
    try:
        # Get all Apps and servers from migration factory
        auth = {"Authorization": token}
        servers = json.loads(requests.get(UserHOST + serverendpoint, headers=auth).text)
        apps = json.loads(requests.get(UserHOST + appendpoint, headers=auth).text)

        # Get App list
        applist = []
        for app in apps:
            if 'wave_id' in app and 'cloudendure_projectname' in app:
                if str(app['wave_id']) == str(waveid) and str(app['cloudendure_projectname']) == str(projectname):
                    applist.append(app['app_id'])
        # Get Server List
        serverlist = []
        for app in applist:
            for server in servers:
                if "app_id" in server:
                    if app == server['app_id']:
                        serverlist.append(server)
        if len(serverlist) == 0:
            print("ERROR: Serverlist for wave " + waveid + " in Migration Factory is empty....")
            sys.exit(5)
        return serverlist
    except:
        print("ERROR: Getting server list failed....")
        sys.exit(6)

def GetInstanceId(project_id, serverlist, session, headers, endpoint, HOST, token):
        # Get Machine List from CloudEndure
        m = requests.get(HOST + endpoint.format('projects/{}/machines').format(project_id), headers=headers, cookies=session)
        if "sourceProperties" not in m.text:
            print("ERROR: Failed to fetch the machines....")
            sys.exit(11)
        InstanceList = []
        for s in serverlist:
            for machine in json.loads(m.text)["items"]:
                if s['server_name'].lower() == machine['sourceProperties']['name'].lower():
                    if 'replica' in machine:
                        if machine['replica'] != '':
                            InstanceInfo = {}
                            # print(machine['replica'])
                            target_replica = requests.get(HOST + endpoint.format('projects/{}/replicas').format(project_id) + '/' + machine['replica'], headers=headers, cookies=session)
                            # print(json.loads(target_replica.text))
                            InstanceInfo['InstanceName'] = machine['sourceProperties']['name'].lower()
                            InstanceInfo['InstanceId'] = json.loads(target_replica.text)['machineCloudId']
                            InstanceInfo["lifeCycle"] = machine["lifeCycle"]
                            InstanceList.append(InstanceInfo)
                    else:
                        print("ERROR: Target instance doesn't exist for machine: " + machine['sourceProperties']['name'])
                        sys.exit(12)
        return InstanceList

def get_instance_ips(InstanceList, serverlist, token, access_key_id, secret_access_key, region_id, waveid, projectname):
        print("")
        auth = {"Authorization": token}
        ec2_client = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region_id)
        instanceIds = []
        for instance in InstanceList:
            instanceIds.append(instance['InstanceId'])
        resp = ec2_client.describe_instances(InstanceIds=instanceIds)
        all_instance_ips = []
        for r in resp['Reservations']:
            for instance in r['Instances']:
                instance_ips = {}
                instance_name = ""
                ips = ""
                name_exist = False
                for tag in instance['Tags']:
                    if tag['Key'] == "Name":
                        if tag['Value'] != "":
                            instance_name = tag['Value']
                            name_exist = True
                if name_exist == False:
                    print("ERROR: Name Tag does not exist for instance " + instance['InstanceId'])
                    sys.exit(7)
                for nic in instance['NetworkInterfaces']:
                     for ip in nic['PrivateIpAddresses']:
                         ips = ips + ip['PrivateIpAddress'] + ","
                instance_ips['instance_name'] = instance_name
                instance_ips['instance_ips'] = ips[:-1]
                all_instance_ips.append(instance_ips)
        filename = "Wave" + waveid + "-" + projectname + "-IPs.csv"
        print("*** Exporting Instance IPs to " + filename + " ***")
        with open(filename, "w", newline='') as csvfile:
            writer = csv.DictWriter(csvfile, all_instance_ips[0].keys())
            writer.writeheader()
            writer.writerows(all_instance_ips)

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--CloudEndureProjectName', required=True)
    parser.add_argument('--Waveid', required=True)
    parser.add_argument('--EndpointConfigFile', default = os.environ.get('MF_ENDPOINT_CONFIG_FILE', '/etc/migration_factory/endpoints.json'), help= "This can also be set in environment variable MF_ENDPOINT_CONFIG_FILE")
    args = parser.parse_args(arguments)

    with open(args.EndpointConfigFile) as json_file:
      endpoints = json.load(json_file)

    global LoginHOST, UserHOST
    LoginHOST = endpoints['LoginApiUrl']
    UserHOST = endpoints['UserApiUrl']

    print("******************************")
    print("* Login to Migration factory *")
    print("******************************")
    if 'MF_USERNAME' not in os.environ:
        username = input('Factory Username: ')
    else:
        username = os.getenv('MF_USERNAME')
    if 'MF_PASSWORD' not in os.environ:
        password = getpass.getpass('Factory Password: ')
    else:
        password = os.getenv('MF_PASSWORD')

    token = Factorylogin(username, password, LoginHOST)

    print("")
    print("************************")
    print("* Login to CloudEndure *")
    print("************************")
    if 'MF_CE_API_TOKEN' not in os.environ:
        ce_api_token = input('CE API Token: ')
    else:
        ce_api_token = os.getenv('MF_CE_API_TOKEN')

    r = CElogin(ce_api_token, endpoint)
    if r is not None and "ERROR" in r:
        print(r)
    project_id = GetCEProject(args.CloudEndureProjectName, session, headers, endpoint, HOST)
    region_id = GetRegion(project_id)

    print("***********************")
    print("* Getting Server List *")
    print("***********************")

    serverlist = GetServerList(args.CloudEndureProjectName, args.Waveid, token)
    for server in serverlist:
        print(server['server_name'])
    print("")

    print("******************************")
    print("* Getting Target Instance Id *")
    print("******************************")

    InstanceList = GetInstanceId(project_id, serverlist, session, headers, endpoint, HOST, token)
    for instance in InstanceList:
        print(instance['InstanceName'] + " : " + instance['InstanceId'])
    print("")
    print("*****************************")
    print("* Get target Instance  IPs *")
    print("*****************************")
    if 'MF_AWS_ACCESS_KEY_ID' not in os.environ:
        aws_access_key_id = input("AWS Access key id: ")
    else:
        aws_access_key_id = os.getenv('MF_AWS_ACCESS_KEY_ID')
    if 'MF_AWS_SECRET_ACCESS_KEY' not in os.environ:
        aws_secret_acess_key = getpass.getpass('Secret access key: ')
    else:
        aws_secret_acess_key = os.getenv('MF_AWS_SECRET_ACCESS_KEY')

    get_instance_ips(InstanceList, serverlist, token, aws_access_key_id, aws_secret_acess_key, region_id, args.Waveid, args.CloudEndureProjectName)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
