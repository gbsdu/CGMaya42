#coding=utf-8

import sys, os
from ctypes import *
import maya.cmds as cmds
import maya.mel as mel
import json
import zipfile
import subprocess
import platform
import ctypes
import pymel
try:
    from PySide2 import QtWidgets as QtCGMaya
    from PySide2 import QtGui
    from PySide2 import QtCore
    import shiboken2
    from shiboken2 import wrapInstance
except:
    from PySide import QtGui as QtCGMaya
    from PySide import QtGui
    from PySide import QtCore
    import shiboken
    from shiboken import wrapInstance
if platform.system == 'windows':
    import _winreg
import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.cmds as cmds
import pymel.core
import shutil
import time, timeit
import CGMaya_config
import CGMaya_parser
import CGMaya_service
#import CGMaya_timer
import RWingRendererIO

monthInfo = {u'一月': 'January', u'二月': 'February', u'三月': 'March', u'四月': 'April',
             u'五月': 'May', u'六月': 'June', u'七月': 'July', u'八月': 'Aguest',
             u'九月': 'September', u'十月': 'October', u'十一月': 'November', u'十二月': 'December'}

nameList = [CGMaya_config.CGMaya_Texture_Dir, CGMaya_config.CGMaya_Submit_Dir, CGMaya_config.CGMaya_Return_Dir,
                CGMaya_config.CGMaya_Light_Dir, CGMaya_config.CGMaya_Shot_Dir, CGMaya_config.CGMaya_Audio_Dir]

taskStageList = [u'布局', u'动画', u'灯光']

def openTask(service, currentTask):
    CGMaya_config.logger.set("openTask")
    CGMaya_config.logger.debug("assetStorageDir = %s\r" % CGMaya_config.assetStorageDir)
    projectDir = CGMaya_config.storageDir + '/' + currentTask['projectName']
    if not os.path.exists(CGMaya_config.storageDir):
        os.mkdir(CGMaya_config.storageDir)
    if not os.path.exists(CGMaya_config.assetStorageDir):
        os.mkdir(CGMaya_config.assetStorageDir)
    if not os.path.exists(projectDir):
        os.mkdir(projectDir)
    CGMaya_config.refAssetIDList = []
    CGMaya_config.processMayaDLL = None
    CGMaya_config.successfulReadMayaFile = True


    ###print 'Processing Create Referenrce Task
    if not CGMaya_config.taskFileID:
        CGMaya_config.logger.info("Processing Create Referenrce Task...\r")
        try:
            refModel = currentTask['refModel']
        except KeyError:
            refModel = ''
        if not refModel:
            CGMaya_config.logger.error("File is Null\r")
            return
        refObj = json.loads(refModel)
        refProjectName = refObj['modelProjectName']

        service.myWFSetTaskAssetRefModel(currentTask['_id'], refProjectName)
        refProjectDir = CGMaya_config.assetStorageDir + '/' + refProjectName
        if not os.path.exists(refProjectDir):
            os.mkdir(refProjectDir)
        refList = refObj['refModelList'].split(',')
        for refModel in refList:
            if not refModel:
                continue
            taskList = service.myWFsearchTask(refModel, refProjectName)
            refTask = taskList[0]
            if refTask:
                sfn = openAsset(service, refTask['fileID'], refTask, CGMaya_config.assetStorageDir)
                fn = os.path.basename(sfn)
                CGMaya_config.refAssetIDList.append({'projectName': refTask['projectName'],
                                                     'name': fn, 'id': refTask['fileID'], 'taskID': refTask['_id']})
                # cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=':')
                CGMaya_config.logger.debug("Reference Asset = %s\r" % currentTask['name'])
                cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=currentTask['name'])
        return

    CGMaya_config.refAssetIDList = CGMaya_config.currentTask['refAssetIDList']
    taskFileName = openAsset(service, CGMaya_config.taskFileID, CGMaya_config.currentTask, CGMaya_config.storageDir)

    ###print 'Processing Audio ...
    CGMaya_config.logger.info("Processing Audio...\r")
    if currentTask['stage'] == u"布局" or currentTask['stage'] == u"动画":
        try:
            audioFileIDList = currentTask['audioFileIDList']
        except KeyError:
            audioFileIDList = None
        audioDir = projectDir + '/' + CGMaya_config.CGMaya_Audio_Dir
        if not os.path.exists(audioDir):
            os.mkdir(audioDir)
        if audioFileIDList:
            for audioFileID in audioFileIDList:
                service.getFile(currentTask, audioDir + '/' + audioFileID['name'], audioFileID['id'], '', False)

    cmds.workspace(dir=projectDir)
    CGMaya_config.assetExtFileName = os.path.basename(taskFileName).split('.').pop()
    CGMaya_config.logger.info("Maya Open File1...\r")
    if not CGMaya_config.successfulReadMayaFile:
        return
    try:
        cmds.file(taskFileName, open = True, force = True)
    except RuntimeError:
        CGMaya_config.logger.error("RuntimeError-----%s\r" % taskFileName)
    return

