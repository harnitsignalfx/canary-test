import os
import asyncio
import time
import signalfx
import random
import uuid
import aiofiles
import pdb
import sys

'''
4 type of events
1) Current --> "same"
2) Bad Canary - only 1 change  --> "bcanary"
3) Good Canary - only 1 change  --> "gcanary"
4) Bad Canary -- rollback -- 3 new containers  --> "rollback"
5) Good Canary -- deploy -- 2 new containers  --> "deploy"
'''

usermap = {}
hostmap = {}

filepath = './userlist'

lastTime = 0

loop = asyncio.get_event_loop()

globalDeployTypes = {}
globalIterNum = {}

if 'SF_TOKEN' in os.environ:
    print (os.environ['SF_TOKEN'])
else:
    print ('SF_TOKEN env variable not found')
    sys.exit(0)

token = os.environ['SF_TOKEN']
endpoint = 'https://mon-ingest.signalfx.com'

#sfx = signalfx.SignalFx().ingest(os.environ['SF_TOKEN'])
sfx = signalfx.SignalFx().ingest(token=token,endpoint=endpoint)

def incrementGlobalIterNum(key):
  global globalIterNum
  if key in globalIterNum:
    globalIterNum[key]=globalIterNum[key]+1
  else:
    globalIterNum[key]=1

def resetGlobalIterNum(key):
  if key in globalIterNum:
    globalIterNum[key]=0

