from __future__ import print_function
import sys
import argparse
import requests
import json
import csv
import getpass
import os

serverendpoint = '/prod/user/servers'

def get_reader(file):
    ordered_dict_list = []
    input_file = csv.DictReader(open(file))
    for row in input_file:
        ordered_dict_list.append(row)
    # return input_file
    return ordered_dict_list

def data_validation(data, servers):
    # Validate if Name column exist
    keys = data[0].keys()
    if "Name" not in keys:
        print ("ERROR: 'Name' column is mandatory")
        sys.exit(3)
    # check if none value exist
    for row in data:
        for key in keys:
            if key not in row:
               print("ERROR: "+ key + " tag value is missing for server " + row['Name'])
               sys.exit(4)
            if row[key] == None:
               print("ERROR: "+ key + " tag value is missing for server " + row['Name'])
               sys.exit(6)
            if row[key] == row[key].strip() == "":
               print("ERROR: "+ key + " tag for server " + row['Name'] + " is empty")
               sys.exit(7)
    # Validate duplicate server names in csv file
    server_list = []
    for row in data:
        if row['Name'].strip().lower() not in server_list:
            server_list.append(str(row['Name']).strip().lower())
        else:
            print("ERROR: Duplicated Server Name: " + row['Name'])
            sys.exit(2)
    # Check if server exist in the migration factory
    for server in server_list:
        match = False
        for s in servers:
            if (server.lower() == s['server_name'].lower()):
                match = True
        if (match == False):
            print("ERROR: Server " + server + " doesn't exist in the migration factory")
            sys.exit(1)


def uploading_data(data, token):
    keys = data[0].keys()
    auth = {"Authorization": token}
    servers = json.loads(requests.get(UserHOST + serverendpoint, headers=auth).text)
    data_validation(data, servers)
    for row in data:
        update_server_tags = {}
        tags = []
        server_id = ""
        for server in servers:
            if row['Name'].strip().lower() == server['server_name'].strip().lower():
                server_id = server["server_id"]
                for key in keys:
                    tag = {}
                    tag['key'] = key
                    tag['value'] = row[key].strip()
                    tags.append(tag)
        update_server_tags['tags'] = tags
        r = requests.put(UserHOST + serverendpoint + '/' + server_id, headers=auth, data=json.dumps(update_server_tags))
        if r.status_code == 200:
           print("Tags for server " + row['Name'] + " updated in the migration factory")
        else:
           print("ERROR: updating tags for server " + row['Name'] + " failed : " + r.text + ".......")
                
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
        sys.exit(5)

def main(arguments):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--Intakeform', required=True)
    parser.add_argument('--EndpointConfigFile', default = os.environ.get('MF_ENDPOINT_CONFIG_FILE', 'FactoryEndpoints.json'), help= "This can also be set in environment variable MF_ENDPOINT_CONFIG_FILE")
    args = parser.parse_args(arguments)

    with open('FactoryEndpoints.json') as json_file:
      endpoints = json.load(json_file)

    global LoginHOST, UserHOST
    LoginHOST = endpoints['LoginApiUrl']
    UserHOST = endpoints['UserApiUrl']


    print("****************************")
    print("*Login to Migration factory*")
    print("****************************")
    if 'MF_USERNAME' not in os.environ:
        username = input('Factory Username: ')
    else:
        username = os.getenv('MF_USERNAME')
    if 'MF_PASSWORD' not in os.environ:
        password = getpass.getpass('Factory Password: ')
    else:
        password = os.getenv('MF_PASSWORD')

    token = Factorylogin(username, password, LoginHOST)

    print("****************************")
    print("*  Reading Tags form List  *")
    print("****************************")
    data = get_reader(args.Intakeform)
    print("Tags loaded for processing....")
    print("")

    print("*********************************************")
    print("*   Updating tags in the migration factory  *")
    print("*********************************************")

    r = uploading_data(data,token)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
