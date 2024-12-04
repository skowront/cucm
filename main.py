import configparser
import requests
import os
import xml.etree.ElementTree as ET
from urllib3.exceptions import InsecureRequestWarning

def parse_host_list(value):
    value = value.strip('[]')
    return [host.strip() for host in value.split(',')]

def parse_config_list(value):
    return [metric.strip() for metric in value.strip().splitlines()]

def readConfig():
    config = configparser.ConfigParser()
    config.read("conf/config.ini")

    url = config["CUCM"]["url"]
    secret = config["CUCM"]["secret"]
    servers = parse_host_list(config["SERVERS"]["hosts"])
    return(url,secret,servers)

def readInfra():
    config = configparser.ConfigParser(interpolation=None)
    config.read("bin/infra.conf")

    cpu = parse_config_list(config["CPU"]["session"])
    memory = parse_config_list(config["MEMORY"]["session"])
    network = parse_config_list(config["NETWORK"]["session"])

    return(cpu,memory,network)

def readPerfList():
    config = configparser.ConfigParser()
    config.read("bin/infra.conf")

    perfmon = config["CPU"]["perfmonListInstance"]

    return(perfmon)

def openSession(cucm, auth):
    headers = {
        'Authorization':'Basic '+auth+'',
        'Content-Type':'text/xml'
    }

    data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Header/><soapenv:Body><soap:perfmonOpenSession/></soapenv:Body></soapenv:Envelope>'

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(cucm+'perfmonservice2/services/PerfmonService?wsdl', verify=False, headers=headers, data=data)
    print(r.content)
    print(r.status_code)
    response = ET.fromstring(r.content)
    session_id = response.find(".//{http://schemas.cisco.com/ast/soap}perfmonOpenSessionReturn").text
    return(session_id)

def collectData(cucm, auth, session, flags):
    headers = {
        'Authorization':'Basic '+auth+'',
        'Content-Type':'text/xml'
    }

    data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Header/><soapenv:Body><soap:perfmonCollectSessionData><soap:SessionHandle>'+session+'</soap:SessionHandle></soap:perfmonCollectSessionData></soapenv:Body></soapenv:Envelope>'

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(cucm+'perfmonservice2/services/PerfmonService?wsdl', verify=False, headers=headers, data=data)
    # print(r.status_code)
    if flags == "check":
        if r.status_code != 200:
            return False
        else: return True

def checkSession(cucm, auth):
    if os.path.exists("bin/session"):
        with open("bin/session", "r") as file:
            session_id = file.read()
            # print("Session ID:"+session_id)
            exists = collectData(cucm, auth, session_id, "check")
            if not exists:
                session_id = openSession(cucm, auth)
                init = True
                with open("bin/session", "w") as file:
                    # Write content to the file
                    file.write(session_id)
            else: init = False
    else:
        session_id = openSession(cucm, auth)
        init = True
        with open("bin/session", "w") as file:
            # Write content to the file
            file.write(session_id)

    return session_id, init

def addCounters(cucm, auth, session, metric):
    headers = {
        'Authorization':'Basic '+auth+'',
        'Content-Type':'text/xml'
    }

    data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Header/><soapenv:Body><soap:perfmonAddCounter><soap:SessionHandle>'+session+'</soap:SessionHandle><soap:ArrayOfCounter><soap:Counter><soap:Name>'+metric+'</soap:Name></soap:Counter></soap:ArrayOfCounter></soap:perfmonAddCounter></soapenv:Body></soapenv:Envelope>'

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(cucm+'perfmonservice2/services/PerfmonService?wsdl', verify=False, headers=headers, data=data)

def getCounters(cucm, auth, session):
    headers = {
        'Authorization':'Basic '+auth+'',
        'Content-Type':'text/xml'
    }

    data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Header/><soapenv:Body><soap:perfmonCollectSessionData><soap:SessionHandle>'+session+'</soap:SessionHandle></soap:perfmonCollectSessionData></soapenv:Body></soapenv:Envelope>'

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(cucm+'perfmonservice2/services/PerfmonService?wsdl', verify=False, headers=headers, data=data)
    response = ET.fromstring(r.content)

    return (response)

