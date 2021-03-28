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
import CGMaya_function
import CGMaya_common
import CGMaya_service
import CGMaya_parser
import CGMaya_mouse

class saveTaskWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent=CGMaya_common.maya_main_window()):
        super(saveTaskWindow, self).__init__(parent)
        self.service = service
        self.menu = menu
        self.menu.setEnable(False)
        self.fileNums = 0
        self.fileList = []
        # CGMaya_config.clipboard.dataChanged.connect(self.on_clipboard_change)
        # self.setAcceptDrops(True)
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        self.setAcceptDrops(True)
        self.stereoFlag = False
        self.setup_ui()

    def setup_ui(self):
        self.main_layout = QtCGMaya.QGridLayout()
        stage = CGMaya_config.currentTask['stage']

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.projectLabel = QtCGMaya.QLabel(u'项目', self)
            self.taskLabel = QtCGMaya.QLabel(u'任务', self)
            self.descriptionLabel = QtCGMaya.QLabel(u'描述', self)
        else:
            self.projectLabel = QtCGMaya.QLabel(u'Project', self)
            self.taskLabel = QtCGMaya.QLabel(u'Task', self)
            self.descriptionLabel = QtCGMaya.QLabel(u'Description', self)

        self.projectText = QtCGMaya.QLineEdit(CGMaya_config.currentProject['name'], self)
        self.projectText.setEnabled(False)
        self.taskText = QtCGMaya.QLineEdit(CGMaya_config.currentTask['name'], self)
        self.taskText.setEnabled(False)
        self.noteText = QtCGMaya.QLineEdit('', self)
        self.radiobutton1 = QtCGMaya.QRadioButton(u'ma', self)
        self.radiobutton2 = QtCGMaya.QRadioButton(u'mb', self)
        scene_FN = cmds.file(sn=True, q=True)
        fn = os.path.basename(scene_FN)
        if fn and fn.split('.')[1] == 'mb':
            self.radiobutton2.setChecked(True)
        else:
            self.radiobutton1.setChecked(True)

        self.layout.addWidget(self.projectLabel, 0, 0, 1, 1)
        self.layout.addWidget(self.projectText, 0, 1, 1, 5)
        self.layout.addWidget(self.radiobutton1, 0, 6, 1, 1)
        self.layout.addWidget(self.taskLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.taskText, 1, 1, 1, 5)
        self.layout.addWidget(self.radiobutton2, 1, 6, 1, 1)
        self.layout.addWidget(self.descriptionLabel, 2, 0, 1, 1)
        self.layout.addWidget(self.noteText, 2, 1, 1, 6)

        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox, 0, 0, 3, 1)
        boxRow = 3
        if stage == u'灯光':
            self.row_Hbox = QtCGMaya.QGroupBox()
            self.layout = QtCGMaya.QGridLayout()

            if CGMaya_config.lang == 'zh':
                self.lightLabel = QtCGMaya.QLabel(u'灯光文件', self)
                self.renderSingleFrameLabel = QtCGMaya.QLabel(u'渲染单帧选择', self)
            else:
                self.lightLabel = QtCGMaya.QLabel(u'Light File', self)
                self.renderSingleFrameLabel = QtCGMaya.QLabel('RenderFrame Select ', self)
            if CGMaya_config.lightFileFlag:
                fn = self.service.getFileName(CGMaya_config.currentTask, CGMaya_config.taskFileID)
                self.lightText = QtCGMaya.QLineEdit(fn.split('.')[0], self)
            else:
                self.lightText = QtCGMaya.QLineEdit(CGMaya_config.currentTask['name'], self)
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
        self.layout5 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.button1 = QtCGMaya.QPushButton(u'保存', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
            self.button4 = QtCGMaya.QPushButton(u'保存提交', self)
        else:
            self.button1 = QtCGMaya.QPushButton(u'Save', self)
            self.button2 = QtCGMaya.QPushButton(u'Cancel', self)
            self.button4 = QtCGMaya.QPushButton(u'Save&Submit', self)
        self.layout5.addWidget(self.button1, 2, 1)
        self.layout5.addWidget(self.button2, 2, 2)
        self.layout5.addWidget(self.button4, 2, 0)

        self.button1.clicked.connect(self.onSave)
        self.button2.clicked.connect(self.onCancel)
        self.button4.clicked.connect(self.onSaveSubmit)
        self.row_Hbox.setLayout(self.layout5)
        self.main_layout.addWidget(self.row_Hbox, boxRow + 4, 0, 1, 1)
        self.setLayout(self.main_layout)

        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'保存任务')
        else:
            self.setWindowTitle(u'Save Task')
        self.setGeometry(0, 0, 500, 200)
        # self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.image = None
        self.center()
        #self.getSubmitsOfTask()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def on_clipboard_change(self):
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
        self.fileListWidget.show()
        if fn in self.fileList:
            return
        else:
            newItem = QtCGMaya.QListWidgetItem()
            newItem.setText(fn)
            self.fileList.append(fn)
            self.fileListWidget.addItem(newItem)
            self.button4.setEnabled(True)
            # self.getSubmitsOfTask()

    def onPress(self, *args):
        #self.releasePoint = cmds.draggerContext('Context', query = True, anchorPoint = True)
        # CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        # print 'anchorPoint =', self.anchorPoint
        pass

    def onDrag(self, *args):
        #self.dragPoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        # print 'anchorPoint =', self.dragPoint
        pass

    def onRelease(self, *args):
        # self.releasePoint = cmds.draggerContext('Context', query = True, dragPoint = True)
        # print ' releasePoint =', self.releasePoint
        pass

    def onSelectFiles(self):
        if CGMaya_config.lang == 'zh':
            dialog = QtCGMaya.QFileDialog(self, "选择上传文件", ".", "*")
        else:
            dialog = QtCGMaya.QFileDialog(self, "Select Upload Files", ".", "*")
        dialog.setFileMode(QtCGMaya.QFileDialog.ExistingFiles)
        if dialog.exec_():
            # self.getSubmitsOfTask()
            # textFont = QtCGMaya.QFont("song", 18, QtCGMaya.QFont.Normal)
            self.fileList = dialog.selectedFiles()
            for submitFile in self.fileList:
                item = QtGui.QListWidgetItem(submitFile)
                # item.setFont(textFont)
                self.fileListWidget.addItem(item)
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
                        self.fileListWidget.addItem(item)
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
        # self.renderWingCheckBox.isChecked(
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
        row = self.fileListWidget.currentRow()
        fn = self.fileList[row]
        self.fileList.remove(fn)
        self.fileListWidget.clear()
        for submitFile in self.fileList:
            item = QtGui.QListWidgetItem(submitFile)
            self.fileListWidget.addItem(item)

    def onSave(self, flag=False):
        # if not CGMaya_function.checkSoftwareVersion(self.service):
        #     if CGMaya_config.lang == 'zh':
        #         response = QtCGMaya.QMessageBox.question(self, u"选择", u"项目要求的软件版本与本软件不一致，是否继续?",
        #                                                  QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
        #     else:
        #         response = QtCGMaya.QMessageBox.question(self, u"Select", u"Software Version is software version of project , is not??",
        #                                                  QtCGMaya.QMessageBox.StandardButton.Yes | QtCGMaya.QMessageBox.StandardButton.No)
        #     if response == QtCGMaya.QMessageBox.No:
        #         self.close()
        #         return False
        stage = CGMaya_config.currentTask['stage']
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, CGMaya_config.currentProject['name'])
        taskDir = CGMaya_common.makeDir(projectDir, CGMaya_config.currentTask['name'])

        scene_fn = CGMaya_config.currentTask['name']
        if stage == u'灯光':
            scene_fn = self.lightText.text()
            singleFrame = self.renderSingleFrameText.text()

        if self.radiobutton1.isChecked():
            scene_fn = scene_fn + '.ma'
            type = 'mayaAscii'
        else:
            scene_fn = scene_fn + '.mb'
            type = 'mayaBinary'

        project = self.service.getProjectInfo(CGMaya_config.currentProject['name'])
        CGMaya_config.logger.set("saveTask")
        if stage == u'布局' or stage == u'动画':
            CGMaya_config.logger.info('Saveing Animation Task...\r')
            scene_fn = taskDir + '/' + scene_fn
            ret = self.saveAniTask(scene_fn, self.noteText.text(), type)
        elif stage == u'灯光':
            CGMaya_config.logger.info('Saveing LightTask...\r')
            lightDir = CGMaya_common.makeDir(taskDir, CGMaya_config.CGMaya_Light_Dir)
            scene_fn = lightDir + '/' + scene_fn
            ret = self.saveLightTask(scene_fn, self.noteText.text(), type)
        else:
            CGMaya_config.logger.info('Saveing Asset Task...\r')
            scene_fn = taskDir + '/' + scene_fn
            ret = self.saveAssetTask(scene_fn, self.noteText.text(), type)

        if not ret:
            # self.menu.setEnable(True)
            # self.close()
            return
        CGMaya_config.logger.info('file is saved')

        CGMaya_config.logger.server(CGMaya_config.currentProject['name'], CGMaya_config.currentTask['name'],
                                    CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Save)

        QtGui.QMessageBox.information(self, u"提示", u"已保存完成.", QtGui.QMessageBox.Yes)

        if flag:
            cmds.file(new=True, force=True)


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
                self.submitTask(self.service, CGMaya_config.currentTask, self.submitID, self.fileList, notes)
                self.service.userActionLog(CGMaya_config.userName, CGMaya_config.projectName, CGMaya_config.sceneName,
                                           CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Submit)
            self.menu.setEnable(True)

    def onCancel(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close

    def onSelect(self):
        self.fileListWidget.show()
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
                self.fileListWidget.insertItem(self.fileNums, newItem)
                self.fileNums = self.fileNums + 1
            self.button4.setEnabled(True)

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

    def processFile(self, filePath, zf, zipFileList):
        if os.path.isfile(filePath) and not filePath in zipFileList:
            zipFileList.append(filePath)
            zf.write(filePath, os.path.basename(filePath))

    def processSeqFiles(self, textureFile, zf, zipFileList):
        if textureFile.find('.<UDIM>.') < 0 and textureFile.find('.<udim>.') < 0 and \
                textureFile.find('.<f>.') < 0 and textureFile.find('.<F>.') < 0:
            return
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

    def processTexture(self, zf):
        textureFileList = cmds.ls(type='file')
        zipFileList = []
        #dirList = []
        for textureFile in textureFileList:
            print('textureFile =', textureFile)
            textureFileName = cmds.getAttr(textureFile + '.fileTextureName')
            print('textureFileName =', textureFileName)
            self.processFile(textureFileName, zf, zipFileList)

            aText = textureFileName.split('.').pop()
            aText = '.' + aText
            TXFile = textureFileName.replace(aText, '.tx')
            self.processFile(TXFile, zf, zipFileList)
            self.processSeqFiles(textureFileName, zf, zipFileList)

    def processProxy(self, zf):
        zipFileList = []
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

    def saveAssetTask(self, scene_fn, note, type):
        projectName = CGMaya_config.currentTask['projectName']
        taskName = CGMaya_config.currentTask['name']
        taskID = CGMaya_config.currentTask['_id']
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, projectName)
        cmds.workspace(dir=projectDir)
        mayaFn = os.path.basename(scene_fn)
        defaults = ['UI', 'shared']
        ## 删除所有的namespace
        CGMaya_config.logger.info('Delete All Namespaces...\r')
        self.remove_allnamespace()

        CGMaya_config.logger.info('Save File...\r')
        b = False
        try:
            cmds.file(rename=scene_fn)
            cmds.file(save=True, type=type, force=True)
        except RuntimeError:
            CGMaya_config.logger.error('RuntimeError\r')
            QtCGMaya.QMessageBox.information(self, u"提示信息", u"不能保存.ma文件")
            return None

        if CGMaya_config.currentProject['render'] == 'renderwing':
            ffffn = os.path.basename(scene_fn).split('.')[0] + '.obj'
            objFilePath = os.path.join(os.path.dirname(scene_fn), ffffn)
            CGMaya_config.logger.info('save OBj File...\r')
            cmds.file(objFilePath, pr=1, typ="OBJexport", es=1,
                      op="groups=0; ptgroups=0;materials=0; smoothing=0; normals=0")
            CGMaya_config.logger.info('Uploading Obj File...\r')
            objFileID = self.service.putFile(CGMaya_config.currentTask, objFilePath)
            self.service.setTaskAssetObjID(CGMaya_config.currentTask['_id'], objFileID)

        textureFileID = ''
        tmpDir = CGMaya_common.makeDir(projectDir, CGMaya_config.CGMaya_Tmp_Dir)

        #zipFileName = tmpDir + '/' + 'texture.zip'
        zipFileName = tmpDir + '/' + taskName + '_texture.zip'

        CGMaya_config.logger.info('Processing Texture...\r')

        zf = zipfile.ZipFile(zipFileName, "w", zipfile.ZIP_STORED, allowZip64=True)
        self.processTexture(zf)
        self.processProxy(zf)
        zf.close()

        CGMaya_config.logger.info('Uploading Texture File...\r')
        textureFileID = self.service.putFile(CGMaya_config.currentTask, zipFileName)
        os.remove(zipFileName)

        CGMaya_config.logger.info('Uploading Task File...\r')
        fileID = self.service.putFile(CGMaya_config.currentTask, scene_fn)
        self.service.setTaskAsset(taskID, scene_fn, projectName, '', fileID, textureFileID, [], note, '', '')
        return True

    def processStereoCamera(self):
        list = cmds.ls(cameras=True)
        cameraList = []
        for camera in list:
            if camera.find('stereoCameraLeft') >= 0:
                cameraList.append(camera)
            elif camera.find('stereoCameraRight') >= 0:
                cameraList.append(camera)
        print('cameraList =', cameraList)
        if len(cameraList) == 2:
            self.service.setShotStereo(CGMaya_config.currentTask['name'], CGMaya_config.currentProject['name'], cameraList)
            return True
        else:
            QtCGMaya.QMessageBox.information(self, u"提示信息", u"没有设置立体摄像机", QtCGMaya.QMessageBox.Yes)
            return False

    def processReference(self):
        refs = pymel.core.listReferences(loaded=True)
        refAssetIDList = CGMaya_config.currentTask['refAssetIDList']
        CGMaya_config.logger.info('Processing Reference...%d, %d\r' % (len(refs), len(refAssetIDList)))
        for ref in refs:
            refn = ref.path
            refName = os.path.basename(refn)
            refModelName = refName.split('.')[0]
            for refAssetID in refAssetIDList:
                if refAssetID['name'] == refModelName:
                    break
            else:
                if CGMaya_config.currentProject['refProject'] == '':
                    CGMaya_config.logger.error(
                        'Reference Project is not Found: %s\r' % CGMaya_config.currentProject['name'])
                    return False, u'资产项目没有发现（AssetProject is not Found)'
                asset = self.service.getAssetByName(refModelName, CGMaya_config.currentProject['refProject'])
                if not asset:
                    CGMaya_config.logger.error('Reference Asset is not Found: %s\r' % refModelName)
                    return False, u'资产（%s）没有发现' % refModelName
                taskL = len(asset['taskList'])
                refAssetIDList.append({'projectName': CGMaya_config.currentProject['refProject'],
                                                         'name': refModelName, 'id': asset['fileID'],
                                                         'taskID': asset['taskList'][taskL - 1]['_id']})
        return True, ''
                    
    def processAudio(self):
        audioFileIDList = []
        soundList = pymel.core.ls(type='audio')
        for sound in soundList:
            sFilePath = sound.attr('filename').get()
            if os.path.isfile(sFilePath):
                audioFileID = self.service.putFile(CGMaya_config.currentTask, sFilePath, False)
                audioFileIDList.append({'id': audioFileID, 'name': os.path.basename(sFilePath)})
        if audioFileIDList:
            self.service.setTaskAudioFileIDList(CGMaya_config.currentTask['_id'], audioFileIDList)
        return audioFileIDList

    def processNextShot(self):
        shotName = CGMaya_config.currentTask['name']
        num = int(shotName.split('_SC').pop()) + 1
        if num <= 9:
            numStr = '000' + str(num)
        elif num <= 99:
            numStr = '00' + str(num)
        elif num <= 999:
            numStr = '0' + str(num)
        else:
            numStr = str(num)
        nextShotName = shotName.split('_SC')[0] + '_SC' + numStr
        ret = self.service.getShotInfo(CGMaya_config.currentTask['projectName'], nextShotName)
        if ret == None:
            executor = ''
        else:
            try:
                executor = ret['executor']
            except KeyError:
                executor = ''
        if ret == None or executor == CGMaya_config.currentTask['executor']:
            if CGMaya_config.lang == 'zh':
                response = QtCGMaya.QMessageBox.question(CGMaya_common.maya_main_window(), u"警告", u"是否创建下一个镜头?",
                                                         QtCGMaya.QMessageBox.StandardButton.No | QtCGMaya.QMessageBox.StandardButton.Yes)
            else:
                response = QtCGMaya.QMessageBox.question(CGMaya_common.maya_main_window(), u"Warning",
                                                         u"Is Is Create Next Shot???",
                                                         QtCGMaya.QMessageBox.StandardButton.No | QtCGMaya.QMessageBox.StandardButton.Yes)
            reply = QtCGMaya.QMessageBox.Yes
            if not response == reply:
                self.service.createNextShot(CGMaya_config.currentTask['project'], shotName, nextShotName)

    def saveAniTask(self, scene_fn, note, type):
        CGMaya_config.logger.set("saveTask")
        projectName = CGMaya_config.currentTask['projectName']
        taskName = CGMaya_config.currentTask['name']
        taskID = CGMaya_config.currentTask['_id']
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, projectName)
        cmds.workspace(dir=projectDir)

        if self.stereoFlag:
            if not self.processStereoCamera():
                return False
        status, message = self.processReference()
        if not status:
            QtCGMaya.QMessageBox.warning(self, u"警告信息", message, QtCGMaya.QMessageBox.Yes)
            return False

        audioFileIDList = self.processAudio()

        CGMaya_config.logger.info('Processing Task File...\r')
        CGMaya_config.logger.info('Save File...\r')
        try:
            cmds.file(rename=scene_fn)
            cmds.file(save=True, type=type, force=True)
        except RuntimeError:
            CGMaya_config.logger.error('RuntimeError\r')
            QtCGMaya.QMessageBox.warning(self, u"警告信息", u"不能保存.ma文件", QtCGMaya.QMessageBox.Yes)
            return False

        CGMaya_config.logger.info('Uploading Task File...\r')
        fileID = self.service.putFile(CGMaya_config.currentTask, scene_fn)
        startFrame = str(cmds.playbackOptions(query=1, min=1))
        endFrame = str(cmds.playbackOptions(query=1, max=1))
        frameListStr = startFrame.split('.')[0] + '-' + endFrame.split('.')[0]
        self.service.setTaskShot(taskID, taskName, projectName, '', fileID, '', audioFileIDList, note, '101', frameListStr)
        refAssetIDList = CGMaya_config.currentTask['refAssetIDList']
        if refAssetIDList:
            self.service.setTaskRefAssetIDList(taskID, refAssetIDList)
            self.service.setShotRefAssetIDList(taskName, projectName, refAssetIDList)

        if CGMaya_config.currentTask['stage'] == u'布局':
            self.processNextShot()
        return True

    def getRenderLayers(self):
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

    def saveLightTask(self, scene_fn, note, type):
        print('scene_fn =', scene_fn)
        projectName = CGMaya_config.currentTask['projectName']
        sceneName = CGMaya_config.currentTask['name']
        taskID = CGMaya_config.currentTask['_id']
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, projectName)
        cmds.workspace(dir=projectDir)

        CGMaya_config.logger.info('Processing Task File...\r')
        try:
            cmds.file(rename=scene_fn)
            cmds.file(save=True, type=type, force=True)
        except RuntimeError:
            CGMaya_config.logger.error('RuntimeError\r')
            QtCGMaya.QMessageBox.information(self, u"提示信息", u"不能保存.ma文件", QtCGMaya.QMessageBox.Yes)
            return False

        CGMaya_config.logger.info('Uploading Light File...\r')
        lightFileID = self.service.putFile(CGMaya_config.currentTask, scene_fn)

        #self.service.setTaskRenderFrames(taskID, singleFrame, frameListStr)

        renderLayers = self.getRenderLayers()
        lightFileIDList = CGMaya_config.currentTask['lightFileIDList']
        for lightFile in lightFileIDList:
            if lightFile['name'] == os.path.basename(scene_fn):
                lightFile['id'] = lightFileID
                lightFile['renderLayers'] = renderLayers
                break
        else:
            lightFileIDList.append(
                {'name': os.path.basename(scene_fn), 'id': lightFileID, 'renderLayers': renderLayers})
        self.service.setTaskLightFileIDList1(taskID, lightFileIDList, '')
        return True

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
            renderwingFileIDList.append(
                {'name': os.path.basename(scene_fn), 'id': renderwingFileID, 'renderLayers': renderLayers})
        service.myWFSetTaskRenderwingFileIDList(CGMaya_config.currentTask['_id'], renderwingFileIDList)
        # CGMaya_config.logger.info('Uploading SingleFrame Output File...\r')
        # saveSingleOutput(service)
        CGMaya_config.logger.info(u"文件已保存")
        print('         Renderwing File is saved')
        return renderwingFileID

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