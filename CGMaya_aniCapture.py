#coding=utf-8

import os
import re
import platform

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

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.cmds as cmds
import pymel.core as pm
import json
import datetime
import random
import subprocess
import urllib2
import shutil
import zipfile
import time
from datetime import datetime, timedelta
import wave
import ctypes
#import pytz
import random

import CGMaya_config
import CGMaya_common
import CGMaya_service
import CGMaya_parser


def maya_HUD_set(v=0):
    setVisStr = '\n    setSelectDetailsVisibility\n    setObjectDetailsVisibility\n    setParticleCountVisibility\n    setPolyCountVisibility\n    setAnimationDetailsVisibility\n    setHikDetailsVisibility\n    setFrameRateVisibility\n    setCurrentFrameVisibility\n    setSceneTimecodeVisibility\n    setCurrentContainerVisibility\n    setViewportRendererVisibility\n    setCameraNamesVisibility\n    setFocalLengthVisibility\n    '
    for x in setVisStr.split():
        if pm.mel.eval('exists %s' % x):
            pm.mel.eval('%s(%d)' % (x, v))

    pm.mel.eval('setViewAxisVisibility(1)')


def get_camSize():
    w = pm.PyNode('defaultResolution').width.get()
    h = pm.PyNode('defaultResolution').height.get()
    return '%d×%d' % (w, h)


def get_sceneName():
    return pm.sceneName().namebase


def get_username():
    if not pm.objExists('defaultObjectSet.userName'):
        pm.addAttr('defaultObjectSet', ln=CGMaya_config.userName, dt='string')
    else:
        pm.setAttr('defaultObjectSet.userName', CGMaya_config.userName, typ='string')
    return CGMaya_config.userName


def set_frameRate(typ='film'):
    pm.currentUnit(time=typ)


def get_frameRate():
    tm = pm.currentUnit(q=True, time=True)
    if tm == 'pal':
        return '  Real [25 fps]'
    if tm == 'film':
        return '  Real [24 fps]'


def get_timeTable():
    tmin = pm.playbackOptions(q=True, min=True)
    tmax = pm.playbackOptions(q=True, max=True)
    return '%d-%d' % (tmin, tmax)


def get_frame():
    ctime = pm.currentTime()
    tmax = pm.playbackOptions(q=True, max=True)
    return '%d/%d' % (ctime, tmax)


def getCurrentTime():
    return pm.date()


def get_zeroParallax():
    if pm.objExists('StereoCamCenterCamShape'):
        return pm.Attribute('StereoCamCenterCamShape.zeroParallax').get()


def get_eyeLength():
    if pm.objExists('StereoCamCenterCamShape'):
        return pm.Attribute('StereoCamCenterCamShape.interaxialSeparation').get()


def get_currentlyCam():
    mp = pm.getPanel(withFocus=True)
    mp_name = mp.name()
    if 'modelPanel' in mp_name:
        return pm.modelPanel(mp, q=True, camera=True)
    if 'StereoPanel' in mp_name:
        return 'StereoCamCenterCamShape'


def get_focalLength():
    cam = get_currentlyCam()
    if cam is not None:
        return pm.PyNode(cam).focalLength.get()
    else:
        return


