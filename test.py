import os
import asyncio
import time
import signalfx
import random
import uuid
import aiofiles

'''
4 type of events
1) Current --> "same"
2) Canary - only 1 change  --> "canary"
3) Bad Canary -- rollback -- 3 new containers  --> "rollback"
4) Good Canary -- deploy -- 2 new containers  --> "deploy"
'''

usermap = {
    "harnit.singh@signalfx.com" : ["a34e8259d629","df3f864ef497","4f67d6a18a74"]
}

filepath = './userlist'

lastTime = 0

loop = asyncio.get_event_loop()

sfx = signalfx.SignalFx().ingest('wta2iie_kkg2S7ocivcN6g')

async def get_modTime():
    global lastTime

    while True:
        newTime = os.path.getmtime(filepath)
        if newTime > lastTime:
            lastTime = newTime
            print('File changed')

            lines = []
            async with aiofiles.open(filepath, mode='r') as f:
                lines = await f.readlines()
            d = {}
            #for line in lines:
            #  print('line is:',line)
            d = dict([line.split() for line in lines])

            print ('old dict is:',d)
            modifiedNames = {}
            for key,value in d.items():
                if value != 'same':
                    modifiedNames[key] = value
                    
            print ('Modified Names:',modifiedNames)

            usermap["harnit.singh@signalfx.com"]=[str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-',''),str(uuid.uuid4())[:13].replace('-','')]
        await asyncio.sleep(1)


async def printList():
    try:
        while(True):
            user = "harnit.singh@signalfx.com"
            '''
            sfx.send(counters=[
              {'metric': 'documents.processed',
              'value': random.randint(900,1000),
              'timestamp':int(round(time.time()*1000)),
              'dimensions': {'containerId': usermap[user][0],'user': user}
              },
              {'metric': 'documents.processed',
              'value': random.randint(900,1000),
              'timestamp':int(round(time.time()*1000)),
              'dimensions': {'containerId': usermap[user][1],'user': user}
              },
              {'metric': 'documents.processed',
              'value': random.randint(900,1000),
              'timestamp':int(round(time.time()*1000)),
              'dimensions': {'containerId': usermap[user][2],'user': user}
              }
            ])
            '''
            print ('sending..')
            await asyncio.sleep(1)
    except:
        sfx.stop()
    finally:
        sfx.stop()

asyncio.ensure_future(get_modTime())
asyncio.ensure_future(printList())

content = loop.run_forever()