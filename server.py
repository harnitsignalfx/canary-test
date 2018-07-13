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

@app.route('/hook', methods=['POST'])
def login():
    
    headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    data = json.loads(request.data)
    if 'event' in data:
        if "start" not in data['event']:
            send_event = {}
            send_event['category']='USER_DEFINED'
            send_event['eventType']='code_build_'+data['event']
            custom_data={'buildName':data['buildName'],'buildUrl':data['buildUrl']}
            send_event['properties']=custom_data
            send_event = [send_event]
            print (json.dumps(send_event,indent=2))
            r = requests.post('https://ingest.signalfx.com/v2/event',headers=headers,data=json.dumps(send_event))
            return(r.text)
    elif 'pusher' in data:
        send_event = {}
        send_event['category']='USER_DEFINED'
        send_event['eventType']='code_push'
        custom_data={'Pusher':data['pusher']['email']}
        send_event['properties']=custom_data
        send_event = [send_event]
        print (json.dumps(send_event,indent=2))   
        r = requests.post('https://ingest.signalfx.com/v2/event',headers=headers,data=json.dumps(send_event))
        return(r.text)
    else:
        print (data)
    return "OK"

@app.route('/write', methods=['POST'])
def write():
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}
    data = json.loads(request.data.decode('utf-8'))
    if ('messageBody' in data) and ('status' in data):
      if not (data['status'].lower()=='anomalous'):  
        # ..Do nothing.. the alert is back to normal
        return "OK"

      body = data['messageBody'].split(" ")
      if 'Rollback' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'rollback')
      elif 'Deployment' == body[1]:
        username = body[3]
        writeFile.modifyFile(filepath,username,'deploy')
    
    return "OK"

@app.route('/write/<string:username>/<int:batchsize>', methods=['POST'])
def writeSize(username,batchsize):
    
    #headers = {'X-SF-TOKEN' : os.environ['SF_TOKEN'],'Content-Type' : 'application/json'}

    print('Received - ',username,' ',batchsize)
    if batchsize > 30000:
      writeFile.modifyFile(filepath,username,'bcanary')
    else:
      writeFile.modifyFile(filepath,username,'gcanary')

    return "OK"    



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051)