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



def assetCheckin(service):
    projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, CGMaya_config.currentProject['name'])
    taskDir = CGMaya_common.makeDir(projectDir, CGMaya_config.currentTask['name'])
    rand = random.randint(0, 10000)
    file_path = os.path.join(taskDir, CGMaya_config.currentTask['name'] + '_' + str(rand) + '.inf')

    # tex = checkAnim()

    # with open(file_path, 'w') as fp:
    #     fp.write(tex.encode('gbk'))


def aniCheckin(service):
    projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, CGMaya_config.currentProject['name'])
    taskDir = CGMaya_common.makeDir(projectDir, CGMaya_config.currentTask['name'])
    rand = random.randint(0, 10000)
    file_path = os.path.join(taskDir, CGMaya_config.currentTask['name'] + '_' + str(rand) + '.inf')

