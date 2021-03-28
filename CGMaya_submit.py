#coding=utf-8

import os
import sys
import platform
import CGMaya_config
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
import time
import datetime
#import MySQLdb.cursors
import datetime
import random
import json
import subprocess
import urllib2
import shutil
import zipfile
#from datetime import datetime, timedelta
import copy
if platform.system() == 'Windows':
    import pyaudio
import wave
import ctypes
#import pytz

import CGMaya_service
import CGMaya_logger
import CGMaya_common


renderList = [{'label': u'山大渲染', 'name': 'ShanDa'},
                {'label': u'女院渲染', 'name': 'Women'},
                {'label': u'渲云渲染', 'name': 'XRender'},
                {'label': u'瑞云渲染', 'name': 'Renderbus'},
                {'label': u'无锡超算', 'name': 'Wuxi'}]

class submitRenderWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = CGMaya_common.maya_main_window()):
        super(submitRenderWindow, self).__init__(parent)
        # And now set up the UI
        self.service = service
        self.menu = menu
        self.projectList = []
        self.taskList = []
        self.project = []
        self.task = []
        self.machine = []
        self.menu.setEnable(False)
        self.shiftKey = False
        self.renderLocation = {}
        self.setup_ui()

    def setup_ui(self):
        if CGMaya_config.lang == 'zh':
            self.projectLabel = QtCGMaya.QLabel(u'项目', self)
            self.noteLabel = QtCGMaya.QLabel(u'说明', self)
            self.renderLabel = QtCGMaya.QLabel(u'渲染器', self)
            self.singleRadiobutton = QtCGMaya.QRadioButton(u'单帧渲染', self)
            self.sequenceRadiobutton = QtCGMaya.QRadioButton(u'序列渲染', self)
            self.leftCheckBox = QtCGMaya.QCheckBox(u'左', self)
            self.rightCheckBox = QtCGMaya.QCheckBox(u'右', self)
            self.button1 = QtCGMaya.QPushButton(u'提交', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
            self.button3 = QtCGMaya.QPushButton(u'刷新', self)
            self.button4 = QtCGMaya.QPushButton(u'全选', self)
            self.button5 = QtCGMaya.QPushButton(u'全不选', self)
        else:
            self.projectLabel = QtCGMaya.QLabel(u'Project', self)
            self.noteLabel = QtCGMaya.QLabel(u'Note', self)
            self.renderLabel = QtCGMaya.QLabel(u'Render', self)
            self.singleRadiobutton = QtCGMaya.QRadioButton(u'Single Render', self)
            self.sequenceRadiobutton = QtCGMaya.QRadioButton(u'Sequence Render', self)
            self.leftCheckBox = QtCGMaya.QCheckBox(u'Left', self)
            self.rightCheckBox = QtCGMaya.QCheckBox(u'Right', self)
            self.button1 = QtCGMaya.QPushButton(u'Submit', self)
            self.button2 = QtCGMaya.QPushButton(u'Close', self)
            self.button3 = QtCGMaya.QPushButton(u'Refresh', self)
            self.button4 = QtCGMaya.QPushButton(u'Select All', self)
            self.button5 = QtCGMaya.QPushButton(u'Unselect All', self)
        self.projectBox = QtCGMaya.QComboBox(self)
        self.projectBox.currentIndexChanged.connect(self.onProjectSelect)
        self.renderBox = QtCGMaya.QComboBox(self)
        for render in renderList:
            self.renderBox.addItem(render['label'])
        self.renderLocation = renderList[0]
        self.renderBox.currentIndexChanged.connect(self.onRenderSelect)
        self.noteText = QtCGMaya.QLineEdit('', self)
        self.noteText.setEnabled(False)
        self.renderText = QtCGMaya.QLineEdit('', self)
        self.renderText.setEnabled(False)
        self.singleRadiobutton.setChecked(False)
        self.sequenceRadiobutton.setChecked(True)

        self.singleRadiobutton.clicked.connect(self.onSingle)
        self.sequenceRadiobutton.clicked.connect(self.onSequence)
        if self.singleRadiobutton.isChecked():
            self.leftCheckBox.setChecked(True)
            self.rightCheckBox.setChecked(True)
        else:
            self.leftCheckBox.setChecked(True)
            self.rightCheckBox.setChecked(False)
        self.treeWidget = QtCGMaya.QTreeWidget(self)
        self.treeWidget.setColumnCount(2)
        # self.treeWidget.header.setDefaultSectionSize(40)
        self.treeWidget.itemExpanded.connect(self.onItemExpanded)
        self.treeWidget.itemClicked.connect(self.onClickItem)
        self.treeWidget.itemDoubleClicked.connect(self.onDoubleClickItem)
        headerList = []
        headerList.append(u'任务')
        headerList.append(u'选中')
        headerList.append(u'')
        headerList.append(u'序列')
        headerList.append(u'单帧')
        self.treeWidget.setHeaderLabels(headerList)
        self.button1.clicked.connect(self.onSubmit)
        self.button2.clicked.connect(self.onCancel)
        self.button3.clicked.connect(self.onRefresh)
        self.button4.clicked.connect(self.onSelectAll)
        self.button5.clicked.connect(self.onUnselectAll)
        #self.button6.clicked.connect(self.onXRenderSetup)

        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        self.layout.addWidget(self.projectLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.projectBox, 0, 2, 1, 3)
        self.layout.addWidget(self.noteLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.noteText, 1, 2, 1, 3)
        self.layout.addWidget(self.renderLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.renderText, 2, 2, 1, 3)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.sequenceRadiobutton, 0, 0)
        self.layout.addWidget(self.singleRadiobutton, 0, 1)
        self.layout.addWidget(self.leftCheckBox, 0, 2)
        self.layout.addWidget(self.rightCheckBox, 0, 3)
        self.layout.addWidget(self.renderBox, 0, 4)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.main_layout.addWidget(self.treeWidget)
        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        layout1.addWidget(self.button3, 0, 2)
        layout1.addWidget(self.button1, 0, 3)
        layout1.addWidget(self.button2, 0, 4)
        layout1.addWidget(self.button4, 0, 0)
        layout1.addWidget(self.button5, 0, 1)
        self.row_Hbox.setLayout(layout1)
        self.main_layout.addWidget(self.row_Hbox)

        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'提交渲染')
        else:
            self.setWindowTitle(u'Submit Render')

        self.setLayout(self.main_layout)
        self.setGeometry(0, 0, 500, 800)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()
        self.show()
        self.getRenderTasks()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def getRenderTasks(self):
        tasks = self.service.getMyTask(CGMaya_config.userName)
        self.projectList = []
        self.taskList = []
        self.rawTasks = []
        for task in tasks:
            if task['stage'] != u'灯光':
                continue
            self.rawTasks.append(task)
            if not task['projectName'] in self.projectList:
                self.projectBox.addItem(task['projectName'])
                self.projectList.append(task['projectName'])
        for task in self.rawTasks:
            if CGMaya_config.currentProject:
                if task['projectName'] == CGMaya_config.currentProject['name']:
                    self.taskList.append(task)
            elif task['projectName'] == self.projectList[0]:
                self.taskList.append(task)
        self.displayTasks()

    def displayTasks(self):
        self.treeWidget.clear()
        self.taskList.sort(cmp=self.myCompare)
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for task in self.taskList:
            task['flag'] = ' '
            task['lightFileList'] = []
            try:
                frameList = task['frameList']
            except KeyError:
                frameList = []
            try:
                singleFrame = task['singleFrame']
            except KeyError:
                singleFrame = '101'
            if not singleFrame:
                singleFrame = '101'
            #item = QtCGMaya.QTreeWidgetItem(self.treeWidget)
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [task['name'], False, '', frameList, singleFrame])
            item.setFont(0, textFont)
            self.treeWidget.resizeColumnToContents(0)
            item.setCheckState(1, QtCore.Qt.CheckState.Unchecked)
            self.treeWidget.resizeColumnToContents(2)
            #self.treeWidget.resizeColumnToContents(3)
            if len(task['lightFileIDList']) > 0:
                item.setChildIndicatorPolicy(QtCGMaya.QTreeWidgetItem.ShowIndicator)
                checkState = item.checkState(1)
                try:
                    checkState = item.checkState(1)
                    for lightFile in task['lightFileIDList']:
                        lightFile['flag'] = ' '
                        sonItem = QtCGMaya.QTreeWidgetItem(item, [lightFile['name'], lightFile['flag']])
                        self.treeWidget.resizeColumnToContents(0)
                        sonItem.setCheckState(1, checkState)
                except KeyError:
                    pass

    def onProjectSelect(self, n):
        self.taskList = []
        if not self.projectList:
            return
        for task in self.rawTasks:
            if task['projectName'] == self.projectList[n]:
                self.taskList.append(task)
        self.treeWidget.clear()
        self.displayTasks()

    def onRenderSelect(self, n):
        self.renderLocation = renderList[n]

    def onSingle(self):
        self.singleRadiobutton.setChecked(True)
        self.sequenceRadiobutton.setChecked(False)
        self.leftCheckBox.setChecked(True)
        self.rightCheckBox.setChecked(True)

    def onSequence(self):
        self.singleRadiobutton.setChecked(False)
        self.sequenceRadiobutton.setChecked(True)
        self.leftCheckBox.setChecked(True)
        self.rightCheckBox.setChecked(False)

    def onClickItem(self, item, column):
        rootIndex = self.treeWidget.indexOfTopLevelItem(item)
        if rootIndex < 0:
            parentItem = item.parent()
            rIndex = self.treeWidget.indexOfTopLevelItem(parentItem)
        else:
            rIndex = rootIndex
        #self.projectText.setText(self.taskList[rIndex]['projectName'])
        #self.stageText.setText(self.taskList[rIndex]['stage'])
        self.noteText.setText(self.taskList[rIndex]['note'])
        project1 = self.service.getProjectInfo(self.taskList[rIndex]['projectName'])
        self.renderText.setText(project1['render'])
        shot = self.service.getShotInfo(self.taskList[rIndex]['projectName'], self.taskList[rIndex]['name'])
        try:
            if shot['stereoMode']:
                self.leftCheckBox.setEnabled(True)
                self.rightCheckBox.setEnabled(True)
            else:
                self.leftCheckBox.setEnabled(False)
                self.rightCheckBox.setEnabled(False)
        except KeyError:
            self.leftCheckBox.setEnabled(False)
            self.rightCheckBox.setEnabled(False)
        if rootIndex < 0:
            parentItem = item.parent()
            child = parentItem.child(0)
            state = child.checkState(1)
            index = 1
            while index < parentItem.childCount():
                child = parentItem.child(index)
                if state != child.checkState(1):
                    state1 = QtCore.Qt.PartiallyChecked
                    break
                else:
                    state1 = state
                index = index + 1
            parentItem.setCheckState(1, state1)
            index = self.treeWidget.indexFromItem(parentItem).row()
        else:
            #if not item.isExpanded():
            #    return
            checkState = item.checkState(1)
            if checkState == QtCore.Qt.PartiallyChecked or checkState == QtCore.Qt.Checked:
                state = QtCore.Qt.Checked
            else:
                #state = checkState
                state = QtCore.Qt.Unchecked
            index = 0
            while index < item.childCount():
                child = item.child(index)
                child.setCheckState(1, state)
                index = index + 1
            index = rootIndex

    def onDoubleClickItem(self, item, column):
        rootIndex = self.treeWidget.indexOfTopLevelItem(item)
        if rootIndex >= 0:
            return
        parentItem = item.parent()
        rIndex = self.treeWidget.indexOfTopLevelItem(parentItem)
        for lightFileID in self.taskList[rIndex]['lightFileIDList']:
            if lightFileID['name'] == item.text(0):
                print('lightFileID--name =', lightFileID['name'], item.text(0))
                response = QtCGMaya.QMessageBox.question(self, u"警告", u"是否删除这个文件?",
                                                         QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
                reply = QtCGMaya.QMessageBox.Yes
                if response == reply:
                    del lightFileID
                    continue
        print self.taskList[rIndex]['lightFileIDList']
        self.onItemExpanded(parentItem)
        #self.service.myWFSetTaskLightFileIDList1(self.taskList[rIndex]['_id'], lightFileIDList, self.taskList[rIndex]['textureFileID'])

    def onItemExpanded(self, item):
        rootIndex = self.treeWidget.indexOfTopLevelItem(item)
        task = self.taskList[rootIndex]
        if not task['lightFileList']:
            return
        checkState = item.checkState(1)
        for lightFile in task['lightFileIDList']:
            lightFile['flag'] = ' '
            sonItem = QtCGMaya.QTreeWidgetItem(item, [lightFile['name'], lightFile['flag']])
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            sonItem.setCheckState(1, checkState)

    def onSelectAll(self):
        index = 0
        while index < self.treeWidget.topLevelItemCount():
            item = self.treeWidget.topLevelItem(index)
            item.setCheckState(1, QtCore.Qt.Checked)
            if self.treeWidget.isItemExpanded(item):
                index1 = 0
                while index1 < item.childCount():
                    child = item.child(index1)
                    child.setCheckState(1, QtCore.Qt.Checked)
                    index1 = index1 + 1
            index = index + 1

    def onUnselectAll(self):
        index = 0
        while index < self.treeWidget.topLevelItemCount():
            item = self.treeWidget.topLevelItem(index)
            item.setCheckState(1, QtCore.Qt.Unchecked)
            if self.treeWidget.isItemExpanded(item):
                index1 = 0
                while index1 < item.childCount():
                    child = item.child(index1)
                    child.setCheckState(1, QtCore.Qt.Unchecked)
                    index1 = index1 + 1
            index = index + 1

    def installRenderWingPlugin(self):
        if cmds.window("unifiedRenderGlobalsWindow", exists=True):
            cmds.deleteUI("unifiedRenderGlobalsWindow")
            return
        Dir = cmds.internalVar(userScriptDir=True)
        pluginFn = Dir + '/CGMaya/RWingForMaya.py'
        print 'pluginFn =', pluginFn
        # pluginFn = 'E:\downloads/RWingForMaya/plug-ins/RWingForMaya.py'
        pluginFn = 'E:\downloads\RWingForMaya\plug-ins/RWingForMaya.py'
        ret = cmds.loadPlugin(pluginFn)
        cmds.setAttr("defaultRenderGlobals.currentRenderer", l=False)
        cmds.setAttr("defaultRenderGlobals.currentRenderer", 'RWing', type="string")
        mel.eval('unifiedRenderGlobalsWindow;')

    def keyPressEvent(self,event):
        key = event.key()
        if key == 16777248:
            self.shiftKey = True

    def onSubmit(self):
        if self.singleRadiobutton.isChecked():
            renderType = 'Single'
        elif self.sequenceRadiobutton.isChecked():
            renderType = 'Sequence'
        if not self.taskList:
            return
        submitTaskList = []
        index = 0
        while index < self.treeWidget.topLevelItemCount():
            item = self.treeWidget.topLevelItem(index)
            state = item.checkState(1)
            if state == QtCore.Qt.Unchecked:
                index = index + 1
                continue
            task = self.taskList[index]
            project = self.service.getProjectInfo(task['projectName'])
            render = project['render']
            submitFileList = []
            lightFileList = task['lightFileIDList']
            if state == QtCore.Qt.Checked:
                for lightFile in lightFileList:
                    submitFileList.append(lightFile)
            else:
                index1 = 0
                while index1 < item.childCount():
                    child = item.child(index1)
                    if child.checkState(1) == QtCore.Qt.Checked:
                        for lightFile in lightFileList:
                            if lightFile['name'] == child.text(0):
                                submitFileList.append(lightFile)
                    index1 = index1 + 1
            submitTaskList.append({'_id': task['_id'], 'submitFileList': submitFileList, 'render': render})
            index = index + 1
        if not submitTaskList:
            return
        if CGMaya_config.lang == 'zh':
            message = u'是提交到（' + self.renderLocation['label'] + u')？'
            response = QtCGMaya.QMessageBox.question(self, u"提示", message,
                                                     QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
        else:
            message = u'is Submit（' + self.renderLocation['label'] + u')？'
            response = QtCGMaya.QMessageBox.question(self, u"Select", message,
                                                     QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
        if response == QtCGMaya.QMessageBox.No:
            return
        if self.leftCheckBox.isChecked():
            lFlag = 1
        else:
            lFlag = 0
        if self.rightCheckBox.isChecked():
            rFlag = 1
        else:
            rFlag = 0
        if project['render'] == 'renderwing' and self.renderLocation['name'] == 'Wuxi':
            #result =self.service.renderJobSubmit(CGMaya_config.userName, submitTaskList, renderType, 'WUXI', '', lFlag, rFlag)
            nowTime = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            randomNum = random.randint(0, 100)
            if randomNum <= 0:
                randomNum = str(0) + str(randomNum)
            uniqueNum = str(nowTime) + str(randomNum)
            print 'uniqueNum', uniqueNum

            # sql = """insert into jobs(id, cameraName, filePath, renderEngineId, xResolution, yResolution, projectId, frameRange, preRenderingTag)
            #      VALUES('e45c905c33eb4bfd9e42403d2566abad', 'testgb', '/home/export/online1/systest/swsdu/xijiao/Users/xjtu/camera7,
            #      'e45c905c33eb4bfd9e42403d2566abad', '320', '160', '5c9a9bbd663f43509b0931e39ca90b60', '101-180', '0')"""
            dt = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sql = "insert into jobs(id, cameraName, filePath, renderEngineId, xResolution, yResolution, jobStatus, jobPriority, projectId, frameRange, preRenderingTag, unitsNumber, createTime, frameNumbers, cameraProgress) " \
                  "values('%s', '%s', '%s', '%s', '%d', '%d', '%d', '%d', '%s', '%s', '%d', '%d', '%s', '%d', '%d')" % \
                  (uniqueNum, task['name'], '/home/export/online1/systest/swsdu/xijiao/Users/xjtu/camera100',
                   'e45c905c33eb4bfd9e42403d2566abad', 320, 160, 1, 2, '5c9a9bbd663f43509b0931e39ca90b60', '1-7', 0, 1022, dt, 7, 0)
            print 'sql =', sql
            """
            conn = MySQLdb.connect(host='58.215.62.133',
                                   port=33061,
                                   user='root',
                                   passwd='123456',
                                   db='renderdata',
                                   charset='utf8')

            cursor = conn.cursor()
            try:
                cursor.execute(sql)
                print 'lll'
                results = cursor.fetchall()
                conn.commit()
            except:
                conn.rollback()
            cursor.close()
            conn.close()
            """
        else:
            result = self.service.renderJobSubmit(CGMaya_config.userName, submitTaskList, renderType, self.renderLocation['name'], '',  '', lFlag, rFlag)
        self.onUnselectAll()
        QtGui.QMessageBox.information(self, u"提示", u"已提交完成.", QtGui.QMessageBox.Yes)
        #self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_RenderJob)
        CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_SubmitRenderJob)
        self.menu.setEnable(True)
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def onRefresh(self):
        self.getRenderTasks()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close
