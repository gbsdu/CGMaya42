
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
#import MySQLdb
#import MySQLdb.cursors
import datetime
import random
import subprocess
import urllib2
import shutil
import zipfile
from datetime import datetime, timedelta
import copy
if platform.system() == 'Windows':
    import pyaudio
import wave
import ctypes
#import pytz

import CGMaya_function
import CGMaya_service
import CGMaya_logger
import CGMaya_main
import CGMaya_mouse

rightPos = 10

def convertHANZI(unicode):
    return unicode.encode('unicode-escape').decode('string_escape')

def _getcls(name):
    result = getattr(QtCGMaya, name, None)
    if result is None:
        result = getattr(QtCore, name, None)
    return result

def wrapinstance(ptr):
    """Converts a pointer (int or long) into the concrete
    PyQt/PySide object it represents."""
    # pointers for Qt should always be long integers
    ptr = long(ptr)
    # Get the pointer as a QObject, and use metaObject
    # to find a better type.
    qobj = shiboken.wrapInstance(ptr, QtCore.QObject)
    metaobj = qobj.metaObject()
    # Look for the real class in qt namespaces.
    # If not found, walk up the hierarchy.
    # When we reach the top of the Qt hierarchy,
    # we'll break out of the loop since we'll eventually
    # reach QObject.
    realcls = None
    while realcls is None:
        realcls = _getcls(metaobj.className())
        metaobj = metaobj.superClass()
    # Finally, return the same pointer/object
    # as its most specific type.
    return shiboken.wrapInstance(ptr, realcls)

def maya_main_window():
    main_win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(long(main_win_ptr), QtCGMaya.QWidget)

def judgelogData(logJsonData, id):
    fileName = ''
    bExist = False
    for log in logJsonData:
        if log['id'] == id:
            fileName = log['fileName']
            bExist = True
            break
    return bExist, fileName

class pngDialog(QtCGMaya.QDialog):
    def __init__(self, service, task, returnFile, parent = maya_main_window()):
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
        tmpDir = os.getenv('TEMP')
        print('tmpDir =', tmpDir)
        localFile = os.path.join(tmpDir, self.returnFile['name'])
        print('localFile =', localFile)
        self.service.getFile(self.task, localFile, self.returnFile['id'], self.returnFile['name'])
        self.image.load(localFile)

    def onClose(self):
        self.close()

class txtDialog(QtCGMaya.QDialog):
    def __init__(self, fileName, parent=maya_main_window()):
        super(txtDialog, self).__init__(parent)

        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.qle = QtCGMaya.QTextEdit(self)

        mytext = ''
        with open(fileName, 'r') as f:
            mytext = f.readlines()
        self.qle.setPlainText(mytext)

        self.layout.addWidget(self.qle)
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
        self.setGeometry(350, 350, 700, 700)
        self.show()

    def onClose(self):
            self.close()

class loginWindow(QtCGMaya.QDialog):
    def __init__(self, service, app, parent = maya_main_window()):
        super(loginWindow, self).__init__(parent)
        self.app = app
        self.app.menu.setEnable(False)
        self.service = service
        #cmds.nameCommand('RCMayaLogin', annotation='RCMaya Login', command='python("onLogin()")')
        #cmds.hotkey(k='Return', name='RCMayaLogin')
        #result, message = service.myWFGetAllTeams()
        result, message = service.getAllTeams()
        CGMaya_config.logger.set("login")
        if not result:
            CGMaya_config.logger.error('myGetAllTeams Error, CGServer API Server is down\r')
            cmds.confirmDialog(title=u'错误信息', message= message, defaultButton=u'确认')
            return
        self.teamList = message
        self.setup_ui()

    def setup_ui(self):
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'用户登录')
            self.teamLabel = QtCGMaya.QLabel(u'团队', self)
            self.nameLabel = QtCGMaya.QLabel(u'帐号', self)
            self.passLabel = QtCGMaya.QLabel(u'密码', self)
            self.button1 = QtCGMaya.QPushButton(u'登录', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            self.setWindowTitle(u'User Login')
            self.teamLabel = QtCGMaya.QLabel(u'TeamName', self)
            self.nameLabel = QtCGMaya.QLabel(u'UserName', self)
            self.passLabel = QtCGMaya.QLabel(u'Password', self)
            self.button1 = QtCGMaya.QPushButton(u'Login', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.teamBox = QtCGMaya.QComboBox(self)
        n = 0
        for team in self.teamList:
            self.teamBox.addItem(team['alias'])
            if CGMaya_config.teamName == team['name']:
                self.teamBox.setCurrentIndex(n)
            n += 1
        self.teamBox.currentIndexChanged.connect(self.onTeamSelect)
        self.nameText = QtCGMaya.QLineEdit(CGMaya_config.userName, self)
        self.passText = QtCGMaya.QLineEdit(CGMaya_config.password, self)
        self.passText.setEchoMode(QtCGMaya.QLineEdit.Password)
        self.button1.clicked.connect(self.onLogin)
        self.button2.clicked.connect(self.onCancel)

        self.main_layout = QtCGMaya.QGridLayout()
        self.row_Hbox1 = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.teamLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.teamBox, 0, 1, 1, 6)
        self.layout.addWidget(self.nameLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.nameText, 1, 1, 1, 6)
        self.layout.addWidget(self.passLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.passText, 2, 1, 1, 6)
        self.row_Hbox1.setLayout(self.layout)

        self.row_Hbox2 = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.button1, 0, 1)
        self.layout.addWidget(self.button2, 0, 0)
        self.row_Hbox2.setLayout(self.layout)

        self.main_layout.addWidget(self.row_Hbox1, 0, 0, 3, 1)
        self.main_layout.addWidget(self.row_Hbox2, 4, 0, 1, 1)
        self.setLayout(self.main_layout)

        self.setGeometry(400, 400, 400, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onTeamSelect(self, n):
        CGMaya_config.teamName = self.teamList[n]['name']

    def onLogin(self):
        CGMaya_config.teamName = self.teamList[self.teamBox.currentIndex()]['name']
        result, message = self.service.login(self.nameText.text(), self.passText.text())
        if not result:
            CGMaya_config.logger.error('login Error: : %s\r' % message)
            cmds.confirmDialog(title=u'错误信息', message=message, defaultButton=u'确认')
            return
        CGMaya_config.userName = self.nameText.text()
        CGMaya_config.password = self.passText.text()
        CGMaya_config.logger.info("login Success...\r")
        CGMaya_config.logger.setUserName(CGMaya_config.userName)
        CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_LoginSucessful)
        self.app.menu.setEnable(True)
        self.app.menuLogin()
        self.close()
        CGMaya_config.selectedProjectName = ''
        #CGMaya_function.readConfigFile_user()

    def onCancel(self):
        self.app.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        self.app.menu.setEnable(True)
        event.accept()

class selectProjectDialog(QtCGMaya.QDialog):
    def __init__(self, service, parent):
        super(selectProjectDialog, self).__init__(parent)
        self.service = service
        self.parent = parent

        self.main_layout = QtCGMaya.QVBoxLayout()
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.projectListWidget = QtCGMaya.QListWidget(self)
        self.layout.addWidget(self.projectListWidget, 0, 0)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 0, 0)
        #self.projectListWidget.hide()
        self.projectListWidget.connect(self.projectListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                       self.onClickProjectItem)

        self.GetProjects()


        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'选择项目')
        else:
            self.setWindowTitle(u' SelectProject')
        self.setGeometry(900, 300, 400, 400)
        #self.parent.setEnabled(False)
        #self.show()

    def GetProjects(self):
        result = self.service.myWFGetAllProjects()
        self.projectList = json.loads(result)
        #textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        for project in self.projectList:
            item = QtCGMaya.QListWidgetItem(project['name'])
            #item.setFont(textFont)
            self.projectListWidget.addItem(item)
        if len(self.projectList) == 0:
            return
        row = 0

    def onClickProjectItem(self, item):
        #cmds.waitCursor(state=True)
        row = self.projectListWidget.currentRow()
        CGMaya_config.selectedProjectName = self.projectList[row]['name']
        self.parent.projectText.setText(CGMaya_config.selectedProjectName)
        self.parent.GetTasks()
        #cmds.waitCursor(state=False)
        self.close()

    def onClose(self):
        self.close()
        self.parent.setEnabled(True)