def openLightTask(service, currentTask):
    CGMaya_config.successfulReadMayaFile = True
    CGMaya_config.logger.set("openLightTask")
    projectDir = CGMaya_config.storageDir + '/' + currentTask['projectName']
    if not os.path.exists(CGMaya_config.storageDir):
        os.mkdir(CGMaya_config.storageDir)
    if not os.path.exists(CGMaya_config.assetStorageDir):
        os.mkdir(CGMaya_config.assetStorageDir)
    if not os.path.exists(projectDir):
        os.mkdir(projectDir)
    refProjectDir = CGMaya_config.assetStorageDir + '/' + CGMaya_config.project['refProject']
    CGMaya_config.refAssetIDList = CGMaya_config.currentTask['refAssetIDList']

    #print CGMaya_config.currentTask
    shotInfo = json.loads(service.myWFGetShotInfo(CGMaya_config.currentTask['projectName'], CGMaya_config.currentTask['name']))

    #taskFileName = openAsset(service, shotInfo['fileID'], CGMaya_config.currentTask, CGMaya_config.storageDir, True)
    if not CGMaya_config.currentTask['refAssetIDList']:
        print('task.refAssetIDList is NULL')
        CGMaya_config.currentTask['refAssetIDList'] = shotInfo['refAssetIDList']
    #print 'shotInfo =', shotInfo

    taskFileName = openAsset(service, shotInfo['fileID'], CGMaya_config.currentTask, CGMaya_config.storageDir)
    cmds.workspace(dir=projectDir)
    CGMaya_config.assetExtFileName = os.path.basename(taskFileName).split('.').pop()
    taskDir = projectDir + '/' + CGMaya_config.currentTask['name']
    lightDir = taskDir + '/' + CGMaya_config.CGMaya_Light_Dir
    if not os.path.exists(lightDir):
        os.mkdir(lightDir)
    tmpDir = projectDir + '/' + CGMaya_config.CGMaya_Tmp_Dir
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)
    if CGMaya_config.lightFileFlag:
        fn = service.getFileName(currentTask, CGMaya_config.taskFileID)
        lightFileName = lightDir + '/' + fn
        tmpFullFN = tmpDir + '/' + 'tmp_' + fn.split('.')[0] + '.' + fn.split('.').pop()
        downloadFile(service, projectDir, currentTask, lightFileName, CGMaya_config.taskFileID, tmpFullFN)
        CGMaya_config.logger.info("     Processing File-----%s\r" % lightFileName)
        processMaya(CGMaya_config.currentTask['name'], tmpFullFN, lightFileName, projectDir, refProjectDir)
        CGMaya_config.logger.info("     Open File-----%s\r" % lightFileName)
        #os.remove(tmpFullFN)
        if not CGMaya_config.successfulReadMayaFile:
            return ''
        cmds.file(lightFileName, open=True, force=True)
    else:
        if not CGMaya_config.successfulReadMayaFile:
            return ''
        if CGMaya_config.lightRefFlag:
            CGMaya_config.logger.info("     Open Reference File-----%s\r" % taskFileName)
            cmds.file(taskFileName, reference=True, options='v=0', ignoreVersion=True, namespace=CGMaya_config.currentTask['name'])
        else:
            CGMaya_config.logger.info("     Open File-----%s\r" % taskFileName)
            cmds.file(taskFileName, open = True, force = True)
    renderer = CGMaya_config.project['render']
    #if CGMaya_config.project['render'] == 'redshift':
    #    convertTextureFile(CGMaya_config.assetStorageDir)
    cmds.setAttr('defaultRenderGlobals.currentRenderer', renderer, type='string')
    CGMaya_config.singleOutputPath = taskDir
    pymel.core.mel.setProject(CGMaya_config.singleOutputPath)
    return True

def convertTextureFile(textureDir):
    userScriptDir = cmds.internalVar(userScriptDir=True)
    exeFile = userScriptDir.replace('/', '\\') + 'CGMaya\\redshiftTextureProcessor.exe'
    for refAssetID in CGMaya_config.currentTask['refAssetIDList']:
        for fn in os.listdir(textureDir):
            path = textureDir + fn
            ext = path.split('.').pop()
            if ext == 'rstexbin' or ext == 'rs':
                continue
            command = exeFile + ' ' + path
            subprocess.Popen(command, shell=True)

def openAsset(service, fileID, task, storageDir):
    CGMaya_config.logger.info('openAsset---%s\r' % task['name'])
    projectName = task['projectName']
    taskName = task['name']
    projectDir = storageDir + '/' + projectName
    if not os.path.exists(projectDir):
        os.mkdir(projectDir)

    taskDir = projectDir + '/' + taskName
    if not os.path.exists(taskDir):
        os.mkdir(taskDir)
    textureDir = taskDir + '/' + CGMaya_config.CGMaya_Texture_Dir
    if not os.path.exists(textureDir):
        os.mkdir(textureDir)
    try:
        refAssetIDList = task['refAssetIDList']
    except KeyError:
        refAssetIDList = []
    refProjectName = ''
    if refAssetIDList:
        refProjectName = refAssetIDList[0]['projectName']
        if task['stage'] == '灯光':
            refTaskList = json.loads(service.getLightTaskInfoFromRefAssetIDList(refAssetIDList))
        else:
            refTaskList = json.loads(service.getAniTaskInfoFromRefAssetIDList(refAssetIDList))
        print('refTaskList =', refTaskList)
        for task1 in refTaskList:
            print('task = ', task1)
            if task1:
                openAsset(service, task1['fileID'], task1, CGMaya_config.assetStorageDir)
    refProjectDir = CGMaya_config.assetStorageDir + '/' + refProjectName
    if not os.path.exists(refProjectDir):
        os.mkdir(refProjectDir)
    print 'fileType =', type(fileID)
    fn = service.getFileName(task, fileID)
    taskFileName = taskDir + '/' + fn
    tmpDir = projectDir + '/' + CGMaya_config.CGMaya_Tmp_Dir
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)
    tmpFullFN = tmpDir + '/' + 'tmp.' + fn.split('.').pop()
    print 'fileID =', fileID
    if downloadFile(service, projectDir, task, taskFileName, fileID, tmpFullFN):
        CGMaya_config.logger.debug('projectDir: %s, refProjectDir = %s----%s\r' % (projectDir, refProjectDir, fileID))
        processMaya(task['name'], tmpFullFN, taskFileName, projectDir, refProjectDir)
        #os.remove(tmpFullFN)
    return taskFileName

def judgelogData(logJsonData, fileName, fileID):
    bExist = 0
    for log in logJsonData:
        if log['fileName'] == fileName and log['id'] == fileID:
            bExist = 2
            break
        elif log['fileName'] == fileName and log['id'] != fileID:
            log['id'] = fileID
            bExist = 1
            break
    return bExist

