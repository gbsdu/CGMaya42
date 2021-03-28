#coding=utf-8

import os
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

import maya.OpenMayaUI as OpenMayaUI
import maya.mel as mel
import maya.cmds as cmds
import pymel.core
import json
import datetime
import random
import subprocess
import urllib2
import shutil
import zipfile
import time
from datetime import datetime, timedelta
import copy
if platform.system() == 'Windows':
    import pyaudio
import wave
import ctypes
#import pytz

import RWingRendererIO

import CGMaya_config
import CGMaya_common
import CGMaya_service
import CGMaya_parser
import CGMaya_mouse


class referenceAssetWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, wayflag, parent=CGMaya_common.maya_main_window()):
        super(referenceAssetWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.wayflag = wayflag
        self.refProjectName = CGMaya_config.currentProject['refProject']
        self.dispFlag = 0
        if menu:
            self.menu.setEnable(False)
        #else:
        #    self.parent1.setEnable(False)
        self.dbFlag = False
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.projectLabel = QtCGMaya.QLabel(u'项目', self)
        else:
            self.projectLabel = QtCGMaya.QLabel(u'Project', self)
        self.projectText = QtCGMaya.QLineEdit('', self)
        self.projectText.setEnabled(False)

        self.layout.addWidget(self.projectLabel, 0, 0)
        self.layout.addWidget(self.projectText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.verRadiobutton = QtCGMaya.QRadioButton(u'所有', self)
            self.lightRadiobutton = QtCGMaya.QRadioButton(u'角色', self)
            self.radiobutton5 = QtCGMaya.QRadioButton(u'场景', self)
            self.radiobutton6 = QtCGMaya.QRadioButton(u'道具', self)
            #self.radiobutton7 = QtCGMaya.QRadioButton(u'特效', self)
            self.radiobutton8 = QtCGMaya.QRadioButton(u'灯光', self)
            self.radiobutton9 = QtCGMaya.QRadioButton(u'其他', self)
        else:
            self.verRadiobutton = QtCGMaya.QRadioButton(u'ALL', self)
            self.lightRadiobutton = QtCGMaya.QRadioButton(u'CHR', self)
            self.radiobutton5 = QtCGMaya.QRadioButton(u'LOC', self)
            self.radiobutton6 = QtCGMaya.QRadioButton(u'PRO', self)
            #self.radiobutton7 = QtCGMaya.QRadioButton(u'VFX', self)
            self.radiobutton8 = QtCGMaya.QRadioButton(u'LIT', self)
            self.radiobutton9 = QtCGMaya.QRadioButton(u'OTH', self)
        self.verRadiobutton.setChecked(True)
        self.lightRadiobutton.setChecked(False)
        self.radiobutton5.setChecked(False)
        self.radiobutton6.setChecked(False)
        #self.radiobutton7.setChecked(False)
        self.radiobutton8.setChecked(False)
        self.radiobutton9.setChecked(False)

        self.layout.addWidget(self.verRadiobutton, 0, 0)
        self.layout.addWidget(self.lightRadiobutton, 0, 1)
        self.layout.addWidget(self.radiobutton5, 0, 2)
        self.layout.addWidget(self.radiobutton6, 0, 3)
        #self.layout.addWidget(self.radiobutton7, 0, 4)
        self.layout.addWidget(self.radiobutton8, 0, 4)
        self.layout.addWidget(self.radiobutton9, 0, 5)
        self.verRadiobutton.clicked.connect(self.onSetAll)
        self.lightRadiobutton.clicked.connect(self.onSetChr)
        self.radiobutton5.clicked.connect(self.onSetLoc)
        self.radiobutton6.clicked.connect(self.onSetPro)
        #self.radiobutton7.clicked.connect(self.onSetVfx)
        self.radiobutton8.clicked.connect(self.onSetLit)
        self.radiobutton9.clicked.connect(self.onSetOth)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.treeWidget = QtCGMaya.QTreeWidget(self)
        #self.treeWidget.setColumnCount(2)

        # self.treeWidget.header.setDefaultSectionSize(40)
        headerList = []
        headerList.append(u'资产')
        headerList.append(u'次数')
        headerList.append(u'增加')
        headerList.append(u'减少')
        self.treeWidget.setHeaderLabels(headerList)
        self.main_layout.addWidget(self.treeWidget)
        header = self.treeWidget.header()
        header.setStretchLastSection(True)
        #header.resizeSection(4, 20)

        self.treeWidget.itemClicked.connect(self.onClickItem)
        self.treeWidget.itemDoubleClicked.connect(self.onDoubleClickItem)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            if self.wayflag:
                self.button1 = QtCGMaya.QPushButton(u'引用', self)
            else:
                self.button1 = QtCGMaya.QPushButton(u'导入', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            if self.wayflag:
                self.button1 = QtCGMaya.QPushButton(u'Reference', self)
            else:
                self.button1 = QtCGMaya.QPushButton(u'Import', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 0)
        self.layout.addWidget(self.button2, 1, 1)
        self.button1.clicked.connect(self.onReference)
        self.button2.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            if self.wayflag:
                self.setWindowTitle(u'引用资产')
            else:
                self.setWindowTitle(u'导入资产')
        else:
            if self.wayflag:
                self.setWindowTitle(u'Reference Model')
            else:
                self.setWindowTitle(u'Import Model')
        self.setGeometry(0, 0, 500, 800)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

        #self.GetProjects()
        self.GetProjectTasks()
        self.SetDispTask(0)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def setEnabled(self, bBool):
        self.button1.setEnabled(bBool)
        self.button2.setEnabled(bBool)

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def GetProjects(self):
        if self.refProjectName:
           return
        rawProjectList = self.service.getAllProjects()
        textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        self.projectList = []
        for project in rawProjectList:
            if not project['templateName'] == '3DAsset':
                continue
            item = QtCGMaya.QListWidgetItem(project['name'])
            item.setFont(textFont)
            self.projectListWidget.addItem(item)
            self.projectList.append(project)
        if len(self.projectList) == 0:
            return
        row = 0
        refProject = self.projectList[row]
        self.refProjectName = refProject['name']
        self.projectText.setText(self.refProjectName)
        self.GetProjectTasks()
        self.SetDispTask(0)

    def GetProjectTasks(self):
        if CGMaya_config.currentProject['refProject'] == '':
            CGMaya_config.logger.error('Reference Project is not Found: %s\r' % CGMaya_config.currentProject['name'])
            return
        else:
            self.refProjectName = CGMaya_config.currentProject['refProject']
        self.projectText.setText(self.refProjectName)
        assetList1 = self.service.getAssetsOfProject(self.refProjectName)
        self.taskList = []
        for asset in assetList1:
            task1 = []
            for task in asset['taskList']:
                if task['stage'] == u'模型':
                    if task1 == []:
                        task1 = task
                if task['stage'] == u'绑定' or task['stage'] == u'标准光':
                    task1 = task
            task1['count'] = 0
            task1['flag'] = ''
            self.taskList.append(task1)
        self.taskList.sort(cmp=self.myCompare)

    def SetDispTask(self, row):
        self.dispTaskList = []
        self.treeWidget.clear()

        textFont = QtGui.QFont("song", 11, QtGui.QFont.Normal)
        count = 0
        itemSelected = None
        for task in self.taskList:
            b = False
            if self.dispFlag == 0:
                b = True
            elif self.dispFlag == 1 and task['name'].find('chr_') >= 0:
                b = True
            elif self.dispFlag == 2 and task['name'].find('loc_') >= 0:
                b = True
            elif self.dispFlag == 3 and task['name'].find('pro_') >= 0:
                b = True
            # elif self.dispFlag == 4 and task['name'].find('vfx_') >= 0:
            #     b = True
            elif self.dispFlag == 5 and task['name'].find('lt_') >= 0:
                b = True
            elif self.dispFlag == 6 and task['name'].find('oth_') >= 0:
                b = True
            if b:
                self.dispTaskList.append(task)
                if task['count'] == 0:
                    string = ''
                else:
                    string = str(task['count'])
                item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [task['name'], '  ' + string, '+', '-'])
                # if count == row:
                #     itemSelected = item
                item.setFont(0, textFont)
                item.setFont(1, textFont)
                item.setFont(2, textFont)
                item.setFont(3, textFont)
                # item.setTextAlignment(0, QtCore.Qt.AlignCenter)
                # item.setTextAlignment(1, QtCore.Qt.AlignCenter)
                item.setTextAlignment(2, QtCore.Qt.AlignCenter)
                item.setTextAlignment(3, QtCore.Qt.AlignCenter)
                self.treeWidget.resizeColumnToContents(0)
                self.treeWidget.resizeColumnToContents(1)
                count = count + 1
        #self.treeWidget.setCurrentItem(itemSelected)

    def onSetAll(self):
        self.dispFlag = 0
        self.SetDispTask(0)

    def onSetChr(self):
        self.dispFlag = 1
        self.SetDispTask(0)

    def onSetLoc(self):
        self.dispFlag = 2
        self.SetDispTask(0)

    def onSetPro(self):
        self.dispFlag = 3
        self.SetDispTask(0)

    def onSetVfx(self):
        self.dispFlag = 4
        self.SetDispTask(0)

    def onSetLit(self):
        self.dispFlag = 5
        self.SetDispTask(0)

    def onSetOth(self):
        self.dispFlag = 6
        self.SetDispTask(0)

    def onClickProjectItem(self, item):
        row = self.projectListWidget.currentRow()
        refProject = self.projectList[row]
        self.refProjectName = refProject['name']
        self.projectText.setText(self.refProjectName)
        self.GetProjectTasks()
        self.SetDispTask()

    def onClickItem(self, item, column):
        print('onClickItem')
        self.taskListIndex = self.treeWidget.indexOfTopLevelItem(item)
        row = self.treeWidget.indexOfTopLevelItem(item)
        if column == 2:
            if self.dispFlag != 4 or self.dispTaskList[row]['count'] == 0:
                self.dispTaskList[row]['count'] = self.dispTaskList[row]['count'] + 1
        elif column == 3:
            if self.dispTaskList[row]['count'] > 0:
                self.dispTaskList[row]['count'] = self.dispTaskList[row]['count'] - 1
            else:
                self.dispTaskList[row]['count'] = 0
        self.SetDispTask(row)

    def onDoubleClickItem(self, item, column):
        pass

    def onAddRef(self, item):
        print('onAddRef')
        # self.taskListIndex = self.treeWidget.indexOfTopLevelItem(item)
        # row = self.treeWidget.indexOfTopLevelItem(item)
        # if self.dispFlag != 4 or self.dispTaskList[row]['count'] == 0:
        #     self.dispTaskList[row]['count'] = self.dispTaskList[row]['count'] + 1
        # self.SetDispTask(row)

    def onDelRef(self, item):
        print('onDelRef')
        # self.taskListIndex = self.treeWidget.indexOfTopLevelItem(item)
        # row = self.treeWidget.indexOfTopLevelItem(item)
        # if self.dispTaskList[row]['count'] > 0:
        #     self.dispTaskList[row]['count'] = self.dispTaskList[row]['count'] - 1
        # else:
        #     self.dispTaskList[row]['count'] = 0
        # self.SetDispTask(row)

    def onCancel(self):
        if self.menu:
            self.menu.setEnable(True)
        else:
            self.parent1.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        if self.menu:
            self.menu.setEnable(True)
        #else:
        #    self.parent1.setEnable(True)
        event.accept() # let the window close

    def onReference(self):
        CGMaya_config.currentDlg = self
        for task in self.taskList:
            list = self.service.searchTask(task['name'], self.refProjectName)
            for task1 in list:
                if task1['stage'] == task['stage'] and task['count'] > 0:
                    for n in range(0, task['count']):
                        if not self.referenceAsset(task1, self.wayflag):
                            print('Scene File is None')
        if self.wayflag:
            #self.service.userActionLog(CGMaya_config.userName, CGMaya_config.projectName, CGMaya_config.sceneName,
            #                           CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Reference)
            CGMaya_config.logger.set("referenceAsset")
            CGMaya_config.logger.server(CGMaya_config.projectName, CGMaya_config.sceneName,
                                       CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Reference)
            #self.service.myWFSetTaskRefAssetProject(CGMaya_config.currentTask['_id'], self.refProjectName)
            #CGMaya_config.currentTask = json.loads(self.service.myWFGetTaskInfo(CGMaya_config.currentTask['_id'])
        else:
            #self.service.userActionLog(CGMaya_config.userName, CGMaya_config.projectName, CGMaya_config.sceneName,
            #                           CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Import)
            CGMaya_config.logger.set("importAsset")
            CGMaya_config.logger.server(CGMaya_config.projectName, CGMaya_config.sceneName,
                                        CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Import)
        self.menu.setEnable(True)
        self.close()

    def referenceAsset(self, task, flag):
        refProjectDir = CGMaya_common.makeDir(CGMaya_config.assetStorageDir, self.refProjectName)
        refTaskDir = CGMaya_common.makeDir(refProjectDir, task['name'])
        status, message, sfn = CGMaya_common.downloadFile(self.service, refProjectDir, refProjectDir, refTaskDir, task,
                                                        task['fileID'])
        if flag:  # reference Model
            CGMaya_config.currentTask['refAssetIDList'].append({'projectName': CGMaya_config.refProjectName, 'name': task['name'],
                                                 'id': task['fileID'], 'taskID': task['_id']})
            cmds.file(sfn, reference=True, options='v=0', ignoreVersion=True, namespace=task['name'])
        else:  # import Model
            cmds.file(sfn, i=True)
        return True