class openTaskWindow(QtCGMaya.QDialog):
    def __init__(self, service, app, parent = maya_main_window()):
        super(openTaskWindow, self).__init__(parent)
        self.service = service
        self.app = app
        self.app.menu.setEnable(False)
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
        CGMaya_config.currentDialog = self
        CGMaya_config.fileID = ''
        CGMaya_config.changeReferenceModelList = []
        CGMaya_config.versionURL = ''
        if not os.path.exists(CGMaya_config.storageDir):
            if platform.system() == 'Windows':
                try:
                    os.mkdir(CGMaya_config.storageDir)
                except WindowsError:
                    cmds.confirmDialog(title=u'提醒', message=u'设置的存储路径不合适, 请设置合适的存储路径', button=[u'是'], defaultButton=u'是')
                    return
        cmds.nameCommand('RCMayaOpen', annotation='RCMaya Open', command='python("onOpen()")')
        cmds.hotkey(k='Return', name='RCMayaOpen')
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        CGMaya_config.taskFileID = ''
        CGMaya_config.lightFileFlag = False
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
        self.layout.addWidget(self.textureCheckBox, 0, 5, 1, 1)
        self.layout.addWidget(self.loadCheckBox, 1, 5, 1, 1)
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
        headerList.append(u'')
        headerList.append(u'总数据量')
        headerList.append(u'')
        headerList.append(u'下载数据量')
        self.taskTreeWidget.setHeaderLabels(headerList)
        self.main_layout.addWidget(self.taskTreeWidget)
        self.taskTreeWidget.itemClicked.connect(self.onClickItemTask)
        self.taskTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItemTask)

        self.row_treeHbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.treeWidget = QtCGMaya.QTreeWidget(self)
        self.row_treeHbox.setLayout(self.layout)
        self.layout.addWidget(self.treeWidget, 0, 0)
        self.main_layout.addWidget(self.row_treeHbox)
        self.treeWidget.hide()
        self.treeWidget.itemClicked.connect(self.onClickItem1)
        self.treeWidget.itemDoubleClicked.connect(self.onDoubleClickItem1)

        self.row_openHbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.openRefRadiobutton = QtCGMaya.QRadioButton(u'引用', self)
            self.openNorRadiobutton = QtCGMaya.QRadioButton(u'正常', self)
            self.row_openHbox.setTitle(u'灯光文件打开方式')
        else:
            self.openRefRadiobutton = QtCGMaya.QRadioButton(u'Reference', self)
            self.openNorRadiobutton = QtCGMaya.QRadioButton(u'Normal', self)
            self.row_openHbox.setTitle(u'Light File Open way')
        self.openRefRadiobutton.setChecked(True)
        self.openNorRadiobutton.setChecked(False)
        self.layout.addWidget(self.openRefRadiobutton, 0, 0)
        self.layout.addWidget(self.openNorRadiobutton, 0, 1)
        self.openRefRadiobutton.clicked.connect(self.onSetRefOpen)
        self.openNorRadiobutton.clicked.connect(self.onSetNorOpen)
        self.row_openHbox.setLayout(self.layout)
        # self.row_openHbox.setCheckable(True)
        # self.row_openHbox.setChecked(False)

        self.row_watchHbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.refRadiobutton = QtCGMaya.QRadioButton(u'引用', self)
            self.verRadiobutton = QtCGMaya.QRadioButton(u'版本', self)
            self.lightRadiobutton = QtCGMaya.QRadioButton(u'灯光', self)
            self.returnRadiobutton = QtCGMaya.QRadioButton(u'附件', self)
            self.attachButton = QtCGMaya.QPushButton(u'下载附件', self)
            self.row_watchHbox.setTitle(u'列表显示')
        else:
            self.refRadiobutton = QtCGMaya.QRadioButton(u'Ref', self)
            self.verRadiobutton = QtCGMaya.QRadioButton(u'Ver', self)
            self.lightRadiobutton = QtCGMaya.QRadioButton(u'Lit', self)
            self.returnRadiobutton = QtCGMaya.QRadioButton(u'Att', self)
            self.attachButton = QtCGMaya.QPushButton(u'Attachment', self)
            self.row_watchHbox.setTitle(u'List Display')
        self.refRadiobutton.setChecked(False)
        self.verRadiobutton.setChecked(False)
        self.lightRadiobutton.setChecked(False)
        self.returnRadiobutton.setChecked(False)
        self.layout.addWidget(self.refRadiobutton, 0, 1)
        self.layout.addWidget(self.verRadiobutton, 0, 0)
        self.layout.addWidget(self.lightRadiobutton, 0, 2)
        self.layout.addWidget(self.returnRadiobutton, 0, 3)
        self.row_watchHbox.setLayout(self.layout)
        self.refRadiobutton.clicked.connect(self.onSetReference)
        self.lightRadiobutton.clicked.connect(self.onSetLight)
        self.verRadiobutton.clicked.connect(self.onSetVersion)
        self.returnRadiobutton.clicked.connect(self.onSetAttach)
        self.attachButton.clicked.connect(self.onDownloadAttach)
        self.attachButton.setEnabled(False)

        optionBox = QtCGMaya.QGroupBox()
        optionLayout = QtCGMaya.QGridLayout()
        optionLayout.addWidget(self.row_openHbox, 0, 4, 1, 2)
        optionLayout.addWidget(self.row_watchHbox, 0, 0, 1, 3)
        optionLayout.addWidget(self.attachButton, 0, 6, 1, 1)
        optionBox.setLayout(optionLayout)
        self.main_layout.addWidget(optionBox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'打开', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
            self.button3 = QtCGMaya.QPushButton(u'刷新', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Open', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button3 = QtCGMaya.QPushButton(u'Refresh', self)
        layout1.addWidget(self.button3, 1, 0)
        layout1.addWidget(self.button1, 1, 2)
        layout1.addWidget(self.button2, 1, 1)
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
        self.setGeometry(350, 350, 950, 850)
        #self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()
        self.show()
        self.getProjects()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onPress(self, *args):
        self.anchorPoint = cmds.draggerContext('Context', query = True, anchorPoint = True)
        CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        print 'anchorPoint =', self.anchorPoint, CGMaya_config.mouseCount

    def onDrag(self, *args):
        #pass
        self.dragPoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        print 'anchorPoint =', self.dragPoint

    def onRelease(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        print ' releasePoint =', self.releasePoint

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def getProjects(self):
        self.rawTasks = json.loads(self.service.myWFGetMyTask(CGMaya_config.userName))
        self.rawProjectList = json.loads(self.service.myWFGetAllProjects())
        self.parentProjectList = []
        self.allTaskList = []
        self.projectList = []
        self.parentProjectBox.clear()

        for rawTask in self.rawTasks:
            for rawProject in self.rawProjectList:
                if rawTask['projectName'] == rawProject['name']:
                    parentProjectName = rawProject['project']
                    break
            self.allTaskList.append({'name': rawTask['name'], 'projectName': rawTask['projectName'],
                                             'parentProjectName': parentProjectName, 'task': rawTask})
        for task in self.allTaskList:
            if not task['parentProjectName'] in self.parentProjectList:
                self.parentProjectBox.addItem(task['parentProjectName'])
                self.parentProjectList.append(task['parentProjectName'])
        if CGMaya_config.parentProjectName:
            for index, project in enumerate(self.parentProjectList):
                if project == CGMaya_config.parentProjectName:
                    self.parentProjectBox.setCurrentIndex(index)
                    break
        else:
            CGMaya_config.parentProjectName = self.parentProjectList[0]
            self.parentProjectBox.setCurrentIndex(0)
        self.onParentProjectSelect(0)

    def onParentProjectSelect(self, index):
        if not self.parentProjectList:
            return
        row = self.parentProjectBox.currentIndex()
        CGMaya_config.parentProjectName = self.parentProjectList[row]
        self.projectList = []
        self.projectBox.clear()
        for task in self.allTaskList:
            if task['parentProjectName'] == CGMaya_config.parentProjectName and (not task['projectName'] in self.projectList):
                self.projectBox.addItem(task['projectName'])
                self.projectList.append(task['projectName'])
        if CGMaya_config.projectName:
            for index, project in enumerate(self.projectList):
                if project == CGMaya_config.projectName:
                    self.projectBox.setCurrentIndex(index)
                    break
        else:
            CGMaya_config.projectName = self.projectList[0]
            self.projectBox.setCurrentIndex(0)
        self.onProjectSelect(0)

    def onProjectSelect(self, index):
        if not self.projectList:
            return
        row = self.projectBox.currentIndex()
        CGMaya_config.projectName = self.projectList[row]
        CGMaya_config.tasks = []
        for task in self.allTaskList:
            if task['projectName'] == CGMaya_config.projectName:
                CGMaya_config.tasks.append(task['task'])
        self.taskIndex = -1
        self.treeWidget.clear()
        self.displayTasks()

    def getTaskDataSize(self, task, sum):
        if not task:
            return sum
        dataSize = ''
        try:
            dataSize = task['dataSize']
        except AttributeError:
            dataSize = ''
        if dataSize != '':
            return int(dataSize)
        total = 0
        if not task:
            return 0
        fileInfo = self.service.getFileInfo(task['fileID'])
        total = total + fileInfo.length
        if task['textureFileID']:
            fileInfo = self.service.getFileInfo(task['textureFileID'])
            total = total + fileInfo.length
        total = sum + total
        task['dataSize'] = str(total)
        self.service.setTaskDataSize(task['_id'], task['name'], str(total))
        return total

    def computTaskDataSize(self):
        dataSize = ''
        for task in CGMaya_config.tasks:
            try:
                dataSize = task['dataSize']
            except AttributeError:
                dataSize = ''
            if dataSize != '':
                continue
            total = 0
            if task['stage'] == '灯光':
                refTaskList = json.loads(self.service.getLightTaskInfoFromRefAssetIDList(task['refAssetIDList']))
            else:
                refTaskList = json.loads(self.service.getAniTaskInfoFromRefAssetIDList(task['refAssetIDList']))
            for refTask in refTaskList:
                self.getTaskDataSize(refTask, 0)
                total = total + refTask['dataSize']
            self.getTaskDataSize(task, total)

    def displayTasks(self):
        self.taskTreeWidget.clear()
        CGMaya_config.tasks.sort(cmp=self.myCompare)
        textFont = QtGui.QFont("song", 11, QtGui.QFont.Normal)
        self.computTaskDataSize()
        for task in CGMaya_config.tasks:
            str = '{0:.2f}'.format(int(task['dataSize']) / (float)(1024 * 1024)) + 'MB'
            sizeStr = '{:>10}'.format(str)
            item = QtCGMaya.QTreeWidgetItem(self.taskTreeWidget, [task['stage'].center(10) + ' ', task['name'], '', sizeStr, '', ''])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(3, textFont)
            item.setFont(5, textFont)
            self.taskTreeWidget.resizeColumnToContents(0)
            self.taskTreeWidget.resizeColumnToContents(1)
            self.taskTreeWidget.resizeColumnToContents(3)
            self.taskTreeWidget.resizeColumnToContents(5)

    def onDownloadAttach(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        try:
            attachFileIDList = CGMaya_config.tasks[row]['attachFileIDList']
        except KeyError:
            return
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, u"选择下载目录", ".", "*")
        else:
            dialog = QtCGMaya.QFileDialog(self, u"Select Download Dir", ".", "*")
        dialog.setFileMode(QtCGMaya.QFileDialog.Directory)
        if dialog.exec_():
            #textFont = QtCGMaya.QFont("song", 18, QtCGMaya.QFont.Normal)
            self.fileList = dialog.selectedFiles()
            attachDir = self.fileList[0]
            for attachID in attachFileIDList:
                localFile = attachDir + '/' + attachID['name']
                #print 'localFile =', attachID['id'], localFile
                self.service.getAttachFileGridFS(localFile, attachID['id'], attachID['name'])

    def onSetIcon(self):
        #CGMaya_config.IconFlag = self.iconCheckBox.isChecked()
        #self.GetTasks()
        pass

    def onSetLoad(self):
        if not self.loadCheckBox.isChecked():
            self.textureCheckBox.setChecked(False)

    def onSetReference(self):
        #if not self.bTaskSelected:
        #    return
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        self.treeWidget.clear()
        self.treeWidget.show()
        headerList = []
        headerList.append(u'项目名')
        headerList.append(u'资产名')
        headerList.append(u'路径')
        #headerList.append('ID')
        self.treeWidget.setHeaderLabels(headerList)

        self.refRadiobutton.setChecked(True)
        self.verRadiobutton.setChecked(False)
        self.returnRadiobutton.setChecked(False)
        self.lightRadiobutton.setChecked(False)
        try:
            refAssetIDList = CGMaya_config.tasks[row]['refAssetIDList']
        except KeyError:
            return
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for refAsset in refAssetIDList:
            refTask = json.loads(self.service.myWFGetTaskInfo(refAsset['taskID']))
            try:
                if refTask:
                    assetPath = ''
                else:
                    assetPath = refTask['assetPath']
            except KeyError:
                assetPath = ''
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [refAsset['projectName'] + '  ', refAsset['name'] + '  ', assetPath])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            self.treeWidget.resizeColumnToContents(2)

    def onSetVersion(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        if CGMaya_config.tasks[row]['storage'] == 'ipfs':
            return

        self.treeWidget.clear()
        self.treeWidget.show()
        headerList = []
        headerList.append(u'文件名')
        headerList.append(u'ID')
        headerList.append(u'日期')
        headerList.append(u'fileID')
        #headerList.append(u'大小')
        self.treeWidget.setHeaderLabels(headerList)
        #header = self.treeWidget.header()
        #header.setStretchLastSection(True)

        self.verRadiobutton.setChecked(True)
        self.returnRadiobutton.setChecked(False)
        self.refRadiobutton.setChecked(False)
        self.lightRadiobutton.setChecked(False)

        self.assetData = self.service.listMayaFile(CGMaya_config.tasks[row]['name'])
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for arr in self.assetData:
            date = arr['uploadDate'] + timedelta(hours=8)
            dd = date.strftime('%b-%d-%Y %H:%M:%S')
            #fstr = '{0:.2f}'.format(arr['length'] / (float)(1024 * 1024))
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [arr['filename'] + '  ', str(arr['id']) + '  ', dd])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            item.setFont(3, textFont)
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            self.treeWidget.resizeColumnToContents(2)

    def onSetLight(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        if CGMaya_config.tasks[row]['stage'] != u'灯光':
            return
        self.treeWidget.clear()
        self.treeWidget.show()
        headerList = []
        headerList.append(u'灯光文件名')
        headerList.append(u' ')
        headerList.append(u'日期')
        self.treeWidget.setHeaderLabels(headerList)

        self.lightRadiobutton.setChecked(True)
        self.returnRadiobutton.setChecked(False)
        self.refRadiobutton.setChecked(False)
        self.verRadiobutton.setChecked(False)

        self.loadLightFile(row)

    def loadLightFile(self, row):
        try:
            self.lightFileIDList = CGMaya_config.tasks[row]['lightFileIDList']
        except KeyError:
            self.lightFileIDList = []
        self.treeWidget.show()
        self.treeWidget.clear()
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        for lightFile in self.lightFileIDList:
            if CGMaya_config.tasks[row]['storage'] == 'ipfs':
                dd = ''
            else:
                fileInfo = self.service.getFileInfo(lightFile['id'])
                date = fileInfo.uploadDate + timedelta(hours=8)
                dd = date.strftime('%b-%d-%Y %H:%M:%S')
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [lightFile['name'], '', dd])
            item.setFont(0, textFont)
            item.setFont(2, textFont)
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            self.treeWidget.resizeColumnToContents(3)

    def onSetAttach(self):
        if self.taskIndex < 0:
            return
        row = self.taskIndex
        self.submitList = json.loads(self.service.getSubmitsOfTask(CGMaya_config.tasks[row]['_id']))

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
        #textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        type = ''
        for sub in self.submitList:
            dStr = sub['createDate'].split('.')[0] + 'Z'
            date = datetime.strptime(dStr, "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
            dd = date.strftime('%Y-%m-%d %H:%M:%S')
            item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [sub['notes'], '', '', dd])
            #tem.setFont(0, textFont)
            #item.setFont(1, textFont)
            self.treeWidget.resizeColumnToContents(0)
            self.treeWidget.resizeColumnToContents(1)
            self.treeWidget.resizeColumnToContents(2)
            for returnFile in sub['returnFileIDList']:
                sonItem = QtCGMaya.QTreeWidgetItem(item, ['', returnFile['name'], '', ''])
                self.treeWidget.resizeColumnToContents(1)

    def onSetClose(self):
        self.verRadiobutton.setChecked(False)
        self.radiobutton5.setChecked(False)
        self.treeWidget.hide()
        self.radioStatus = ''

    def onSetRefOpen(self):
        pass

    def onSetNorOpen(self):
        pass

    def onClickItemTask(self, item, cloumn):
        #cmds.waitCursor(state = True)
        row = self.taskTreeWidget.indexOfTopLevelItem(item)
        self.fileListIndex = row
        self.taskIndex = row
        self.currentTask = CGMaya_config.tasks[row]
        result = self.service.myWFGetProjectInfo(CGMaya_config.tasks[row]['projectName'])
        project = json.loads(result)
        CGMaya_config.taskFileID = CGMaya_config.tasks[row]['fileID']
        try:
            timeUnit = project['timeUnit']
        except KeyError or ValueError:
            timeUnit = 'pal:25fps'
        if not timeUnit:
            time = timeUnit.split(':')[0]
            cmds.currentUnit(time=time)

        #if CGMaya_config.frameList and (CGMaya_config.tasks[row]['stage'] == u'布局' or \
        #                CGMaya_config.tasks[row]['stage'] == u'动画' or CGMaya_config.tasks[row]['stage'] == u'灯光'):
        #    self.stageText.setText(CGMaya_config.tasks[row]['stage'] + '(' + CGMaya_config.frameList + ')')
        self.treeWidget.clear()
        self.bTaskSelected = True
        if CGMaya_config.tasks[row]['stage'] == u'灯光':
            CGMaya_config.lightFileFlag = False
            self.row_openHbox.setEnabled(True)
            self.openRefRadiobutton.setEnabled(True)
            self.openNorRadiobutton.setEnabled(True)
            self.row_watchHbox.setChecked(True)
            self.lightRadiobutton.setChecked(True)
            self.refRadiobutton.setChecked(False)
            self.verRadiobutton.setChecked(False)
            self.onSetLight()
        else:
            self.row_openHbox.setEnabled(False)
            self.openRefRadiobutton.setEnabled(False)
            self.openNorRadiobutton.setEnabled(False)
            self.lightRadiobutton.setChecked(False)
            if self.verRadiobutton.isChecked():
                self.onSetVersion()
            elif self.refRadiobutton.isChecked():
                self.onSetReference()
        try:
            attachFileIDList = CGMaya_config.tasks[row]['attachFileIDList']
            if attachFileIDList:
                self.attachButton.setEnabled(True)
                if self.returnRadiobutton.isChecked():
                    self.onSetAttach()
            else:
                self.attachButton.setEnabled(False)
                self.attachButton.setChecked(False)
        except KeyError:
            self.attachButton.setEnabled(False)
            self.attachButton.setChecked(False)
        #cmds.waitCursor(state=False)
        task = CGMaya_config.tasks[row]
        fileInfo = self.service.getFileInfo(task['fileID'])
        print(fileInfo)
        total = fileInfo.length
        if task['textureFileID']:
            fileInfo = self.service.getFileInfo(task['textureFileID'])
            total = total + fileInfo.length

        assetProjectDir = CGMaya_config.assetStorageDir + '/' + project['refProject']
        print('assetProjectDir =', assetProjectDir)
        logPath = assetProjectDir + '/' + CGMaya_config.CGMaya_Log_Dir
        total = 0
        if task['stage'] == '灯光':
            refTaskList = json.loads(self.service.getLightTaskInfoFromRefAssetIDList(task['refAssetIDList']))
        else:
            refTaskList = json.loads(self.service.getAniTaskInfoFromRefAssetIDList(task['refAssetIDList']))
        for refAssetTask in refTaskList:
            taskDir = assetProjectDir + '/' + refAssetTask['name']
            logFilePath = logPath + '/' + refAssetTask['name'] + CGMaya_config.logFileExt
            if os.path.exists(logFilePath):
                with open(logFilePath, "r") as json_file:
                    logJsonData = json.load(json_file)
                fn = self.service.getFileName(refAssetTask, refAssetTask['fileID'])
                taskFileName = taskDir + '/' + fn
                bExist = CGMaya_function.judgelogData(logJsonData, fn, refAssetTask['fileID'])
                if not os.path.exists(taskFileName) or bExist != 2:
                    total = total + int(refAssetTask['dataSize'])
            else:
                total = total + int(refAssetTask['dataSize'])
        str = '{0:.2f}'.format(total / (float)(1024 * 1024)) + 'MB'
        sizeStr = '{:>10}'.format(str)
        item.setText(5, sizeStr)

    def onDoubleClickItemTask(self, item, column):
        row = self.taskTreeWidget.indexOfTopLevelItem(item)
        self.fileListIndex = row
        self.taskIndex = row
        if not CGMaya_config.tasks[row]['stage'] == u'灯光':
            try:
                CGMaya_config.assetID = CGMaya_config.tasks[row]['fileID']
            except KeyError:
                CGMaya_config.assetID = ''
        else:
            CGMaya_config.lightFileFlag = False
        CGMaya_config.taskFileID = CGMaya_config.tasks[row]['fileID']
        self.onOpen()

    def onClickItem1(self, item, column):
        row = self.treeWidget.indexOfTopLevelItem(item)
        if self.verRadiobutton.isChecked():
            #CGMaya_config.taskFileID = self.assetData[row]['id']
            CGMaya_config.taskFileID = CGMaya_service.objectIDToUnicode(self.assetData[row]['id'])
        elif self.lightRadiobutton.isChecked():
            """
            if column == 1:
                response = cmds.confirmDialog(title=u'警告', message=u'是否删除？', button=[u'是', u'否'],
                                              defaultButton=u'是', cancelButton=u'否', dismissString=u'是')
                res = u'是'
                if not response == res:
                    return
                del self.lightFileIDList[row]
                textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
                for lightFile in self.lightFileIDList:
                    fileInfo = self.service.getFileInfo(lightFile['id'])
                    date = fileInfo.uploadDate + timedelta(hours=8)
                    dd = date.strftime('%b-%d-%Y %H:%M:%S')
                    # item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [lightFile['name'], lightFile['id'], dd])
                    item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [lightFile['name'], '-', dd])
                    item.setFont(0, textFont)
                    item.setFont(1, textFont)
                    item.setFont(2, textFont)
                    self.treeWidget.resizeColumnToContents(0)
                    self.treeWidget.resizeColumnToContents(1)
                self.service.myWFSetTaskLightFileIDList1(taskID, lightFileIDList, textureFileID)
            """
            CGMaya_config.lightFileFlag = True
            CGMaya_config.lightFile = self.lightFileIDList[row]
            CGMaya_config.taskFileID = CGMaya_config.lightFile['id']

    def onDoubleClickItem1(self, item, column):
        row = self.treeWidget.indexOfTopLevelItem(item)
        if self.verRadiobutton.isChecked():
            if CGMaya_config.lang == 'zh':
                msg = u'是否删除这个版本?'
                response = cmds.confirmDialog(title=u'警告', message=msg, button=[u'是', u'否'],
                                              defaultButton=u'是', cancelButton=u'否', dismissString=u'是')
                res = u'是'
            else:
                msg = 'Is Delete File?'
                response = cmds.confirmDialog(title=u'', message=msg, button=[u'Yes', u'No'],
                                              defaultButton=u'Yes', cancelButton=u'No', dismissString=u'Yes')
                res = u'Yes'
            if not response == res:
                return
            self.service.deleteMayaFile(self.assetData[row]['id'])
            self.onSetVersion()
            return
        elif self.lightRadiobutton.isChecked():
            CGMaya_config.lightFileFlag = True
            CGMaya_config.lightFile = self.lightFileIDList[row]
            CGMaya_config.fileID = CGMaya_config.lightFile['id']
            CGMaya_config.taskFileID = CGMaya_config.lightFile['id']
            self.onOpen()
            return
        elif self.returnRadiobutton.isChecked():
            print('row =', row)
            if row > 0:
                return
            parentItem = item.parent()
            submitIndex = self.treeWidget.indexOfTopLevelItem(parentItem)
            submit = self.submitList[submitIndex]
            #returnIndex= self.treeWidget.indexFromItem(item)
            returnIndex = self.treeWidget.indexFromItem(parentItem).row()
            returnFile = submit['returnFileIDList'][returnIndex]
            print('returnFile =', returnFile)
            #dlg = pngDialog(self.service, self.currentTask, returnFile)
            dlg = pngDialog(self.service, self.currentTask, submit['submitFileIDList'][0])


    def closeEvent(self, event):
        self.app.menu.setEnable(True)
        event.accept() # let the window close
        
    def onCancel(self):
        self.app.menu.setEnable(True)
        self.close()

    def onRefresh(self):
        self.getProjects()
        self.treeWidget.hide()

    def onOpen(self):
        item = self.taskTreeWidget.currentItem()
        currentRow = self.taskTreeWidget.indexOfTopLevelItem(item)
        self.currentTask = copy.deepcopy(CGMaya_config.tasks[currentRow])
        CGMaya_config.currentTask = CGMaya_config.tasks[currentRow]
        CGMaya_config.frameList = ''
        taskName = self.currentTask['name']
        CGMaya_config.sceneName = taskName
        projectName = self.currentTask['projectName']
        CGMaya_config.projectName = projectName
        CGMaya_config.taskIndex = self.fileListIndex

        result = self.service.myWFGetProjectInfo(projectName)
        CGMaya_config.project = json.loads(result)

        if self.currentTask['stage'] == u'绑定' or self.currentTask['stage'] == u'标准光':
            self.app.menuOpen(True)
        elif CGMaya_config.project['templateName'] == '3DShot':
            self.app.menuOpen(False)
        else:
            self.app.menuOpen(True)

        cmds.file(new = True, force = True)
        CGMaya_config.currentTask = copy.deepcopy(self.currentTask)

        projectList = json.loads(self.service.myWFGetProjectInfo(CGMaya_config.currentTask['projectName']))
        CGMaya_config.currentProject = projectList
        self.loadFlag = self.loadCheckBox.isChecked()
        CGMaya_config.textureReadFlag = self.textureCheckBox.isChecked()
        CGMaya_config.refAssetIDList = []

        projectStorage = 'GridFS'
        try:
            if CGMaya_config.currentProject['storage'] == 'ipfs':
                projectStorage = 'ipfs'
        except KeyError:
            pass
        if projectStorage == 'ipfs':
            if self.service.IPFSConnect() == None:
                CGMaya_config.logger.error('IPFS Error: : %s\r' % CGMaya_config.IPFSUrl)
                QtCGMaya.QMessageBox.information(self.parent, u"错误", CGMaya_config.IPFSUrl,
                                                 QtCGMaya.QMessageBox.Yes)
                #cmds.confirmDialog(title=u'错误信息', message=CGMaya_config.IPFSUrl, defaultButton=u'确认')
                self.close()
                return
            else:
                CGMaya_config.logger.info('IPFS Connect: : %s\r' % CGMaya_config.IPFSUrl)

        if not self.loadFlag:
            CGMaya_config.logger.info('Create newFile-------\r')
            CGMaya_config.logger.server(projectName, taskName, self.currentTask['_id'], CGMaya_config.CGMaya_Action_Open)
            CGMaya_config.textureReadFlag = True
            self.close()
            return

        CGMaya_config.currentDlg = self
        CGMaya_config.currentTask = self.currentTask
        if self.currentTask['stage'] == u'灯光':
            CGMaya_config.lightRefFlag = self.openRefRadiobutton.isChecked()
            CGMaya_function.openLightTask(self.service, self.currentTask)
        else:
            CGMaya_function.openTask(self.service, self.currentTask)

        if not CGMaya_config.successfulReadMayaFile:
            return

        CGMaya_config.logger.server(projectName, taskName, self.currentTask['_id'], CGMaya_config.CGMaya_Action_Open)
        if self.currentTask['stage'] == u'动画' or self.currentTask['stage'] == u'布局' or self.currentTask['stage'] == u'灯光':
            if CGMaya_config.frameList:
                cmds.playbackOptions(min=int(CGMaya_config.frameList.split('-')[0]), max=int(CGMaya_config.frameList.split('-')[1]))
            mel.eval("setCurrentFrameVisibility(1)")
            mel.eval("setCameraNamesVisibility(1)")
            mel.eval("setFocalLengthVisibility(1)")
            #mel.eval("setCurrentFrameVisibility(!`optionVar -q currentFrameVisibility`)")
            #mel.eval("setCameraNamesVisibility(!`optionVar -q cameraNamesVisibility`)")
            #mel.eval("setFocalLengthVisibility(!`optionVar -q focalLengthVisibility`)")
        self.app.menu.setEnable(True)
        CGMaya_config.logger.info('Finish-----------------\r')
        self.hide()
        self.mousePoint = CGMaya_mouse.mousePoint()

class affectDialog(QtCGMaya.QDialog):
    def __init__(self, refProjectName, refTaskName, service, parent):
        super(affectDialog, self).__init__(parent)
        self.refProjectName = refProjectName
        self.refTaskName = refTaskName
        self.service = service
        self.parent = parent

        self.main_layout = QtCGMaya.QVBoxLayout()
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.projectListWidget = QtCGMaya.QListWidget(self)
        self.affectTaskListWidget = QtCGMaya.QListWidget(self)
        self.layout.addWidget(self.projectListWidget, 0, 0)
        self.layout.addWidget(self.affectTaskListWidget, 1, 0)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 0, 0)
        #self.projectListWidget.hide()
        self.projectListWidget.connect(self.projectListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                       self.onClickProjectItem)

        self.GetProjects()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.countLabel = QtCGMaya.QLabel(u'任务数', self)
            self.button1 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.countLabel = QtCGMaya.QLabel(u'TaskCounts', self)
            self.button1 = QtCGMaya.QPushButton(u'Close', self)
        self.countText = QtCGMaya.QLineEdit('', self)
        self.layout.addWidget(self.countLabel, 0, 0)
        self.layout.addWidget(self.countText, 0, 1)
        self.layout.addWidget(self.button1, 0, 2)
        self.button1.clicked.connect(self.onClose)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 8, 0)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'引用资产的镜头任务列表')
        else:
            self.setWindowTitle(u'Affect')
        self.setGeometry(900, 300, 400, 400)
        #self.parent.setEnabled(False)
        #self.show()

    def GetProjects(self):
        result = self.service.myWFGetAllProjects()
        self.projectList = json.loads(result)
        #textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        for project in self.projectList:
            item = QtCGMaya.QListWidgetItem(project['name'])
            #item.setFont(textFont)
            self.projectListWidget.addItem(item)
        if len(self.projectList) == 0:
            return
        row = 0

    def onClickProjectItem(self, item):
        cmds.waitCursor(state=True)
        row = self.projectListWidget.currentRow()
        projectName = self.projectList[row]['name']
        result = self.service.myWFGetProjectTask(projectName)
        taskList = json.loads(result)
        #textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        count = 0
        for task in taskList:
            try:
                refAssetIDList = task['refAssetIDList']
            except KeyError:
                continue
            if not refAssetIDList:
                continue
            for ref in refAssetIDList:
                if self.refProjectName == ref['projectName'] and self.refTaskName == ref['name']:
                    msg = task['name'] + '   ' + task['stage'] + '   ' + task['executor']
                    item = QtCGMaya.QListWidgetItem(msg)
                    #item.setFont(textFont)
                    self.affectTaskListWidget.addItem(item)
                    count = count + 1
                    break
        cmds.waitCursor(state=False)
        self.countText.setText(str(count))

    def onClose(self):
        self.close()
        self.parent.setEnabled(True)