def downloadFile(service, projectDir, task, filePath, fileID, downLoadFilePath):
    if not CGMaya_config.successfulReadMayaFile:
        return False
    logPath = projectDir + '/' + CGMaya_config.CGMaya_Log_Dir
    if not os.path.exists(logPath):
        os.mkdir(logPath)

    lockFilePath = logPath + '/' + task['name'] + CGMaya_config.lockFileExt
    if os.path.exists(lockFilePath):
        str = u'文件正在被其他用户下载。。。，请等待--' + task['name']
        QtCGMaya.QMessageBox.information(CGMaya_config.currentDlg, u"提示信息", str, QtCGMaya.QMessageBox.Yes)
        CGMaya_config.successfulReadMayaFile = False
        return False
    with open(lockFilePath, 'w') as lockFP:
        lockFP.write('jjj')

    logJsonData = []
    logFilePath = logPath + '/' + task['name'] + CGMaya_config.logFileExt
    if os.path.isfile(logFilePath):
        with open(logFilePath, "r") as json_file:
            logJsonData = json.load(json_file)

    taskDir = projectDir + '/' + task['name']
    if not os.path.exists(taskDir):
        os.mkdir(taskDir)
    textureDir = taskDir + '/' + CGMaya_config.CGMaya_Texture_Dir
    if not os.path.exists(textureDir):
        os.mkdir(textureDir)
    tmpDir = projectDir + '/' + CGMaya_config.CGMaya_Tmp_Dir
    if not os.path.exists(tmpDir):
        os.mkdir(tmpDir)
    #texturePath = textureDir + '/texture.zip'

    fileName = os.path.basename(filePath)
    bExist = judgelogData(logJsonData, fileName, fileID)
    if not os.path.exists(filePath) or bExist != 2:
        CGMaya_config.logger.info("Downloading File-----%s\r" % filePath)
        service.getFile(task, downLoadFilePath, fileID, fileName)
        print 'textureFileID =', task['textureFileID']
        if CGMaya_config.textureReadFlag and task['textureFileID'] and not task['stage'] in taskStageList:
            print('TEXTURE......', task)
            textureFileName = service.getFileInfo(task['textureFileID']).filename
            texturePath = tmpDir + '/' + textureFileName
            CGMaya_config.logger.debug("Downloading texture File-----%s\r" % texturePath)
            service.getFile(task, texturePath, task['textureFileID'], textureFileName)
            zf = zipfile.ZipFile(texturePath, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)
            fileList = zf.namelist()
            for names in zf.namelist():
                try:
                    zf.extract(names, path = textureDir)
                except Exception as e:
                    print 'File Read is failed----', names
            if CGMaya_config.project['render'] == 'redshift':
                convertTextureFile(textureDir)
            for file1 in fileList:
                if file1.split('.').pop() == 'rs':  # redshift Proxy
                    file = textureDir + '/' + file1
                    bakFile = file.split('.')[0] + '.bak'
                    print 'proxy------', file, bakFile, len(file1)
                    CGMaya_config.logger.debug("     Processing Proxy File-----%s\r" % file)
                    if os.path.exists(file):
                        parser = CGMaya_parser.processRedshiftProxyFile(file, bakFile)
                        parser.replaceFilePath()
                        shutil.copy(bakFile, file)
                        os.remove(bakFile)
                    else:
                        CGMaya_config.logger.debug('Proxy File is not existed---%s\r' % file)
            #os.remove(texturePath)
        if bExist == 0:
            logJsonData.append({"fileName": fileName, 'id': fileID})
        with open(logFilePath, "w") as json_file:
            json.dump(logJsonData, json_file)
        if os.path.exists(lockFilePath):
            os.remove(lockFilePath)
        return True
    if os.path.exists(lockFilePath):
        os.remove(lockFilePath)
    return False

def processMaya(assetName, fileName_in, fileName_out, projectDir, refProjectDir):
    CGMaya_config.logger.debug('processMaya---%s %s\r' % (fileName_in, fileName_out))
    t0 = timeit.default_timer()
    parser = CGMaya_parser.mayaParser(fileName_in)
    t1 = timeit.default_timer() - t0
    CGMaya_config.logger.debug("  => Create Struct elasped : [%0.8fs]\r" % t1)
    refList, textureList = parser.replaceFilePath(assetName, fileName_out, projectDir, refProjectDir)
    t2 = timeit.default_timer() - t1
    CGMaya_config.logger.debug("  => process Struct elasped : [%0.8fs]\r" % t2)
    return refList, textureList

def readRefFile(fileName):
    fp = open(fileName, "r")
    lines = fp.readlines()
    fp.close()
    if not lines:
        return None, None
    refModelList = []
    textureList = []
    for i in range(1, int(lines[0])):
        refModelList.append(lines[i])
    n = int(lines[0])
    for j in range(n, n + int(lines[n + 1])):
        textureList.append(lines[j])
    #os.remove(fileName)
    return refModelList, textureList

