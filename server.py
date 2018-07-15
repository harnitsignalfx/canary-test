from flask import Flask, request
import json
import requests
import os
import writeFile
import sys

app = Flask(__name__)

if 'SF_TOKEN' in os.environ:
    print (os.environ['SF_TOKEN'])
else:
    print ('SF_TOKEN env variable not found')
    sys.exit(0)

filepath = './userlist'

endpoint = 'https://mon-ingest.signalfx.com'
token = os.environ['SF_TOKEN']

@app.route('/health', methods=['POST'])
def healthCheck():
    '''Sends dummy event'''

    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    headers = {'X-SF-TOKEN' : token,'Content-Type' : 'application/json'}
    
    send_event = {}
    send_event['category']='USER_DEFINED'
    send_event['eventType']='Health Check'
    send_event['properties']={'status':'OK'}
    send_event = [send_event]
    print (json.dumps(send_event,indent=2))   
    r = requests.post(endpoint+'/v2/event',headers=headers,data=json.dumps(send_event))
    print(r.text)

    return "OK"

@app.route('/health/<string:username>', methods=['POST'])
def healthCheckWithUser(username):
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    headers = {'X-SF-TOKEN' : token,'Content-Type' : 'application/json'}
    print('Received Health Check for - ',username)

    send_event = {}
    send_event['category']='USER_DEFINED'
    send_event['eventType']='Health Check'
    send_event['properties']={'user':username,'status':'OK'}
    send_event = [send_event]
    print (json.dumps(send_event,indent=2))   
    r = requests.post(endpoint+'/v2/event',headers=headers,data=json.dumps(send_event))
    return(r.text)

    return "OK" 

@app.route('/write', methods=['POST'])
def write():
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    headers = {'X-SF-TOKEN' : token,'Content-Type' : 'application/json'}
    data = json.loads(request.data.decode('utf-8'))
    if ('messageBody' in data) and ('status' in data):
      if not (data['status'].lower()=='anomalous'):  
        # ..Do nothing.. the alert is back to normal
        return "OK"

      if not data['messageBody']:
        print('Empty message Body, returning..')
        return "OK"  
        
      body = data['messageBody'].split(" ")
      if 'Rollback' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'rollback')

        send_event = {}
        send_event['category']='USER_DEFINED'
        send_event['eventType']='Automated Rollback initiated'
        send_event['properties']={'user':username}
        send_event = [send_event]
        print (json.dumps(send_event,indent=2))   
        r = requests.post(endpoint+'/v2/event',headers=headers,data=json.dumps(send_event))
        print(r.text)

      elif 'Deployment' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'deploy')

        send_event = {}
        send_event['category']='USER_DEFINED'
        send_event['eventType']='Automated Deployment initiated'
        send_event['properties']={'user':username}
        send_event = [send_event]
        print (json.dumps(send_event,indent=2))   
        r = requests.post(endpoint+'/v2/event',headers=headers,data=json.dumps(send_event))
        print(r.text)
    
    return "OK"

@app.route('/write/<string:username>/<int:batchsize>', methods=['POST'])
def writeSize(username,batchsize):
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    headers = {'X-SF-TOKEN' : token,'Content-Type' : 'application/json'}
    print('Received - ',username,' ',batchsize)
    if batchsize > 30000:
      writeFile.modifyFile(filepath,username,'bcanary')
    else:
      writeFile.modifyFile(filepath,username,'gcanary')

    send_event = {}
    send_event['category']='USER_DEFINED'
    send_event['eventType']='canary push event'
    send_event['properties']={'user':username}
    send_event = [send_event]
    print (json.dumps(send_event,indent=2))   
    r = requests.post(endpoint+'/v2/event',headers=headers,data=json.dumps(send_event))
    return(r.text)

    return "OK"    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)
