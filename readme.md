# CUCM Integration
This enables the functionality of monitoring CUCM and reporting that data into AppDynamics.

## Pre-Requisites
- Python 3.x
- PIP Packages:
	- requests
## Installation Steps:
1. Download and place the files into any of the following servers:
- PG
- AW
- HDS
- CVP
2. Place the files into the Machine Agent/monitors directory.  Example: ```C:\AppDynamics\MachineAgent\monitors\cucm\```
3. Run the setup.ps1 file to provide the following details:
- CUCM URL
- CUCM Username
- CUCM Password
- CUCM Hosts
4. Once the setup is complete, give it a few minutes and there should be data reporting into the controller.