def saveTask(dlg, service, scene_fn, pixmap, note, pluginStr, frameListStr, type, audioLoadFlag, bMovFlag):
    CGMaya_config.logger.set("saveTask")
    projectName = CGMaya_config.currentTask['projectName']
    sceneName = CGMaya_config.currentTask['name']
    taskID = CGMaya_config.currentTask['_id']
    projectDir = CGMaya_config.storageDir + '/' + projectName
    cmds.workspace(dir=projectDir)

    cameraList = []
    if CGMaya_config.currentProject['templateName'] == '3DShot' and CGMaya_config.stereoFlag:
        cameraL = ''
        cameraR = ''
        #list = cmds.listCameras(p=True)
        list = cmds.ls(cameras=True)
        for camera in list:
            if camera.find('stereoCameraLeft') >= 0:
                cameraL = camera
            elif camera.find('stereoCameraRight') >= 0:
                cameraR = camera
        cameraList.append(cameraL)
        cameraList.append(cameraR)
        print('cameraList =', cameraList)
        if len(cameraList) == 2:
            service.myWFSetShotStereo(sceneName, projectName, cameraList)
        else:
            QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有设置立体摄像机", QtCGMaya.QMessageBox.Yes)
            return ''

    refs = pymel.core.listReferences()
    CGMaya_config.logger.info('Processing Reference...%d, %d\r' % (len(refs), len(CGMaya_config.refAssetIDList)))
    for ref in refs:
        refn = ref.path
        refName = os.path.basename(refn)
        refModelName = refName.split('.')[0]
        bExist = True
        for refAssetID in CGMaya_config.refAssetIDList:
            if refAssetID['name'] == refModelName:
                bExist = False
        if bExist:
            if CGMaya_config.currentProject['refProject'] == '':
                CGMaya_config.logger.error('Reference Project is not Found: %s\r' % CGMaya_config.currentProject['name'])
            else:
                asset = json.loads(service.myWFGetAssetByName(refModelName, CGMaya_config.currentProject['refProject']))
                print('asset =', asset)
                if asset:
                    taskL = len(asset['taskList'])
                    CGMaya_config.refAssetIDList.append({'projectName': CGMaya_config.currentProject['refProject'],
                                'name': refModelName, 'id': asset['fileID'], 'taskID': asset['taskList'][taskL - 1]['_id']})
                else:
                    CGMaya_config.logger.error('Reference Asset is not Found: %s\r' % refModelName)

    CGMaya_config.logger.info('Processing Task File...%d\r' % len(refs))
    mayaFn = os.path.basename(scene_fn)

    defaults = ['UI', 'shared']
    ## 删除所有的namespace
    if CGMaya_config.currentProject['templateName'] == '3DAsset':
        CGMaya_config.logger.info('Delete All Namespaces...\r')
        remove_allnamespace()
    else:
        CGMaya_config.textureReadFlag = False

    CGMaya_config.logger.info('Save File...\r')
    b = False
    try:
        cmds.file(rename=scene_fn)
        cmds.file(save=True, type=type, force=True)
    except RuntimeError:
        CGMaya_config.logger.error('RuntimeError\r')
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"不能保存.ma文件", QtCGMaya.QMessageBox.Yes)
        return None

    if CGMaya_config.currentProject['templateName'] == '3DAsset' and CGMaya_config.currentProject['render'] == 'renderwing':
        ffffn = os.path.basename(scene_fn).split('.')[0] + '.obj'
        objFilePath = os.path.join(os.path.dirname(scene_fn), ffffn)
        CGMaya_config.logger.info('save OBj File...\r')
        cmds.file(objFilePath, pr=1, typ="OBJexport", es=1, op="groups=0; ptgroups=0;materials=0; smoothing=0; normals=0")
        CGMaya_config.logger.info('Uploading Obj File...\r')
        objFileID = service.putFile(CGMaya_config.currentTask, objFilePath)
        service.myWFSetTaskAssetObjID(CGMaya_config.currentTask['_id'], objFileID)

    textureFileID = ''
    if CGMaya_config.textureReadFlag:
        tmpDir = projectDir + '/' + CGMaya_config.CGMaya_Tmp_Dir
        if not os.path.exists(tmpDir):
            os.mkdir(tmpDir)
        zipFileName = tmpDir + '/' + 'texture.zip'
        zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
        #textureFileList = cmds.ls(type='file')
        parser = CGMaya_parser.mayaParser(scene_fn)
        refAssetList = []
        textureFileList =[]
        try:
            refAssetList, textureFileList = parser.getFilePath()
        except TypeError:
            pass
        CGMaya_config.logger.info('Processing Texture...%d\r' % len(textureFileList))
        zipFileList = []
        dirList = []
        for textureFile in textureFileList:
            """
            #print 'textureFile =', textureFile
            textureFileName = cmds.getAttr(textureFile + '.fileTextureName')
            #print ' textureFileName =', textureFileName
            """
            if os.path.isfile(textureFile) and not textureFile in zipFileList:
                textureDir = os.path.dirname(textureFile)
                if not textureDir in dirList:
                    dirList.append(textureDir)
                    fList = os.listdir(textureDir)
                    for subFile in fList:
                        subFilePath = textureDir + '/' + subFile
                        if os.path.isfile(subFilePath) and not subFilePath in zipFileList:
                            zipFileList.append(subFilePath)
                            zf.write(subFilePath, subFile)
                aText = textureFile.split('.').pop()
                aText = '.' + aText
                TXFile = textureFile.replace(aText, '.tx')
                if os.path.isfile(TXFile)  and not TXFile in zipFileList:
                    zipFileList.append(TXFile)
                    arcName = os.path.basename(TXFile)
                    zf.write(TXFile, arcName)
            if textureFile.find('.<UDIM>.') > 0 or textureFile.find('.<udim>.') > 0 or \
                    textureFile.find('.<f>.') > 0 or textureFile.find('.<F>.') > 0:
                print 'UDIM------', textureFile
                dir = os.path.dirname(textureFile)
                if textureFile.find('.<UDIM>.') > 0:
                    fn = textureFile.split('.<UDIM>.')[0]
                elif textureFile.find('.<udim>.') > 0:
                    fn = textureFile.split('.<udim>.')[0]
                elif textureFile.find('.<f>.') > 0:
                    fn = textureFile.split('.<f>.')[0]
                elif textureFile.find('.<F>.') > 0:
                    fn = textureFile.split('.<F>.')[0]
                if os.path.exists(dir):
                    fileList = os.listdir(dir)
                    for file in fileList:
                        fPath = dir + '/' + file
                        if file.find(fn) >= 0 and os.path.isfile(fPath) and not fPath in zipFileList:
                            zipFileList.append(fPath)
                            zf.write(fPath, file)
                else:
                    print 'Error: Directory is not found---', dir

        CGMaya_config.logger.info('     TextureDirList...%d\r' % len(dirList))
        CGMaya_config.logger.info('     ZIPTextureFileList...%d\r' % len(zipFileList))

        redshiftProxyFileList = cmds.ls(type='RedshiftProxyMesh')
        for redshiftProxyFile in redshiftProxyFileList:
            redshiftProxyFileName = cmds.getAttr(redshiftProxyFile + '.fileName')
            if os.path.isfile(redshiftProxyFileName):
                if redshiftProxyFileName in zipFileList:
                    continue
                zipFileList.append(redshiftProxyFileName)
                zf.write(redshiftProxyFileName, os.path.basename(redshiftProxyFileName))

        for redshiftProxyFileName in zipFileList:
            if redshiftProxyFileName.split('.').pop() != 'rs':
                continue
            print 'proxy File --------------', redshiftProxyFileName
            test = CGMaya_parser.processRedshiftProxyFile(redshiftProxyFileName)
            refs = test.getFilePath()
            for ref in refs:
                if os.path.exists(ref):
                    if ref in zipFileList:
                        continue
                    zipFileList.append(ref)
                    print '         texture File:', ref
                    zf.write(ref, os.path.basename(ref))
                else:
                    print '         Proxy texture File is not Exist', ref
            """
            #texture_info = CGMaya_parser.get_proxyInfo_cmd(redshiftProxyFileName, mode="printdependencies")
            for key in texture_info:
                print 'proxy-REf--------', key
                if os.path.exists(key):
                    arcName = os.path.basename(key)
                    zf.write(key, arcName)
                else:
                    CGMaya_config.logger.error('Proxy File is not Found...%s\r' % key)
                    #print "\t\t[Error] " + key + " (not exist)"
            """
        zf.close()
        CGMaya_config.logger.info('Uploading Texture File...\r')
        textureFileID = service.putFile(CGMaya_config.currentTask, zipFileName)
        os.remove(zipFileName)

    # print 'Processing Sound....'
    audioFileIDList = []
    audioFileID = ''
    if audioLoadFlag:
        soundList = pymel.core.ls(type='audio')
        for sound in soundList:
            sFilePath = sound.attr('filename').get()
            if os.path.isfile(sFilePath):
                audioFileID = service.putFile(CGMaya_config.currentTask, sFilePath, False)
                audioFileIDList.append({'id': audioFileID, 'name': os.path.basename(sFilePath)})
        if audioFileIDList:
            service.myWFSetTaskAudioFileIDList(taskID, audioFileIDList)

    CGMaya_config.logger.info('Uploading Task File...\r')
    fileID = service.putFile(CGMaya_config.currentTask, scene_fn)
    if CGMaya_config.currentProject['templateName'] == '3DAsset':
        service.myWFSetTaskAsset(taskID, sceneName, projectName, '', fileID, textureFileID, audioFileIDList,
                                 note, pluginStr, frameListStr)
    elif CGMaya_config.currentProject['templateName'] == '3DShot':
        service.myWFSetTaskShot(taskID, sceneName, projectName, '', fileID, textureFileID, audioFileIDList,
                                 note, pluginStr, frameListStr)
    else:
        service.myWFSetTaskAsset(taskID, sceneName, projectName, '', fileID, textureFileID, audioFileIDList,
                             note, pluginStr, frameListStr)

    if CGMaya_config.refAssetIDList:
        service.myWFSetTaskRefAssetIDList(taskID, CGMaya_config.refAssetIDList)
        service.myWFSetShotRefAssetIDList(sceneName, projectName, CGMaya_config.refAssetIDList)

    CGMaya_config.logger.info('file is saved')
    return scene_fn

