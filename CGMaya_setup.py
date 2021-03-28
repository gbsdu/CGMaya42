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

import CGMaya_common
import CGMaya_service
import CGMaya_logger
import CGMaya_main

class urlPngDialog(QtCGMaya.QDialog):
    def __init__(self, parent, qr):
        super(urlPngDialog, self).__init__(parent)
        self.parent = parent
        self.qr = qr
        self.main_layout = QtCGMaya.QVBoxLayout()

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
        self.setGeometry(0, 0, 500, 200)
        self.show()
        self.movePosition()

    def movePosition(self):
        self.move(self.qr)

    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.ShiftModifier):
            self.parent.urlDlg = None
            self.close()

    def onClose(self):
        CGMaya_config.myRootURL = self.myRootURLText.text()
        CGMaya_config.IPFSUrl = self.myIPFSURLText.text()
        print(CGMaya_config.myRootURL)
        print(CGMaya_config.IPFSUrl)
        self.parent.urlDlg = None
        self.close()

class setupWindow(QtCGMaya.QDialog):
    def __init__(self, service, parent=CGMaya_common.maya_main_window()):
        super(setupWindow, self).__init__(parent)
        self.service = service
        self.urlDlg = None
        CGMaya_config.logger.set("setup")
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtCGMaya.QVBoxLayout()

        # self.row_Hbox1 = QtCGMaya.QGroupBox()
        # self.layout1 = QtCGMaya.QGridLayout()
        # self.myRootURLLabel = QtCGMaya.QLabel(u'入口：', self)
        # self.myRootURLText = QtCGMaya.QLineEdit(CGMaya_config.myRootURL, self)
        # self.myIPFSURLLabel = QtCGMaya.QLabel(u'IPFS入口：', self)
        # self.myIPFSURLText = QtCGMaya.QLineEdit(CGMaya_config.IPFSUrl, self)
        # self.layout1.addWidget(self.myRootURLLabel, 0, 0)
        # self.layout1.addWidget(self.myRootURLText, 0, 1)
        # self.layout1.addWidget(self.myIPFSURLLabel, 1, 0)
        # self.layout1.addWidget(self.myIPFSURLText, 1, 1)
        # self.row_Hbox1.setLayout(self.layout1)
        # self.main_layout.addWidget(self.row_Hbox1)

        self.row_Hbox2 = QtCGMaya.QGroupBox()
        self.layout2 = QtCGMaya.QGridLayout()
        self.assetStorageLabel = QtCGMaya.QLabel(u'资产缓冲区路径：', self)
        self.assetStorageText = QtCGMaya.QLineEdit(CGMaya_config.assetStorageDir, self)
        self.storageLabel = QtCGMaya.QLabel(u'项目缓冲区路径：', self)
        self.storageText = QtCGMaya.QLineEdit(CGMaya_config.storageDir, self)
        self.layout2.addWidget(self.assetStorageLabel, 0, 0, 1, 1)
        self.layout2.addWidget(self.assetStorageText, 0, 1, 1, 4)
        self.layout2.addWidget(self.storageLabel, 1, 0, 1, 1)
        self.layout2.addWidget(self.storageText, 1, 1, 1, 4)
        self.row_Hbox2.setLayout(self.layout2)
        self.main_layout.addWidget(self.row_Hbox2)

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
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
            self.button3 = QtCGMaya.QPushButton(u'清除缓冲区', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Setup', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button3 = QtCGMaya.QPushButton(u'ClearBuffer', self)
        self.layout.addWidget(self.button1, 1, 1)
        self.layout.addWidget(self.button2, 1, 2)
        self.layout.addWidget(self.button3, 1, 0)
        self.button1.clicked.connect(self.onSetup)
        self.button2.clicked.connect(self.onCancel)
        self.button3.clicked.connect(self.onClear)
        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'环境设置')
        else:
            self.setWindowTitle(u'Setup')
        self.setGeometry(0, 0, 500, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def keyPressEvent(self, event):
        if (event.modifiers() & QtCore.Qt.ShiftModifier):
            if not self.urlDlg:
                self.urlDlg = urlPngDialog(self, self.qr.bottomLeft())
                self.urlDlg.show()
            else:
                self.urlDlg.close()
                self.urlDlg = None

    def center(self):
        self.qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        self.qr.moveCenter(cp)
        self.move(self.qr.topLeft())

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

        self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.RCMaya_Action_ClearBuffer)
        CGMaya_config.logger.server(CGMaya_config.userName, '', '', CGMaya_config.RCMaya_Action_ClearBuffer)

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
                QtGui.QMessageBox.information(self, u"提示", u"目录不存在！！！" + self.assetStorageText.text(), QtGui.QMessageBox.Yes)
                #os.mkdir(CGMaya_config.assetStorageDir)
            elif not os.path.exists(self.storageText.text()):
                QtGui.QMessageBox.information(self, u"提示", u"目录不存在！！！" + self.storageText.text(), QtGui.QMessageBox.Yes)
                #os.mkdir(CGMaya_config.storageDir)

        self.service.userActionLog(CGMaya_config.userName, '', '', '', CGMaya_config.CGMaya_Action_Setup)
        CGMaya_config.logger.server(CGMaya_config.userName, '', '', CGMaya_config.CGMaya_Action_Setup)
        # print(CGMaya_config.assetStorageDir)
        # print(CGMaya_config.storageDir)
        CGMaya_common.writeConfigFile_user()
        self.close()

    def onCancel(self):
        self.close()

    def closeEvent(self, event):
        event.accept() # let the window close