def intilize():
    if not pm.headsUpDisplay('cbd_HUD_camSize', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_camSize', section=1, block=2)
        pm.headsUpDisplay('cbd_HUD_camSize', e=True, section=1, block=1, blockAlignment='center', dataWidth=10, label='CamSize:', command=get_camSize, dataFontSize='large', attributeChange='defaultResolution.width')
    if not pm.headsUpDisplay('cbd_HUD_producerName_name', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_producerName_name', section=3, block=1)
        pm.headsUpDisplay('cbd_HUD_producerName_name', e=True, section=3, block=1, blockSize='small', blockAlignment='right', dataFontSize='large', label='user:', command=get_username, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_producerName_label', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_producerName_label', section=3, block=2)
        pm.headsUpDisplay('cbd_HUD_producerName_label', e=True, section=3, block=2, blockAlignment='right', label='producerName:', command=get_sceneName)
    if not pm.headsUpDisplay('cbd_HUD_frameRate', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_frameRate', section=5, block=7)
        pm.headsUpDisplay('cbd_HUD_frameRate', e=True, section=5, block=4, blockAlignment='left', dataWidth=50, dataFontSize='large', decimalPrecision=1, command=get_frameRate, event='timeUnitChanged')
    if not pm.headsUpDisplay('cbd_HUD_timeTable', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_timeTable', section=5, block=6)
        pm.headsUpDisplay('cbd_HUD_timeTable', e=True, section=5, block=3, blockAlignment='left', label='TimeTable:', dataWidth=50, dataFontSize='large', decimalPrecision=1, command=get_timeTable, event='playbackRangeChanged')
    if not pm.headsUpDisplay('cbd_HUD_frame', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_frame', section=5, block=5)
        pm.headsUpDisplay('cbd_HUD_frame', e=True, section=5, block=2, blockAlignment='left', label='Frame:', dataWidth=50, dataFontSize='large', decimalPrecision=1, command=get_frame, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_date', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_date', section=5, block=5)
        pm.headsUpDisplay('cbd_HUD_date', e=True, section=5, block=1, blockAlignment='left', label='Date:', dataWidth=50, dataFontSize='large', decimalPrecision=1, command=getCurrentTime, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_zeroParallax', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_zeroParallax', section=8, block=5)
        pm.headsUpDisplay('cbd_HUD_zeroParallax', e=True, section=8, block=5, blockAlignment='left', label='ZeroParallax:', dataWidth=50, dataFontSize='large', decimalPrecision=1, command=get_zeroParallax, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_focalLength', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_focalLength', section=8, block=4)
        pm.headsUpDisplay('cbd_HUD_focalLength', e=True, section=8, block=4, blockAlignment='left', label='FocalLength:', labelWidth=100, dataWidth=100, dataFontSize='large', decimalPrecision=5, command=get_focalLength, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_eyeLength', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_eyeLength', section=8, block=3)
        pm.headsUpDisplay('cbd_HUD_eyeLength', e=True, section=8, block=3, blockAlignment='left', label='EyeLength:', labelWidth=100, dataWidth=100, dataFontSize='large', decimalPrecision=5, command=get_eyeLength, attachToRefresh=True)
    if not pm.headsUpDisplay('cbd_HUD_camName', q=True, ex=True):
        pm.headsUpDisplay('cbd_HUD_camName', section=8, block=2)
        pm.headsUpDisplay('cbd_HUD_camName', e=True, section=8, block=2, blockAlignment='left', label='CurrentlyCam:', labelWidth=100, dataWidth=100, dataFontSize='large', decimalPrecision=1, command=get_currentlyCam, attachToRefresh=True)
    maya_HUD_set(0)

def setDataColor(v=17):
    try:
        pm.displayColor('headsUpDisplayValues', v, dormant=True)
        print '\nDisplay color set success !'
    except:
        pass

def getAll():
    listHeadsUpDisplays = pm.headsUpDisplay(listHeadsUpDisplays=True)
    return [ x for x in listHeadsUpDisplays if 'cbd_HUD_' in x ]


def playblast1(**kw):
    print('playblast1')
    kw.setdefault('format', 'movie')
    kw.setdefault('forceOverwrite', True)
    kw.setdefault('sequenceTime', 0)
    kw.setdefault('clearCache', 1)
    kw.setdefault('viewer', 1)
    kw.setdefault('showOrnaments', 1)
    kw.setdefault('percent', 50)
    kw.setdefault('widthHeight', [2048, 858])
    kw.setdefault('quality', 100)
    kw.setdefault('compression', 'MS-CRAM')
    kw.setdefault('offScreen', 1)
    sound = pm.mel.eval('timeControl -q -sound $gPlayBackSlider')
    if sound != '':
        kw.setdefault('sound', sound)
    else:
        sounds = pm.ls(type='audio')
        if len(sounds) == 1:
            kw.setdefault('sound', str(sounds[0]))
        cmdStr = 'pm.playblast('
        for k, v in kw.iteritems():
            print k, v
            cmdStr += k + '=' + str(v) + ', '

    cmdStr += ')'
    print('playblast1---------')
    print '-' * 40
    print cmdStr
    return pm.playblast(**kw)


def playblast(**kw):
    print('playblast')
    projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, CGMaya_config.currentProject['name'])
    taskDir = CGMaya_common.makeDir(projectDir, CGMaya_config.currentTask['name'])

    rand = random.randint(0, 10000)
    file_path = os.path.join(taskDir, CGMaya_config.currentTask['name'] + '_' + str(rand) + '.avi')

    if 'widthHeight' not in kw:
        dr = pm.PyNode('defaultResolution')
        kw['widthHeight'] = (dr.w.get(), dr.h.get())
    fpath = kw.setdefault('filename', file_path)
    playblast1(**kw)
    return file_path


def capture(service):
    cbd_HUDs = getAll()
    if not len(cbd_HUDs):
        intilize()
        setDataColor(v=17)
    else:
        for hud in cbd_HUDs:
            pm.headsUpDisplay(hud, e=True, remove=True)

        setDataColor(v=16)

    allFormats = pm.playblast(q=True, format=True)
    format = 'qt'
    compression = 'H.264'
    if format not in allFormats:
        format = 'avi'
        compression = 'MS-CRAM'
    kwargs = {'compression': compression, 'format': format}
    # kwargs.update(kw)
    file_path = playblast(percent=100, **kwargs)

    submitFileID = service.putFile(CGMaya_config.currentTask, file_path)
    length = os.path.getsize(file_path)
    dr = pm.PyNode('defaultResolution')
    width = dr.w.get()
    height = dr.h.get()
    name = os.path.basename(file_path)
    type = 'video'

    submit = service.createSubmit2(CGMaya_config.currentTask['_id'], submitFileID,
                                        name, length, width, height, type)

    service.submitTask2(CGMaya_config.currentTask['_id'], submit['_id'])

    CGMaya_config.logger.info('file is saved')

    CGMaya_config.logger.server(CGMaya_config.currentProject['name'], CGMaya_config.currentTask['name'],
                                CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Submit)

    # NOTE 输出成功信息
    QtCGMaya.QMessageBox.information(None, u"输出完成", u"图片输出成功\n输出路径:%s" % file_path)