def remove_allnamespace():
    nsp = cmds.namespaceInfo(lon = True, r = True)
    nsp.remove('UI')
    nsp.remove('shared')
    for ns in nsp[::-1]:
        try:
            cmds.namespace(mv = (ns, ':'), f = True)
            cmds.namespace(rm = ns)
        except RuntimeError:
            pass

def saveLightTask(dlg, service, scene_fn, pixmap, note, pluginStr, singleFrame, frameListStr, type, textureLoadFlag):
    CGMaya_config.logger.set("saveLightTask")
    projectName = CGMaya_config.currentTask['projectName']
    sceneName = CGMaya_config.currentTask['name']
    taskID = CGMaya_config.currentTask['_id']

    projectDir = CGMaya_config.storageDir + '/' + projectName
    cmds.workspace(dir=projectDir)
    CGMaya_config.logger.info('Processing Task File...\r')
    mayaFn = os.path.basename(scene_fn)
    try:
        cmds.file(rename=scene_fn)
        cmds.file(save=True, type=type, force=True)
    except RuntimeError:
        CGMaya_config.logger.error('RuntimeError\r')
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"不能保存.ma文件", QtCGMaya.QMessageBox.Yes)
        return None
        """
        unknownNodeList = cmds.ls(type='unknown')
        for unknownNode in unknownNodeList:
            response = QtCGMaya.QMessageBox.question(dlg, u"提示信息", u"是否删除下面unknown节点?",
                                                     QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
            if not response == QtCGMaya.QMessageBox.Yes:
                break
            cmds.delete(unknownNode)
        else:
            ffffn = os.path.basename(scene_fn).split('.')[0] + '.ma'
            sceneDir = os.path.join(os.path.dirname(scene_fn), CGMaya_config.CGMaya_Light_Dir)
            scene_fn = os.path.join(os.path.dirname(sceneDir), ffffn)
            cmds.file(rename=scene_fn)
            cmds.file(save=True, type='mayaAscii', force=True)
        """

    CGMaya_config.logger.info('Uploading Light File...\r')
    lightFileID = service.putFile(CGMaya_config.currentTask, scene_fn)

    CGMaya_config.logger.info('Processing Texture...')
    parser = CGMaya_parser.mayaParser(scene_fn)
    refAssetList, textureFileList = parser.getFilePath()
    textureFileID = ''
    if not textureFileList:
        tmpDir = projectDir + '/' + CGMaya_config.CGMaya_Tmp_Dir
        if not os.path.exists(tmpDir):
            os.mkdir(tmpDir)
        zipFileName = tmpDir + '/' + 'texture.zip'
        zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
        for textureFile in textureFileList:
            arcName = os.path.basename(textureFile)
            zf.write(textureFile, arcName)
        zf.close()
        CGMaya_config.logger.info('Uploading Texture File...\r')
        textureFileID = service.putFile(CGMaya_config.currentTask, zipFileName)
        os.remove(zipFileName)

    service.myWFsetTaskRenderFrames(taskID, singleFrame, frameListStr)

    renderLayers = getRenderLayers()
    lightFileIDList = CGMaya_config.currentTask['lightFileIDList']
    for lightFile in lightFileIDList:
        if lightFile['name'] == os.path.basename(scene_fn):
            lightFile['id'] = lightFileID
            lightFile['renderLayers'] = renderLayers
            break
    else:
        lightFileIDList.append({'name': os.path.basename(scene_fn), 'id': lightFileID, 'renderLayers': renderLayers})
    service.myWFSetTaskLightFileIDList1(taskID, lightFileIDList, textureFileID)
    CGMaya_config.logger.info(u"文件已保存")
    return scene_fn

def saveLightTaskRenderwing(service, scene_fn, frameListStr):
    projectDir = CGMaya_config.storageDir + '/' + CGMaya_config.currentTask['projectName']
    renderWingDir = projectDir + '/' + CGMaya_config.currentTask['name'] + '/renderWing'
    if not os.path.exists(renderWingDir):
        os.mkdir(renderWingDir)

    existingSettings = cmds.ls(type='RWingRenderSettings')
    if existingSettings:
        # Just use the first one?
        CGMaya_config.renderSettingsSave = existingSettings[0]
        print("         Using existing RWing settings node : %s" % CGMaya_config.renderSettingsSave)
    else:
        CGMaya_config.renderSettingsSave = cmds.createNode('RWingRenderSettings', name='defaultRWingRenderGlobals',
                                                           shared=True)
        print("         Creating new RWing settings node : %s" % CGMaya_config.renderSettingsSave)

    frame = 1
    extensionPadding = cmds.getAttr("defaultRenderGlobals.extensionPadding")
    outFileName = renderWingDir + '/' + scene_fn + "_" + str(frame).zfill(extensionPadding) + '.xml'
    geometryFiles = RWingRendererIO.writeScene(outFileName, renderWingDir, CGMaya_config.renderSettingsSave, True)

    zipFileName = renderWingDir + '/renderwing.zip'
    if os.path.exists(zipFileName):
        os.remove(zipFileName)
    zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
    rwFileList = os.listdir(renderWingDir)
    for rwFile in rwFileList:
        arcName = rwFile
        rwFile = renderWingDir + '/' + rwFile
        zf.write(rwFile, arcName)
    zf.close()
    renderwingFileID = service.putFile(CGMaya_config.currentTask, zipFileName)

    renderLayers = getRenderLayers()
    renderwingFileIDList = CGMaya_config.currentTask['renderwingFileIDList']
    for renderwingFile in renderwingFileIDList:
        if renderwingFile['name'] == os.path.basename(scene_fn):
            renderwingFile['id'] = renderwingFileID
            renderwingFile['renderLayers'] = renderLayers
            break
    else:
        renderwingFileIDList.append({'name': os.path.basename(scene_fn), 'id': renderwingFileID, 'renderLayers': renderLayers})
    service.myWFSetTaskRenderwingFileIDList(CGMaya_config.currentTask['_id'], renderwingFileIDList)
    # CGMaya_config.logger.info('Uploading SingleFrame Output File...\r')
    # saveSingleOutput(service)
    CGMaya_config.logger.info(u"文件已保存")
    print('         Renderwing File is saved')
    return renderwingFileID

