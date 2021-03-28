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


class ImageUtil(object):
    """
    ImageUtil 图片处理库通用基类
    """
    def __init__(self):
        pass

    def getActiveM3dViewImage(self):
        '''
        getActiveM3dViewImage 获取当前 Viewport 视窗截图

        Returns:
            [MImage] -- 当前视窗截图
        '''

        # NOTE 通过 API 获取 viewport
        viewport = OpenMayaUI.M3dView.active3dView()
        viewport.refresh()

        # NOTE 获取 viewport 中缓存的渲染图
        img = OpenMaya.MImage()
        viewport.readColorBuffer(img, True)
        return img

    def getImagePixel(self, image, number=True):
        u'''
        getImagePixel 获取MImage像素

        Arguments:
            image {MImage} -- Maya API的图片对象

        Returns:
            [list] -- 像素序列
        '''
        width, height = image.getSize()

        # NOTE https://gist.github.com/hmasato/b72a95fbadf1c63b56ec
        pxiel = image.pixels().__long__()
        ptr = ctypes.cast(pxiel, ctypes.POINTER(ctypes.c_char))
        size = width * height * 4
        # NOTE ord将字符转换为 0 - 255 ASCII码区间
        if number:
            return [ord(char) for char in ctypes.string_at(ptr, size)]
        else:
            return ctypes.string_at(ptr, size)

class MayaImageUtil(ImageUtil):
    """
    MayaImageUtil Maya图片处理库
    """

    def __init__(self):
        pass

    def cropImage(self, image, x=0, y=0, width=200, height=200):
        u'''
        cropImage 图片裁剪

        Arguments:
            image {MImage} --  Maya API的图片对象

        Keyword Arguments:
            x {int} -- 裁剪起始像素 (default: {0})
            y {int} -- 裁剪结束像素 (default: {0})
            width {int} -- 宽度 (default: {200})
            height {int} -- 高度 (default: {200})

        Returns:
            [MImage] -- 裁剪的图像
            * None -- 报错返回空值
        '''

        img_width, img_height = image.getSize()

        # NOTE 如果数值不合法则返回 None
        if width <= 0 or height <= 0 or x < 0 or y < 0:
            print u"输入值不合法"
            return

        # NOTE 如果裁剪区域超过原图范围则限制到原图的边界上
        if x+width > img_width:
            width = img_width - x
        if y+height > img_height:
            height = img_height - y

        _pixels = self.getImagePixel(image)

        # NOTE https://groups.google.com/forum/#!topic/python_inside_maya/Q9NuAd6Av20
        pixels = bytearray(width*height*4)
        for i, _i in enumerate(range(x, x+width)):
            for j, _j in enumerate(range(y, y+height)):
                # NOTE 分别获取当前像素的坐标
                _pos = (_i+_j*img_width)*4
                pos = (i+j*width)*4
                # NOTE 这里加数字代表当前像素下 RGBA 四个通道的值
                pixels[pos+0] = _pixels[_pos+0]
                pixels[pos+1] = _pixels[_pos+1]
                pixels[pos+2] = _pixels[_pos+2]
                pixels[pos+3] = _pixels[_pos+3]

        # NOTE 返回裁剪的 Image
        img = OpenMaya.MImage()
        img.setPixels(pixels, width, height)
        return img

    def centerCropImage(self, image, width=500, height=500):
        '''
        centerCropImage 居中裁切图片 改变图片的长宽比

        Arguments:
            image {MImage} --  Maya API的图片对象

        Keyword Arguments:
            width {int} -- 宽度 (default: {500})
            height {int} -- 高度 (default: {500})

        Returns:
            [MImage] -- 裁剪的图像
            * None -- 报错返回空值
        '''

        img_width, img_height = image.getSize()
        x = img_width/2 - width/2
        y = img_height/2 - height/2
        return self.cropImage(image, x, y, width, height)

    def mergeImage(self, image_list, horizontal=True):
        '''
        mergeImage 图片合成

        Arguments:
            image_list {list} -- Maya API的图片对象组成的数组

        Keyword Arguments:
            horizontal {bool} -- True为横向排列 False为纵向排列  (default: {True})

        Returns:
            [MImage] -- 合成的图像
        '''

        # NOTE 获取图片数组的长宽及像素数据
        img_width_list = []
        img_height_list = []
        img_pixels_list = []
        for image in image_list:
            img_width, img_height = image.getSize()
            img_pixels = self.getImagePixel(image)
            img_width_list.append(img_width)
            img_height_list.append(img_height)
            img_pixels_list.append(img_pixels)

        # NOTE 获取图片数组的长宽及像素数据
        total_width = sum(img_width_list) if horizontal else max(
            img_width_list)
        total_height = max(img_height_list) if horizontal else sum(
            img_height_list)

        # NOTE 初始化变量
        pixels = bytearray(total_width*total_height*4)
        width = 0
        height = 0
        width_list = []
        height_list = []
        for _width, _height, _pixels in zip(img_width_list, img_height_list, img_pixels_list):
            # NOTE 纵向和横向不同的循环模式
            if horizontal:
                width_list = range(width, width+_width)
                height_list = range(_height)
                width += _width
            else:
                height_list = range(height, height+_height)
                width_list = range(_width)
                height += _height

            # NOTE 循环获取像素
            for _i, i in enumerate(width_list):
                for _j, j in enumerate(height_list):
                    _pos = (_i+_j*_width)*4
                    pos = (i+j*total_width)*4
                    pixels[pos+0] = _pixels[_pos+0]
                    pixels[pos+1] = _pixels[_pos+1]
                    pixels[pos+2] = _pixels[_pos+2]
                    pixels[pos+3] = _pixels[_pos+3]

        # NOTE 返回合成的图像
        img = OpenMaya.MImage()
        img.setPixels(pixels, total_width, total_height)
        return img