async def get_modTime():
    global lastTime
    global globalDeployTypes

    while True:
        newTime = os.path.getmtime(filepath)
        if newTime > lastTime:
            lastTime = newTime
            print('File changed')

            lines = []
            async with aiofiles.open(filepath, mode='r') as f:
                lines = await f.readlines()
            newDeployTypes = {}

            #for line in lines:
            #  print('line is:',line)
            newDeployTypes = dict([line.split() for line in lines])

            print ('new Deploy Types:',newDeployTypes)

            if not globalDeployTypes:
              globalDeployTypes = newDeployTypes

            modifiedNames = {}
            global usermap
            global hostmap
            

            for key,value in newDeployTypes.items():
                if key not in usermap:
                  usermap[key]=[str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-','')]
                  hostmap[key]=[str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-','')]
                else:
                  if value != globalDeployTypes[key]:
                    modifiedNames[key] = value
                    globalDeployTypes[key] = value

                    if value == 'bcanary':
                      print ('in bcanary file check',usermap[key])
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                      hostmap[key][0] = '72498da78000'
                      incrementGlobalIterNum(key)
                    elif value == 'gcanary':
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                      hostmap[key][0] = '72498da78000'
                      resetGlobalIterNum(key)
                    elif value == 'rollback':
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                      hostmap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                      resetGlobalIterNum(key)
                    elif value == 'deploy':
                      usermap[key][1] = str(uuid.uuid4())[:13].replace('-','')
                      usermap[key][2] = str(uuid.uuid4())[:13].replace('-','')
                      hostmap[key][1] = str(uuid.uuid4())[:13].replace('-','')
                      hostmap[key][2] = str(uuid.uuid4())[:13].replace('-','')
                      resetGlobalIterNum(key)

                  print ('Modified Names:',modifiedNames)
                  modifiedNames = {}

        await asyncio.sleep(1)



def getTrendingRequestsProcessedValue(key):
  if not key in globalIterNum:
    incrementGlobalIterNum(key)
  if globalIterNum[key]<=10:
    return random.randint(900,1000)
  elif globalIterNum[key]>10:
    lowValue = round(1200/(1.04**globalIterNum[key]))
    highValue = round(1200/(1.04**(globalIterNum[key]-1)))
    print('lowValue:',lowValue,' highValue:',highValue)
    return random.randint(lowValue,highValue)

def getTrendingRequestsLatencyValue(key):
  if not key in globalIterNum:
    incrementGlobalIterNum(key)
  if globalIterNum[key]<=10:
    return random.randint(100,130)
  elif globalIterNum[key]>10:
    lowValue = round(globalIterNum[key]**2.08)
    highValue = round(globalIterNum[key]**2.08)
    print('lowValue:',lowValue,' highValue:',highValue)
    return random.randint(lowValue,highValue)


async def printList():
    try:
        metricName = 'requests.processed'
        latencyMetric = 'requests.latency'

        global usermap
        global globalDeployTypes

        iterationNum = 0

        while(True):
            startTime = int(round(time.time()*1000))
            
            sendList = []
            userData = {}

            while not usermap:
                print ('sleeping for 1 sec..')
                await asyncio.sleep(1)

            for user,data in usermap.items():
              userData1 = {}
              userData2 = {}
              userData3 = {}

              latencyData1 = {}
              latencyData2 = {}
              latencyData3 = {}


              dim1 = {}
              dim2 = {}
              dim3 = {}

              latencyDim1 = {}
              latencyDim2 = {}
              latencyDim3 = {}

              value1 = random.randint(900,1000)
              value2 = random.randint(900,1000)
              value3 = random.randint(900,1000)

              latencyValue1 = random.randint(80,130)
              latencyValue2 = random.randint(80,130)
              latencyValue3 = random.randint(80,130)

              if user in globalDeployTypes:
                #pdb.set_trace()
                if globalDeployTypes[user] == 'bcanary':
                  value1 = getTrendingRequestsProcessedValue(user)
                  latencyValue1 = getTrendingRequestsLatencyValue(user)
                  dim1['canary']='true'
                  latencyDim1['canary']='true'
                  print ('in bad canary for ',user)
                  incrementGlobalIterNum(user)
                elif globalDeployTypes[user] == 'gcanary':
                  dim1['canary']='true'
                  latencyDim1['canary']='true'
                  print ('in good canary for ',user)

              dim1['containerId']=usermap[user][0]
              dim1['host']=hostmap[user][0]
              dim1['user']=user
              latencyDim1['containerId']=usermap[user][0]
              latencyDim1['user']=user
              latencyDim1['customer']='Hooli'

              dim2['containerId']=usermap[user][1]
              dim2['host']=hostmap[user][1]
              dim2['user']=user
              latencyDim2['containerId']=usermap[user][1]
              latencyDim2['user']=user
              latencyDim2['customer']='Acme Corp'
              
              dim3['containerId']=usermap[user][2]
              dim3['host']=hostmap[user][2]
              dim3['user']=user
              latencyDim3['containerId']=usermap[user][2]
              latencyDim3['user']=user
              latencyDim3['customer']='Pied Piper'

              userData1['metric'] = metricName
              userData1['value'] = value1
              userData1['dimensions'] = dim1

              latencyData1['metric'] = latencyMetric
              latencyData1['value']=latencyValue1
              latencyData1['dimensions']=latencyDim1

              userData2['metric'] = metricName
              userData2['value'] = value2
              userData2['dimensions'] = dim2

              latencyData2['metric'] = latencyMetric
              latencyData2['value']=latencyValue2
              latencyData2['dimensions']=latencyDim2

              userData3['metric'] = metricName
              userData3['value'] = value3
              userData3['dimensions'] = dim3

              latencyData3['metric'] = latencyMetric
              latencyData3['value']=latencyValue3
              latencyData3['dimensions']=latencyDim3



              sendList.append(userData1)
              sendList.append(userData2)
              sendList.append(userData3)

              sendList.append(latencyData1)
              sendList.append(latencyData2)
              sendList.append(latencyData3)

            
            sfx.send(counters=sendList)
            #print('Sending..',sendList)
            endTime = int(round(time.time()*1000))
            delta = endTime-startTime

            if delta >= 1000:
              await asyncio.sleep(1)
            else:
              sleepTime = ((1000-delta)/1000)
              await asyncio.sleep(sleepTime)
    except:
        sfx.stop()
    finally:
        sfx.stop()

asyncio.ensure_future(get_modTime())
asyncio.ensure_future(printList())

content = loop.run_forever()