def getRenderLayers():
    renderLayerList = cmds.ls(type='renderLayer')
    renderRawLayers = []
    for layer in renderLayerList:
        if cmds.getAttr(layer + '.renderable'):
            renderRawLayers.append(layer)
    renderLayers = []
    for rawLayer in renderRawLayers:
        if rawLayer.find('defaultRenderLayer') < 0:
            renderLayers.append(rawLayer)
    return renderLayers

def submitTask(service, task, submitID, fileList, notes):
    submitFileIDList = []
    for file in fileList:
        if not os.path.exists(file):
            print('file is not Exist!!!---', file)
            continue
        id, sizeStr = service.putFile2(CGMaya_config.currentTask, file)
        submitFileIDList.append({'id': id, 'name': os.path.basename(file), 'size': sizeStr})
    if submitFileIDList:
        if submitID:
            service.myWFSetSubmitFileIDList(submitID, submitFileIDList, notes)
        else:
            service.myWFSetTaskSubmitFileIDList(task['_id'], submitFileIDList, notes)
    service.myWFSubmitTask(task['_id'])

def replaceRawAsset(service, ref, refProjectName, task):
    #sfn = openAsset(service, task['fileID'], task, CGMaya_config.assetStorageDir, True)
    sfn = openAsset(service, task['fileID'], task, CGMaya_config.assetStorageDir)
    fn = os.path.basename(sfn)
    CGMaya_config.refAssetIDList.append({'projectName': refProjectName, 'name': fn,
                                'id': task['fileID'], 'taskID': task['_id']})
    ref.replaceWith(sfn)
    #cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=fn.split('.')[0])
    #cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=':')

def replaceAsset(service, srcRefAssetID, destRefAssetTask):
    projectDir = os.path.join(CGMaya_config.storageDir, destRefAssetTask['projectName'])
    #sfn = openAsset(service, projectDir, projectDir, destRefAssetTask, True)
    sfn = openAsset(service, projectDir, projectDir, destRefAssetTask)
    refs = cmds.ls(type='reference')
    refnList = []
    for ref in refs:
        try:
            refn = cmds.referenceQuery(ref, f=True)
        except:
            continue
        refName = os.path.basename(refn)
        refAssetName = refName.split('.')[0]
        if refAssetName == srcRefAssetID['name']:
            refnList.append(refn)
            cmds.file(unloadReference=ref)
            cmds.file(cr=ref)
    srcRefAssetID['id'] = destRefAssetTask['assetID']
    srcRefAssetID['name'] = destRefAssetTask['name']
    srcRefAssetID['projectName'] = destRefAssetTask['projectName']
    for refn in refnList:
        cmds.file(refn, removeReference=True)
        cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=':')
        # cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=sfn.split('.')[0])True
    return

def referenceAsset(service, task, flag):
    CGMaya_config.successfulReadMayaFile = True
    if flag:  # reference Model
        #sfn = openAsset(service, task['fileID'], task, CGMaya_config.assetStorageDir, True )
        sfn = openAsset(service, task['fileID'], task, CGMaya_config.assetStorageDir)
        CGMaya_config.refAssetIDList.append({'projectName': CGMaya_config.refProjectName, 'name': task['name'],
                                             'id': task['fileID'], 'taskID': task['_id']})
        #cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=fn.split('.')[0])
        cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=task['name'])
    else:     # import Model
        #sfn = openAsset(service, task['fileID'], task, CGMaya_config.storageDir, True)
        sfn = openAsset(service, task['fileID'], task, CGMaya_config.storageDir)
        if CGMaya_config.successfulReadMayaFile:
            cmds.file(sfn, i=True)
    return True

def transferTexture(service):
    result = service.myWFGetAssetByName(CGMaya_config.currentTask['name'], CGMaya_config.currentTask['projectName'])
    CGMaya_config.currentAsset = json.loads(result)
    taskList = CGMaya_config.currentAsset['taskList']
    for task in taskList:
        if task['stage'] == u'贴图':
            srcID = task['_id']
            break
    else:
        print('Error')
        return
    srcTask = json.loads(service.myWFGetTaskInfo(srcID))
    if CGMaya_config.currentTask['fileID'] == srcTask['fileID']:
        cmds.confirmDialog(title=u'信息', message=u'贴图没有改变!!!', defaultButton=u'确认')
        return
    rDir = CGMaya_config.assetStorageDir + '/transfer'
    if not os.path.exists(rDir):
        os.mkdir(rDir)
    #sfn = openAsset(service, srcTask['fileID'], srcTask, rDir, True)
    sfn = openAsset(service, srcTask['fileID'], srcTask, rDir)

    objectList1 = cmds.ls(selection = True)
    #objectList1 = []
    if len(objectList1) < 1:
        objectList1 = cmds.ls(dagObjects = True, long = True, geometry = True, shapes = True, visible = True)
    ass1 = cmds.ls(assemblies = True)
    cmds.file(sfn, i = True, ns = 'ns')
    #cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace='ns')
    #cmds.file(sfn, reference=True, namespace='ns')

    delList = []
    objectList2 = cmds.ls(dag=True, l=True, g=True, s=True, v=True)
    for object1 in objectList1:
        for object2 in objectList2:
            if object1 == object2:
                continue
            obj1 = object1.split('|').pop()
            obj2 = object2.split('|').pop()
            if obj1 == obj2.split(':').pop():
                cmds.select([object2, object1])
                try:
                    cmds.polyTransfer(object1, uvSets = True, alternateObject = object2, constructionHistory = True)
                    #uvs = cmds.polyEvaluate(object1, uvComponent = True)
                    #-print 'uvs =', uvs
                except:
                    pass
                shaders = cmds.listConnections(object2, t='shadingEngine')
                if not shaders:
                    continue
                for shader in shaders:
                    cmds.sets(object1, forceElement=shader)

    ass2 = cmds.ls(assemblies=True)
    for ass in ass2:
        if ass not in ass1:
            pass
            #cmds.delete(ass)

