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

filepath = './userlist'

lastTime = 0

loop = asyncio.get_event_loop()

globalDeployTypes = {}

if 'SF_TOKEN' in os.environ:
    print (os.environ['SF_TOKEN'])
else:
    print ('SF_TOKEN env variable not found')
    sys.exit(0)

sfx = signalfx.SignalFx().ingest(os.environ['SF_TOKEN'])

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

            for key,value in newDeployTypes.items():
                if key not in usermap:
                  usermap[key]=[str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-','')]
                else:
                  if value != globalDeployTypes[key]:
                    modifiedNames[key] = value
                    globalDeployTypes[key] = value

                    if value == 'bcanary':
                      print ('in bcanary file check',usermap[key])
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                    elif value == 'gcanary':
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                    elif value == 'rollback':
                      usermap[key][0] = str(uuid.uuid4())[:13].replace('-','')
                    elif value == 'deploy':
                      usermap[key][1] = str(uuid.uuid4())[:13].replace('-','')
                      usermap[key][2] = str(uuid.uuid4())[:13].replace('-','')

                  print ('Modified Names:',modifiedNames)
                  modifiedNames = {}

            #print ('usermap:',usermap)

            #print ('Modified Names:',modifiedNames)

        await asyncio.sleep(1)


async def printList():
    try:
        metricName = 'requests.processed'
        global usermap
        global globalDeployTypes
        timestamp = int(round(time.time())*1000)+1

        while(True):
            #user = "harnit.singh@signalfx.com"
            startTime = int(round(time.time()*1000))
            
            sendList = []
            userData = {}
            #print ('usermap-',usermap)

            while not usermap:
                print ('sleeping for 1 sec..')
                await asyncio.sleep(1)

            for user,data in usermap.items():
              userData1 = {}
              userData2 = {}
              userData3 = {}
              dim1 = {}
              dim2 = {}
              dim3 = {}

              value1 = random.randint(900,1000)
              value2 = random.randint(900,1000)
              value3 = random.randint(900,1000)

              if user in globalDeployTypes:
                #global value1
                #pdb.set_trace()
                if globalDeployTypes[user] == 'bcanary':
                  value1 = random.randint(200,300)
                  dim1['canary']='true'
                  print ('in bad canary for ',user)
                elif globalDeployTypes[user] == 'rollback':
                  value1 = random.randint(900,1000)
                elif globalDeployTypes[user] == 'gcanary':
                  dim1['canary']='true'
                  print ('in good canary for ',user)

              dim1['containerId']=usermap[user][0]
              dim1['user']=user
              dim2['containerId']=usermap[user][1]
              dim2['user']=user
              dim3['containerId']=usermap[user][2]
              dim3['user']=user

              userData1['metric'] = metricName
              userData1['value'] = value1
              #userData1['timestamp'] = timestamp
              userData1['dimensions'] = dim1

              userData2['metric'] = metricName
              userData2['value'] = value2
              #userData2['timestamp'] = timestamp
              userData2['dimensions'] = dim2

              userData3['metric'] = metricName
              userData3['value'] = value3
              #userData3['timestamp'] = timestamp
              userData3['dimensions'] = dim3

              sendList.append(userData1)
              sendList.append(userData2)
              sendList.append(userData3)

            
            sfx.send(counters=sendList)
            #print ('sending..',sendList)
            endTime = int(round(time.time()*1000))
            delta = endTime-startTime
            #print ('delta - ',delta)
            timestamp += 1000

            if delta > 1000:
              await asyncio.sleep(1)
            else:
              sleepTime = ((1000-delta)/1000)
              #print('sleeping for ..',sleepTime)
              await asyncio.sleep(sleepTime)
    except:
        sfx.stop()
    finally:
        sfx.stop()

asyncio.ensure_future(get_modTime())
asyncio.ensure_future(printList())

content = loop.run_forever()
