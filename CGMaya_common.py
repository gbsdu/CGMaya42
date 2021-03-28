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

def maya_main_window():
    main_win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtCGMaya.QWidget)

def makeDir(dir, name):
    #dir = os.path.join(dir, name)
    dir = dir + '/' + name
    if not os.path.exists(dir):
        os.mkdir(dir)
    return dir

def readConfigFile(ConfigFilePath):
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

def writeConfigFile():
    config = {'myRootURL': CGMaya_config.myRootURL,
              'IPFSUrl': CGMaya_config.IPFSUrl,
              'teamName': CGMaya_config.teamName,
              'userName': CGMaya_config.userName,
              'password': CGMaya_config.password,
              'softwareVersion': CGMaya_config.softwareVersion
              }
    with open(CGMaya_config.ConfigFileName, 'w') as fp:
        json.dump(config, fp, indent=4)

def readConfigFile_user():
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

def writeConfigFile_user():
    config = {
              'storageDir': CGMaya_config.storageDir,
              'assetStorageDir': CGMaya_config.assetStorageDir
              }
    with open(CGMaya_config.ConfigFileName_user, 'w') as fp:
        json.dump(config, fp, indent=4)


class fileLog:
    def __init__(self, filePath):
        self.filePath = filePath
        if os.path.isfile(self.filePath):
            with open(self.filePath, "r") as json_file:
                self.logJsonData = json.load(json_file)
        else:
            self.logJsonData = []

    def __del__(self):
        self.close()

    def getData(self, fileName, fileID):
        if not self.logJsonData:
            return 0
        for log in self.logJsonData:
            if log['fileName'] == fileName and log['id'] == fileID:
                return 2
            elif log['fileName'] == fileName and log['id'] != fileID:
                log['id'] = fileID
                return 1
        return 0

    def setData(self, fileName, fileID):
        self.logJsonData.append({"fileName": fileName, 'id': fileID})

    def close(self):
        with open(self.filePath, "w") as json_file:
            json.dump(self.logJsonData, json_file)

def judgelogData(logJsonData, fileName, fileID):
    for log in logJsonData:
        if log['fileName'] == fileName and log['id'] == fileID:
            return 2
        elif log['fileName'] == fileName and log['id'] != fileID:
            log['id'] = fileID
            return 1
    return 0

def convertTextureFile(textureDir):
    if platform.system() == "Linux" or platform.system() == "Darwin":
        return
    userScriptDir = cmds.internalVar(userScriptDir=True)
    exeFile = userScriptDir.replace('/', '\\') + 'CGMaya\\redshiftTextureProcessor.exe'
    for fn in os.listdir(textureDir):
        path = textureDir + fn
        ext = path.split('.').pop()
        if ext == 'rstexbin' or ext == 'rs':
            continue
        command = exeFile + ' ' + path
        subprocess.Popen(command, shell=True)
    # for refAssetID in CGMaya_config.currentTask['refAssetIDList']:
    #     for fn in os.listdir(textureDir):
    #         path = textureDir + fn
    #         ext = path.split('.').pop()
    #         if ext == 'rstexbin' or ext == 'rs':
    #             continue
    #         command = exeFile + ' ' + path
    #         subprocess.Popen(command, shell=True)

taskStageList = [u'布局', u'动画', u'灯光']

def downloadFile(service, projectDir, refProjectDir, task, fileID, textureFileID='', dir=''):
    if dir:
        taskDir = dir
    else:
        taskDir = makeDir(projectDir, task['name'])
    fn = service.getFileName(task, fileID)
    filePath = os.path.join(taskDir, fn)
    tmpDir = makeDir(projectDir, CGMaya_config.CGMaya_Tmp_Dir)
    downLoadFilePath = os.path.join(tmpDir, 'tmp.' + fn.split('.').pop())
    logPath = makeDir(projectDir, CGMaya_config.CGMaya_Log_Dir)
    lockFilePath = os.path.join(logPath, task['name'] + CGMaya_config.lockFileExt)
    print('lockFilePath =', lockFilePath)
    if os.path.exists(lockFilePath):
        str = u'文件正在被其他用户下载。。。，请等待--' + task['name']
        QtCGMaya.QMessageBox.information(CGMaya_config.currentDlg, u"提示信息", str, QtCGMaya.QMessageBox.Yes)
        return False, str, ''

    with open(lockFilePath, 'w') as lockFP:
        lockFP.write('jjj')
    logFilePath = os.path.join(logPath, task['name'] + CGMaya_config.logFileExt)
    fLog = fileLog(logFilePath)
    taskDir = makeDir(projectDir, task['name'])
    tmpDir = makeDir(projectDir, CGMaya_config.CGMaya_Tmp_Dir)
    fileName = os.path.basename(filePath)
    bExist = fLog.getData(fileName, fileID)
    if not os.path.exists(filePath) or bExist != 2:
        CGMaya_config.logger.info("Downloading File begin----%s\r" % filePath)
        begin = time.time()
        service.getFile(task, downLoadFilePath, fileID, fileName)
        #CGMaya_config.textureReadFlag = False
        if textureFileID and CGMaya_config.textureReadFlag and not task['stage'] in taskStageList:
            textureDir = makeDir(taskDir, CGMaya_config.CGMaya_Texture_Dir)
            textureFileName = service.getFileInfo(textureFileID).filename
            texturePath = os.path.join(tmpDir, textureFileName)
            CGMaya_config.logger.info("Downloading texture File-----%s\r" % texturePath)
            service.getFile(task, texturePath, textureFileID, textureFileName)
            zf = zipfile.ZipFile(texturePath, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)
            fileList = zf.namelist()
            for names in fileList:
                try:
                    zf.extract(names, path=textureDir)
                except Exception as e:
                    print 'File Read is failed----', names
            zf.close()
            project = service.getProjectInfo(task['projectName'])
            if project['render'] == 'redshift':
                convertTextureFile(textureDir)
            for file1 in fileList:
                if file1.split('.').pop() == 'rs':  # redshift Proxy
                    file = os.path.join(textureDir, file1)
                    bakFile = file.split('.')[0] + '.bak'
                    CGMaya_config.logger.info("     Processing Proxy File-----%s\r" % file)
                    if os.path.exists(file):
                        parser = CGMaya_parser.processRedshiftProxyFile(file, bakFile)
                        parser.replaceFilePath()
                        shutil.copy(bakFile, file)
                        os.remove(bakFile)
                    else:
                        CGMaya_config.logger.info('Proxy File is not existed---%s\r' % file)
            os.remove(texturePath)
        if bExist == 0:
            fLog.setData(fileName, fileID)
        end = time.time()
        str = '{0:.2f}'.format(end - begin) + 's'
        CGMaya_config.logger.info("Downloading File end----%s\r" % str)
        processMaya(task['name'], downLoadFilePath, filePath, projectDir, refProjectDir)
        os.remove(downLoadFilePath)
    fLog.close()
    # try:
    #     textureAttachIDList = task['textureAttachIDList']
    #     for textureAttachID in textureAttachIDList:
    #
    # except KeyError:
    #     pass
    if os.path.exists(lockFilePath):
        os.remove(lockFilePath)
    return True, '', filePath

def processMaya(assetName, fileName_in, fileName_out, projectDir, refProjectDir):
    CGMaya_config.logger.info('processMaya---%s %s\r' % (fileName_in, fileName_out))
    parser = CGMaya_parser.mayaParser(fileName_in)
    refList, textureList = parser.replaceFilePath(assetName, fileName_out, projectDir, refProjectDir)
    return refList, textureList

