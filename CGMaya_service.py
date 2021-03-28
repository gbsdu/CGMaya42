
#coding=utf-8
import urllib
import urllib2
import cookielib
import time
import CGMaya_config
import CGMaya_logger
import zipfile
import os
import json
import sys

import inspect
filename = inspect.getframeinfo(inspect.currentframe()).filename
path = os.path.dirname(os.path.abspath(filename))
sys.path.append(path)

from pymongo import MongoClient
from gridfs import *
from bson import ObjectId
import bson.binary
from cStringIO import StringIO
import ipfsapi
import shutil
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.cmds as cmds
import pymel.core
import random



monthInfo = {u'一月': 'January', u'二月': 'February', u'三月': 'March', u'四月':'April', 
                u'五月': 'May', u'六月': 'June', u'七月': 'July', u'八月': 'Aguest', 
                u'九月': 'September', u'十月': 'October', u'十一月': 'November', u'十二月': 'December'}

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def objectIDToUnicode(id):
    if isinstance(id, ObjectId):
        #str = JSONEncoder().encode(id)
        return id.decode('utf8')
    else:
        return id

class CGService():
    def __init__(self):
        self.teamList = []
        self.myDAMURL = ''

    def send_server(self, path, params={}, bjwt=True):
        if bjwt:
            headers = {'Authorization': 'JWT ' + CGMaya_config.userToken['token']}
        else:
            headers = {'Content-Type': 'Application/json'}
        url = CGMaya_config.myRootURL + path
        try:
            data = urllib.urlencode(params)
            req = urllib2.Request(url, data, headers)
            result_data = urllib2.urlopen(req)
            result = result_data.read()
            result_data.close()
            return json.loads(result)
        except urllib2.HTTPError, e:
            print('url =', url, e)
            return '0'
        except urllib2.URLError, e:
            print('url =', url, e)
            return '1'

    def send(self, url, params={}):
        headers = {'Authorization': 'JWT ' + CGMaya_config.userToken['teamToken']}
        try:
            data = urllib.urlencode(params)
            req = urllib2.Request(self.myDAMURL + url, data, headers)
            result_data = urllib2.urlopen(req)
            result = result_data.read()
            result_data.close()
            return json.loads(result)
        except urllib2.HTTPError, e:
            print('url =', url, e)
            return '0'
        except urllib2.URLError, e:
            print('url =', url, e)
            return '1'

    def testConnection(self):
        status, result = self.getAllTeams()
        if not status:
            return result
        else:
            return ''

    def getAllTeams(self):
        if self.teamList:
            return True, self.teamList
        result = self.send_server('/cgserver/getAllTeams', {}, False)
        if result['status'] == 1:
            return False, result['message']
        else:
            self.teamList = result['team']
            return True, result['team']

    def login(self, name, password, teamName):
        headers = {'Content-Type': 'Application/json'}
        data = json.dumps({'username': name, 'password': password, 'team': teamName})
        try:
            req = urllib2.Request(CGMaya_config.myRootURL + '/cgserver/login', data, headers)
            result_data = urllib2.urlopen(req)
            result = json.loads(result_data.read())
            result_data.close()
            if result['status'] != 0:
                return result['message']
            CGMaya_config.userToken = result
            CGMaya_config.teamInfo = CGMaya_config.userToken['team']
            self.myDAMURL = CGMaya_config.teamInfo['apiUrl']
            CGMaya_config.userRole = result['user']['role']
            CGMaya_config.userAlias = result['user']['alias']
            return ''
        except urllib2.HTTPError, e:
            return e
        except urllib2.URLError, e:
            return e

    def getTeamInfo(self, teamName):
        if not self.teamList:
            result = self.send_server('/cgserver/getAllTeams', {}, False)
            if result['status'] == 1:
                return {}
            else:
                self.teamList = result['team']
        for team in self.teamList:
            if team['name'] == teamName:
                return team
        return {}

    def userActionLog(self, user, projectName, sceneName, taskID, action):
        count = CGMaya_config.mouseCount
        return self.send('/cgteam/userActionLog', {'user': user, 'taskID': taskID, 'mouseCount': count,
                             'projectName': projectName, 'taskName': sceneName, 'action': action})

    def getSoftwareInfo(self, softwareName):
        return self.send_server('/cgserver/getSoftwareInfo', {'name': softwareName})

    def getSoftwareInfoByID(self, softwareID):
        soft = self.send_server('/cgserver/getSoftwareConfigInfo', {})
        client = MongoClient(soft['url'])
        db = client[soft['DBName']]
        fs = GridFS(db, collection='software')
        file = fs.find_one({"_id": ObjectId(softwareID)})
        return file

    def getSoftware(self, localFile, fileID):
        if CGMaya_config.softInfo == {}:
            CGMaya_config.softInfo = self.send_server('/cgserver/getSoftwareConfigInfo', {})
        client = MongoClient(CGMaya_config.softInfo['url'])
        db = client[CGMaya_config.softInfo['DBName']]
        fs = GridFS(db, collection='software')
        with open(localFile, "wb") as f:
            with fs.get(ObjectId(fileID)) as fd:
                for line in fd:
                    f.write(line)
        f.close()

    def getMyTask(self, user):
        return self.send('/cgteam/getMyTasks', {'user': user})

    def getAllProjects(self):
        return self.send('/cgteam/getAllProjects')

    def setTaskDataSize(self, id, name, dataSize):
        return self.send('/cgteam/setTaskDataSize', {'id': id, 'name': name, 'dataSize': dataSize})

    def getTaskDataSize(self, id):
        return self.send('/cgteam/getTaskDataSize', {'id': id})

    def getLightTaskInfoFromRefAssetIDList(self, refAssetIDList):
        return self.send('/cgteam/getLightTaskInfoFromRefAssetIDList', {'refAssetIDList': json.dumps(refAssetIDList)})

    def getAniTaskInfoFromRefAssetIDList(self, refAssetIDList):
        return self.send('/cgteam/getAniTaskInfoFromRefAssetIDList', {'refAssetIDList': json.dumps(refAssetIDList)})

    def getTaskInfo(self, taskID):
        return self.send('/cgteam/getTaskInfo', {'taskID': taskID})

    def getProjectInfo(self, projectName):
        return self.send('/cgteam/getProjectInfo1', {'name': projectName})

    def myWFGetUserInfo(self):
        return self.send_cgserver(CGMaya_config.myRootURL + '/cgserver/getUserInfo', {'userName': CGMaya_config.userName})

    def myWFGetProjects(self, user):
        return self.send(self.myDAMURL + '/cgteam/getProjects', {'user': user})

    def getProjectTask(self, projectName):
        return self.send('/cgteam/getTasksOfProject', {'projectName': projectName})

    def searchTask(self, name, projectName):
        return self.send('/cgteam/searchTask', {'name': name, 'projectName': projectName})

    def createTaskByName(self, task):
        return self.send('/cgteam/createTaskByName', {'task': json.dumps(task)})

    def getAssetsOfProject(self, projectName):
        return self.send('/cgteam/getAssetsOfProject', {'projectName': projectName})

    def getShotInfo(self, projectName, name):
        return self.send('/cgteam/getShotInfo', {'projectName': projectName, 'name': name})

    def createNextShot(self, projectName, shotName, nextShotName):
        return self.send('/cgteam/createNextShot', {'projectName': projectName, 'shotName': shotName,
                                                                 'nextShotName': nextShotName})

    def setTaskAssetObjID(self, id, objFileID):
        return self.send('/cgteam/setTaskAssetObjID', {'id': id, 'objFileID': objFileID})

    def setTaskAsset(self, id, taskName, projectName, IconFileID, fileID, textureFileID, audioFileIDList, note,
                                        plugin, frameList):
        return self.send('/cgteam/setTaskAsset2', {'id': id, 'taskName': taskName, 'projectName': projectName,
                                'IconFileID': IconFileID, 'fileID': fileID, 'textureFileID': textureFileID,
                                'audioFileIDList': audioFileIDList, 'note': note, 'plugin': plugin, 'frameList': frameList})

    def setShotStereo(self, name, projectName, cameraList):
        return self.send('/cgteam/setShotStereo', {'name': name, 'projectName': projectName, 'cameraList': json.dumps(cameraList)})

    def getAssetByName(self, name, projectName):
        return self.send('/cgteam/getAssetByName', {'name': name, 'projectName': projectName})

    def setTaskAudioFileIDList(self, id, audioFileIDList):
        return self.send('/cgteam/setTaskAudioFileIDList_short', {'taskID': id, 'audioFileIDList': JSONEncoder().encode(audioFileIDList)})

    def setTaskShot(self, id, taskName, projectName, IconFileID, fileID, textureFileID, audioFileIDList, note,
                                        plugin, frameList):
        return self.send('/cgteam/setTaskShot2', {'id': id, 'taskName': taskName, 'projectName': projectName,
                                'IconFileID': IconFileID, 'fileID': fileID, 'textureFileID': textureFileID,
                                'audioFileIDList': audioFileIDList, 'note': note, 'plugin': plugin, 'frameList': frameList})

    def setTaskRefAssetIDList(self, taskID, refAssetIDList):
        return self.send('/cgteam/setTaskRefAssetIDList', {'taskID': taskID, 'refAssetIDList': json.dumps(refAssetIDList)})

    def setShotRefAssetIDList(self, name, projectName, refAssetIDList):
        return self.send('/cgteam/setShotRefAssetIDList', {'name': name, 'projectName': projectName, 'refAssetIDList': json.dumps(refAssetIDList)})

    def setTaskRenderFrames(self, taskID, singleFrame, frameList):
        return self.send('/cgteam/setTaskRenderFrames', {'taskID': taskID, 'singleFrame': singleFrame, 'frameList': frameList})

    def setTaskLightFileIDList1(self, id, lightFileIDList, textureFileID):
        return self.send('/cgteam/setTaskLightFileIDList1',
                         {'taskID': id, 'lightFileIDList': JSONEncoder().encode(lightFileIDList), 'textureFileID': textureFileID})

    def renderJobSubmit(self, user, submitTaskList, renderType, renderLocation, nodeName, type, lFlag, rFlag):
        return self.send('/cgteam/renderJobSubmit', {'user': user, 'submitTaskList': json.dumps(submitTaskList),
                                 'renderType': renderType, 'renderLocation': renderLocation, 'nodeName': nodeName, 'type': type, 'lFlag': lFlag, 'rFlag': rFlag})







    def myWFGetProjectTaskByStage(self, projectName, stage):
        return self.send(self.myDAMURL + '/cgteam/getTasksOfProjectByS tage', {'projectName': projectName, 'stage': stage})

    def myWFSubmitTask(self, task_id):
        return self.send(self.myDAMURL + '/cgteam/submitTask', {'id': task_id})

    def myWFReturnTask(self, taskName, projectName, upfolderid):
        return self.send(self.myDAMURL + '/DAM/returnTask', {'taskName': taskName, 'projectName': projectName, 'upfolderid': upfolderid})




    def myWFSetTaskAssetRenderWingFileID(self, id, renderwingFileID):
        return self.send(self.myDAMURL + '/cgteam/setTaskAssetRenderWingFileID',
                         {'id': id, 'renderwingFileID': renderwingFileID})


    def myWFSetTaskRenderwingFileIDList(self, id, renderwingFileIDList):
        return self.send(self.myDAMURL + '/cgteam/setTaskRenderwingFileIDList',
                         {'taskID': id, 'renderwingFileIDList': JSONEncoder().encode(renderwingFileIDList)})

    def myWFSetTaskLightFileID(self, id, fileName, lightFileID):
        return self.send(self.myDAMURL + '/cgteam/setTaskLightFileID',
                         {'id': id, 'fileName': fileName, 'lightFileID': lightFileID})



    def myWFSetTaskSubmitFileIDList(self, id, submitFileIDList, notes):
        return self.send(self.myDAMURL + '/cgteam/setTaskSubmitFileIDList',
                         {'taskID': id, 'submitFileIDList': JSONEncoder().encode(submitFileIDList), 'notes': notes})

    def myWFSetSubmitFileIDList(self, id, submitFileIDList):
        return self.send(self.myDAMURL + '/cgteam/setSubmitFileIDList',
                         {'submitID': id, 'submitFileIDList': JSONEncoder().encode(submitFileIDList), 'notes': notes})

    def myWFSetTaskSubmitMovID(self, id, movID):
        return self.send(self.myDAMURL + '/cgteam/setTaskSubmitMovID', {'id': id, 'submitMovID': movID})



    def myWFSearchReFModel(self, name, projectName):
        result = self.send(self.myDAMURL + '/cgteam/searchTaskRefModel', {'name': name, 'projectName': projectName})
        return json.loads(result)

    def myWFSearchTaskByStageAndName(self, projectName, name, stage):
        result = self.send(self.myDAMURL + '/cgteam/searchTaskByStageAndName', {'name': name, 'projectName': projectName, 'stage': stage})
        return json.loads(result)

    def myWFSearchTaskByID(self, id):
        result = self.send(self.myDAMURL + '/cgteam/searchTaskByID', {'id': id})
        return json.loads(result)


    def myWFGetTaskLightList(self, taskID):
        return self.send(self.myDAMURL + '/cgteam/getTaskLightList', {'taskID': taskID})



    def myWFcreateTask(self, task):
        return self.send(self.myDAMURL + '/cgteam/createTask1', {'task': task})

    def myWFgetAllRenderTasks(self):
        return self.send(self.myDAMURL + '/cgteam/getAllRenderTasks', {})

    def myWFgetRenderMyTasks(self, user):
        return self.send(self.myDAMURL + '/cgteam/getRenderMyTasks', {'user': user})



    def myWFsetTaskAudioFileID(self, taskID, audioFileIDList):
        return self.send(self.myDAMURL + '/cgteam/setTaskAudioFileID', {'taskID': taskID, 'audioFileIDList': audioFileIDList})

    def myWFsetTaskLightList(self, taskID, lightName, lightID):
        return self.send(self.myDAMURL + '/cgteam/setTaskLightIDList', {'taskID': taskID, 'lightName': lightName, 'lightID': lightID})

    def myWFSetTaskByReturnID(self, taskID, returnFolderID):
        return self.send(self.myDAMURL + '/cgteam/setTaskByReturnID', {'taskID': taskID, 'returnFolderID': returnFolderID})

    def myWFSetTaskRefAssetProject(self, id, refModelProjectName):
        return self.send(self.myDAMURL + '/cgteam/setTaskRefAssetProject', {'id': id, 'refModelProjectName': refModelProjectName})

    def TBUpdateTaskStatus(self, task, status):
        return self.send(self.myDAMURL + '/TB/updateTaskStatus', {'taskID': task['_id'], 'status': status})

    def TBSubmitTask(self, taskID):
        return self.send(self.myDAMURL + '/TB/submitTask', {'taskID': taskID})

    def getUpdateSoftware(self):
        return self.send(CGMaya_config.myDAMURL + '/DAM/getUpdateSoftware', {'software': 'RCMaya', 'version': CGMaya_config.softwareVersion})

    def getPluginList(self, software, pluginType):
        return self.send(self.myDAMURL + '/DAM/getPluginList', {'software': software, 'pluginType': pluginType})

    def findPlugin(self, file, software, pluginType):
        return self.send(self.myDAMURL + '/DAM/findPlugin', {'file': file, 'software': software, 'pluginType': pluginType})

    def getPluginFolderID(self, software, pluginType):
        return self.send(self.myDAMURL + '/DAM/getPluginFolderID', {'software': software, 'pluginType': pluginType})

    def getPlugin(self, software, pluginType, pluginName):
        result = self.send(self.myDAMURL + '/DAM/getPlugin', {'software': software, 'pluginType': pluginType, 'pluginName': pluginName})
        data = json.loads(result)
        url = data['url']
        pluginFn = os.path.join(CGMaya_config.storageDir, url[url.rfind('/')+1:])
        ret =self.myDownload(url, pluginFn)
        if ret:
            return pluginFn
        else:
            return None

    def judgeOpen(self, id):
        return self.send(self.myDAMURL + '/cgteam/judgeOpen', {'id': id})

    def assetClose(self, id):
        return self.send(self.myDAMURL + '/cgteam/assetClose', {'id': id})



    def DBOpen(self, pramaDB):
        client = MongoClient(CGMaya_config.teamInfo['mongoDBUrl_Out'])
        db = client[pramaDB]
        client.admin.authenticate(CGMaya_config.teamInfo['mongoDBUser'],
                                  CGMaya_config.teamInfo['mongoDBPassword'],
                                  mechanism='SCRAM-SHA-1', source='admin')
        return db

    def putFileGridFS(self, uploadFile, bType = True):
        if bType:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        else:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoDBName'])

        filename = os.path.basename(uploadFile)
        if bType:
            total = os.path.getsize(uploadFile)
            fstr = '{0:.2f}'.format(total / (float)(1024 * 1024))
            status = 'Uploading File(' + fstr + 'MB): ' + os.path.basename(uploadFile)
            gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(gMainProgressBar,
                             edit=True,
                             beginProgress=True,
                             isInterruptable=True,
                             status=status,
                             minValue=0,
                             maxValue=100
                             )
            inc = 0
            fs = GridFS(db, collection='LargeFiles')
            with open(uploadFile, "rb") as f:
                buffer = f.read()
                invoice = fs.put(buffer, encoding='utf-8', filename=filename)
                inc = inc + len(buffer)
                progress = int(float(inc) / float(total) * 100.0)
                cmds.progressBar(gMainProgressBar, edit=True, progress=progress)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        else:
            with open(uploadFile, "rb") as f:
                coll = db.SmallFiles
                content = StringIO(f.read())
                invoice = coll.save(dict(content=bson.binary.Binary(content.getvalue()), filename=filename))

        #print 'type(invoice) =', type(invoice)
        return invoice

    def getFileNameGridFS(self, fileID, bType = True):
        if bType:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        else:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoDBName'])

        if bType:
            fs = GridFS(db, collection='LargeFiles')
            file = fs.find_one({"_id": ObjectId(fileID)})
        else:
            coll = db.SmallFiles
            file = coll.find_one({"_id": ObjectId(fileID)})
        try:
            return file.filename
        except AttributeError:
            return None

    def getFileInfo(self, fileID):
        db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        fs = GridFS(db, collection='LargeFiles')
        result = fs.find_one({"_id": ObjectId(fileID)})
        return result

    def getFileGridFS(self, localFile, fileID, fileName, bType = True):
        if bType:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        else:
            db = self.DBOpen(CGMaya_config.teamInfo['mongoDBName'])

        if bType:
            fs = GridFS(db, collection='LargeFiles')
            file = fs.find_one({"_id": ObjectId(fileID)})
            total = file.length
            fstr = '{0:.2f}'.format(total / (float)(1024 * 1024))
            status = 'Downloading File(' + fstr + 'MB): ' + fileName
            gMainProgressBar = mel.eval('$tmp = $gMainProgressBar')
            cmds.progressBar(gMainProgressBar,
                             edit=True,
                             beginProgress=True,
                             isInterruptable=True,
                             status=status,
                             minValue=0,
                             maxValue=100
                             )
            inc = 0
            with open(localFile, "wb") as f:
                with fs.get(ObjectId(fileID)) as fd:
                    for line in fd:
                        f.write(line)
                        inc = inc + len(line)
                        progress = int(float(inc) / float(total) * 100.0)
                        cmds.progressBar(gMainProgressBar, edit=True, progress=progress)
            cmds.progressBar(gMainProgressBar, edit=True, endProgress=True)
        else:
            coll = db.SmallFiles
            file = coll.find_one({"_id": ObjectId(fileID)})
            f = open(localFile.decode('utf-8'), "wb")
            try:
                f.write(file['content'])
            except TypeError:
                f.close()
                return False
        f.close()
        return True

    def getAttachFileGridFS(self, localFile, fileID, fileName):
        db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        fs = GridFS(db, collection='fs')
        with open(localFile, "wb") as f:
            with fs.get(ObjectId(fileID)) as fd:
                for line in fd:
                    f.write(line)
        f.close()
        return True

    def listMayaFile(self, name):
        db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        fs = GridFS(db, collection='LargeFiles')
        list = fs.find({'$or': [{'filename': name + '.ma'}, {'filename': name + '.mb'}]})
        returnList =[]
        for ll in list:
            returnList.append({'id': unicode(ll._id), 'filename': ll.filename, 'uploadDate': ll.uploadDate, 'length': ll.length})
            #returnList.append({'id': ll['_id'], 'filename': ll['filename'], 'uploadDate': ll['uploadDate']})
        return returnList

    def deleteMayaFile(self, fileID):
        db = self.DBOpen(CGMaya_config.teamInfo['mongoFileDBName'])
        fs = GridFS(db, collection='LargeFiles')
        fs.delete(fileID)

    def putSoftware(self, uploadFile, softwareName):
        if CGMaya_config.softInfo == {}:
            result = self.send_server('/cgserver/getSoftwareConfigInfo', {})
            CGMaya_config.softInfo = json.loads(result)
        client = MongoClient(CGMaya_config.softInfo['url'])
        db = client[CGMaya_config.softInfo['DBName']]
        with open(uploadFile, "rb") as f:
            fs = GridFS(db, collection=CGMaya_config.softInfo['collection'])
            invoice = fs.put(f.read(), encoding='utf-8', filename=softwareName)
        self.send_cgserver('/cgserver/setSoftwareInfo', {'name': softwareName, 'fileID': invoice})
        return invoice



    def IPFSConnect(self):
        url = CGMaya_config.IPFSUrl.split(':')[0]
        port = int(CGMaya_config.IPFSUrl.split(':')[1])
        try:
            self.IPFSApi = ipfsapi.connect(url, port)
        except ipfsapi.exceptions.ConnectionError as ce:
            print(str(ce))
            self.IPFSApi = None
        return self.IPFSApi

    def putFileIPFS(self, uploadFile):
        res = self.IPFSApi.add(uploadFile)
        #self.send(self.myDAMURL + '/file/put', {'id': res['Hash']})
        return json.dumps(res)

    def getFileIPFS(self, localFile, fileID):
        ipfs = json.loads(fileID)
        srcDir = os.getcwd()
        os.chdir('d:/temp')
        self.IPFSApi.get(ipfs['Hash'])
        os.chdir(srcDir)
        shutil.copyfile('d:/temp/' + ipfs['Hash'], localFile)

    def getFileNameIPFS(self, fileID):
        ipfs = json.loads(fileID)
        return ipfs['Name']

    def getFileName(self, task, fileID, bType=True):
        storage = 'GridFS'
        try:
            if task['storage'] == 'ipfs':
                storage = 'ipfs'
        except KeyError:
            pass
        if storage == 'ipfs':
            return self.getFileNameIPFS(fileID)
        else:
            return self.getFileNameGridFS(fileID, bType)

    def getFile(self, task, localFile, fileID, fileName, bType=True):
        storage = 'GridFS'
        try:
            if task['storage'] == 'ipfs':
                storage = 'ipfs'
        except KeyError:
            pass
        if storage == 'ipfs':
            self.getFileIPFS(localFile, fileID)
        else:
            self.getFileGridFS(localFile, fileID, fileName, bType)

    def putFile(self, task, uploadFile, bType=True):
        storage = 'GridFS'
        try:
            if task['storage'] == 'ipfs':
                storage = 'ipfs'
        except KeyError:
            pass
        if storage == 'ipfs':
            return self.putFileIPFS(uploadFile)
        else:
            return self.putFileGridFS(uploadFile, bType)

    def putFile2(self, task, uploadFile, bType=True):
        storage = 'GridFS'
        try:
            if task['storage'] == 'ipfs':
                storage = 'ipfs'
        except KeyError:
            pass
        total = os.path.getsize(uploadFile)
        fstr = '{0:.2f}'.format(total / (float)(1024 * 1024))
        if storage == 'ipfs':
            return self.putFileIPFS(uploadFile), fstr
        else:
            return self.putFileGridFS(uploadFile, bType), fstr





    def myWFSetTaskSingleOutputID(self, task_id, fileID):
        return self.send(self.myDAMURL + '/cgteam/setTaskSingleOutputID', {'id': task_id, 'fileID': fileID})



    def transferShot(self, srcProjectName, srcShotName, destProjectName, destShotName):
        return self.send(self.myDAMURL + '/cgteam/transferShot', {'srcProjectName': srcProjectName, 'srcShotName': srcShotName,
                                                                  'destProjectName': destProjectName, 'destShotName': destShotName})


    def getSubmitsOfTask(self, id):
        return self.send(self.myDAMURL + '/cgteam/getSubmitsOfTask', {'id': id})