def updateReference(service):
    cmds.waitCursor(state=True)
    projectDir = os.path.join(CGMaya_config.storageDir, CGMaya_config.projectName)

    refAssetIDList = getRefModelList(service)

    refChangeList = []
    for refAsset in refAssetIDList:
        list = json.loads(service.myWFGetTaskInfo(refAsset['id']))
        refTask = list[0]
        refModel = ''
        if refTask['stage'] == u'标准光':
            refModel = refTask
        if not refModel or refModel['fileID'] == refAsset['id']:
            continue
        refAsset['id'] = refModel['fileID']
        refChangeList.append({'name': refModel['name'], 'id': refModel['fileID']})
        refProjectDir = CGMaya_config.storageDir + '/' + refModel['projectName']
        taskDir = refProjectDir + '/' + refModel['name']
        fnn = service.getFileName(refModel, refModel['fileID'])
        sfn = taskDir + fnn
        if os.path.isfile(sfn):
            os.remove(sfn)
        service.getFile(refModel, sfn, refModel['fileID'], fnn)
        if CGMaya_config.currentTask['stage'] == u'布局' or CGMaya_config.currentTask['stage'] == u'动画':
            continue
        textureFileID = refModel['textureFileID']
        textureDir = taskDir + '/' + CGMaya_config.CGMaya_Texture_Dir
        textureFile = textureDir + '/texture.zip'
        service.getFile(refModel, textureFile, textureFileID, fnn)
        zf = zipfile.ZipFile(textureFile, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)
        zf.extractall(textureDir)
        zf.close()
    refs = pymel.core.listReferences()
    for ref in refs:
        rfn = ref.path
        refName = os.path.basename(rfn)
        for refn in refChangeList:
            if refn == refName.split('.')[0]:
                sfn = projectDir + '/' + refName
                ref.replaceWith(sfn)
    cmds.waitCursor(state=False)
    msg = ''
    for refName in refChangeList:
        msg = msg + refName['name'] + '-' + refName['id'] + '\n'
    if not msg:
        msg = u'没有模型引用更新'
    cmds.confirmDialog(title = u'更新引用模型列表', message = msg, defaultButton=u'确认')

def shotTransfer(service):
    pass

def gotoMari(service):
    cmds.file(CGMaya_config.MariObjFileName, pr = 1, type = "OBJexport", es = 1, \
                op = "groups = 0; ptgroups = 0 ; smoothing = 0; normals = 0", force=True)
    if platform.system() == 'Windows':
        command = CGMaya_config.MariCommand + ' C:/Users/HP/Documents/maya/2015-x64/zh_CN/scripts/RCMaya/RCMari.py'
        ret = subprocess.Popen(command, shell=True)

def saveRenderWingFile(service, project, task, lightFile):
    projectDir = CGMaya_config.storageDir + '/' + task['projectName']
    if not os.path.exists(CGMaya_config.storageDir):
        os.mkdir(CGMaya_config.storageDir)
    if not os.path.exists(CGMaya_config.assetStorageDir):
        os.mkdir(CGMaya_config.assetStorageDir)
    if not os.path.exists(projectDir):
        os.mkdir(projectDir)
    refProjectDir = CGMaya_config.assetStorageDir + '/' + project['refProject']
    taskFileName = openAsset(service, task['fileID'], task, CGMaya_config.storageDir)
    taskDir = projectDir + '/' + task['name']
    lightDir = taskDir + '/' + CGMaya_config.CGMaya_Light_Dir
    if not os.path.exists(lightDir):
        os.mkdir(lightDir)
    fn = service.getFileName(task, task['fileID'])
    lightFileName = lightDir + '/' + fn
    tmpFullFN = lightDir + '/' + 'tmp_' + fn.split('.')[0] + '.' + fn.split('.').pop()
    downloadFile(service, projectDir, task, lightFileName, CGMaya_config.taskFileID, tmpFullFN)
    CGMaya_config.logger.info("     Processing File-----%s\r" % lightFileName)
    processMaya(task['name'], tmpFullFN, lightFileName, projectDir, refProjectDir)
    CGMaya_config.logger.info("     Open File-----%s\r" % lightFileName)
    os.remove(tmpFullFN)

    renderWingDir = projectDir + '/' + task['name'] + '/renderWing'
    if not os.path.exists(renderWingDir):
        os.mkdir(renderWingDir)

    existingSettings = cmds.ls(type='RWingRenderSettings')
    if existingSettings:
        # Just use the first one?
        CGMaya_config.renderSettingsSave = existingSettings[0]
        print("         Using existing RWing settings node : %s" % CGMaya_config.renderSettingsSave)
    else:
        CGMaya_config.renderSettingsSave = cmds.createNode('RWingRenderSettings', name='defaultRWingRenderGlobals',
                                                           shared=True)
        print("         Creating new RWing settings node : %s" % CGMaya_config.renderSettingsSave)

    frame = 1
    extensionPadding = cmds.getAttr("defaultRenderGlobals.extensionPadding")
    outFileName = renderWingDir + '/' + CGMaya_config.sceneName + "_" + str(frame).zfill(extensionPadding) + '.xml'
    geometryFiles = RWingRendererIO.writeScene(outFileName, renderWingDir, CGMaya_config.renderSettingsSave, True)

    zipFileName = renderWingDir + '/renderwing.zip'
    if os.path.exists(zipFileName):
        os.remove(zipFileName)
    zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
    rwFileList = os.listdir(renderWingDir)
    for rwFile in rwFileList:
        arcName = rwFile
        rwFile = renderWingDir + '/' + rwFile
        zf.write(rwFile, arcName)
    zf.close()
    renderWingFileID = service.putFile(task, zipFileName)
    print('         Renderwing File is saved')
    return 'renderwing.zip', renderWingFileID

def readConfigFile2(ConfigFilePath):
    CGMaya_config.ConfigFileName = os.path.join(ConfigFilePath, CGMaya_config.ConfigFileName)
    if os.path.exists(CGMaya_config.ConfigFileName):
        with open(CGMaya_config.ConfigFileName, 'r') as fp:
            config = json.load(fp)
        CGMaya_config.IPFSUrl = config['IPFSUrl']
        CGMaya_config.teamName = config['teamName']
        CGMaya_config.userName = config['userName']
        CGMaya_config.password = config['password']
        CGMaya_config.softwareVersion = config['softwareVersion']
        return True
    else:
        return False