class referenceDialog(QtCGMaya.QDialog):
    def __init__(self, service, parent):
        super(referenceDialog, self).__init__(parent)
        self.service = service
        self.parent = parent
        #self.parent.setEnabled(False)

        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.fileLabel = QtCGMaya.QLabel(u'文件', self)
        else:
            self.fileLabel = QtCGMaya.QLabel(u'File', self)
        self.fileText = QtCGMaya.QLineEdit('', self)
        self.fileText.setEnabled(False)
        self.layout.addWidget(self.fileLabel, 0, 0)
        self.layout.addWidget(self.fileText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.referenceListWidget = QtCGMaya.QListWidget(self)
        self.layout.addWidget(self.referenceListWidget)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        #self.projectListWidget.hide()
        self.referenceListWidget.connect(self.referenceListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                       self.onClickReferenceItem)
        self.referenceListWidget.connect(self.referenceListWidget, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem*)"),
                                         self.onDoubleClickReferenceItem)

        self.GetReferences()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'确认', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Ok', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 0)
        self.button1.clicked.connect(self.onOk)
        self.button2.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'替换引用')
        else:
            self.setWindowTitle(u'Replace reference')
        self.setGeometry(900, 300, 500, 400)
        #self.parent.setEnabled(False)
        #self.show()

    def GetReferences(self):
        refs = pymel.core.listReferences()
        # print 'refs =', refs
        textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        refFileList = []
        for ref in refs:
            refn = ref.path
            refName = os.path.basename(refn)
            if refName in refFileList:
                continue
            item = QtCGMaya.QListWidgetItem(refName)
            item.setFont(textFont)
            self.referenceListWidget.addItem(item)
            self.fileText.setText(refn)
            refFileList.append(refName)

    def onClickReferenceItem(self, item):
        pass

    def onDoubleClickReferenceItem(self, item):
        #self.setEnable(False)
        #win = referenceModelWindow(self.service, None, True, True, item, self)
        #win.show()
        pass

    def onOk(self):
        CGMaya_config.changeReferenceModelList = []
        for index in xrange(self.referenceListWidget.count()):
            item = self.referenceListWidget.item(index)
            string = item.text()
            refName = string.split('->')[0]
            refName = refName.split('.')[0]
            try:
                refString = string.split('->')[1]
            except IndexError:
                continue
            projectName = refString.split(':')[0]
            refModelName = refString.split(':')[1]
            if not projectName:
                continue
            if not refModelName:
                continue
            taskList = self.service.myWFsearchTask(refModelName, projectName)
            if len(taskList) == 0:
                continue
            task = taskList[0]
            asset = self.service.getasset(task['assetID'], 'doc')
            CGMaya_config.changeReferenceModelList.append({'refName': refName, 'projectName': projectName, 'taskID': task['_id'],
                                                           'refModelName': refModelName, 'refFileName': asset['name']})
        #print 'changeReferenceModelList =', CGMaya_config.changeReferenceModelList
        self.close()
        self.parent.setEnabled(True)
        self.parent.onSave()

    def onCancel(self):
        self.close()
        self.parent.setEnabled(True)

    def closeEvent(self, event):
        self.close()
        self.parent.setEnabled(True)
        event.accept() # let the window close

class saveTaskWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(saveTaskWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.menu.setEnable(False)
        self.fileNums = 0
        self.fileList = []
        #CGMaya_config.clipboard.dataChanged.connect(self.on_clipboard_change)
        #self.setAcceptDrops(True)
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()
        self.root_layout = QtCGMaya.QVBoxLayout()
        #stage = convertHANZI(CGMaya_config.currentTask['stage'])
        stage = CGMaya_config.currentTask['stage']

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.projectLabel = QtCGMaya.QLabel(u'项目', self)
            self.sceneLabel = QtCGMaya.QLabel(u'任务', self)
            self.descriptionLabel = QtCGMaya.QLabel(u'描述', self)
        else:
            self.projectLabel = QtCGMaya.QLabel(u'Project', self)
            self.sceneLabel = QtCGMaya.QLabel(u'Scene', self)
            self.descriptionLabel = QtCGMaya.QLabel(u'Description', self)

        self.projectText = QtCGMaya.QLineEdit(CGMaya_config.projectName, self)
        self.projectText.setEnabled(False)
        self.sceneText = QtCGMaya.QLineEdit(CGMaya_config.sceneName, self)
        self.sceneText.setEnabled(False)
        self.noteText = QtCGMaya.QLineEdit('', self)
        self.affectButton = QtCGMaya.QPushButton(u'影响', self)
        self.affectButton.clicked.connect(self.onAffect)
        if CGMaya_config.currentProject['templateName'] == '3DAsset':
            self.affectButton.setEnabled(True)
        else:
            self.affectButton.setEnabled(False)

        self.layout.addWidget(self.projectLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.projectText, 0, 1, 1, 6)
        self.layout.addWidget(self.sceneLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.sceneText, 1, 1, 1, 6)
        self.layout.addWidget(self.descriptionLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.noteText, 2, 1, 1, 5)
        self.layout.addWidget(self.affectButton, 2, 6, 1, 1)

        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 0, 0)
        boxRow = 3
        if stage == u'灯光':
            self.sceneText.setEnabled(False)
            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()

            if CGMaya_config.lang == 'zh':
                self.lightLabel = QtCGMaya.QLabel(u'灯光文件', self)
                self.renderSingleFrameLabel = QtCGMaya.QLabel(u'渲染单帧选择', self)
            else:
                self.lightLabel = QtCGMaya.QLabel(u'Light File', self)
                self.renderSingleFrameLabel = QtCGMaya.QLabel('RenderFrame Select ', self)
            if CGMaya_config.lightFileFlag:
                fn = self.service.getFileNameGridFS(CGMaya_config.taskFileID)
                self.lightText = QtCGMaya.QLineEdit(fn.split('.')[0], self)
            else:
                self.lightText = QtCGMaya.QLineEdit(CGMaya_config.sceneName, self)
            """
            if CGMaya_config.lightFileIDList:
                lightName = CGMaya_config.lightFileIDList['name'].split('.')[0]
                self.lightText = QtCGMaya.QLineEdit(lightName, self)
            else:
                self.lightText = QtCGMaya.QLineEdit(CGMaya_config.sceneName, self)
            """
            self.layout.addWidget(self.lightLabel, 0, 0)
            self.layout.addWidget(self.lightText, 0, 1)

            try:
                singleFrameText = CGMaya_config.currentTask['singleFrame']
                if not singleFrameText:
                    singleFrameText = '101'
            except KeyError:
                singleFrameText = '101'
            self.renderSingleFrameText = QtCGMaya.QLineEdit(singleFrameText, self)
            self.layout.addWidget(self.renderSingleFrameLabel, 1, 0)
            self.layout.addWidget(self.renderSingleFrameText, 1, 1)
            self.row_Hbox.setLayout(self.layout)
            self.main_layout.addWidget(self.row_Hbox, boxRow, 0)
            boxRow = boxRow + 2

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.radiobutton1 = QtCGMaya.QRadioButton(u'ma', self)
        self.radiobutton2 = QtCGMaya.QRadioButton(u'mb', self)
        if CGMaya_config.lang == 'zh':
            #self.textureCheckBox = QtCGMaya.QCheckBox(u'材质', self)
            self.audioCheckBox = QtCGMaya.QCheckBox(u'音频', self)
            self.pluginLabel = QtCGMaya.QLabel(u'渲染器插件', self)
            self.frameLabel = QtCGMaya.QLabel(u'帧序列', self)
            self.qualityLabel = QtCGMaya.QLabel(u'质量', self)
            self.scaleLabel = QtCGMaya.QLabel(u'放缩', self)
            #self.nextShotText = QtCGMaya.QLineEdit('', self)
        else:
            #self.textureCheckBox = QtCGMaya.QCheckBox(u'texture', self)
            self.audioCheckBox = QtCGMaya.QCheckBox(u'audio', self)
            self.pluginLabel = QtCGMaya.QLabel(u'Render Plugin', self)
            self.frameLabel = QtCGMaya.QLabel(u'FrameList', self)
            self.qualityLabel = QtCGMaya.QLabel(u'Quality', self)
            self.scaleLabel = QtCGMaya.QLabel(u'Scale', self)

            #self.nextShotText = QtCGMaya.QLineEdit('', self)
        self.qualityText = QtCGMaya.QLineEdit(CGMaya_config.layoutQuality, self)
        self.scaleText = QtCGMaya.QLineEdit(CGMaya_config.layoutScale, self)
        Renderer = cmds.getAttr('defaultRenderGlobals.currentRenderer')
        self.pluginText = QtCGMaya.QLineEdit(Renderer, self)
        self.pluginText.setEnabled(False)
        startFrame = str(cmds.playbackOptions(query=1, min=1))
        endFrame = str(cmds.playbackOptions(query=1, max=1))
        frame = startFrame.split('.')[0] + '-' + endFrame.split('.')[0]
        self.frameText = QtCGMaya.QLineEdit(frame, self)
        self.frameText.setEnabled(False)
        self.audioCheckBox.setChecked(True)

        scene_FN = cmds.file(sn=True, q=True)
        fn = os.path.basename(scene_FN)
        if fn and fn.split('.')[1] == 'mb':
        #if CGMaya_config.assetExtFileName  == 'mb':
            self.radiobutton2.setChecked(True)
        else:
            self.radiobutton1.setChecked(True)
        if stage == u'布局' or stage == u'动画':
            if CGMaya_config.lang == 'zh':
                #self.captureCheckBox = QtCGMaya.QCheckBox(u'捕屏', self)
                self.stereoCheckBox = QtCGMaya.QCheckBox(u'立体', self)
            else:
                #self.captureCheckBox = QtCGMaya.QCheckBox(u'capture', self)
                self.stereoCheckBox = QtCGMaya.QCheckBox(u'Stereo', self)
            self.layout.addWidget(self.radiobutton1, 0, 0, 1, 1)
            self.layout.addWidget(self.radiobutton2, 0, 1, 1, 1)
            self.layout.addWidget(self.audioCheckBox, 0, 2, 1, 1)
            #self.layout.addWidget(self.captureCheckBox, 0, 3, 1, 1)
            self.layout.addWidget(self.stereoCheckBox, 0, 3, 1, 1)
            #self.captureCheckBox.setChecked(False)
            self.bMovFlag = True
        elif stage == u'特效':
            self.layout.addWidget(self.radiobutton1, 0, 0, 1, 1)
            self.layout.addWidget(self.radiobutton2, 0, 1, 1, 1)
            self.layout.addWidget(self.audioCheckBox, 0, 2, 1, 1)
        else:
            self.layout.addWidget(self.radiobutton1, 0, 0, 1, 1)
            self.layout.addWidget(self.radiobutton2, 0, 1, 1, 1)
            self.layout.addWidget(self.audioCheckBox, 0, 2, 1, 1)
            self.bMovFlag = False
        #self.nextShotCheckBox.setChecked(False)
        #self.nextShotText.setEnabled(False)
        #self.nextShotCheckBox.clicked.connect(self.onSetNextShot)

        self.layout.addWidget(self.pluginLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.pluginText, 1, 1, 1, 2)
        self.layout.addWidget(self.frameLabel, 1, 4, 1, 1)
        self.layout.addWidget(self.frameText, 1, 5, 1, 2)
        self.layout.addWidget(self.qualityLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.qualityText, 2, 1, 1, 2)
        self.layout.addWidget(self.scaleLabel, 2, 4, 1, 1)
        self.layout.addWidget(self.scaleText, 2, 5, 1, 2)
        #self.layout.addWidget(self.nextShotCheckBox, 3, 0, 1, 1)
        #self.layout.addWidget(self.nextShotText, 3, 2, 1, 2)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, boxRow, 0)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout4 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.submitLabel = QtCGMaya.QLabel(u'提交说明', self)
        else:
            self.submitLabel = QtCGMaya.QLabel(u'Submit Notes', self)
        self.submitText = QtCGMaya.QLineEdit('', self)
        self.taskListWidget = QtCGMaya.QListWidget(self)

        if CGMaya_config.lang == 'zh':
            self.selectButton = QtCGMaya.QPushButton(u'选择', self)
        else:
            self.selectButton = QtGui.QPushButton(u'Select', self)
        self.layout4.addWidget(self.submitLabel, 0, 0, 1, 1)
        self.layout4.addWidget(self.submitText, 0, 1, 1, 6)
        self.layout4.addWidget(self.taskListWidget, 1, 0, 1, 5)
        self.layout4.addWidget(self.selectButton, 1, 6, 1, 1)
        self.row_Hbox.setLayout(self.layout4)
        self.main_layout.addWidget(self.row_Hbox, boxRow + 3, 0)
        self.selectButton.clicked.connect(self.onSelectFiles)
        self.taskListWidget.connect(self.taskListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                    self.onClickItem)
        self.taskListWidget.connect(self.taskListWidget,
                                    QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem*)"),
                                    self.onDoubleClickItem)
        boxRow = boxRow + 3

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout5 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            #self.button3 = QtGui.QPushButton(u'截屏', self)
            #self.button5 = QtCGMaya.QPushButton(u'选择', self)
            self.button1 = QtCGMaya.QPushButton(u'保存', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
            self.button4 = QtCGMaya.QPushButton(u'保存提交', self)
            #self.button6 = QtCGMaya.QPushButton(u'替换引用', self)
        else:
            #self.button3 = QtGui.QPushButton(u'Capture', self)
            #self.button5 = QtCGMaya.QPushButton(u'Select', self)
            self.button1 = QtCGMaya.QPushButton(u'Save', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button4 = QtCGMaya.QPushButton(u'Save&Submit', self)
            #self.button6 = QtCGMaya.QPushButton(u'RepalceReference', self)
        #self.layout5.addWidget(self.button6, 2, 0)
        self.layout5.addWidget(self.button1, 2, 2)
        self.layout5.addWidget(self.button2, 2, 1)
        #self.layout5.addWidget(self.button3, 2, 0)
        self.layout5.addWidget(self.button4, 2, 3)
        #self.layout5.addWidget(self.button5, 2, 1)

        if stage == u'布局' or stage == u'动画' or stage == u'灯光':
            self.button4.setEnabled(True)
            #self.button6.setEnabled(True)
        else:
            self.button4.setEnabled(False)
            #self.button6.setEnabled(False)

        self.button1.clicked.connect(self.onSave)
        self.button2.clicked.connect(self.onCancel)
        #self.button3.clicked.connect(self.onCapture)
        self.button4.clicked.connect(self.onSaveSubmit)
        #self.button5.clicked.connect(self.onSelect)
        #self.button6.clicked.connect(self.onReplaceRef)
        self.row_Hbox.setLayout(self.layout5)
        self.main_layout.addWidget(self.row_Hbox, boxRow + 4, 0)
        self.setLayout(self.main_layout)

        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'保存任务')
        else:
            self.setWindowTitle(u'Save Task')
        self.setGeometry(300, 300, 600, 400)
        #self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.image = None
        if stage == u'动画' or stage == u'布局':
            CGMaya_config.layoutScale = self.scaleText.text()
            CGMaya_config.layoutQuality = self.qualityText.text()
            self.button4.setEnabled(True)
        self.center()
        self.getSubmitsOfTask()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_clipboard_change(self):
        projectDir = CGMaya_config.storageDir + CGMaya_config.projectName
        data = CGMaya_config.clipboard.mimeData()
        if data.hasImage():
            image = data.imageData()
            pix = QtGui.QPixmap.fromImage(image)
            pixmap = pix.scaled(CGMaya_config.IconWidth, CGMaya_config.IconHeight)
            self.imageLabel.setPixmap(QtGui.QPixmap(pixmap))

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(CGMaya_config.specialMimeType):
            event.acceptProposedAction()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat(CGMaya_config.specialMimeType):
            return
        filenameBytes = event.mimeData().data(CGMaya_config.specialMimeType)
        filename = QtCore.QTextCodec.codecForName("utf-16").toUnicode(filenameBytes)
        fn = filename.replace('\\', '/')
        self.taskListWidget.show()
        if fn in self.fileList:
            return
        else:
            newItem = QtCGMaya.QListWidgetItem()
            newItem.setText(fn)
            self.fileList.append(fn)
            self.taskListWidget.addItem(newItem)
            self.button4.setEnabled(True)
            #self.getSubmitsOfTask()

    def onPress(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query = True, anchorPoint = True)
        #CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        #print 'anchorPoint =', self.anchorPoint 
            
    def onDrag(self, *args):
        self.dragPoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        #print 'anchorPoint =', self.dragPoint
            
    def onRelease(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        #print ' releasePoint =', self.releasePoint

    def onAffect(self):
        win = affectDialog(self.projectText.text(), self.sceneText.text(), self.service, self)
        win.show()

    def onSelectFiles(self):
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, "选择上传文件", ".", "*")
        else:
            dialog = QtCGMaya.QFileDialog(self, "Select Upload Files", ".", "*")
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFiles)
        if dialog.exec_():
            #self.getSubmitsOfTask()
            #textFont = QtCGMaya.QFont("song", 18, QtCGMaya.QFont.Normal)
            self.fileList = dialog.selectedFiles()
            for submitFile in self.fileList:
                item = QtGui.QListWidgetItem(submitFile)
                #item.setFont(textFont)
                self.taskListWidget.addItem(item)
            self.button4.setEnabled(True)

    def getSubmitsOfTask(self):
        submits = json.loads(self.service.getSubmitsOfTask(CGMaya_config.currentTask['_id']))
        self.submitID = ''
        if len(submits) > 0:
            for index, sub in enumerate(submits):
                if sub['status'] == '0':
                    self.submitText.setText(str(index + 1) + ':')
                    self.submitID = sub['_id']
                    for submitFile in sub['submitFileIDList']:
                        item = QtGui.QListWidgetItem(submitFile['name'])
                        self.taskListWidget.addItem(item)
                    break
        else:
            self.submitText.setText('1:')

    def onSetNextShot(self):
        shotName = CGMaya_config.currentTask['name']
        num = int(shotName.split('_SC').pop()) + 1
        numStr = ''
        if num <= 9:
            numStr = '000' + str(num)
        elif num <= 99:
            numStr = '00' + str(num)
        elif num <= 999:
            numStr = '0' + str(num)
        else:
            numStr = str(num)
        self.nextShotText.setText(numStr)

    def onSetRenderWing(self):
        #self.renderWingCheckBox.isChecked(
        pass
        """
        if not self.renderWingCheckBox.isChecked() and cmds.window("unifiedRenderGlobalsWindow", exists=True):
            cmds.deleteUI("unifiedRenderGlobalsWindow")
            return
        Dir = cmds.internalVar(userScriptDir=True)
        pluginFn = Dir + '/RCMaya/RWingForMaya.py'
        print 'pluginFn =', pluginFn
        #pluginFn = 'E:\downloads/RWingForMaya/plug-ins/RWingForMaya.py'
        pluginFn = 'E:\downloads\RWingForMaya\plug-ins/RWingForMaya.py'
        ret = cmds.loadPlugin(pluginFn)
        #print 'ret =', ret

        #if not cmds.pluginInfo(pluginFn, query=True, autoload=True):
        #    cmds.pluginInfo(pluginFn, edit=True, autoload=True)

        #if not cmds.pluginInfo(pluginFn, query=True, loaded=True):
        #    cmds.loadPlugin(pluginFn)

        cmds.setAttr("defaultRenderGlobals.currentRenderer", l=False)

        cmds.setAttr("defaultRenderGlobals.currentRenderer", 'RWing', type="string")
        mel.eval('unifiedRenderGlobalsWindow;')
        """

    def onSetABC(self):
        pass

    def onClickItem(self, item):
        pass

    def onDoubleClickItem(self, item):
        row = self.taskListWidget.currentRow()
        fn = self.fileList[row]
        self.fileList.remove(fn)
        self.taskListWidget.clear()
        for submitFile in self.fileList:
            item = QtGui.QListWidgetItem(submitFile)
            self.taskListWidget.addItem(item)

    def onSave(self, flag = False):
        newSceneName = self.sceneText.text()
        stage = CGMaya_config.currentTask['stage']

        if not CGMaya_function.checkSoftwareVersion(self.service):
            if CGMaya_config.lang == 'zh':
                response = QtCGMaya.QMessageBox.question(self, u"选择", u"项目要求的软件版本与本软件不一致，是否继续?",
                                                         QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
            else:
                response = QtCGMaya.QMessageBox.question(self, u"Select", u"Software Version is software version of project , is not??",
                                                         QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
            if response == QtCGMaya.QMessageBox.No:
                self.close()
                return False

        audioLoadFlag = self.audioCheckBox.isChecked()
        #CGMaya_config.renderWingFlag = self.renderWingCheckBox.isChecked()
        if stage == u'布局' or stage == u'动画':
            #self.bMovFlag = self.captureCheckBox.isChecked()
            self.bMovFlag = False
            CGMaya_config.stereoFlag = self.stereoCheckBox.isChecked()
        if newSceneName != CGMaya_config.sceneName:
            newTaskList = self.service.myWFsearchTask(newSceneName, CGMaya_config.projectName)
            if len(newTaskList) == 0:
                if CGMaya_config.lang == 'zh':
                    response = QtCGMaya.QMessageBox.question(self, u"选择", u"是否创建新任务?",
                                 QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
                else:
                    response = QtCGMaya.QMessageBox.question(self, u"Select", u"Is New task Creating??",
                                                          QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
                if response == QtCGMaya.QMessageBox.Yes:
                    task1 = copy.deepcopy(CGMaya_config.currentTask)
                    task1['name'] = newSceneName
                    task1['referenceTaskID'] = CGMaya_config.currentTask['_id']
                    result = self.service.myWFCreateTaskByName(task1)
                    newTaskList = self.service.myWFsearchTask(newSceneName, CGMaya_config.projectName)
                    CGMaya_config.currentTask = newTaskList[0]
                elif QtCGMaya.QMessageBox.No:
                    pass
                else:
                    print('You choose wisely')
        projectDir = CGMaya_config.storageDir + '/' + CGMaya_config.projectName
        if not os.path.exists(projectDir):
            os.mkdir(projectDir)
        taskDir = projectDir + '/' + CGMaya_config.currentTask['name']
        if not os.path.exists(taskDir):
            os.mkdir(taskDir)

        if stage == u'灯光':
            if CGMaya_config.currentTask['name'] != self.lightText.text():
                CGMaya_config.sceneName = self.lightText.text()
            singleFrame = self.renderSingleFrameText.text()

        scene_fn = CGMaya_config.sceneName
        if self.radiobutton1.isChecked():
            scene_fn = scene_fn + '.ma'
            type = 'mayaAscii'
        else:
            scene_fn = scene_fn + '.mb'
            type = 'mayaBinary'

        pixmap = None
        """
        if stage != u'灯光' or CGMaya_config.currentTask['name'] == self.lightText.text():
            cmds.waitCursor(state=True)
            panelList = cmds.getPanel(all=True)
            #print 'panelList =', panelList
            cmds.modelEditor(panelList[3], edit=True, displayAppearance='smoothShaded', displayTextures=True)

            Dir = os.path.join(CGMaya_config.storageDir, 'tmp.png')
            ret = cmds.playblast(frame = cmds.currentTime(q=True),
                           f=Dir,
                           fo = True, fmt ='image', viewer=False,
                           c='PNG', quality=60)
            #print 'ret =', ret
            tmpFile = Dir + '.0000.png'
            #print tmpFile
            pix = QtGui.QPixmap(tmpFile)
            pixmap = pix.scaled(CGMaya_config.IconWidth, CGMaya_config.IconHeight)
            #self.imageLabel.setPixmap(QtGui.QPixmap(pixmap))
            cmds.modelEditor(panelList[3], edit=True, displayAppearance='boundingBox')
            cmds.waitCursor(state=False)
        """
        project = json.loads(self.service.myWFGetProjectInfo(CGMaya_config.projectName))
        if project['templateName'] == '3DShot' and (stage == u'布局' or stage == u'动画'):
            CGMaya_config.logger.info('Saveing Task...\r')
            scene_fn = taskDir + '/' + scene_fn
            ret = CGMaya_function.saveTask(self, self.service, scene_fn, pixmap, self.noteText.text(),
                                 self.pluginText.text(), self.frameText.text(), type,
                                audioLoadFlag, self.bMovFlag)
        elif project['templateName'] == '3DShot' and stage == u'灯光':
            CGMaya_config.logger.info('Saveing LightTask...\r')
            lightDir = taskDir + '/light'
            if not os.path.exists(lightDir):
                os.mkdir(lightDir)
            scene_fn = lightDir + '/' + scene_fn
            ret = CGMaya_function.saveLightTask(self, self.service, scene_fn, pixmap, self.noteText.text(),
                                           self.pluginText.text(), singleFrame, self.frameText.text(), type, False)
            if project['render'] == 'renderwing':
                ret = CGMaya_function.saveLightTaskRenderwing(self.service, scene_fn, self.frameText.text())
        else:
            CGMaya_config.logger.info('Saveing Task...\r')
            scene_fn = taskDir + '/' + scene_fn
            ret = CGMaya_function.saveTask(self, self.service, scene_fn, pixmap, self.noteText.text(),
                                     self.pluginText.text(), self.frameText.text(), type,
                                        audioLoadFlag, False)

        if not ret:
            #self.menu.setEnable(True)
            #self.close()
            return

        CGMaya_config.logger.server(CGMaya_config.projectName, CGMaya_config.sceneName,
                                    CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Save)
        if flag:
            cmds.file(new=True, force=True)

        if CGMaya_config.renderWingFlag:
            CGMaya_function.saveRenderWingFile(self.service, projectDir)

        if project['templateName'] == '3DShot' and stage == u'布局':
            shotName = CGMaya_config.currentTask['name']
            num = int(shotName.split('_SC').pop()) + 1
            numStr = ''
            if num <= 9:
                numStr = '000' + str(num)
            elif num <= 99:
                numStr = '00' + str(num)
            elif num <= 999:
                numStr = '0' + str(num)
            else:
                numStr = str(num)
            nextShotName = shotName.split('_SC')[0] + '_SC' + numStr
            ret = json.loads(self.service.myWFGetShotInfo(project['name'], nextShotName))
            if ret == None:
                executor = ''
            else:
                try:
                    executor = ret['executor']
                except KeyError:
                    executor = ''
            if ret == None or executor == CGMaya_config.currentTask['executor']:
                if CGMaya_config.lang == 'zh':
                    response = cmds.confirmDialog(title=u'警告', message=u'是否创建下一个镜头？', button=[u'是', u'否'],
                                                defaultButton=u'是', cancelButton=u'否', dismissString=u'是')
                    res = u'是'
                else:
                    response = cmds.confirmDialog(title=u'', message=u'Is Create Next Shot??', button=[u'Yes', u'No'],
                                                defaultButton=u'Yes', cancelButton=u'No', dismissString=u'Yes')
                    res = u'Yes'
                #print response
                if response == res:
                    self.service.myWFCreateNextShot(project['name'], shotName, nextShotName)

        QtGui.QMessageBox.information(self, u"提示", u"已保存完成.", QtGui.QMessageBox.Yes)
        self.menu.setEnable(True)
        self.close()
        return True

    def onSaveSubmit(self):
        if not self.fileList and CGMaya_config.currentTask['stage'] != u'布局' and \
                                    CGMaya_config.currentTask['stage'] != u'动画' and \
                                    CGMaya_config.currentTask['stage'] != u'灯光':
            if CGMaya_config.lang == 'zh':
                QtCGMaya.QMessageBox.information(self, u"提示信息", u"没有选择单帧效果图!!!")
            else:
                QtCGMaya.QMessageBox.information(self, u"Prompt", u"NO File Upload!!!")
        else:
            notes = self.submitText.text()
            if self.onSave(True):
                CGMaya_function.submitTask(self.service, CGMaya_config.currentTask, self.submitID, self.fileList, notes)
                self.service.userActionLog(CGMaya_config.userName, CGMaya_config.projectName, CGMaya_config.sceneName,
                                       CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Submit)
            self.menu.setEnable(True)

    def onReplaceRef(self):
        #self.onSave(True)
        #self.setEnable(False)
        win = referenceDialog(self.service, self)
        win.show()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

    def onSelect(self):
        self.taskListWidget.show()
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, u"选择文件", ".", "*.*")
        else:
            dialog = QtCGMaya.QFileDialog(self, "Select Scene File", ".", "*.*")
        dialog.setOption(QtCGMaya.QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFile)
        if dialog.exec_():
            self.submitFiles = dialog.selectedFiles()
            for file in self.submitFiles:
                newItem = QtCGMaya.QListWidgetItem()
                newItem.setText(file)
                self.fileList.append(file)
                self.taskListWidget.insertItem(self.fileNums, newItem)
                self.fileNums = self.fileNums + 1
            self.button4.setEnabled(True)

class saveAsTaskWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent=maya_main_window()):
        super(saveAsTaskWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.menu.setEnable(False)
        #self.setAcceptDrops(True)
        self.oldTask = copy.deepcopy(CGMaya_config.currentTask)
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
        self.projectText = QtCGMaya.QLineEdit(CGMaya_config.projectName, self)
        self.projectText.setEnabled(False)

        self.layout.addWidget(self.projectLabel, 0, 0)
        self.layout.addWidget(self.projectText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        if CGMaya_config.lang == 'zh':
            self.newTaskLabel = QtCGMaya.QLabel(u'新任务', self)
        else:
            self.newTaskLabel = QtCGMaya.QLabel(u'New Task', self)

        self.newTaskText = QtCGMaya.QLineEdit('', self)
        self.newTaskText.setEnabled(False)
        self.layout.addWidget(self.newTaskLabel, 0, 0)
        self.layout.addWidget(self.newTaskText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        self.taskListWidget = QtCGMaya.QListWidget(self)
        self.taskListWidget.setIconSize(QtCore.QSize(60, 60))

        self.GetTasks()
        self.main_layout.addWidget(self.taskListWidget)
        self.taskListWidget.connect(self.taskListWidget, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem*)"), self.onDoubleClickItem)
        self.taskListWidget.connect(self.taskListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"), self.onClickItem)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'另存', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Save', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 0)
        self.button1.clicked.connect(self.onSaveAs)
        self.button2.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        #self.setLayout(self.super_layout)
        self.setLayout(self.main_layout)

        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'另存任务')
        else:
            self.setWindowTitle(u'SaveAs')
        self.setGeometry(300, 300, 600, 500)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.image = None

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def GetTasks(self):
        self.taskListWidget.clear()
        result = self.service.myWFGetMyTask(CGMaya_config.userName)
        if not result:
            return None
        CGMaya_config.tasks = json.loads(result)
        CGMaya_config.tasks.sort(cmp = self.myCompare)
        textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        for task in CGMaya_config.tasks:
            if not task or not task['name']:
                continue
            str = task['name']
            # print str
            try:
                if task['isReturn']:
                    str = str.ljust(40, ' ') + 'X'
                else:
                    str = str.ljust(40, ' ')
            except KeyError:
                str = str.ljust(40, ' ')
            item = QtCGMaya.QListWidgetItem('  ' + str)
            item.setFont(textFont)
            self.taskListWidget.addItem(item)

    def onDoubleClickItem(self, item):
        self.fileListIndex = self.taskListWidget.currentRow()
        row = self.taskListWidget.currentRow()
        CGMaya_config.currentTask = CGMaya_config.tasks[row]
        if not CGMaya_config.tasks[row]['stage'] == u'灯光':
            try:
                CGMaya_config.fileID = CGMaya_config.currentTask['fileID']
            except KeyError:
                CGMaya_config.fileID = ''
        #self.onOpen()

    def onClickItem(self, item):
        row = self.taskListWidget.currentRow()
        CGMaya_config.currentTask = CGMaya_config.tasks[row]
        self.newTaskText.setText(CGMaya_config.currentTask['name'])

    def on_clipboard_change(self):
        projectDir = CGMaya_config.storageDir + CGMaya_config.projectName
        data = CGMaya_config.clipboard.mimeData()
        if data.hasImage():
            image = data.imageData()
            pix = QtGui.QPixmap.fromImage(image)
            pixmap = pix.scaled(CGMaya_config.IconWidth, CGMaya_config.IconHeight)
            self.imageLabel.setPixmap(QtGui.QPixmap(pixmap))

    def onPress(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query = True, anchorPoint = True)
        #CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        #print 'anchorPoint =', self.anchorPoint

    def onDrag(self, *args):
        self.dragPoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        #print 'anchorPoint =', self.dragPoint

    def onRelease(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        #print ' releasePoint =', self.releasePoint

    def onSaveAs(self):
        CGMaya_config.sceneName = self.newTaskText.text()
        projectDir = CGMaya_config.storageDir + '/' + CGMaya_config.projectName
        if not os.path.exists(projectDir):
            os.mkdir(projectDir)
        assetData = self.service.getasset(self.oldTask['assetID'], 'doc')
        url = assetData['URL']
        fn = url[url.rfind('/') + 1:]
        scene_fn = os.path.join(projectDir, CGMaya_config.sceneName)
        if fn.split('.').pop() == 'ma':
            scene_fn = scene_fn + '.ma'
            type = 'mayaAscii'
        else:
            scene_fn = scene_fn + '.mb'
            type = 'mayaBinary'

        noteText = self.oldTask['note']
        try:
            pluginText = self.oldTask['plugin']
        except KeyError:
            pluginText = ''
        frameList = self.oldTask['frameList']
        cmds.waitCursor(state=True)
        panelList = cmds.getPanel(all=True)
        #print 'panelList =', panelList
        cmds.modelEditor(panelList[3], edit=True, displayAppearance='smoothShaded', displayTextures=True)

        Dir = os.path.join(CGMaya_config.storageDir, 'tmp.png')
        ret = cmds.playblast(frame = cmds.currentTime(q = True),
                       f = Dir,
                       fo = True, fmt = 'image', viewer = False,
                       c = 'PNG', quality = 60)
        tmpFile = Dir + '.0000.png'
        pix = QtGui.QPixmap(tmpFile)
        pixmap = pix.scaled(CGMaya_config.IconWidth, CGMaya_config.IconHeight)
        #self.imageLabel.setPixmap(QtGui.QPixmap(pixmap))
        cmds.modelEditor(panelList[3], edit=True, displayAppearance='boundingBox')
        #cmds.waitCursor(state=False)

        try:
            #CGMaya_function.saveTask(self.service, scene_fn, None, noteText, pluginText, frameList, type, False, False, False)
            CGMaya_function.saveTask(self.service, scene_fn, pixmap, noteText, pluginText, frameList, type, False, False,
                                   False)
            self.service.assetClose(CGMaya_config.currentTask['_id'])
            CGMaya_config.logger.server(CGMaya_config.projectName, CGMaya_config.sceneName,
                                        CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_SaveAs)
        except Exception:
            if CGMaya_config.lang == 'zh':
                cmds.confirmDialog(title=u'错误信息', message=u'文件保存出错?', button=[u'关闭'], defaultButton=u'关闭')
            else:
                cmds.confirmDialog(title='Error', message='Save File is Errr?', button=['Close'],
                                defaultButton=u'Close')

        list = json.loads(self.service.myWFGetTaskInfo(CGMaya_config.currentTask['_id']))
        CGMaya_config.currentTask = list[0]
        #print 'currentTask =', CGMaya_config.currentTask
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        CGMaya_config.currentTask = copy.deepcopy(self.oldTask)
        self.close()

    def closeEvent(self, event):
        # do stuff
        #print 'closeEvent'
        self.menu.setEnable(True)
        event.accept() # let the window close

class countDialog(QtCGMaya.QDialog):
    def __init__(self, task, item, parent):
        super(countDialog, self).__init__(parent)
        self.task = task
        self.item = item
        self.parent = parent

        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        if CGMaya_config.lang == 'zh':
            self.countLabel = QtCGMaya.QLabel(u'次数', self)
        else:
            self.countLabel = QtCGMaya.QLabel(u'Count', self)
        self.countText = QtCGMaya.QLineEdit('1', self)

        self.layout.addWidget(self.countLabel, 0, 0)
        self.layout.addWidget(self.countText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'取消', self)
            self.button2 = QtCGMaya.QPushButton(u'确认', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button2 = QtCGMaya.QPushButton(u'OK', self)
        self.layout.addWidget(self.button1, 1, 0)
        self.layout.addWidget(self.button2, 1, 1)
        self.button1.clicked.connect(self.onCancel)
        self.button2.clicked.connect(self.onOK)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'输入次数')
        else:
            self.setWindowTitle(u'Input Count')
        self.setGeometry(350, 350, 100, 50)
        self.parent.setEnabled(False)
        self.show()

    def onOK(self):
        CGMaya_config.refCount = int(self.countText.text())
        self.task['flag'] = 'X'
        self.task['count'] = CGMaya_config.refCount
        string = 'X' + str(CGMaya_config.refCount)
        self.item.setText(self.task['name'].ljust(40, ' ') + string)
        self.close()
        self.parent.setEnabled(True)

    def onCancel(self):
        self.close()
        self.parent.setEnabled(True)

class assetDialog(QtCGMaya.QDialog):
    def __init__(self, service, parent):
        super(assetDialog, self).__init__(parent)
        self.service = service
        self.parent = parent
        self.projectList = []
        self.taskList = []
        self.projectName  = ''
        self.taskName = ''
        self.tasKID = ''
        self.fileID = ''

        self.main_layout = QtCGMaya.QVBoxLayout()
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.projectListWidget = QtCGMaya.QListWidget(self)
        self.assetListWidget = QtCGMaya.QListWidget(self)
        self.layout.addWidget(self.projectListWidget, 0, 0)
        self.layout.addWidget(self.assetListWidget, 1, 0)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 0, 0)
        #self.projectListWidget.hide()
        self.projectListWidget.itemClicked.connect(self.onClickProjectItem)
        #self.treeWidget.itemDoubleClicked.connect(self.onDoubleClickItem)
        self.assetListWidget.itemClicked.connect(self.onClickAssetItem)
        self.assetListWidget.itemDoubleClicked.connect(self.onDoubleClickAssetItem)

        self.GetProjects()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.closeButton = QtCGMaya.QPushButton(u'关闭', self)
            self.selectButton = QtCGMaya.QPushButton(u'选择', self)
        else:
            self.closeButton = QtCGMaya.QPushButton(u'Close', self)
            self.selectButton = QtCGMaya.QPushButton(u'Select', self)
        self.layout.addWidget(self.closeButton, 0, 0)
        self.layout.addWidget(self.selectButton, 0, 1)
        self.closeButton.clicked.connect(self.onClose)
        self.selectButton.clicked.connect(self.onSelect)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 8, 0)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'资产任务列表')
        else:
            self.setWindowTitle(u'Asset List')
        self.setGeometry(900, 300, 400, 400)
        #self.parent.setEnabled(False)
        #self.show()

    def GetProjects(self):
        result = self.service.myWFGetAllProjects()
        projectRawList = json.loads(result)
        #textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        for project in projectRawList:
            if project['templateName'].find('Asset') < 0:
                continue
            item = QtCGMaya.QListWidgetItem(project['name'])
            #item.setFont(textFont)
            self.projectListWidget.addItem(item)
            self.projectList.append(project)
        if len(self.projectList) == 0:
            return
        row = 0

    def onClickProjectItem(self, item):
        row = self.projectListWidget.currentRow()
        self.projectName = self.projectList[row]['name']
        result = self.service.myWFGetProjectTask(self.projectName)
        self.taskList = json.loads(result)
        #textFont = QtGui.QFont("song", 12, QtGui.QFont.Normal)
        count = 0
        for task in self.taskList:
            item = QtCGMaya.QListWidgetItem(task['name'])
            self.assetListWidget.addItem(item)

    def onClickAssetItem(self, item):
        row = self.assetListWidget.currentRow()
        self.taskName = self.taskList[row]['name']
        self.tasKID = self.taskList[row]['_id']
        self.fileID = self.taskList[row]['fileID']

    def onDoubleClickAssetItem(self, item):
        self.onSelect()

    def onClose(self):
        self.close()
        self.parent.setEnabled(True)

    def onSelect(self):
        self.close()
        self.parent.setEnabled(True)
        self.parent.setAsset(self.projectName, self.taskName, self.tasKID, self.fileID)

class replaceAssetWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, wayflag, dlgFlag, item, parent1, parent = maya_main_window()):
        super(replaceAssetWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.wayflag = wayflag
        self.dlgFlag = dlgFlag
        self.parent1 = parent1
        self.selectItem = item
        self.dispFlag = 0
        self.refAssetIDList = []
        if menu:
            self.menu.setEnable(False)
        #else:
        #    self.parent1.setEnabled(False)
        self.dbFlag = False
        self.projectName = ''
        self.assetName = ''
        projectList = json.loads(service.myWFGetAllProjects())
        CGMaya_config.logger.set("replaceAsset")
        self.refProjectList = []
        for project in projectList:
            if project['templateName'].find('Asset') > 0:
                self.refProjectList.append(project)
        self.refAssetItemList = []
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.refProjectLabel = QtCGMaya.QLabel(u'引用资产项目', self)
        if CGMaya_config.lang == 'zh':
            self.taskLabel = QtCGMaya.QLabel(u'任务', self)
        else:
            self.taskLabel = QtCGMaya.QLabel(u'Task', self)
        try:
            CGMaya_config.refProjectName = CGMaya_config.currentTask['refModelProjectName']
        except KeyError:
            CGMaya_config.refProjectName = ''
        self.taskText = QtCGMaya.QLineEdit(CGMaya_config.currentTask['name'], self)
        self.taskText.setEnabled(False)
        self.refProjectBox = QtCGMaya.QComboBox(self)
        for refProject in self.refProjectList:
            self.refProjectBox.addItem(refProject['name'])
        self.refProjectBox.currentIndexChanged.connect(self.onRefProjectSelect)

        self.layout.addWidget(self.taskLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.taskText, 0, 1, 1, 6)
        self.layout.addWidget(self.refProjectLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.refProjectBox, 1, 1, 1, 6)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.refTreeWidget = QtCGMaya.QTreeWidget(self)
        headerList = []
        headerList.append(u'原资产')
        headerList.append(u'资产')
        headerList.append(u'状态')
        self.refTreeWidget.setHeaderLabels(headerList)
        self.layout.addWidget(self.refTreeWidget)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.refTreeWidget.itemClicked.connect(self.onClickItem)
        self.refTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItem)
        #self.refTreeWidget.connect(self.refTreeWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
        #                               self.onClicktItem)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.closeButton = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.closeButton = QtCGMaya.QPushButton(u'Close', self)
        self.layout.addWidget(self.closeButton, 1, 0)
        self.closeButton.clicked.connect(self.onClose)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'替换资产')
        else:
            self.setWindowTitle(u'Reference Model')
        self.setGeometry(300, 300, 800, 650)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        if CGMaya_config.currentTask['refAssetIDList']:
            self.refAssetIDList = json.loads(CGMaya_config.currentTask['refAssetIDList'])
        else:
            self.refAssetIDList = None
        if self.refProjectList:
            self.onRefProjectSelect(0)
        #self.DispRefAssets()

    def onRefProjectSelect(self, n):
        self.refProjectName = self.refProjectList[n]['name']
        self.refAssetList = json.loads(self.service.myWFGetProjectTask(self.refProjectName))
        self.DispRefAssets()

    def DispRefAssets(self):
        self.refTreeWidget.clear()
        self.refAssetItemList = []
        textFont = QtGui.QFont("song", 16, QtGui.QFont.Normal)
        refs = pymel.core.listReferences()
        for ref in refs:
            refn = ref.path
            refName = os.path.basename(refn)
            refModelName = refName.split('.')[0]
            rawAssetName = refModelName
            assetName = ''
            status = u'问题'
            self.refAssetItemList.append({'ref': ref, 'refAsset': None, 'status': '问题'})
            for refAsset in self.refAssetList:
                #print refAsset['assetPath']
                if refAsset['assetPath']:
                    assetName1 = os.path.basename(refAsset['assetPath'])
                else:
                    assetName1 = ''
                if refAsset['name'] == refModelName:
                    status = u'正常'
                    rawAssetName = refAsset['name']
                    assetName = ''
                    self.refAssetItemList.pop()
                    self.refAssetItemList.append({'ref': ref, 'refAsset': refAsset, 'status': '正常'})
                    break
                elif assetName1 == refName:
                    rawAssetName = refModelName
                    assetName = refAsset['name']
                    status = u'匹配'
                    self.refAssetItemList.pop()
                    self.refAssetItemList.append({'ref': ref, 'refAsset': refAsset, 'status': '匹配'})
                    break

            item = QtCGMaya.QTreeWidgetItem(self.refTreeWidget, [rawAssetName, assetName, status])
            item.setFont(0, textFont)
            item.setFont(1, textFont)
            item.setFont(2, textFont)
            self.refTreeWidget.resizeColumnToContents(0)
            self.refTreeWidget.resizeColumnToContents(1)
            self.refTreeWidget.resizeColumnToContents(2)

    def setAsset(self, projectName, taskName, taskID, fileID):
        self.currentItem.setText(0, taskName)

    def onClickItem(self, item, column):
        self.currentItem = item
        row = self.refTreeWidget.indexOfTopLevelItem(item)
        if column == 2:
            if self.refAssetItemList[row]['status'] == '匹配':
                CGMaya_function.replaceRawAsset(self.service, self.refAssetItemList[row]['ref'], self.refProjectName,
                                                self.refAssetItemList[row]['refAsset'])
                self.DispRefAssets()

            #win = assetDialog(self.service, self)
            #win.show()

    def onDoubleClickItem(self, item, column):
        #row = self.refTreeWidget.currentRow()
        row = self.refTreeWidget.indexOfTopLevelItem(item)
        #win = assetWindow(self.service, CGMaya_config.currentTask, self.refAssetIDList[row], self)
        #win.show()

    def onClose(self):
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

    def onClose(self):
        if self.menu:
            self.menu.setEnable(True)
        else:
            self.parent1.setEnable(True)
        self.close()

class referenceAssetWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, wayflag, dlgFlag, item, parent1, parent = maya_main_window()):
        super(referenceAssetWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.wayflag = wayflag
        self.dlgFlag = dlgFlag
        self.parent1 = parent1
        self.selectItem = item
        self.refProjectName = ''
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
            self.radiobutton7 = QtCGMaya.QRadioButton(u'特效', self)
            self.radiobutton8 = QtCGMaya.QRadioButton(u'灯光', self)
            self.radiobutton9 = QtCGMaya.QRadioButton(u'其他', self)
        else:
            self.verRadiobutton = QtCGMaya.QRadioButton(u'ALL', self)
            self.lightRadiobutton = QtCGMaya.QRadioButton(u'CHR', self)
            self.radiobutton5 = QtCGMaya.QRadioButton(u'LOC', self)
            self.radiobutton6 = QtCGMaya.QRadioButton(u'PRO', self)
            self.radiobutton7 = QtCGMaya.QRadioButton(u'VFX', self)
            self.radiobutton8 = QtCGMaya.QRadioButton(u'LIT', self)
            self.radiobutton9 = QtCGMaya.QRadioButton(u'OTH', self)
        self.verRadiobutton.setChecked(True)
        self.lightRadiobutton.setChecked(False)
        self.radiobutton5.setChecked(False)
        self.radiobutton6.setChecked(False)
        self.radiobutton7.setChecked(False)
        self.radiobutton8.setChecked(False)
        self.radiobutton9.setChecked(False)

        self.layout.addWidget(self.verRadiobutton, 0, 0)
        self.layout.addWidget(self.lightRadiobutton, 0, 1)
        self.layout.addWidget(self.radiobutton5, 0, 2)
        self.layout.addWidget(self.radiobutton6, 0, 3)
        self.layout.addWidget(self.radiobutton7, 0, 4)
        self.layout.addWidget(self.radiobutton8, 0, 5)
        self.layout.addWidget(self.radiobutton9, 0, 6)
        self.verRadiobutton.clicked.connect(self.onSetAll)
        self.lightRadiobutton.clicked.connect(self.onSetChr)
        self.radiobutton5.clicked.connect(self.onSetLoc)
        self.radiobutton6.clicked.connect(self.onSetPro)
        self.radiobutton7.clicked.connect(self.onSetVfx)
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
        headerList.append(u'路径')
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
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            if self.wayflag:
                self.button1 = QtCGMaya.QPushButton(u'Reference', self)
            else:
                self.button1 = QtCGMaya.QPushButton(u'Import', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 0)
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
        self.setGeometry(300, 300, 900, 650)
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
        result = self.service.myWFGetAllProjects()
        rawProjectList = json.loads(result)
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
        result = self.service.myWFGetAssetsOfProject(self.refProjectName)
        assetList1 = json.loads(result)
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
        self.taskList.sort(cmp = self.myCompare)

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
            elif self.dispFlag == 4 and task['name'].find('vfx_') >= 0:
                b = True
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
                try:
                    item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [task['name'], string, '+', '-', task['assetPath']])
                except KeyError:
                    item = QtCGMaya.QTreeWidgetItem(self.treeWidget, [task['name'], string, '+', '-', ''])
                if count == row:
                    itemSelected = item
                item.setFont(0, textFont)
                item.setFont(1, textFont)
                item.setFont(2, textFont)
                item.setFont(3, textFont)
                item.setFont(4, textFont)
                item.setTextAlignment(1, QtCore.Qt.AlignCenter)
                item.setTextAlignment(2, QtCore.Qt.AlignCenter)
                item.setTextAlignment(3, QtCore.Qt.AlignCenter)
                self.treeWidget.resizeColumnToContents(0)
                count = count + 1
        self.treeWidget.setCurrentItem(itemSelected)

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
        CGMaya_config.refProjectName = self.refProjectName
        for task in self.taskList:
            list = self.service.myWFsearchTask(task['name'], self.refProjectName)
            for task1 in list:
                if task1['stage'] == task['stage'] and task['count'] > 0:
                    for n in range(0, task['count']):
                        if not CGMaya_function.referenceAsset(self.service, task1, self.wayflag):
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

