#coding=utf-8

import os
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
import json
import datetime
import random
import subprocess
import urllib2
import shutil
import zipfile
import time
from datetime import datetime, timedelta
if platform.system() == 'Windows':
    import pyaudio
import wave
import ctypes
#import pytz

import CGMaya_common
import CGMaya_service
import CGMaya_parser
import CGMaya_mouse


class pngDialog(QtCGMaya.QDialog):
    def __init__(self, service, task, returnFile, parent=CGMaya_common.maya_main_window()):
        super(pngDialog, self).__init__(parent)
        self.service = service
        self.task = task
        self.returnFile = returnFile

        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.image = QtCGMaya.QImage()
        self.getFile()
        self.imageLabel = QtCGMaya.QLabel('', self)
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(self.image))

        self.layout.addWidget(self.imageLabel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.button = QtCGMaya.QPushButton(u'Close', self)

        self.layout.addWidget(self.button)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.button.clicked.connect(self.onClose)

        self.setLayout(self.main_layout)
        self.setGeometry(700, 350, 700, 700)
        self.show()

    def getFile(self):
        localFile = os.path.join(CGMaya_config.tmpStorageDir, self.returnFile['name'])
        self.service.getFile(self.task, localFile, self.returnFile['id'], self.returnFile['name'])
        self.image.load(localFile)

    def onClose(self):
        self.close()

class openTaskWindow(QtCGMaya.QDialog):
    def __init__(self, service, CGMenu, parent=CGMaya_common.maya_main_window()):
        super(openTaskWindow, self).__init__(parent)
        self.service = service
        self.CGMenu = CGMenu
        self.CGMenu.menu.setEnable(False)
        self.projectID = None
        self.sceneID = None
        self.folderID = ''
        self.textureID = None
        self.taskFlag = False
        self.loadFlag = True
        self.fileList = []
        self.returnFileList = []
        self.lightFileList = []
        self.lightAssetList = []
        self.fileListIndex = -1
        self.lightFolderid = ''
        self.lightAsset = {}
        self.bTaskSelected = False
        self.currentTask = None
        self.tasks = []
        self.parentProjectName = ''
        self.projectName = ''
        self.dataSize = 0
        self.tabIndex = 0
        if not CGMaya_config.storageDir or not CGMaya_config.assetStorageDir or \
                not os.path.exists(CGMaya_config.storageDir) or not os.path.exists(CGMaya_config.assetStorageDir):
            QtCGMaya.QMessageBox.information(parent, u"错误信息", u"设置的存储路径不合适, 请设置合适的存储路径",
                                          QtGui.QMessageBox.Yes)
            self.close()
            return
        # cmds.nameCommand('RCMayaOpen', annotation='RCMaya Open', command='python("onOpen()")')
        # cmds.hotkey(k='Return', name='RCMayaOpen')

        # 裁剪版设置
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        self.taskFileID = ''
        self.taskTextureFileID = ''
        self.lightFileFlag = False
        CGMaya_config.logger.set("openTaskWindow")
        self.taskIndex = -1
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.parentProjectLabel = QtCGMaya.QLabel(u'主项目', self)
            self.projectLabel = QtCGMaya.QLabel(u'项目', self)
            self.textureCheckBox = QtCGMaya.QCheckBox(u'贴图', self)
            self.loadCheckBox = QtCGMaya.QCheckBox(u'装载', self)
        else:
            self.parentProjectLabel = QtCGMaya.QLabel(u'ParentProject', self)
            self.projectLabel = QtCGMaya.QLabel(u'Project', self)
            self.textureCheckBox = QtCGMaya.QCheckBox(u'Texture', self)
            self.loadCheckBox = QtCGMaya.QCheckBox(u'Load', self)
        self.parentProjectBox = QtCGMaya.QComboBox(self)
        self.parentProjectBox.currentIndexChanged.connect(self.onParentProjectSelect)
        self.projectBox = QtCGMaya.QComboBox(self)
        self.projectBox.currentIndexChanged.connect(self.onProjectSelect)

        self.layout.addWidget(self.parentProjectLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.parentProjectBox, 0, 1, 1, 4)
        self.layout.addWidget(self.projectLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.projectBox, 1, 1, 1, 4)
        self.layout.addWidget(self.textureCheckBox, 1, 5, 1, 1)
        self.layout.addWidget(self.loadCheckBox, 0, 5, 1, 1)
        self.textureCheckBox.setChecked(True)
        self.loadCheckBox.setChecked(True)
        self.loadCheckBox.clicked.connect(self.onSetLoad)

        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.taskTreeWidget = QtCGMaya.QTreeWidget(self)
        self.taskTreeWidget.setColumnCount(2)
        headerList = []
        headerList.append(u'阶段')
        headerList.append(u'任务名')
        headerList.append(u'总数据量')
        headerList.append(u'下载数据量')
        self.taskTreeWidget.setHeaderLabels(headerList)
        self.main_layout.addWidget(self.taskTreeWidget)
        self.taskTreeWidget.itemClicked.connect(self.onClickItemTask)
        self.taskTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItemTask)

        self.row_treeHbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        self.tabWidget = QtCGMaya.QTabWidget(self)
        self.verTreeWidget = QtCGMaya.QTreeWidget(self)
        self.refTreeWidget = QtCGMaya.QTreeWidget(self)
        self.litTreeWidget = QtCGMaya.QTreeWidget(self)
        self.attTreeWidget = QtCGMaya.QTreeWidget(self)
        if CGMaya_config.lang == 'zh':
            self.tabWidget.addTab(self.verTreeWidget, u'版本')
            self.tabWidget.addTab(self.refTreeWidget, u'引用')
            self.tabWidget.addTab(self.litTreeWidget, u'灯光')
            self.tabWidget.addTab(self.attTreeWidget, u'附件')
        else:
            self.tabWidget.addTab(self.verTreeWidget, u'Ver')
            self.tabWidget.addTab(self.refTreeWidget, u'Ref')
            self.tabWidget.addTab(self.litTreeWidget, u'Lit')
            self.tabWidget.addTab(self.attTreeWidget, u'Att')
        self.tabWidget.currentChanged.connect(self.onCurrentChanged)
        self.verTreeWidget.itemClicked.connect(self.onClickItem1)
        self.verTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItem1)

        self.litTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItem1)
        self.litTreeWidget.itemClicked.connect(self.onClickItem1)

        self.attTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItem1)
        self.attTreeWidget.itemClicked.connect(self.onClickItem1)

        self.main_layout.addWidget(self.tabWidget)
        self.tabIndex = 0

        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'打开', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
            self.button3 = QtCGMaya.QPushButton(u'刷新', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Open', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button3 = QtCGMaya.QPushButton(u'Refresh', self)
        layout1.addWidget(self.button3, 1, 0)
        layout1.addWidget(self.button1, 1, 1)
        layout1.addWidget(self.button2, 1, 2)
        self.button1.clicked.connect(self.onOpen)
        self.button2.clicked.connect(self.onCancel)
        self.button3.clicked.connect(self.onRefresh)
        self.row_Hbox.setLayout(layout1)
        self.main_layout.addWidget(self.row_Hbox)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'我的任务')
        else:
            self.setWindowTitle(u'My Task')

        self.setLayout(self.main_layout)
        self.setGeometry(0, 0, 700, 800)
        # self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()
        self.show()
        self.getProjects()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onPress(self, *args):
        self.anchorPoint = cmds.draggerContext('Context', query=True, anchorPoint=True)
        CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        print 'anchorPoint =', self.anchorPoint, CGMaya_config.mouseCount

    def onDrag(self, *args):
        # pass
        self.dragPoint = cmds.draggerContext('Context', query=True, dragPoint=True)
        print 'anchorPoint =', self.dragPoint

    def onRelease(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query=True, dragPoint=True)
        print ' releasePoint =', self.releasePoint

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def getProjects(self):
        cmds.waitCursor(state=True)
        # 获得当前用户的所有任务列表
        self.rawTasks = self.service.getMyTask(CGMaya_config.userName)
        # 获得所有项目列表
        self.rawProjectList = self.service.getAllProjects()
        self.parentProjectList = []
        self.allTaskList = []
        self.projectList = []
        self.parentProjectBox.clear()

        # 所有任务所属的主项目列表，
        for rawTask in self.rawTasks:
            for rawProject in self.rawProjectList:
                if rawTask['projectName'] == rawProject['name']:
                    self.parentProjectName = rawProject['project']
                    break
            self.allTaskList.append({'name': rawTask['name'], 'projectName': rawTask['projectName'],
                                     'parentProjectName': self.parentProjectName, 'task': rawTask})
        for task in self.allTaskList:
            if not task['parentProjectName'] in self.parentProjectList:
                self.parentProjectBox.addItem(task['parentProjectName'])
                self.parentProjectList.append(task['parentProjectName'])
        if self.parentProjectName:
            for index, project in enumerate(self.parentProjectList):
                if project == self.parentProjectName:
                    self.parentProjectBox.setCurrentIndex(index)
                    break
        else:
            self.parentProjectName = self.parentProjectList[0]
            self.parentProjectBox.setCurrentIndex(0)
        self.onParentProjectSelect(0)
        cmds.waitCursor(state=False)

    def onParentProjectSelect(self, index):
        self.taskFileID = ''
        self.taskTextureFileID = ''
        if not self.parentProjectList:
            return
        row = self.parentProjectBox.currentIndex()
        self.parentProjectName = self.parentProjectList[row]
        self.projectList = []
        self.projectBox.clear()
        for task in self.allTaskList:
            if task['parentProjectName'] == self.parentProjectName and (
            not task['projectName'] in self.projectList):
                self.projectBox.addItem(task['projectName'])
                self.projectList.append(task['projectName'])
        if self.projectName:
            for index, project in enumerate(self.projectList):
                if project == self.projectName:
                    self.projectBox.setCurrentIndex(index)
                    break
        else:
            self.projectName = self.projectList[0]
            self.projectBox.setCurrentIndex(0)
        self.onProjectSelect(0)

    def onProjectSelect(self, index):
        self.taskFileID = ''
        self.taskTextureFileID = ''
        if not self.projectList:
            return
        row = self.projectBox.currentIndex()
        self.projectName = self.projectList[row]
        self.tasks = []
        for task in self.allTaskList:
            if task['projectName'] == self.projectName:
                self.tasks.append(task['task'])
        self.taskIndex = -1
        self.tabIndex = 0
        self.displayTasks()

    def getTaskDataSize(self, task):
        if not task or task['fileID'] == '':
            return 0
        # try:
        #     dataSize = task['dataSize']
        #     return int(dataSize)
        # except AttributeError:
        #     pass
        fileInfo = self.service.getFileInfo(task['fileID'])
        total = fileInfo.length
        if task['textureFileID']:
            fileInfo = self.service.getFileInfo(task['textureFileID'])
            total = total + fileInfo.length
        task['dataSize'] = str(total)
        self.service.setTaskDataSize(task['_id'], task['name'], str(total))
        return total

    def computTaskDataSize(self, task):
        total = self.getTaskDataSize(task)
        if task['stage'] == '灯光':
            refTaskList = self.service.getLightTaskInfoFromRefAssetIDList(task['refAssetIDList'])
        elif task['stage'] == '布局' or task['stage'] == '动画':
            refTaskList = self.service.getAniTaskInfoFromRefAssetIDList(task['refAssetIDList'])
        else:
            refTaskList = {}
        for refTask in refTaskList:
            total = total + self.getTaskDataSize(refTask)
        return total

    def displayTasks(self):
        self.taskTreeWidget.clear()
        self.tasks.sort(cmp=self.myCompare)
        textFont = QtGui.QFont("song", 11, QtGui.QFont.Normal)
        for task in self.tasks:
            # str = '{0:.2f}'.format((taskDataSize) / (float)(1024 * 1024)) + 'MB'
            # sizeStr = '{:>10}'.format(str)
            sizeStr = ''
            item = QtCGMaya.QTreeWidgetItem(self.taskTreeWidget,
                                            [task['stage'].center(10) + ' ', task['name'], sizeStr, ''])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            item.setFont(3, textFont)
            self.taskTreeWidget.resizeColumnToContents(0)
            self.taskTreeWidget.resizeColumnToContents(1)
            self.taskTreeWidget.resizeColumnToContents(2)
            self.taskTreeWidget.resizeColumnToContents(3)

    def onCurrentChanged(self, index):
        if index == 0:
            self.onSetVersion()
            self.tabIndex = index
        elif index == 1:
            self.onSetReference()
            self.tabIndex = index
        elif index == 2:
            self.onSetLight()
            self.tabIndex = index

    def onDownloadAttach(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        try:
            attachFileIDList = self.tasks[row]['attachFileIDList']
        except KeyError:
            return
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, u"选择下载目录", ".", "*")
        else:
            dialog = QtCGMaya.QFileDialog(self, u"Select Download Dir", ".", "*")
        dialog.setFileMode(QtCGMaya.QFileDialog.Directory)
        if dialog.exec_():
            # textFont = QtGui.QFont("song", 18, QtGui.QFont.Normal)
            self.fileList = dialog.selectedFiles()
            attachDir = self.fileList[0]
            for attachID in attachFileIDList:
                localFile = attachDir + '/' + attachID['name']
                # print 'localFile =', attachID['id'], localFile
                #self.service.getAttachFileGridFS(localFile, attachID['id'], attachID['name'])

    def onSetLoad(self):
        if not self.loadCheckBox.isChecked():
            self.textureCheckBox.setChecked(False)

    def dateStr(self, date1):
        if not date1:
            return ''
        dStr = date1.split('.')[0] + 'Z'
        date = datetime.strptime(dStr, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
        return date.strftime('%Y-%m-%d %H:%M:%S')

    def onSetReference(self):
        self.refTreeWidget.clear()
        headerList = []
        headerList.append(u'项目名')
        headerList.append(u'资产名')
        headerList.append(u'路径')
        self.refTreeWidget.setHeaderLabels(headerList)

        try:
            refAssetIDList = self.currentTask['refAssetIDList']
        except KeyError:
            refAssetIDList = []
            return
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for refAsset in refAssetIDList:
            refTask = self.service.getTaskInfo(refAsset['taskID'])
            try:
                if refTask:
                    assetPath = ''
                else:
                    assetPath = refTask['assetPath']
            except KeyError:
                assetPath = ''
            item = QtCGMaya.QTreeWidgetItem(self.refTreeWidget,
                    [refAsset['projectName'] + '  ', refAsset['name'] + '  ', assetPath])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            self.refTreeWidget.resizeColumnToContents(0)
            self.refTreeWidget.resizeColumnToContents(1)
            self.refTreeWidget.resizeColumnToContents(2)

    def onSetVersion(self):
        self.verTreeWidget.clear()
        headerList = []
        headerList.append(u'日期')
        headerList.append(u'说明')
        headerList.append(u'fileID')
        headerList.append(u'textureFileID')
        self.verTreeWidget.setHeaderLabels(headerList)

        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        try:
            fileVersionList = self.currentTask['fileVersionList']
        except KeyError:
            fileVersionList = []
        for arr in fileVersionList:
            item = QtCGMaya.QTreeWidgetItem(self.verTreeWidget, [self.dateStr(arr['createDate']), '  ' + arr['note'],
                                    '   ' + arr['fileID'], '  ' + arr['textureFileID']])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            item.setFont(3, textFont)
            self.verTreeWidget.resizeColumnToContents(0)
            self.verTreeWidget.resizeColumnToContents(1)
            self.verTreeWidget.resizeColumnToContents(2)
            self.verTreeWidget.resizeColumnToContents(3)

    def onSetLight(self):
        if self.currentTask['stage'] != '灯光':
            return
        self.litTreeWidget.clear()
        headerList = []
        headerList.append(u'灯光文件名')
        headerList.append(u'日期')
        self.litTreeWidget.setHeaderLabels(headerList)
        self.loadLightFile()

    def loadLightFile(self):
        try:
            self.lightFileIDList = self.currentTask['lightFileIDList']
        except KeyError:
            self.lightFileIDList = []
        self.litTreeWidget.clear()
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for lightFile in self.lightFileIDList:
            if self.currentTask['storage'] == 'ipfs':
                dd = ''
            else:
                fileInfo = self.service.getFileInfo(lightFile['id'])
                date = fileInfo.uploadDate + timedelta(hours=8)
                dd = date.strftime('%b-%d-%Y %H:%M:%S')
            item = QtCGMaya.QTreeWidgetItem(self.litTreeWidget, [lightFile['name'], '    ' + dd])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            self.litTreeWidget.resizeColumnToContents(0)
            self.litTreeWidget.resizeColumnToContents(1)

    def onSetAttach(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        #self.submitList = json.loads(self.service.getSubmitsOfTask(self.tasks[row]['_id']))

        self.treeWidget.clear()
        self.treeWidget.show()
        headerList = []
        headerList.append(u'提交名')
        headerList.append(u'文件名')
        headerList.append(u'')
        headerList.append(u'提交日期')
        self.treeWidget.setHeaderLabels(headerList)
        header = self.treeWidget.header()
        header.setStretchLastSection(True)

        self.returnRadiobutton.setChecked(True)
        self.verRadiobutton.setChecked(False)
        self.refRadiobutton.setChecked(False)
        self.lightRadiobutton.setChecked(False)

        self.treeWidget.show()
        # textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        type = ''
        for sub in self.submitList:
            dStr = sub['createDate'].split('.')[0] + 'Z'
            date = datetime.strptime(dStr, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
            dd = date.strftime('%Y-%m-%d %H:%M:%S')
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [sub['notes'], '', '', dd])
            # tem.setFont(0, textFont)
            # item.setFont(1, textFont)
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            self.treeWidget.resizeColumnToContents(2)
            for returnFile in sub['returnFileIDList']:
                sonItem = QtCGMaya.QTreeWidgetItem(item, ['', returnFile['name'], '', ''])
                self.treeWidget.resizeColumnToContents(1)

    def onClickItemTask(self, item, column):
        cmds.waitCursor(state=True)
        row = self.taskTreeWidget.indexOfTopLevelItem(item)
        self.fileListIndex = row
        self.taskIndex = row
        project = self.service.getProjectInfo(self.tasks[row]['projectName'])
        self.currentTask = self.tasks[row]
        self.taskFileID = self.currentTask['fileID']
        self.taskTextureFileID = self.currentTask['textureFileID']

        if project['templateName'] == '3DAsset':
            self.tabWidget.setTabEnabled(0, True)
            self.tabWidget.setTabEnabled(1, False)
            self.tabWidget.setTabEnabled(2, False)
            self.tabWidget.setTabEnabled(3, False)
            if self.tabIndex > 0:
                self.tabIndex = 0
            self.tabWidget.setCurrentIndex(0)
            self.onCurrentChanged(0)
        elif project['templateName'] == '3DShot':
            self.tabWidget.setTabEnabled(0, True)
            self.tabWidget.setTabEnabled(1, True)
            self.tabWidget.setTabEnabled(2, False)
            self.tabWidget.setTabEnabled(3, False)
            if self.currentTask['stage'] == '灯光':
                self.tabWidget.setTabEnabled(2, True)
                self.tabWidget.setCurrentIndex(2)
                self.onCurrentChanged(2)
            else:
                self.tabWidget.setCurrentIndex(self.tabIndex)
                self.onCurrentChanged(self.tabIndex)

        if column < 2 or not self.currentTask['fileID'] or item.text(2) != '':
            cmds.waitCursor(state=False)
            return

        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, project['name'])
        logPath = CGMaya_common.makeDir(projectDir, CGMaya_config.CGMaya_Log_Dir)
        refTaskDir = CGMaya_common.makeDir(projectDir, self.currentTask['name'])
        logFilePath = os.path.join(logPath, self.currentTask['name'] + CGMaya_config.logFileExt)
        fileLog = CGMaya_common.fileLog(logFilePath)
        fn = self.service.getFileName(self.currentTask, self.currentTask['fileID'])
        bExist = fileLog.getData(fn, self.currentTask['fileID'])
        taskDataSize = self.getTaskDataSize(self.currentTask)
        total = taskDataSize
        if not os.path.exists(os.path.join(refTaskDir, fn)) or bExist != 2:
            totalDownload = taskDataSize
        else:
            totalDownload = 0

        if self.currentTask['stage'] == '灯光':
            refTaskList = self.service.getLightTaskInfoFromRefAssetIDList(self.currentTask['refAssetIDList'])
        elif self.currentTask['stage'] == '布局' or self.currentTask['stage'] == '动画':
            refTaskList = self.service.getAniTaskInfoFromRefAssetIDList(self.currentTask['refAssetIDList'])
        else:
            refTaskList = []

        assetProjectDir = CGMaya_common.makeDir(CGMaya_config.assetStorageDir, project['refProject'])
        logPath = CGMaya_common.makeDir(assetProjectDir, CGMaya_config.CGMaya_Log_Dir)
        for refAssetTask in refTaskList:
            refTaskDir = CGMaya_common.makeDir(assetProjectDir, refAssetTask['name'])
            logFilePath = os.path.join(logPath, refAssetTask['name'] + CGMaya_config.logFileExt)
            refTaskDataSize = self.getTaskDataSize(refAssetTask)
            total = total + refTaskDataSize
            fileLog = CGMaya_common.fileLog(logFilePath)
            fn = self.service.getFileName(refAssetTask, refAssetTask['fileID'])
            bExist = fileLog.getData(fn, refAssetTask['fileID'])
            if not os.path.exists(os.path.join(refTaskDir, fn)) or bExist != 2:
                totalDownload = totalDownload + refTaskDataSize
        sizeStr = '{:>10}'.format('{0:.2f}'.format(total / (float)(1024 * 1024)) + 'MB')
        sizeStrDownload = '{:>10}'.format('{0:.2f}'.format(totalDownload / (float)(1024 * 1024)) + 'MB')
        item.setText(2, sizeStr)
        item.setText(3, sizeStrDownload)
        self.taskTreeWidget.resizeColumnToContents(2)
        self.taskTreeWidget.resizeColumnToContents(3)
        cmds.waitCursor(state=False)

    def onDoubleClickItemTask(self, item, column):
        row = self.taskTreeWidget.indexOfTopLevelItem(item)
        self.fileListIndex = row
        self.taskIndex = row
        self.taskFileID = self.tasks[row]['fileID']
        self.taskTextureFileID = self.tasks[row]['textureFileID']
        self.onOpen()

    def onClickItem1(self, item, column):
        if self.tabIndex == 0:
            row = self.verTreeWidget.indexOfTopLevelItem(item)
            fileVersionList = self.currentTask['fileVersionList']
            #self.taskFileID = CGMaya_service.objectIDToUnicode(self.assetData[row]['id'])
            self.taskFileID = fileVersionList[row]['fileID']
            self.taskTextureFileID = fileVersionList[row]['textureFileID']
        elif self.tabIndex == 2:
            row = self.litTreeWidget.indexOfTopLevelItem(item)
            self.lightFileFlag = True
            self.taskFileID = self.lightFileIDList[row]['id']
            self.taskTextureFileID = ''

    def onDoubleClickItem1(self, item, column):
        if self.tabIndex == 0:
            row = self.verTreeWidget.indexOfTopLevelItem(item)
            fileVersionList = self.currentTask['fileVersionList']
            # self.taskFileID = CGMaya_service.objectIDToUnicode(self.assetData[row]['id'])
            self.taskFileID = fileVersionList[row]['fileID']
            self.taskTextureFileID = fileVersionList[row]['textureFileID']
            self.onOpen()
            return
        elif self.tabIndex == 2:
            row = self.litTreeWidget.indexOfTopLevelItem(item)
            self.lightFileFlag = True
            self.taskFileID = self.lightFileIDList[row]['id']
            self.taskTextureFileID = ''
            self.onOpen()
            return
        elif self.tabIndex == 3:
            parentItem = item.parent()
            submitIndex = self.treeWidget.indexOfTopLevelItem(parentItem)
            submit = self.submitList[submitIndex]
            returnIndex = self.treeWidget.indexFromItem(parentItem).row()
            returnFile = submit['returnFileIDList'][returnIndex]
            print('returnFile =', returnFile)
            pngDialog(self.service, self.currentTask, submit['submitFileIDList'][0])

    def closeEvent(self, event):
        self.CGMenu.menu.setEnable(True)
        event.accept()  # let the window close

    def onCancel(self):
        self.CGMenu.menu.setEnable(True)
        self.close()

    def onRefresh(self):
        self.getProjects()

    def onOpen(self):
        CGMaya_config.currentTask = self.currentTask
        CGMaya_config.currentProject = self.service.getProjectInfo(self.currentTask['projectName'])

        cmds.file(new=True, force=True)
        self.loadFlag = self.loadCheckBox.isChecked()
        CGMaya_config.textureReadFlag = self.textureCheckBox.isChecked()
        CGMaya_config.refAssetIDList = []

        # projectStorage = 'GridFS'
        # try:
        #     if CGMaya_config.currentProject['storage'] == 'ipfs':
        #         projectStorage = 'ipfs'
        # except KeyError:
        #     pass
        # if projectStorage == 'ipfs':
        #     if self.service.IPFSConnect() == None:
        #         CGMaya_config.logger.error('IPFS Error: : %s\r' % CGMaya_config.IPFSUrl)
        #         QtCGMaya.QMessageBox.information(self.parent, u"错误", CGMaya_config.IPFSUrl,
        #                                          QtCGMaya.QMessageBox.Yes)
        #         # cmds.confirmDialog(title=u'错误信息', message=CGMaya_config.IPFSUrl, defaultButton=u'确认')
        #         self.close()
        #         return
        #     else:
        #         CGMaya_config.logger.info('IPFS Connect: : %s\r' % CGMaya_config.IPFSUrl)

        if not self.loadFlag:
            CGMaya_config.logger.info('Create newFile-------\r')
            CGMaya_config.logger.server(self.currentTask['projectName'], self.currentTask['name'], self.currentTask['_id'],
                                        CGMaya_config.CGMaya_Action_New)
            CGMaya_config.textureReadFlag = True
            self.CGMenu.menu.setEnable(True)
            if CGMaya_config.currentProject['templateName'] == '3DShot':
                self.CGMenu.menuOpen(False)
            else:
                self.CGMenu.menuOpen(True)
            self.close()
            return

        if self.currentTask['stage'] == u'灯光':
            CGMaya_config.lightRefFlag = True
            status, message =self.openLightTask(self.currentTask, self.taskFileID)
        elif self.currentTask['stage'] == u'布局' or self.currentTask['stage'] == u'动画':
            status, message = self.openAniTask(self.currentTask, self.taskFileID)
        else:
            status, message = self.openAssetTask(self.currentTask, self.taskFileID, self.taskTextureFileID)
        if not status:
            # QtCGMaya.QMessageBox.information(self, u"错误", message, QtCGMaya.QMessageBox.Yes)
            # self.CGMenu.menu.setEnable(True)
            # self.close()
            return
        # stage = currentTask['stage']
        # if stage == u'动画' or stage == u'布局' or stage == u'灯光':
        #     if CGMaya_config.frameList:
        #         cmds.playbackOptions(min=int(CGMaya_config.frameList.split('-')[0]),
        #                              max=int(CGMaya_config.frameList.split('-')[1]))
        #     mel.eval("setCurrentFrameVisibility(1)")
        #     mel.eval("setCameraNamesVisibility(1)")
        #     mel.eval("setFocalLengthVisibility(1)")
        #     # mel.eval("setCurrentFrameVisibility(!`optionVar -q currentFrameVisibility`)")
        #     # mel.eval("setCameraNamesVisibility(!`optionVar -q cameraNamesVisibility`)")
        #     # mel.eval("setFocalLengthVisibility(!`optionVar -q focalLengthVisibility`)")
        CGMaya_config.logger.server(self.currentTask['projectName'], self.currentTask['name'], self.currentTask['_id'],
                                        CGMaya_config.CGMaya_Action_Open)
        CGMaya_config.logger.info('Open Task---Finish-----------------\r')
        self.CGMenu.menu.setEnable(True)
        if CGMaya_config.currentProject['templateName'] == '3DShot':
            self.CGMenu.menuOpen(False)
        else:
            self.CGMenu.menuOpen(True)
        self.close()
        self.mousePoint = CGMaya_mouse.mousePoint()


    #  打开资产任务
    def openAssetTask(self, currentTask, taskFileID, taskTextureFileID):
        CGMaya_config.logger.info('Open Asset Task, %s(%s)\r' % (currentTask['name'], currentTask['stage'].encode('utf-8')))

        if not taskFileID:
            return True, 'taskFileID is None'

        projectDir = CGMaya_common.makeDir(CGMaya_config.assetStorageDir, currentTask['projectName'])
        taskDir = CGMaya_common.makeDir(projectDir, currentTask['name'])
        status, message, taskFileName = CGMaya_common.downloadFile(self.service, projectDir, projectDir, taskDir,
                                                    currentTask, taskFileID, taskTextureFileID)
        if status:
            self.hide()
            cmds.workspace(dir=projectDir)
            CGMaya_config.assetExtFileName = os.path.basename(taskFileName).split('.').pop()
            CGMaya_config.logger.info("Maya Open File2...\r")
            try:
                cmds.file(taskFileName, open=True, force=True)
            except RuntimeError, e:
                CGMaya_config.logger.error("RuntimeError-----%s\r" % taskFileName)
                CGMaya_config.logger.error("e-----%s\r" % e)
            return True, ''
        else:
            return False, message

    #  打开布局、动画任务
    def openAniTask(self, currentTask, taskFileID):
        CGMaya_config.logger.info('Open Animation Task, %s(%s)\r' % (currentTask['name'], currentTask['stage']))

        if not taskFileID:
            return True, 'taskFileID is None'

        refProjectDir = CGMaya_common.makeDir(CGMaya_config.assetStorageDir, CGMaya_config.currentProject['refProject'])
        # 获得引用资产列表
        refTaskList = self.service.getAniTaskInfoFromRefAssetIDList(currentTask['refAssetIDList'])
        for refTask in refTaskList:
            if not refTask:
                continue
            refTaskDir = CGMaya_common.makeDir(refProjectDir, refTask['name'])
            # 下载引用资产并处理
            status, message, _ = CGMaya_common.downloadFile(self.service, refProjectDir, refProjectDir, refTaskDir, refTask, refTask['fileID'], refTask['textureFileID'])
            if not status:
                return False, message

        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, currentTask['projectName'])
        taskDir = CGMaya_common.makeDir(projectDir, currentTask['name'])
        # 下载动画模型文件
        status, message, taskFileName = CGMaya_common.downloadFile(self.service, projectDir, refProjectDir, taskDir, currentTask, taskFileID)
        if not status:
            return False, message

        # 下载音频文件
        CGMaya_config.logger.info("Processing Audio...\r")
        try:
            audioFileIDList = currentTask['audioFileIDList']
        except KeyError:
            audioFileIDList = []
        audioDir = CGMaya_common.makeDir(projectDir, CGMaya_config.CGMaya_Audio_Dir)
        for audioFileID in audioFileIDList:
            filePath = os.path.join(audioDir, audioFileID['name'])
            self.service.getFile(currentTask, filePath, audioFileID['id'], '', False)

        cmds.workspace(dir=projectDir)
        CGMaya_config.assetExtFileName = os.path.basename(taskFileName).split('.').pop()
        CGMaya_config.logger.info("Maya Open File...\r")
        self.hide()
        try:
            cmds.file(taskFileName, open=True, force=True)
        except RuntimeError, e:
            CGMaya_config.logger.error("RuntimeError-----%s\r" % taskFileName)
            # return False, 'RuntimeError-----'
            CGMaya_config.logger.error("e-----%s\r" % e)
        return True, ''

    def openLightTask(self, currentTask, taskFileID):
        CGMaya_config.logger.info('Open Light Task, %s(%s)\r' % (currentTask['name'], currentTask['stage']))

        if not taskFileID:
            return True, 'taskFileID is None'

        refProjectDir = CGMaya_common.makeDir(CGMaya_config.assetStorageDir, CGMaya_config.currentProject['refProject'])
        # 获得引用资产列表
        refTaskList = self.service.getLightTaskInfoFromRefAssetIDList(currentTask['refAssetIDList'])
        for refTask in refTaskList:
            if not refTask:
                continue
            refTaskDir = CGMaya_common.makeDir(refProjectDir, refTask['name'])
            # 下载引用资产并处理
            status, message, _ = CGMaya_common.downloadFile(self.service, refProjectDir, refProjectDir, refTaskDir,
                                            refTask, refTask['fileID'], refTask['textureFileID'])
            if not status:
                return False, message

        # 下载动画模型文件
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, currentTask['projectName'])
        taskDir = CGMaya_common.makeDir(projectDir, currentTask['name'])
        status, message, aniFileName = CGMaya_common.downloadFile(self.service, projectDir, refProjectDir, taskDir, currentTask, currentTask['fileID'])
        if not status:
            return False, message

        taskDir = CGMaya_common.makeDir(projectDir, currentTask['name'])
        if self.lightFileFlag:
            #  下载灯光文件
            lightDir = CGMaya_common.makeDir(taskDir, CGMaya_config.CGMaya_Light_Dir)
            status, message, lightFileName = CGMaya_common.downloadFile(self.service, projectDir, refProjectDir,
                                                            lightDir, currentTask, taskFileID)
            CGMaya_config.logger.info("     Open File-----%s\r" % lightFileName)
            self.hide()
            cmds.file(lightFileName, open=True, force=True)
        else:
            self.hide()
            if CGMaya_config.lightRefFlag:
                CGMaya_config.logger.info("     Open Reference File-----%s\r" % aniFileName)
                cmds.file(aniFileName, reference=True, options='v=0', ignoreVersion=True,
                          namespace=CGMaya_config.currentTask['name'])
            else:
                CGMaya_config.logger.info("     Open File-----%s\r" % aniFileName)
                cmds.file(aniFileName, open=True, force=True)
        renderer = CGMaya_config.currentProject['render']

        cmds.setAttr('defaultRenderGlobals.currentRenderer', renderer, type='string')
        CGMaya_config.singleOutputPath = taskDir
        pymel.core.mel.setProject(CGMaya_config.singleOutputPath)
        return True, ''