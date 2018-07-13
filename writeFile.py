import os
import asyncio
import time
import signalfx
import random
import uuid
import aiofiles
import pdb
import sys
import fcntl

'''
4 type of events
1) Current --> "same"
2) Bad Canary - only 1 change  --> "bcanary"
3) Good Canary - only 1 change  --> "gcanary"
4) Bad Canary -- rollback -- 3 new containers  --> "rollback"
5) Good Canary -- deploy -- 2 new containers  --> "deploy"
'''

usermap = {}

modifiedNames = {}

filepath = './userlist'

lastTime = 0

#defaultEventType = 'same'

def modifyFile(filepath,username,eventType):
  defaultEventType = 'same'

  lines = []

  with open(filepath, mode='r') as f:
    while True:
      try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lines = f.readlines()
        break
      except IOError as e:
        print ('Temporary locked or some other error: ',e)
        time.sleep(0.1)    
      finally:
        fcntl.flock(f, fcntl.LOCK_UN)

  d = {}
  #for line in lines:
  #  print('line is:',line)
  d = dict([line.split() for line in lines])     
  print ('old dict is: ',d)
  
  if username in d:
    d[username] = eventType
  else:  
    d[username] = defaultEventType
    
  print ('new dict is: ',d)

  writeToFile = ""
  lengthOfDict = len(d)
  iter = 1
  for key,value in d.items():
    if iter==lengthOfDict:
      writeToFile+=key+" "+value
    else:
      writeToFile+=key+" "+value+"\n"
    iter += 1

  with open(filepath, mode='w') as f:
    while True:
      try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(writeToFile)
        break
      except IOError as e:
        print ('Temporary locked or some other error: ',e)
        time.sleep(0.1)    
      finally:
        fcntl.flock(f, fcntl.LOCK_UN)


if __name__ == "__main__":  
  if len(sys.argv) != 3:
    print ('Something went wrong with the arguments, exiting ..')
    sys.exit(0)

  username = sys.argv[1]
  eventType = sys.argv[2]
  
  modifyFile(filepath,username,eventType)