class assetCaptureWindow(QtCGMaya.QDialog):
    def __init__(self, service, parent=CGMaya_common.maya_main_window()):
        super(assetCaptureWindow, self).__init__(parent)
        self.service = service
        CGMaya_config.logger.set("assetCaptureWindow")
        self.camPara = {}
        self.grp = ""
        self.sel_list = pm.ls(sl=1)
        if not self.sel_list:
            self.sel_list = [mesh.getParent() for mesh in pm.ls(type="mesh")]

        self.setup_ui()

    def setup_ui(self):
        self.super_layout = QtCGMaya.QHBoxLayout()
        self.main_layout = QtCGMaya.QVBoxLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.assetLabel = QtCGMaya.QLabel(u'资产名', self)
            self.widthLabel = QtCGMaya.QLabel(u'单帧图片宽度', self)
            self.heightLabel = QtCGMaya.QLabel(u'单帧图片高度', self)
        else:
            self.assetLabel = QtCGMaya.QLabel(u'Asset Name', self)
            self.widthLabel = QtCGMaya.QLabel(u'PIC Width', self)
            self.heightLabel = QtCGMaya.QLabel(u'PIC Height', self)
        self.assetText = QtCGMaya.QLineEdit(CGMaya_config.currentTask['name'], self)
        self.assetText.setEnabled(False)
        self.widthText = QtCGMaya.QLineEdit('500', self)
        self.heightText = QtCGMaya.QLineEdit('500', self)

        self.layout.addWidget(self.assetLabel, 0, 0, 1, 2)
        self.layout.addWidget(self.assetText, 0, 1, 1, 3)
        self.layout.addWidget(self.widthLabel, 1, 0, 1, 1)
        self.layout.addWidget(self.widthText, 1, 1, 1, 1)
        self.layout.addWidget(self.heightLabel, 1, 2, 1, 1)
        self.layout.addWidget(self.heightText, 1, 3, 1, 1)

        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)

        self.camTreeWidget = QtCGMaya.QTreeWidget(self)
        # self.camTreeWidget.setColumnCount(2)
        headerList = []
        headerList.append(u'名称')
        headerList.append(u'')
        headerList.append(u'x')
        headerList.append(u'y')
        headerList.append(u'z')
        headerList.append(u'ax')
        headerList.append(u'ay')
        headerList.append(u'az')
        headerList.append(u'正交')
        headerList.append(u'预览')
        self.camTreeWidget.setHeaderLabels(headerList)
        self.main_layout.addWidget(self.camTreeWidget)
        self.camTreeWidget.itemClicked.connect(self.onClickItemCam)
        # self.camTreeWidget.itemDoubleClicked.connect(self.onDoubleClickItemTask)

        self.row_treeHbox = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()

        self.row_Hbox = QtCGMaya.QGroupBox()
        layout1 = QtCGMaya.QGridLayout()
        if CGMaya_config.lang == 'zh':
            self.saveButton = QtCGMaya.QPushButton(u'保存', self)
            self.addButton = QtCGMaya.QPushButton(u'增加', self)
            self.setupButton = QtCGMaya.QPushButton(u'重置', self)
            self.RecordButton = QtCGMaya.QPushButton(u'截图', self)
            self.closeBbutton = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.saveButton = QtCGMaya.QPushButton(u'Save', self)
            self.addButton = QtCGMaya.QPushButton(u'Add', self)
            self.setupButton = QtCGMaya.QPushButton(u'Setup', self)
            self.RecordButton = QtCGMaya.QPushButton(u'Record', self)
            self.closeBbutton = QtCGMaya.QPushButton(u'Close', self)
        layout1.addWidget(self.saveButton, 0, 0)
        layout1.addWidget(self.addButton, 0, 1)
        layout1.addWidget(self.setupButton, 0, 2)
        layout1.addWidget(self.RecordButton, 0, 3)
        layout1.addWidget(self.closeBbutton, 0, 4)
        self.saveButton.clicked.connect(self.onSave)
        self.addButton.clicked.connect(self.onAdd)
        self.setupButton.clicked.connect(self.onSetup)
        self.RecordButton.clicked.connect(self.onRecord)
        self.closeBbutton.clicked.connect(self.onClose)
        self.row_Hbox.setLayout(layout1)
        self.main_layout.addWidget(self.row_Hbox)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'资产截图')
        else:
            self.setWindowTitle(u'Asset Capture')

        self.setLayout(self.main_layout)
        self.setGeometry(0, 0, 1000, 400)
        # self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()
        self.camParaFilePath = os.path.join(CGMaya_config.sysStorageDir, CGMaya_config.camParaFileName)
        self.readCamParaConfig()
        self.displayCamPara()
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def displayCamPara(self):
        self.camTreeWidget.clear()
        for cam in self.camPara['camList']:
            xStr = '{0:.2f}'.format(cam['translate'][0]) + ' '
            yStr = '{0:.2f}'.format(cam['translate'][1]) + ' '
            zStr = '{0:.2f}'.format(cam['translate'][2]) + ' '
            axStr = '{0:.2f}'.format(cam['rotate'][0]) + ' '
            ayStr = '{0:.2f}'.format(cam['rotate'][1]) + ' '
            azStr = '{0:.2f}'.format(cam['rotate'][2]) + ' '
            item = QtCGMaya.QTreeWidgetItem(self.camTreeWidget,
                                            [cam['name'].center(10) + ' ', '',
                                             xStr.center(10), yStr.center(10), zStr.center(10),
                                             axStr.center(10), ayStr.center(10), azStr.center(10),
                                             '', ''])
            if cam['enable']:
                item.setCheckState(1, QtCore.Qt.CheckState.Checked)
            else:
                item.setCheckState(1, QtCore.Qt.CheckState.Unchecked)
            if cam['orthographic']:
                item.setCheckState(8, QtCore.Qt.CheckState.Checked)
            else:
                item.setCheckState(8, QtCore.Qt.CheckState.Unchecked)
            item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
            # self.camTreeWidget.resizeColumnToContents(0)
            # self.camTreeWidget.resizeColumnToContents(1)
            # self.camTreeWidget.resizeColumnToContents(2)
            # self.camTreeWidget.resizeColumnToContents(3)
            # self.camTreeWidget.resizeColumnToContents(4)
            # self.camTreeWidget.resizeColumnToContents(5)
            # self.camTreeWidget.resizeColumnToContents(6)
            # self.camTreeWidget.resizeColumnToContents(7)
            # self.camTreeWidget.resizeColumnToContents(8)

    def onClickItemCam(self, item, column):
        row = self.camTreeWidget.indexOfTopLevelItem(item)
        cam = self.camPara['camList'][row]
        if column == 1:
            if not cam['enable']:
                cam['enable'] = True
                item.setCheckState(1, QtCore.Qt.CheckState.Checked)
            else:
                cam['enable'] = False
                item.setCheckState(1, QtCore.Qt.CheckState.Unchecked)
        elif column == 8:
            if not cam['orthographic']:
                cam['orthographic'] = True
                item.setCheckState(8, QtCore.Qt.CheckState.Checked)
            else:
                cam['orthographic'] = False
                item.setCheckState(8, QtCore.Qt.CheckState.Unchecked)
        elif column == 9:
            pm.lookThru(self.camList[row])
        return


    def readCamParaConfig(self):
        if os.path.exists(self.camParaFilePath):
            with open(self.camParaFilePath, 'r') as f:
                self.camPara = json.load(f)
            print(self.camPara)
            self.camList = []
            for cam in self.camPara['camList']:
                r_list = cam["rotate"]
                t_list = cam["translate"]
                ortho = cam["orthographic"]
                self.camList.append(self.addCam(cam['name'], ortho=ortho, json=False, t_r_list=(t_list, r_list)))
        else:
            self.resetCamParaConfig()

    def writeCamParaConfig(self):
        try:
            with open(self.camParaFilePath, 'w') as f:
                json.dump(self.camPara, f, indent=4)
        except:
            QtCGMaya.QMessageBox.warning(self, "Warning", u"保存失败")

    def addCam(self, text, rx=-45, ry=45, ortho=False, json=True, t_r_list=None):
        """addCam 添加摄像机
        Arguments:
            text {str} -- 摄像机名称

        Keyword Arguments:
            rx {int} -- x轴旋转角度 (default: {-45})
            ry {int} -- y轴旋转角度 (default: {45})
            ortho {bool} -- 正交属性 (default: {False})
            json {bool} -- 是否存储当前设置的属性 (default: {True})
            t_r_list {tuple} -- 位移和旋转的组合元组 (default: {None})

        Returns:
            [camera] -- Maya 的 Camera 对象
        """

        cam, cam_shape = pm.camera(n=text)
        text = cam.name()

        # pm.parent(cam, self.grp)

        # Note 隐藏摄像机
        cam.visibility.set(0)

        # Note 如果传入这个变量说明是读取数据 安装数据设置摄像机
        pm.select(self.sel_list)
        if t_r_list:
            t, r = t_r_list
            cam.t.set(t)
            cam.r.set(r)
        else:
            cam.rx.set(rx)
            cam.ry.set(ry)
            pm.lookThru(cam)
            pm.viewFit(f=self.camPara['fit'], all=0)

        if ortho:
            cam_shape.orthographic.set(ortho)
            pm.lookThru(cam)
            pm.viewFit(f=self.camPara['fit'] / 2, all=0)

        # NOTE 是否将数组输出到到字典上
        if json:
            self.camList.append(cam)
            self.camPara['camList'].append({'name': text, 'enable': True, 'translate': cam.t.get().tolist(),
                                    'rotate': cam.r.get().tolist(), 'orthographic': ortho})
        return cam

    def resetCamParaConfig(self):
        self.camPara = {'width': 500, 'height': 500, 'fit': 0.8, 'camList': []}
        self.fit = 0.8

        self.camList = []
        self.camList.append(self.addCam("front_cam", 0, 0, ortho=True))
        self.camList.append(self.addCam("side_cam", 0, -90, ortho=True))
        self.camList.append(self.addCam("top_cam", -90, 0, ortho=True))
        self.camList.append(self.addCam("fs45_cam", -45, 45))
        self.camList.append(self.addCam("bs45_cam", -45, -135))

    def closeEvent(self, event):
        event.accept()  # let the window close

    def onSave(self):
        self.writeCamParaConfig()
        pass

    def onAdd(self):
        self.addCam('cam', 0, 0)
        self.displayCamPara()
        pass

    def onSetup(self):
        del self.camPara
        del self.camList
        self.resetCamParaConfig()
        self.displayCamPara()
        pass

    def onClose(self):
        self.close()

    def onRecord(self):
        projectDir = CGMaya_common.makeDir(CGMaya_config.storageDir, CGMaya_config.currentProject['name'])
        taskDir = CGMaya_common.makeDir(projectDir, CGMaya_config.currentTask['name'])

        rand = random.randint(0, 10000)
        file_path = os.path.join(taskDir, CGMaya_config.currentTask['name'] + '_' + str(rand) + '.png')

        # NOTE 获取当前激活的面板 (modelPanel4)
        for panel in pm.getPanel(type="modelPanel"):
            if pm.modelEditor(panel, q=1, av=1):
                active_cam = pm.modelEditor(panel, q=1, camera=1)
                active_panel = panel
                break

        # NOTE 获取当前 HUD 相关的显示状态
        display_1 = pm.modelEditor(active_panel, q=1, hud=1)
        display_2 = pm.modelEditor(active_panel, q=1, grid=1)
        display_3 = pm.modelEditor(active_panel, q=1, m=1)
        display_4 = pm.modelEditor(active_panel, q=1, hos=1)
        display_5 = pm.modelEditor(active_panel, q=1, sel=1)

        # NOTE 隐藏界面显示
        pm.modelEditor(active_panel, e=1, hud=0)
        pm.modelEditor(active_panel, e=1, grid=0)
        pm.modelEditor(active_panel, e=1, m=0)
        pm.modelEditor(active_panel, e=1, hos=0)
        pm.modelEditor(active_panel, e=1, sel=0)

        self.util = MayaImageUtil()

        # NOTE 创建临时摄像机组
        # self.cam_setting.showProcess()

        # NOTE 获取摄像机截取的画面
        img_list = []
        for index, cam in enumerate(self.camPara['camList']):
            if not cam['enable']:
                continue
            pm.lookThru(self.camList[index])
            img = self.captureImage()
            if img:
                img_list.append(img)

        # Note 合并图片
        img = self.util.mergeImage(img_list, horizontal=True)

        ext = os.path.splitext(file_path)[-1][1:]
        # Note 不同API的输出指令不一样进行区分
        img.writeToFile(file_path, ext)

        # NOTE 恢复HUD显示
        pm.modelEditor(active_panel, e=1, hud=display_1)
        pm.modelEditor(active_panel, e=1, grid=display_2)
        pm.modelEditor(active_panel, e=1, m=display_3)
        pm.modelEditor(active_panel, e=1, hos=display_4)
        pm.modelEditor(active_panel, e=1, sel=display_5)

        # NOTE 恢复之前的摄像机视角并删除临时的摄像机组
        pm.lookThru(active_cam)
        # pm.delete(self.cam_setting.grp)

        submitFileID = self.service.putFile(CGMaya_config.currentTask, file_path)

        length = os.path.getsize(file_path)
        width = self.camPara['width'] * len(self.camPara['camList'])
        height = self.camPara['height']
        name = os.path.basename(file_path)
        type = 'image'

        submit = self.service.createSubmit2(CGMaya_config.currentTask['_id'], submitFileID,
                                            name, length, width, height, type)

        self.service.submitTask2(CGMaya_config.currentTask['_id'], submit['_id'])

        CGMaya_config.logger.info('file is saved')

        CGMaya_config.logger.server(CGMaya_config.currentProject['name'], CGMaya_config.currentTask['name'],
                                    CGMaya_config.currentTask['_id'], CGMaya_config.CGMaya_Action_Submit)

        # NOTE 输出成功信息
        QtCGMaya.QMessageBox.information(self, u"输出完成", u"图片输出成功\n输出路径:%s" % file_path)
        self.close()

    def captureImage(self):
        """
        captureImage 截取单个视角的图片

        Returns:
            [Image] -- 根据图片处理API返回相应的图片
        """
        img = self.util.getActiveM3dViewImage()

        width = self.camPara['width']
        height = self.camPara['height']
        img = self.util.centerCropImage(img, width, height)

        if not img:
            QtGui.QMessageBox.warning(self, u"警告", u"图片输出失败")
            return

        return img