def writeConfigFile2():
    config = {'myRootURL': CGMaya_config.myRootURL,
              'IPFSUrl': CGMaya_config.IPFSUrl,
              'teamName': CGMaya_config.teamName,
              'userName': CGMaya_config.userName,
              'password': CGMaya_config.password,
              'softwareVersion': CGMaya_config.softwareVersion
              }
    with open(CGMaya_config.ConfigFileName, 'w') as fp:
        json.dump(config, fp, indent=4)

def readConfigFile_user2():
    ext = CGMaya_config.ConfigFileName.split('.').pop()
    configFileName_user = CGMaya_config.ConfigFileName.split('.')[
                                            0] + '_' + CGMaya_config.userName + '.' + ext
    configFilePath = os.path.dirname(CGMaya_config.ConfigFileName)
    CGMaya_config.ConfigFileName_user = os.path.join(configFilePath, configFileName_user)
    if os.path.exists(CGMaya_config.ConfigFileName_user):
        with open(CGMaya_config.ConfigFileName_user, 'r') as fp:
            config = json.load(fp)
        CGMaya_config.assetStorageDir = config['assetStorageDir']
        CGMaya_config.storageDir = config['storageDir']
        return True
    else:
        return False

def writeConfigFile_user2():
    config = {
              'storageDir': CGMaya_config.storageDir,
              'assetStorageDir': CGMaya_config.assetStorageDir
              }
    with open(CGMaya_config.ConfigFileName_user, 'w') as fp:
        json.dump(config, fp, indent=4)

def singleRender(service):
    pass

def gotoNuke(service):
    CGMaya_config.logger.info('Uploading SingleFrame Output File...\r')
    saveSingleOutput(service)
    """
    writeConfigFile()

    CGMaya_config.logger.set("gotoNuke")
    projectName = CGMaya_config.currentTask['projectName']
    taskName = CGMaya_config.currentTask['name']
    taskID = CGMaya_config.currentTask['_id']
    projectDir = CGMaya_config.storageDir + '/' + projectName
    scriptFilePath = CGMaya_config.sysStorageDir + '/' + 'gotoNuke.py'
    print 'scriptFilePath =', scriptFilePath
    fp = open(scriptFilePath, 'w')
    fp.write('# coding=utf-8\n')
    fp.write('import os\n')
    dir = os.path.dirname(CGMaya_config.nukeScriptPath)
    fp.write('os.sys.append("' + dir + '")\n')
    fp.write('import CGNuke\n')
    teamName = CGMaya_config.teamName
    userName = CGMaya_config.userName
    password = CGMaya_config.password
    fp.write('CGNuke.CGMain_nuke.mayaStart(' + teamName + ', ' + userName + ', ' +
                                   password + ', ' + projectName + ', ' + taskName + ')\n')
    fp.close()
    commandList = []
    if platform.system() == 'Windows':
        commandList.append(CGMaya_config.nukePath)
        commandList.append(scriptFilePath)
        nukeProcess = subprocess.Popen(commandList)
        print 'nukeProcess =', nukeProcess
    """

def saveSingleOutput(service):
    projectName = CGMaya_config.currentTask['projectName']
    taskName = CGMaya_config.currentTask['name']
    lightFileIDList = CGMaya_config.currentTask['lightFileIDList']

    zipFileName = CGMaya_config.singleOutputPath + '/' + taskName + '_s.zip'
    zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
    rootDir = CGMaya_config.singleOutputPath + '/images/tmp'

    for lightFileID in lightFileIDList:
        lightFilePath = CGMaya_config.singleOutputPath + '/images/tmp/' + lightFileID['name']
        lightDir = lightFilePath.split('.')[0]
        if not os.path.isdir(lightDir):
            continue
        dirList = os.listdir(lightDir)
        for dir in dirList:
            dirPath = lightDir + '/' + dir
            fileList = os.listdir(dirPath)
            for file in fileList:
                filePath = dirPath + '/' + file
                if os.path.isdir(filePath):
                    subFileList = os.listdir(filePath)
                    for subFile in subFileList:
                        subFilePath = filePath + '/' + subFile
                        zf.write(subFilePath, dir + '/' + file + '/' + subFile)
                else:
                    zf.write(filePath, dir + '/' + file)
    zf.close()
    fileID = service.putFile(CGMaya_config.currentTask, zipFileName)
    service.myWFSetTaskSingleOutputID(CGMaya_config.currentTask['_id'], fileID)

def redshiftToRenderWingByTexture():
    pass

def checkSoftwareVersion(service):
    presetsDir = cmds.internalVar(userPresetsDir=True)
    presetsDir = presetsDir.lower()
    version = presetsDir.split('/maya/').pop()
    version = version.split('/')[0]
    projectInfo = json.loads(service.myWFGetProjectInfo(CGMaya_config.currentTask['projectName']))
    version1 = projectInfo['designTool'].lower().split('maya').pop()
    print version, version1
    return version == version1

def getStorageDir(self):
    def get_free_space_mb(folder):
        """ Return folder/drive free space (in bytes)
        """
        if platform.system() == 'Windows':
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None,
                                                       ctypes.pointer(free_bytes))
            return free_bytes.value / 1024 / 1024 / 1024
        else:
            st = os.statvfs(folder)
            return st.f_bavail * st.f_frsize / 1024 / 1024

    def drivesList():
        drive_list = []
        for drive in range(ord('A'), ord('F')):
            if os.path.exists(chr(drive) + ':'):
                drive_list.append(chr(drive))
        return drive_list

    total = 0
    for drive in drivesList():
        size = get_free_space_mb(drive + ':\\')
        if total < size:
            total = size
            path = drive + ':\\'
    path = path + CGMaya_config.project_Dir
    if not os.path.exists(path):
        os.mkdir(path)
    return path

def getStorageSize(dir):
    if platform.system() == 'Windows':
        drive = dir.split(':')[0]
        folder = drive + ':\\'
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None,
                                                   ctypes.pointer(free_bytes))
        storageSize = free_bytes.value / 1024 / 1024 / 1024
    else:
        st = os.statvfs(dir)
        storageSize = st.f_bavail * st.f_frsize / 1024 / 1024
    return str(storageSize * 1024 * 1024) + 'MB'