def parseCounters(x):
    # Find all 'perfmonCollectSessionDataReturn' elements
    data_elements = x.findall('.//ns1:perfmonCollectSessionDataReturn', namespaces={'ns1': 'http://schemas.cisco.com/ast/soap'})

    # Extract memory usage data
    data = {}
    for element in data_elements:
      name_element = element.find('ns1:Name', namespaces={'ns1': 'http://schemas.cisco.com/ast/soap'})
      value_element = element.find('ns1:Value', namespaces={'ns1': 'http://schemas.cisco.com/ast/soap'})

      if name_element is not None and value_element is not None:
        # Extract name and value
        name = name_element.text
        value = value_element.text

        data[name] = value
    return (data)

def getPerf(cucm, auth, host, metric):
    headers = {
        'Authorization':'Basic '+auth+'',
        'Content-Type':'text/xml'
    }

    data = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:soap="http://schemas.cisco.com/ast/soap"><soapenv:Header/><soapenv:Body><soap:perfmonListInstance><soap:Host>'+host+'</soap:Host><soap:Object>'+metric+'</soap:Object></soap:perfmonListInstance></soapenv:Body></soapenv:Envelope>'

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    r = requests.post(cucm+'perfmonservice2/services/PerfmonService?wsdl', verify=False, headers=headers, data=data)
    response = ET.fromstring(r.content)
    return (response)

def parsePerf(x):
    # Find all 'perfmonListInstanceReturn' elements
    data_elements = x.findall('.//ns1:perfmonListInstanceReturn', namespaces={'ns1': 'http://schemas.cisco.com/ast/soap'})

    # Extract instance names
    instance_names = []
    for element in data_elements:
      name_element = element.find('ns1:Name', namespaces={'ns1': 'http://schemas.cisco.com/ast/soap'})
      if name_element is not None:
        if "Total" not in name_element.text:
            instance_names.append(name_element.text)
    return(len(instance_names))

def printInfraData(x, y):
    ext = "name=Custom Metrics|CUCM|"
    value = ",value="
    if "" == y:
        for i in x:
            if "Processor" in i:
                print(ext+i.split("\\")[2]+"|"+"CPU|"+i.split("\\")[-1]+value+x[i])
            elif "Memory" in i:
                print(ext+i.split("\\")[2]+"|"+"Memory|"+i.split("\\")[-1]+value+x[i])
            elif "Network" in i:
                print(ext+i.split("\\")[2]+"|"+"Network|"+i.split("\\")[-1]+value+x[i])
    else:
        if x != 0:
            print(ext+y+"|"+"CPU|Core Count"+value+str(x))

try:
    cucm_url, cucm_secret, cucm_hosts = readConfig()
except:
    print("Please run the 'setup.ps1' or 'setup.sh' script to setup the configuration.")
    exit(1)
# print(cucm_url)
# print(cucm_secret)
# print(cucm_hosts)
session_id, init = checkSession(cucm_url, cucm_secret)
# print("Session ID:"+session_id)
basecpu, basememory, basenetwork = readInfra()
# init = True
metrics = {}
if init:
    for h in cucm_hosts:
        metrics[h] = {}
        metrics[h]["CPU"] = {}
        metrics[h]["MEMORY"] = {}
        metrics[h]["NETWORK"] = {}
        for i in basecpu:
            addCounters(cucm_url, cucm_secret, session_id, i.replace("<SERVER>", h))
            metrics[h]["CPU"][i.split("\\")[-1]] = 0
        for i in basememory:
            addCounters(cucm_url, cucm_secret, session_id, i.replace("<SERVER>", h))
            metrics[h]["MEMORY"][i.split("\\")[-1]] = 0
        for i in basenetwork:
            addCounters(cucm_url, cucm_secret, session_id, i.replace("<SERVER>", h))
            metrics[h]["NETWORK"][i.split("\\")[-1]] = 0

perfList = readPerfList()
for h in cucm_hosts:
    r = getPerf(cucm_url, cucm_secret, h, perfList)
    d = parsePerf(r)
    printInfraData(d, h)
root = getCounters(cucm_url, cucm_secret, session_id)
data = parseCounters(root)
printInfraData(data, "")
