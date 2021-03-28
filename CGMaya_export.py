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


def getSubstancePainterPath():
    return 'C:\Program Files\Allegorithmic\Substance Painter\Substance Painter.exe'


def exportMeshToSubstancePainter(service, dlg):
    """
    if CGMaya_config.currentTask['stage'] != u'贴图':
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有贴图任务", QtCGMaya.QMessageBox.Yes)
        return

    if not CGMaya_config.currentTask['projectName']:
        return

    #sys.path.append(os.path.dirname(__file__) + '/ObjectExporter')
    import ObjectExporter
    ui = ObjectExporter.ObjectExporterUI()
    ui.show()
    """

    if not CGMaya_config.currentTask['projectName']:
        return
    projectName = CGMaya_config.currentTask['projectName']
    taskName = CGMaya_config.currentTask['name']
    print projectName, taskName
    projectDir = CGMaya_config.storageDir + '/' + projectName
    taskDir = projectDir + '/' + taskName
    textureDir = taskDir + '/texture'
    if not os.path.exists(textureDir):
        os.mkdir(textureDir)

    objFile = taskDir + '/' + taskName + '.obj'
    cmds.file(rename=objFile)
    cmds.file(save=True, type='OBJexport', force=True)
    #abcPath = exportAbc(dlg, os.getenv("TEMP"))

    from SubstancePainterToMaya import main
    main.SPtoM()

    SubstancePainterPath = getSubstancePainterPath()
    command = '"' + SubstancePainterPath + '" --mesh ' + objFile + ' --export-path ' + textureDir + ' ' + taskDir
    print 'command =', command
    subprocess.Popen(command, shell=None)
    return


def getMariPath():
    return 'C:/Program Files/Mari2.6v2/Bundle/bin/Mari2.6v2.exe'

def exportMeshToMari(service, dlg):
    if CGMaya_config.currentTask['stage'] != u'贴图':
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有贴图任务", QtCGMaya.QMessageBox.Yes)
        return
    if not CGMaya_config.currentTask['projectName']:
        return
    """
    selectGeo = cmds.ls(sl=True)
    if not selectGeo:
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有选择对象", QtCGMaya.QMessageBox.Yes)
        return ''
    """
    #mariPath = getMariPath()
    mariPath = CGMaya_config.mariPath
    mariScriptPath = cmds.internalVar(userScriptDir=True) + 'CGMaya/Scripts/mariMeBridge.py'
    command = '"' + mariPath + '" ' + mariScriptPath
    ####"C:\Program Files\Side Effects Software\Houdini 16.5.268/bin/houdinifx.exe" D:/CGHoudini/CGMayaToHoudini.py
    print 'command =', command
    subprocess.Popen(command, shell=None)
    mayaScriptPath = cmds.internalVar(userScriptDir=True) + 'CGMaya/Scripts/mariMe.py'
    cmds.loadPlugin(mayaScriptPath)
    return

def getHoudiniPath():
    try:
        key = _winreg.OpenKey(
            _winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Side Effects Software",
            0,
            _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
        )
        validVersion = (_winreg.QueryValueEx(key, "ActiveVersion"))[0]

        key = _winreg.OpenKey(
            _winreg.HKEY_LOCAL_MACHINE,
            "SOFTWARE\\Side Effects Software\\Houdini " + validVersion,
            0,
            _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
        )

        return (_winreg.QueryValueEx(key, "InstallPath"))[0]

    except:
        return ""

def exportAbcToHoudini(service, dlg):
    if not CGMaya_config.currentTask['projectName']:
        return
    projectName = CGMaya_config.currentTask['projectName']
    taskName = CGMaya_config.currentTask['name']
    print projectName, taskName
    taskList = service.myWFsearchTask(taskName, projectName)
    vfxTask = None
    for task in taskList:
        if task['stage'] == '特效':
            vfxTask = task
            break
    else:
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有特效任务", QtCGMaya.QMessageBox.Yes)
        return
    projectDir = CGMaya_config.storageDir + '/' + projectName
    taskDir = projectDir + '/' + taskName
    abcPath = exportAbc(dlg, os.getenv("TEMP"))
    print 'abcPath =', abcPath
    if not abcPath:
        return
    dict_all = {'myRootURL': CGMaya_config.myRootURL,
                'IPFSUrl': CGMaya_config.IPFSUrl,
                'teamName': CGMaya_config.teamName,
                'userName': CGMaya_config.userName,
                'password': CGMaya_config.password,
                'vfxTaskID': vfxTask['_id'],
                'abcPath': abcPath}

    with open("%s\%s.json" % (os.getenv("TEMP"), "abc"), "w") as files:
        end = json.dumps(dict_all, indent = 4)
        files.write(end)
    scriptPath = 'D:/CGHoudini/CGMayaToHoudini.py'
    if not os.path.isfile(scriptPath):
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有找到python文件:" + scriptPath, QtCGMaya.QMessageBox.Yes)
        return
    HoudiniPath = getHoudiniPath()
    command = '"' + HoudiniPath + '/bin/houdinifx.exe"' + " " + scriptPath
    ####"C:\Program Files\Side Effects Software\Houdini 16.5.268/bin/houdinifx.exe" D:/CGHoudini/CGMayaToHoudini.py
    print 'command =', command
    subprocess.Popen(command, shell=None)
    return

def exportAbc(dlg, abcPath):
    print 'abcPath =', abcPath
    abcPath = abcPath.replace('\\', '/')
    selectGeo = cmds.ls(sl=True)
    if not selectGeo:
        QtCGMaya.QMessageBox.information(dlg, u"提示信息", u"没有选择对象", QtCGMaya.QMessageBox.Yes)
        return ''
    startTime = cmds.playbackOptions(q=True, min=True)
    endTime = cmds.playbackOptions(q=True, max=True)
    print 'selectGeo =', selectGeo
    selectGeoName = selectGeo[0].split(':').pop()
    print 'selectGeoName =', selectGeoName
    # mel.eval('AbcExport -j "-frameRange %d %d -dataFormat ogawa -root |%s -file %s";' % (startTime, endTime, selectGeo[0], abcPath))
    melStr = 'AbcExport -j "-frameRange %d %d -dataFormat ogawa -root |%s -file %s/%s.abc";' % (startTime, endTime, selectGeo[0], abcPath, selectGeoName)
    print 'melStr =', melStr
    mel.eval('AbcExport -j "-frameRange %d %d -dataFormat ogawa -root |%s -file %s/%s.abc";' % (startTime, endTime, selectGeo[0], abcPath, selectGeoName))
    return "%s/%s.abc" % (abcPath, selectGeoName)


def exportFbx(service):
    filename = cmds.file(q=True, sn=True)

    # build the fbx filename
    ext = filename.split('.').pop()
    filename = filename.replace('.' + ext, '.fbx')

    # select the root bone in the scene
    cmds.select("Root")

    # select all joints in the hierarchy
    jointHierarchy = cmds.select(cmds.ls(dag=1, sl=1, type='joint'))

    # Export the given fbx filename
    mel.eval(('FBXExport -f \"{}\" -s').format(filename))