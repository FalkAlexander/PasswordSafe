import pykeepass
from pykeepass import PyKeePass

kp = 0
group = 0

def readDB():
    global kp
    kp = PyKeePass('db.kdbx', password='654321')

def addGroup():
    global group
    group = kp.add_group(kp.root_group, 'total_wichtig')

def addEntry():
    kp.add_entry(group, 'hszg.de', 'kruhland', 'ichmagkernel')

def printGroup():
    print(group.entries)

def saveGroup():
    kp.save()

def changePassword():
    #kp = PyKeePass('db.kdbx', password='123456')
    readDB()
    kp.set_credentials("654321")
    saveGroup()
    #kp.save()