class shotTransferWindow(QtCGMaya.QDialog):
    def __init__(self, service, parent=maya_main_window()):
        super(shotTransferWindow, self).__init__(parent)
        self.service = service
        self.srcProjectName = ''
        self.srcShotName = ''
        self.destProjectName = ''
        self.destShotName = ''
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()


        if CGMaya_config.lang == 'zh':
            self.srcShotLabel = QtCGMaya.QLabel(u'源镜头', self)
            self.destShotLabel = QtCGMaya.QLabel(u'目标镜头', self)
        else:
            self.srcShotLabel = QtCGMaya.QLabel('srcShot', self)
            self.destShotLabel = QtCGMaya.QLabel('destShot', self)
        self.srcShotText = QtCGMaya.QLineEdit('', self)
        self.destShotText = QtCGMaya.QLineEdit('', self)
        self.srcShotListWidget = QtCGMaya.QListWidget(self)
        self.destShotListWidget = QtCGMaya.QListWidget(self)

        self.srcShotListWidget.connect(self.srcShotListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                          self.onClickItemSrcShot)
        self.destShotListWidget.connect(self.destShotListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"),
                                          self.onClickItemDestShot)
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.srcShotLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.srcShotText, 0, 1, 1, 4)
        self.layout.addWidget(self.destShotLabel, 0, 5, 1, 1)
        self.layout.addWidget(self.destShotText, 0, 6, 1, 4)
        self.layout.addWidget(self.srcShotListWidget, 1, 0, 1, 4)
        self.layout.addWidget(self.destShotListWidget, 1, 5, 1, 5)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.getTaskList()
        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.transferButton = QtCGMaya.QPushButton(u'传递', self)
            self.cancelButton = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.transferButton = QtCGMaya.QPushButton(u'Transfer', self)
            self.cancelButton = QtCGMaya.QPushButton(u'Close', self)
        layout1.addWidget(self.transferButton, 1, 1)
        layout1.addWidget(self.cancelButton, 1, 0)
        self.transferButton.clicked.connect(self.onTransfer)
        self.cancelButton.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(layout1)
        self.main_layout.addWidget(self.row_Hbox)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'镜头传递')
        else:
            self.setWindowTitle(u'Shot Transfer')

        self.setLayout(self.main_layout)
        self.setGeometry(350, 350, 800, 850)
        # self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

        self.show()

    def getTaskList(self):
        self.srcShotListWidget.clear()
        self.destShotListWidget.clear()
        self.shotList = []
        for task in json.loads(self.service.myWFGetMyTask(CGMaya_config.userName)):
            if task['stage'] == u'布局':
                self.shotList.append(task)
                item1 = QtCGMaya.QListWidgetItem(task['name'])
                #item.setFont(textFont)
                self.srcShotListWidget.addItem(item1)
                item2 = QtCGMaya.QListWidgetItem(task['name'])
                self.destShotListWidget.addItem(item2)

    def onClickItemSrcShot(self):
        row = self.srcShotListWidget.currentRow()
        self.srcShotText.setText(self.shotList[row]['name'])
        self.srcProjectName = self.shotList[row]['projectName']
        self.srcShotName = self.shotList[row]['name']

    def onClickItemDestShot(self):
        row = self.destShotListWidget.currentRow()
        self.destShotText.setText(self.shotList[row]['name'])
        self.destProjectName = self.shotList[row]['projectName']
        self.destShotName = self.shotList[row]['name']

    def closeEvent(self, event):
        event.accept()  # let the window close

    def onCancel(self):
        self.hide()

    def onTransfer(self):
        if not self.srcShotName:
            return
        if not self.destShotName:
            return
        self.service.transferShot(self.srcProjectName, self.srcShotName, self.destProjectName, self.destShotName)
        CGMaya_config.logger.info('Transfer Finish-----------------\r')
        if CGMaya_config.lang == 'zh':
            response = cmds.confirmDialog(title=u'提示', message=u'已传递完毕', button=[u'是'], defaultButton=u'是')
            res = u'是'
        else:
            response = cmds.confirmDialog(title=u'information', message=u'Have Transfer', button=[u'Yes'], defaultButton=u'Yes')
            res = u'Yes'
        self.srcShotText.setText('')
        self.destShotText.setText('')
        self.srcProjectName = ''
        self.srcShotName = ''
        self.destProjectName = ''
        self.destShotName = ''
        self.srcShotListWidget.setCurrentRow(-1)
        self.destShotListWidget.setCurrentRow(-1)
        #self.hide()

class loadpluginWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(loadpluginWindow, self).__init__(parent)
        # And now set up the UI
        self.service = service
        self.menu = menu
        self.pluginType = 'mel'
        self.menu.setEnable(False)
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.radiobutton1 = QtCGMaya.QRadioButton(u'python', self)
        self.radiobutton2 = QtCGMaya.QRadioButton(u'mel', self)
        if self.pluginType == 'script':
            self.radiobutton1.setChecked(True)
            self.radiobutton2.setChecked(False)
        else:
            self.radiobutton1.setChecked(False)
            self.radiobutton2.setChecked(True)
        self.layout.addWidget(self.radiobutton1, 0, 0)
        self.layout.addWidget(self.radiobutton2, 0, 1)

        self.radiobutton1.clicked.connect(self.onSetScript)
        self.radiobutton2.clicked.connect(self.onSetMel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.pluginLabel = QtCGMaya.QLabel(u'插件说明', self)
        else:
            self.pluginLabel = QtCGMaya.QLabel(u'Plugin', self)
        self.pluginText = QtCGMaya.QLineEdit('', self)
        self.pluginText.setEnabled(False)

        self.layout.addWidget(self.pluginLabel, 0, 0)
        self.layout.addWidget(self.pluginText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.taskListWidget = QtCGMaya.QListWidget(self)
        self.taskListWidget.setIconSize(QtCore.QSize(60, 60))
        self.GetPlugins()
        self.main_layout.addWidget(self.taskListWidget)
        self.taskListWidget.connect(self.taskListWidget, QtCore.SIGNAL("itemClicked (QListWidgetItem*)"), self.onClickItem)
        self.taskListWidget.connect(self.taskListWidget, QtCore.SIGNAL("itemDoubleClicked (QListWidgetItem*)"), self.onDoubleClickItem)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'装载', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Load', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 0)
        self.button1.clicked.connect(self.onLoad)
        self.button2.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'装载插件')
        else:
            self.setWindowTitle(u'Load Plugin')
        self.setGeometry(300, 300, 500, 500)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

    def onSetScript(self):
        self.pluginType = 'py'
        self.radiobutton1.setChecked(True)
        self.radiobutton2.setChecked(False)
        self.GetPlugins()

    def onSetMel(self):
        self.pluginType = 'mel '
        self.radiobutton1.setChecked(False)
        self.radiobutton2.setChecked(True)
        self.GetPlugins()

    def onClickItem(self, item):
        self.pluginListIndex = self.taskListWidget.currentRow()
        #result = self.service.getmetadata(self.pluginList['DATA'][self.pluginListIndex][0], 'doc', 'file_desc')
        #ret = json.loads(result)
        #print 'ret =', ret

    def onDoubleClickItem(self, item):
        self.pluginListIndex = self.taskListWidget.currentRow()
        self.onLoad()

    def GetPlugins(self):
        self.taskListWidget.clear()
        result = self.service.getPluginList(CGMaya_config.CGMaya_plugin_Dir, self.pluginType)
        self.pluginList = json.loads(result)
        if self.pluginList['DATA'][0][0] == '1':
            return
        textFont = QtGui.QFont("song",12, QtGui.QFont.Bold)
        for plugin in self.pluginList['DATA']:
            item = QtCGMaya.QListWidgetItem(plugin[1])
            item.setFont(textFont)
            self.taskListWidget.addItem(item)

    def onLoad(self):
        url = self.pluginList['DATA'][self.pluginListIndex][19]
        scriptsDir = os.path.join(CGMaya_config.storageDir, 'scripts')
        if not os.path.exists(scriptsDir):
            os.mkdir(scriptsDir)
        pluginFn = scriptsDir + '/' + url[url.rfind('/') + 1:]
        ret = self.service.myDownload(url, pluginFn)
        if ret == None:
            self.close()
            return

        #mel.eval('if (`shelfLayout -exists RCMenu2 `) deleteUI RCMenu2;')
        #shelfTab = mel.eval('global string $gShelfTopLevel;')
        #mel.eval('global string $RCMenu2;')
        #mel.eval('$RCMenu2 = `shelfLayout -cellWidth 33 -cellHeight 33 -p $gShelfTopLevel RCMenu2`;')

        #file_object = open(pluginFn, "r")
        #getCommand = file_object.read()
        #file_object.close()
        #str = 'source "'+ pluginFn + '"'
        #cmds.shelfButton(command="import maya.cmds as cmds;cmds.launch(webPage='http://222.173.12.4:3000')",
        #                            annotation='', image='')
        #cmds.shelfButton(command='import maya; maya.mel.eval(str)', annotation='', image='')
        if pluginFn.split('.').pop() == 'mel':
            mel.eval('source "' + pluginFn + '"')
            #mel.eval('cra_sprObjects()')
        else:
            cmds.loadPlugin(pluginFn)

        #os.remove(pluginFn)

        self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_LoadPlugin)
        self.menu.setEnable(True)
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

class upLoadpluginWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(upLoadpluginWindow, self).__init__(parent)
        # And now set up the UI
        self.service =  service
        self.menu = menu
        self.menu.setEnable(False)
        self.fileList = []
        self.fileDescriptionList = []
        self.fileNums = 0
        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.pluginLabel = QtCGMaya.QLabel(u'插件', self)
        else:
            self.pluginLabel = QtCGMaya.QLabel(u'Plugin', self)
        self.pluginFileName = QtCGMaya.QLineEdit('', self)
        if CGMaya_config.lang == 'zh':
            self.selectButton = QtCGMaya.QPushButton(u'选择', self)
        else:
            self.selectButton = QtCGMaya.QPushButton(u'Select', self)
        self.layout.addWidget(self.pluginLabel, 0, 0)
        self.layout.addWidget(self.pluginFileName, 0, 1)
        self.layout.addWidget(self.selectButton, 0, 2)
        self.selectButton.clicked.connect(self.onSelect)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.pluginDesLabel = QtCGMaya.QLabel(u'插件说明', self)
        else:
            self.pluginDesLabel = QtCGMaya.QLabel(u'Plugin Description', self)
        self.pluginDesText = QtCGMaya.QLineEdit('', self)
        self.layout.addWidget(self.pluginDesLabel, 0, 0)
        self.layout.addWidget(self.pluginDesText, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'上传', self)
            self.button2 = QtCGMaya.QPushButton(u'取消', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 0)
        self.button1.clicked.connect(self.onUpLoad)
        self.button2.clicked.connect(self.onCancel)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'上传插件')
        else:
            self.setWindowTitle(u'UpLoad Plugin')
        self.setGeometry(300, 300, 600, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

    def onSelect(self):
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, "选择文件", ".", "*.mel *.py")
        else:
            dialog = QtCGMaya.QFileDialog(self, "Select Script File", ".", "*.mel *.py")
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFile)
        if dialog.exec_():
            files = dialog.selectedFiles()
            self.pluginFileName.setText(files[0])

    def onUpLoad(self):
        pluginFile = os.path.basename(self.pluginFileName.text())
        ext = pluginFile.split('.').pop()
        pluginFolderID = self.service.getPluginFolderID(CGMaya_config.CGMaya_plugin_Dir, ext)

        url = self.service.getUploadURL()
        result = self.service.findPlugin(pluginFile, CGMaya_config.CGMaya_plugin_Dir, ext)
        if result == '0': # existed
            if CGMaya_config.lang == 'zh':
                QtCGMaya.QMessageBox.information( self, u"提示信息", u"这个插件存在!!!")
            else:
                QtCGMaya.QMessageBox.information( self, u"Prompt", u"The Plugin is Existed!!!")
        else:
            result = self.service.upload(url, pluginFolderID, self.pluginFileName.text())
            assetid = result['assetid']
            self.service.setmetadata(assetid, 'doc', '[["file_desc","' + self.pluginDesText.text() + '"]]')

        self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_UploadPlugin)
        self.menu.setEnable(True)
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

class exportFileWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(exportFileWindow, self).__init__(parent)
        # And now set up the UI
        self.service = service
        self.menu = menu
        self.projectList = []
        self.taskList = []
        self.project = []
        self.task = []
        self.menu.setEnable(False)
        self.setup_ui()

    def setup_ui(self):
        self.abcRadiobutton = QtCGMaya.QRadioButton(u'ABC', self)
        self.renderwingRadiobutton = QtCGMaya.QRadioButton(u'RenderWing', self)

        self.noneRadiobutton = QtCGMaya.QRadioButton(u'None', self)
        self.houdiniRadiobutton = QtCGMaya.QRadioButton(u'Houdini', self)
        self.maxRadiobutton = QtCGMaya.QRadioButton(u'3DSMax', self)

        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'导出', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Export', self)
            self.button2 = QtCGMaya.QPushButton(u'Close', self)
        self.button1.clicked.connect(self.onExport)
        self.button2.clicked.connect(self.onCancel)

        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.abcRadiobutton, 0, 0)
        self.layout.addWidget(self.renderwingRadiobutton, 0, 1)
        if CGMaya_config.lang == 'zh':
            self.row_Hbox.setTitle(u'导出文件格式')
        else:
            self.row_Hbox.setTitle(u'Export File Format')
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.abcRadiobutton.setChecked(True)
        self.renderwingRadiobutton.setChecked(False)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.noneRadiobutton, 0, 0)
        self.layout.addWidget(self.houdiniRadiobutton, 0, 1)
        self.layout.addWidget(self.maxRadiobutton, 0, 2)
        if CGMaya_config.lang == 'zh':
            self.row_Hbox.setTitle(u'启动软件')
        else:
            self.row_Hbox.setTitle(u'Start Software')
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.noneRadiobutton.setChecked(False)
        self.houdiniRadiobutton.setChecked(True)
        self.maxRadiobutton.setChecked(False)

        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        layout1.addWidget(self.button1, 0, 1)
        layout1.addWidget(self.button2, 0, 0)
        self.row_Hbox.setLayout(layout1)
        self.main_layout.addWidget(self.row_Hbox)

        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'导出文件')
        else:
            self.setWindowTitle(u'Export File')

        self.setLayout(self.main_layout)
        self.setGeometry(550, 550, 450, 450)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

        self.show()

    def exportAbc(self, abcPath):
        selectGeo = cmds.ls(sl=True)
        if not selectGeo:
            cmds.confirmDialog(title=u'提示', message=u'没有选择对象', defaultButton=u'确认')
            self.menu.setEnable(True)
            self.close()
        startTime = cmds.playbackOptions(q=True, min=True)
        endTime = cmds.playbackOptions(q=True, max=True)
        selectGeoName = selectGeo[0].split(':').pop()
        #mel.eval('AbcExport -j "-frameRange %d %d -dataFormat ogawa -root |%s -file %s";' % (startTime, endTime, selectGeo[0], abcPath))
        mel.eval('AbcExport -j "-frameRange %d %d -dataFormat ogawa -root |%s -file %s/%s.abc";' % (startTime, endTime, selectGeo[0], abcPath, selectGeoName))
        return "%s/%s.abc" % (abcPath, selectGeoName)

    def onExport(self):
        projectName = CGMaya_config.currentTask['projectName']
        taskName = CGMaya_config.currentTask['name']
        projectDir = CGMaya_config.storageDir + '/' + projectName
        taskDir = projectDir + '/' + taskName
        if self.abcRadiobutton.isChecked():
            #path = taskDir + '/' + taskName + '.abc'
            path = 'D:\\'
            temPath = os.getenv("TEMP")
            abcPath = self.exportAbc(path)
            dict_all = {'userName': CGMaya_config.userName,
                        'password': CGMaya_config.password,
                        'taskID': CGMaya_config.currentTask['_id'],
                        'abcPath': abcPath}

            with open("%s\%s.json" % (temPath, "abc"), "w") as files:
                end = json.dumps(dict_all, indent=4)
                files.write(end)
            Dir = cmds.internalVar(userScriptDir=True)
            houdiniPath = Dir + '/CGMaya//Houdini.py'
            #currentPath = os.path.dirname(__file__)
            command = r'"C:/Program Files/Side Effects Software/Houdini 17.0.352/bin/houdinifx.exe"' + " " + houdiniPath
            subprocess.Popen(command, shell=None)

        elif self.renderwingRadiobutton.isChecked():
            #if cmds.window("unifiedRenderGlobalsWindow", exists=True):
            #    cmds.deleteUI("unifiedRenderGlobalsWindow")
            #    return
            Dir = cmds.internalVar(userScriptDir=True)
            pluginFn = Dir + '/RCMaya/RWingForMaya.py'
            cmds.loadPlugin(pluginFn)
            cmds.setAttr("defaultRenderGlobals.currentRenderer", l=False)
            cmds.setAttr("defaultRenderGlobals.currentRenderer", 'RWing', type="string")
            mel.eval('unifiedRenderGlobalsWindow;')
        self.menu.setEnable(True)
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

class setupWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(setupWindow, self).__init__(parent)
        # And now set up the UI
        self.service = service
        self.menu = menu
        self.menu.setEnable(False)
        self.tenantListIndex = 0
        CGMaya_config.logger.set("setup")
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtCGMaya.QVBoxLayout()
        """
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.myRootURLLabel = QtCGMaya.QLabel(u'入口：', self)
        self.myRootURLText = QtCGMaya.QLineEdit(CGMaya_config.myRootURL, self)
        self.myIPFSURLLabel = QtCGMaya.QLabel(u'IPFS入口：', self)
        self.myIPFSURLText = QtCGMaya.QLineEdit(CGMaya_config.IPFSUrl, self)
        self.layout.addWidget(self.myRootURLLabel, 0, 0)
        self.layout.addWidget(self.myRootURLText, 0, 1)
        self.layout.addWidget(self.myIPFSURLLabel, 1, 0)
        self.layout.addWidget(self.myIPFSURLText, 1, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        """
        if CGMaya_config.userToken:
            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()
            self.assetStorageLabel = QtCGMaya.QLabel(u'资产缓冲区路径：', self)
            self.assetStorageText = QtCGMaya.QLineEdit(CGMaya_config.assetStorageDir, self)
            #self.assetStorageSizeLabel = QtCGMaya.QLabel(u'剩余空间：', self)
            #self.assetStorageSizeText = QtCGMaya.QLineEdit(CGMaya_function.getStorageSize(CGMaya_config.assetStorageDir), self)
            self.storageLabel = QtCGMaya.QLabel(u'项目缓冲区路径：', self)
            self.storageText = QtCGMaya.QLineEdit(CGMaya_config.storageDir, self)
            #self.storageSizeLabel = QtCGMaya.QLabel(u'剩余空间：', self)
            #self.storageSizeText = QtCGMaya.QLineEdit(CGMaya_function.getStorageSize(CGMaya_config.storageDir), self)
            #self.sysStorageLabel = QtCGMaya.QLabel(u'系统缓冲区路径：', self)
            #self.sysStorageText = QtCGMaya.QLineEdit(CGMaya_config.sysStorageDir, self)
            self.layout.addWidget(self.assetStorageLabel, 0, 0, 1, 1)
            self.layout.addWidget(self.assetStorageText, 0, 1, 1, 2)
            #self.layout.addWidget(self.assetStorageSizeLabel, 0, 3, 1, 1)
            #self.layout.addWidget(self.assetStorageSizeText, 0, 4, 1, 1)
            self.layout.addWidget(self.storageLabel, 1, 0, 1, 1)
            self.layout.addWidget(self.storageText, 1, 1, 1, 2)
            #self.layout.addWidget(self.storageSizeLabel, 1, 3, 1, 1)
            #self.layout.addWidget(self.storageSizeText, 1, 4, 1, 1)
            #self.layout.addWidget(self.sysStorageLabel, 3, 0)
            #self.layout.addWidget(self.sysStorageText, 3, 1)
            #self.sysStorageText.setEnabled(False)
            self.row_Hbox.setLayout(self.layout)
            self.main_layout.addWidget(self.row_Hbox)

            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()
            self.softwareVersionLabel = QtCGMaya.QLabel(u'目前软件版本 ：', self)
            self.softwareVersionText = QtCGMaya.QLineEdit(CGMaya_config.softwareVersion, self)
            self.updateButton = QtCGMaya.QPushButton(u'更新', self)
            self.layout.addWidget(self.softwareVersionLabel, 0, 0)
            self.layout.addWidget(self.softwareVersionText, 0, 1)
            self.layout.addWidget(self.updateButton, 0, 2)
            self.row_Hbox.setLayout(self.layout)
            self.main_layout.addWidget(self.row_Hbox)

            self.updateButton.clicked.connect(self.onUpdateSoftware)

            softInfo = self.service.getSoftwareInfo('CGMaya')
            srcVersion = float(CGMaya_config.softwareVersion) * 100
            destVersion = float(softInfo['version']) * 100
            if srcVersion >= destVersion:
                self.updateButton.setEnabled(False)
            else:
                self.updateButton.setEnabled(True)

            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()
            if CGMaya_config.lang == 'zh':
                self.button1 = QtCGMaya.QPushButton(u'设置', self)
                self.button2 = QtCGMaya.QPushButton(u'取消', self)
                self.button3 = QtCGMaya.QPushButton(u'清除缓冲区', self)
            else:
                self.button1 = QtCGMaya.QPushButton(u'Setup', self)
                self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
                self.button3 = QtCGMaya.QPushButton(u'ClearBuffer', self)
            self.layout.addWidget(self.button1, 1, 2)
            self.layout.addWidget(self.button2, 1, 1)
            self.layout.addWidget(self.button3, 1, 0)
            self.button1.clicked.connect(self.onSetup)
            self.button2.clicked.connect(self.onCancel)
            self.button3.clicked.connect(self.onClear)
            self.row_Hbox.setLayout(self.layout)
            self.main_layout.addWidget(self.row_Hbox)
        else:
            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()
            if CGMaya_config.lang == 'zh':
                self.button1 = QtCGMaya.QPushButton(u'设置', self)
                self.button2 = QtCGMaya.QPushButton(u'取消', self)
            else:
                self.button1 = QtCGMaya.QPushButton(u'Setup', self)
                self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.layout.addWidget(self.button1, 0, 1)
            self.layout.addWidget(self.button2, 0, 0)
            self.button1.clicked.connect(self.onSetup)
            self.button2.clicked.connect(self.onCancel)
            self.row_Hbox.setLayout(self.layout)
            self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'设置')
        else:
            self.setWindowTitle(u'Setup')
        self.setGeometry(300, 300, 700, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def myCompare(self, a, b):
        str1 = a['name'].lower()
        str2 = b['name'].lower()
        return cmp(str1, str2)

    def getTeamList(self):
        self.teamListWidget.clear()
        self.teamList = json.loads(self.service.myWFGetAllTeams())
        # print 'result =', result

        self.teamList.sort(cmp=self.myCompare)
        textFont = QtCGMaya.QFont("song", 18, QtCGMaya.QFont.Normal)
        for team in self.teamList:
            item = QtGui.QListWidgetItem(team['alias'])
            item.setFont(textFont)
            self.teamtListWidget.addItem(item)

    def onTeamClickItem(self, item):
        row = self.teamtListWidget.currentRow()
        self.team = self.teamList[row]
        self.teamText.setText(self.team['alias'])

    def onClickItem(self, item):
        str = self.preItem.text().split(' ')[0]
        self.preItem.setText(str.ljust(30, ' ') + ' ')

        str = item.text().split(' ')[0]
        item.setText(str.ljust(30, ' ') + 'X')
        self.preItem = item

    def editUserSetup(self, fileName, softVer):
        ffn = fileName.split('.')[0] + '.bak'
        shutil.copy(fileName, ffn)

        fp1 = open(ffn, 'r')
        lines = fp1.readlines()
        fp2 = open(fileName, 'w')
        srcName = ''
        name = 'CGMaya' + repr(int(softVer))
        n = 0
        while n < len(lines):
            line = lines[n]
            if line.find('import CGMaya') > 0:
                str = line.split('import ').pop()
                str1 = line.split('import ')[0]
                srcName = str.split(' as CGMaya')[0]
                line1 = str1 + 'import ' + name + ' as CGMaya\";\n'
                fp2.write(line1)
            else:
                fp2.write(line)
            # print line1
            n = n + 1
        fp1.close()
        fp2.close()
        return os.path.dirname(fileName) + '/' + name

    def onUpdateSoftware(self):
        softInfo = self.service.getSoftwareInfo('CGMaya')
        srcVersion = float(CGMaya_config.softwareVersion) * 100
        destVersion = float(softInfo['version']) * 100
        if srcVersion >= destVersion:
            return

        CGMaya_config.softwareVersion = softInfo['version']
        userScriptDir = cmds.internalVar(userScriptDir=True)
        setupFile = userScriptDir.replace('/', '\\') + 'userSetup.mel'
        downloadDir = self.editUserSetup(setupFile, destVersion)
        if not os.path.exists(downloadDir):
            os.mkdir(downloadDir)
        softFile = downloadDir + '/' + softInfo['name'] + '.zip'
        self.service.getSoftware(softFile, softInfo['fileID'])
        zf = zipfile.ZipFile(softFile, 'r', zipfile.ZIP_DEFLATED, allowZip64=True)
        try:
            zf.extractall(downloadDir)
        except:
            pass
        zf.close()
        CGMaya_function.writeConfigFile()
        self.close()
        cmds.quit()

    def onClear(self):
        CGMaya_config.assetStorageDir = self.assetStorageText.text()
        if os.path.exists(CGMaya_config.assetStorageDir):
            reply = QtCGMaya.QMessageBox.question(self, u"问题", u"是否删除资产缓冲区?",
                        QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
            if reply == QtCGMaya.QMessageBox.Yes:
                shutil.rmtree(CGMaya_config.assetStorageDir)
                os.rmkdir(CGMaya_config.assetStorageDir)
        CGMaya_config.storageDir = self.storageText.text()
        if os.path.exists(CGMaya_config.storageDir):
            reply = QtCGMaya.QMessageBox.question(self, u"问题", u"是否删除项目缓冲区?",
                                                  QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
            if reply == QtCGMaya.QMessageBox.Yes:
                shutil.rmtree(CGMaya_config.storageDir)
                os.rmkdir(CGMaya_config.storageDir)

        #self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_ClearBuffer)
        CGMaya_config.logger.server('', '', '', CGMaya_config.RCMaya_Action_ClearBuffer)
        #self.menu.setEnable(True)
        #self.close()

    def onUploadPhoto(self):
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, u"选择照片文件", ".", "*.*")
        else:
            dialog = QtCGMaya.QFileDialog(self, "Select Photo File", ".", "*.*")
        dialog.setOption(QtCGMaya.QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFile)
        if dialog.exec_():
            photoFiles = dialog.selectedFiles()
            self.service.putUserPhotoFileGridfs(photoFiles)
            self.icon.addFile(photoFiles)

    def onSetup(self):
        #CGMaya_config.myRootURL = self.myRootURLText.text()
        #CGMaya_config.IPFSUrl = self.myIPFSURLText.text()
        if CGMaya_config.userToken:
            CGMaya_config.assetStorageDir = self.assetStorageText.text()
            if os.path.exists(self.assetStorageText.text()) and os.path.exists(self.storageText.text()):
                CGMaya_config.assetStorageDir = self.assetStorageText.text()
                CGMaya_config.storageDir = self.storageText.text()
                self.close()
            elif not os.path.exists(self.assetStorageText.text()):
                QtGui.QMessageBox.information(self, u"提示", u"目录不存在！！！---" + self.assetStorageText.text(), QtGui.QMessageBox.Yes)
                #os.mkdir(CGMaya_config.assetStorageDir)
            elif not os.path.exists(self.storageText.text()):
                QtGui.QMessageBox.information(self, u"提示", u"目录不存在！！！---" + self.storageText.text(), QtGui.QMessageBox.Yes)
                #os.mkdir(CGMaya_config.storageDir)

        #self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_Setup)
        #self.menu.setEnable(True)
        #CGMaya_config.logger.server(CGMaya_config.userName, '', '', CGMaya_config.CGMaya_Action_Setup)
        self.close()

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

class aboutWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent = maya_main_window()):
        super(aboutWindow, self).__init__(parent)
        # And now set up the UI
        self.service = service
        self.menu = menu
        self.menu.setEnable(False)
        CGMaya_config.logger.set("about")
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        textFont = QtGui.QFont("song", 14, QtGui.QFont.Normal)
        message = u'视觉云（北京）科技有限公司\nCopyright @2016-2019\n版本 ：' + CGMaya_config.softwareVersion
        self.copyRightLabel = QtCGMaya.QLabel(message, self)
        #self.copyRightLabel.setEnabled(False)
        self.copyRightLabel.setFont(textFont)
        self.copyRightLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.userLabel = QtCGMaya.QLabel(u'用户: ' + CGMaya_config.userName, self)
        # self.copyRightLabel.setEnabled(False)
        self.userLabel.setFont(textFont)
        self.userLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.layout.addWidget(self.copyRightLabel, 1, 1)
        self.layout.addWidget(self.userLabel, 2, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            if CGMaya_config.myDAMURL:
                self.button1 = QtCGMaya.QPushButton(u'软件更新', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            if CGMaya_config.myDAMURL:
                self.button1 = QtCGMaya.QPushButton(u'Update', self)
            self.button2 = QtCGMaya.QPushButton(u'Close', self)

        self.layout.addWidget(self.button2, 1, 1)
        if CGMaya_config.myDAMURL:
            self.layout.addWidget(self.button1, 1, 2)
            self.button1.clicked.connect(self.onUpdate)
        self.button2.clicked.connect(self.onClose)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'关于')
        else:
            self.setWindowTitle(u'About')
        self.setGeometry(300, 300, 400, 400)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onUpdate(self):
        if self.service.checkinSoftware():
            cmds.confirmDialog(title=u'提示', message=u'目前软件是最新的', defaultButton=u'确认')
        else:
            #self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_UpdateSoftware)
            CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_About)
        self.close()

    def onClose(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

class transferWindow(QtCGMaya.QDialog):
    def __init__(self, parent = maya_main_window()):
        super(transferWindow, self).__init__(parent)
        self.srcFile = ''
        self.setup_ui()
        self.remove_allnamespace()

    def setup_ui(self):
        self.setWindowTitle(u'传送UV和材质')
        self.buttonSelect = QtCGMaya.QPushButton(u'选择文件', self)
        self.buttonCancel = QtCGMaya.QPushButton(u'取消', self)
        self.buttonTransfer = QtCGMaya.QPushButton(u'传送', self)
        self.buttonSelect.clicked.connect(self.onSelect)
        self.buttonCancel.clicked.connect(self.onCancel)
        self.buttonTransfer.clicked.connect(self.onTransfer)

        self.main_layout = QtCGMaya.QVBoxLayout()
        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.buttonSelect, 0, 0)
        self.layout.addWidget(self.buttonCancel, 0, 2)
        self.layout.addWidget(self.buttonTransfer, 0, 1)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)
        self.setLayout(self.main_layout)

        self.setGeometry(400, 400, 400, 100)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

    def remove_allnamespace(self):
        nsp = cmds.namespaceInfo(lon=True, r=True)
        nsp.remove('UI')
        nsp.remove('shared')
        for ns in nsp[::-1]:
            try:
                cmds.namespace(mv=(ns, ':'), f=True)
                cmds.namespace(rm=ns)
            except RuntimeError:
                pass

    def onSelect(self):
        dialog = QtCGMaya.QFileDialog(self, "选择传送的文件", ".", "*")
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFiles)
        if dialog.exec_():
            # textFont = QtCGMaya.QFont("song", 18, QtCGMaya.QFont.Normal)
            fileList = dialog.selectedFiles()
            self.srcFile = fileList[0]

    def onTransfer(self):
        objectList1 = cmds.ls(selection=True)
        if len(objectList1) < 1:
            objectList1 = cmds.ls(dagObjects=True, long=True, geometry=True, shapes=True, visible=True)
        ass1 = cmds.ls(assemblies=True)
        cmds.file(self.srcFile, i=True, ns='ns')
        self.remove_allnamespace()
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
                        cmds.polyTransfer(object1, uvSets=True, alternateObject=object2, constructionHistory=True)
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
                cmds.delete(ass)

    def onCancel(self):
        self.close()

    def closeEvent(self, event):
        event.accept() # let the window close


