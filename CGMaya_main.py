#coding=utf-8

import pymel.core as pmc
import maya.cmds as cmds
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
import os, sys
import platform

import CGMaya_logger
import CGMaya_config
import CGMaya_common
import CGMaya_login
import CGMaya_open
import CGMaya_save
import CGMaya_reference
import CGMaya_setup
import CGMaya_export
import CGMaya_submit
import CGMaya_service

class CGMayaMenu():
    def __init__(self, service):
        self.service = service
        CGMaya_config.isLogin = False
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        CGMaya_common.readConfigFile(CGMaya_config.sysStorageDir)
        CGMaya_config.logger.info("CGMaya_config.myRootURL = %s\r" % CGMaya_config.myRootURL)
        if not CGMaya_config.myRootURL:
            QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(), u"错误信息", u"请在设置中输入社区入口点",
                                             QtCGMaya.QMessageBox.Yes)
            return None
        message = self.service.testConnection()
        if len(message) > 0:
            CGMaya_config.logger.error('myGetAllTeams Error, CGServer API Server is down\r')
            QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(), u"错误信息", message,
                                             QtCGMaya.QMessageBox.Yes)
            return
        self.init()

    def init(self):
        def callback_login(_):
            win = CGMaya_login.loginWindow(self.service, self)
            win.show()

        def callback_logout(_):
            self.menuLogout()

        def callback_openTask(_):
            win = CGMaya_open.openTaskWindow(self.service, self)
            #win = CGMaya_dialog.openTaskWindow(self.service, self)
            win.show()

        def callback_saveTask(_):
            #win = CGMaya_save.saveTaskWindow(self.service, self.menu)
            win = CGMaya_save.saveTaskWindow(self.service, self.menu)
            win.show()

        def callback_referenceAsset(_):
            win = CGMaya_reference.referenceAssetWindow(self.service, self.menu, True)
            win.show()

        def callback_importAsset(_):
            win = CGMaya_reference.referenceAssetWindow(self.service, self.menu, False)
            win.show()

        def callback_transferTexture(_):
            CGMaya_function.transferTexture(self.service)

        def callback_updateReference(_):
            CGMaya_function.updateReference(self.service)

        def callback_shotTransfer(_):
            win = CGMaya_dialog.shotTransferWindow(self.service)
            win.show()

        def callback_loadplugin(_):
            win = CGMaya_dialog.loadpluginWindow(self.service, self.menu)
            win.show()

        def callback_upLoadplugin(_):
            win = CGMaya_dialog.upLoadpluginWindow(self.service, self.menu)
            win.show()

        def callback_submitRender(_):
            # win = CGMaya_dialog.submitRenderWindow(self.service, self.menu)
            win = CGMaya_submit.submitRenderWindow(self.service, self.menu)
            win.show()

        def callback_exportFile(_):
            win = CGMaya_dialog.exportFileWindow(self.service, self.menu)
            win.show()

        # https://github.com/FXTD-ODYSSEY/MayaViewportCapture
        def callback_assetScreenShot(_):
            print(__file__)
            dir = os.path.dirname(__file__)
            if not dir in sys.path:
                sys.path.append(dir)
            from MayaViewportCapture import ViewportCapture
            reload(ViewportCapture)
            capture_tool = ViewportCapture.mayaWin()

        # https://github.com/Colorbleed/maya-capture-gui
        def callback_aniCapture(_):
            import sys
            import capture_gui
            sys.path.append(os.path.dirname(__file__) + '/capture_gui')
            print(os.path.dirname(__file__) + '/capture_gui')
            capture_gui.main()

            # from capture_gui.vendor.Qt import QtCore

            def callback(options):
                """Implement your callback here"""

                print("Callback before launching viewer..")
                # Debug print all options for example purposes
                import pprint
                pprint.pprint(options)
                filename = options['filename']
                print("Finished callback for video {0}".format(filename))

        # https://github.com/Strangenoise/SubstancePainterToMaya
        def callback_exportMeshToSubstancePainter(_):
            CGMaya_export.exportMeshToSubstancePainter(self.service, CGMaya_dialog.maya_main_window())

        # https://github.com/cgbeige/MariMe
        def callback_exportMeshToMari(_):
            CGMaya_export.exportMeshToMari(self.service, CGMaya_dialog.maya_main_window())

        def callback_exportAbcToHoudini(_):
            CGMaya_export.exportAbcToHoudini(self.service, CGMaya_dialog.maya_main_window())

        def callback_exportAbcToMax(_):
            CGMaya_export.exportAbcToMax(CGMaya_dialog.maya_main_window())

        def callback_setup(_):
            win = CGMaya_setup.setupWindow(self.service)
            win.show()

        def callback_about(_):
            win = CGMaya_login.aboutWindow(self.service, self.menu)
            win.show()

        def callback_exportFile(_):
            win = CGMaya_dialog.exportFileWindow(self.service, self.menu)
            win.show()

        def callback_redshiftToRenderWingByTexture(_):
            CGMaya_function.redshiftToRenderWingByTexture()

        def callback_transferUV(_):
            win = CGMaya_dialog.transferWindow()
            win.show()

        self.menuList = [{'type': 0, 'initStatus': True, 'loginStatus': False, 'openStatus': False,
                        'name_zh': u'登录系统', 'name_en': 'Login', 'command': callback_login},
                    {'type': 0, 'initStatus': False, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'退出系统', 'name_en': 'Logout', 'command': callback_logout},
                    {'type': 1,  'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                        'name_en': '', 'command': None},
                    {'type': 0, 'initStatus': False, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'我的任务', 'name_en': 'MyTask', 'command': callback_openTask},
                    {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                        'name_zh': u'保存任务', 'name_en': 'Save Task', 'command': callback_saveTask},
                    {'type': 1, 'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                          'name_en': '', 'command': None},
                    {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                        'name_zh': u'引用资产', 'name_en': 'Reference Asset', 'command': callback_referenceAsset},
                    {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                        'name_zh': u'导入资产', 'name_en': 'Import Asset', 'command': callback_importAsset},
                    {'type': 1, 'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                          'name_en': '', 'command': None},
                    {'type': 0, 'initStatus': False, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'提交渲染', 'name_en': 'Submit Render', 'command': callback_submitRender},
                    {'type': 0, 'initStatus': False, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'环境设置', 'name_en': 'Setup', 'command': callback_setup},
                    {'type': 2, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                        'name_zh': u'实用工具', 'name_en': 'Utilities', 'child':
                         [
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'资产截图', 'name_en': 'Asset ScreenShot', 'command': callback_assetScreenShot},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'动画捕屏', 'name_en': 'Animation Capture', 'command': callback_aniCapture},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'导出Mesh(OBJ->Substance', 'name_en': 'ExportMesh->Substance', 'command': callback_exportMeshToSubstancePainter},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'导出Mesh->Mari', 'name_en': 'ExportMesh->Mari', 'command': callback_exportMeshToMari},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'导出ABC文件->Houdini', 'name_en': 'ExportAbc->Houdini', 'command': callback_exportAbcToHoudini},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'导出ABC文件->3DsMax', 'name_en': 'ExportAbc->3DMax', 'command': callback_exportAbcToMax}
                        ],
                     },
                    {'type': 1, 'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                        'name_en': '', 'command': None},
                    {'type': 0, 'initStatus': True, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'关于插件', 'name_en': 'About', 'command': callback_about}
                    ]

        CGMaya_config.menuTitle = CGMaya_config.menuTitle + '(' + CGMaya_config.softwareVersion + ')'
        self.menu = pmc.menu(CGMaya_config.menuTitle, parent=pmc.MelGlobals()['gMainWindow'])
        for menuItem in self.menuList:
            if menuItem['type'] == 0:
                menuItem['handle'] = pmc.menuItem(parent=self.menu, label=menuItem['name_en'], command=menuItem['command'])
                menuItem['handle'].setEnable(menuItem['initStatus'])
            elif menuItem['type'] == 1:
                pmc.menuItem(divider=True)
            elif menuItem['type'] == 2:
                menuItem['handle'] = pmc.menuItem(parent=self.menu, label=menuItem['name_en'], subMenu=True)
                menuItem['handle'].setEnable(menuItem['initStatus'])
                for subMenuItem in menuItem['child']:
                    if subMenuItem['type'] == 0:
                        subMenuItem['handle'] = pmc.menuItem(label=subMenuItem['name_en'],
                                                          command=subMenuItem['command'])
                        menuItem['handle'].setEnable(subMenuItem['initStatus'])
                cmds.setParent('..', menu=True)
        #self.menu_setStatus('initStatus')
            
        # #self.menuItem_login = pmc.menuItem(parent=self.menu, label=u'登录系统', command=callback_login)
        # self.menuItem_login = pmc.menuItem(parent=self.menu, label='Login', command=callback_login)
        # self.menuItem_logout = pmc.menuItem(parent=self.menu, label='退出系统', command=callback_logout)
        # self.menuItem_logout.setEnable(False)
        # pmc.menuItem(divider=True)
        #
        # self.menuItem_openTask = pmc.menuItem(parent = self.menu, label=u'我的任务', command=callback_openTask)
        # self.menuItem_openTask.setEnable(False)
        # self.menuItem_saveTask = pmc.menuItem(parent = self.menu, label=u'保存任务', command=callback_saveTask)
        # self.menuItem_saveTask.setEnable(False)
        # pmc.menuItem(divider=True)
        #
        # self.menuItem_referenceAsset = pmc.menuItem(parent = self.menu, label=u'引用资产', command=callback_referenceAsset)
        # self.menuItem_referenceAsset.setEnable(False)
        # self.menuItem_importAsset = pmc.menuItem(parent = self.menu, label=u'导入资产', command=callback_importAsset)
        # self.menuItem_importAsset.setEnable(False)
        # pmc.menuItem(divider=True)
        # """
        # self.menuItem_transferTexture = pmc.menuItem(parent = self.menu, label = u'传递材质', command = callback_transferTexture)
        # self.menuItem_transferTexture.setEnable(False)
        # self.menuItem_updateReference = pmc.menuItem(parent = self.menu, label = u'更新引用', command = callback_updateReference)
        # self.menuItem_updateReference.setEnable(False)
        #
        # self.menuItem_shotTransfer = pmc.menuItem(parent = self.menu, label = menuLabel[8], command = callback_shotTransfer)
        # self.menuItem_shotTransfer.setEnable(False)
        # pmc.menuItem(divider=True)
        # self.menuItem_loadplugin = pmc.menuItem(parent = self.menu, label = menuLabel[10], command = callback_loadplugin)
        # self.menuItem_loadplugin.setEnable(False)
        # self.menuItem_upLoadplugin = pmc.menuItem(parent=self.menu, label=menuLabel[9], command=callback_upLoadplugin)
        # self.menuItem_upLoadplugin.setEnable(False)
        #
        # pmc.menuItem(divider=True)
        # """
        # self.menuItem_submitRender = pmc.menuItem(parent=self.menu, label=u'提交渲染', command=callback_submitRender)
        # self.menuItem_submitRender.setEnable(False)
        #
        # """
        # self.menuItem_exportFile = pmc.menuItem(parent=self.menu, label=menuLabel[9], command=callback_exportFile)
        # self.menuItem_exportFile.setEnable(False)
        #
        # self.menuItem_exportFile = pmc.menuItem(parent=self.menu, subMenu=True, label=u'导出文件')
        # pmc.menuItem(label=u'导出ABC文件->Houdini', command=callback_exportAbcToHoudini)
        # pmc.menuItem(label=u'导出ABC文件->3DsMax')
        # pmc.menuItem(divider=True)
        # pmc.menuItem(label=u'导出ABC文件')
        # pmc.menuItem(label=u'导出FBX文件')
        # pmc.menuItem(label=u'导出RenderWing文件')
        # cmds.setParent('..', menu=True)
        # """
        # pmc.menuItem(divider=True)
        # self.menuItem_setup = pmc.menuItem(parent=self.menu, label=u'环境设置', command=callback_setup)
        # self.menuItem_setup.setEnable(False)
        #
        # self.menuItem_tools = pmc.menuItem(parent=self.menu, subMenu=True, label=u'实用工具')
        # self.menuItem_tools.setEnable(False)
        # self.menuItem_assetScreenShot = pmc.menuItem(label=u'资产截图', command=callback_assetScreenShot)
        # self.menuItem_assetScreenShot.setEnable(False)
        # self.menuItem_aniCapture = pmc.menuItem(label=u'动画抓屏', command=callback_aniCapture)
        # self.menuItem_aniCapture.setEnable(True)
        # self.menuItem_exportMeshToSubstancePainter = pmc.menuItem(label=u'导出Mesh(OBJ）->Substance', command=callback_exportMeshToSubstancePainter)
        # self.menuItem_exportMeshToSubstancePainter.setEnable(True)
        # self.menuItem_exportMeshToMari = pmc.menuItem(label=u'导出Mesh->Mari', command=callback_exportMeshToMari)
        # self.menuItem_exportMeshToMari.setEnable(False)
        # self.menuItem_exportAbcToHoudini = pmc.menuItem(label=u'导出ABC文件->Houdini', command=callback_exportAbcToHoudini)
        # self.menuItem_exportAbcToHoudini.setEnable(False)
        # self.menuItem_exportAbcToMax = pmc.menuItem(label=u'导出ABC文件->3DsMax', command=callback_exportAbcToMax)
        # self.menuItem_exportAbcToMax.setEnable(False)
        # """
        # self.menuItem_tools = pmc.menuItem(parent=self.menu, subMenu=True, label=u'实用工具')
        # pmc.menuItem(label=u'Redshift材质->Renderwing材质', command=callback_redshiftToRenderWingByTexture)
        # cmds.setParent('..', menu=True)
        # self.menuItem_transferUV = pmc.menuItem(parent = self.menu, label = menuLabel[11], command = callback_transferUV)
        # self.menuItem_transferUV.setEnable(True)
        #
        # self.menuArray = [self.menuItem_login, self.menuItem_logout, self.menuItem_openTask, self.menuItem_saveTask,
        #                         self.menuItem_referenceAsset, self.menuItem_importAsset, self.menuItem_transferTexture,
        #                         self.menuItem_updateReference, self.menuItem_submitRender, self.menuItem_exportFile,
        #                         self.menuItem_setup, self.menuItem_about, self.menuItem_tools]
        # """
        # self.menuItem_about = pmc.menuItem(parent=self.menu, label=u'关于插件', command=callback_about)
        # self.menuItem_about.setEnable(True)

    # def __del__(self):
    #     pass

    def close(self):
        if self.loginFlag:
            self.menuLogout(True)

    def menu_setStatus(self, key):
        for menuItem in self.menuList:
            if menuItem['type'] == 0:
                menuItem['handle'].setEnable(menuItem[key])
            elif menuItem['type'] == 2:
                menuItem['handle'].setEnable(menuItem[key])
                for subMenuItem in menuItem['child']:
                    if subMenuItem['type'] == 0:
                        subMenuItem['handle'].setEnable(subMenuItem[key])

    def menuLogin(self):
        self.menu_setStatus('loginStatus')
        CGMaya_config.isLogin = True
        CGMaya_common.readConfigFile_user()

    def menuLogout(self, bForce=False):
        CGMaya_config.logger.set("logout")
        if not CGMaya_config.isLogin:
            return

        if not bForce:
            if CGMaya_config.lang == 'zh':
                response = QtCGMaya.QMessageBox.question(CGMaya_common.maya_main_window(), u"警告", u"是否退出账号?",
                                                         QtCGMaya.QMessageBox.StandardButton.No | QtCGMaya.QMessageBox.StandardButton.Yes)
            else:
                response = QtCGMaya.QMessageBox.question(CGMaya_common.maya_main_window(), u"Warning", u"Is Quit???",
                                                         QtCGMaya.QMessageBox.StandardButton.No | QtCGMaya.QMessageBox.StandardButton.Yes)
            reply = QtCGMaya.QMessageBox.Yes
            if not response == reply:
                return

        cmds.file(new=True, force=True)

        if CGMaya_config.currentTask:
            self.service.assetClose(CGMaya_config.currentTask['_id'])
            CGMaya_config.currentTask = None

        CGMaya_config.logger.info("logout ...\r")
        CGMaya_config.logger.setUserName(CGMaya_config.userName)
        CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_Logout)
        CGMaya_config.userToken = None

        CGMaya_common.writeConfigFile()
        CGMaya_common.writeConfigFile_user()

        self.menu_setStatus('initStatus')
        CGMaya_config.isLogin = False

    # flag:True----Asset rig            False-----Shot
    def menuOpen(self, flag):
        self.menu_setStatus('openStatus')
        if flag:
            for menuItem in self.menuList:
                if menuItem['name_zh'] == u'引用资产' or menuItem['name_zh'] == u'导入资产':
                    menuItem['handle'].setEnable(False)
                elif menuItem['type'] == 2:
                    for subMenuItem in menuItem['child']:
                        if subMenuItem['name_zh'] == u'动画捕屏':
                            subMenuItem['handle'].setEnable(False)

        #cmds.nameCommand('RCMayaLogin', annotation='RCMaya Login', command=callback_login)
        #cmds.hotkey(k='F5', alt=True, name='RCMayaLogin')

class app():
    def __init__(self):
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')

        service = CGMaya_service.CGService()
        if platform.system() == 'Windows':
            CGMaya_config.tmpStorageDir = os.environ['TEMP']
            CGMaya_config.sysStorageDir = os.path.join(os.environ["userprofile"], "Documents", "CGTeam")
        elif platform.system() == "Linux":
            CGMaya_config.tmpStorageDir = '/tmp'
            CGMaya_config.sysStorageDir = os.path.join(os.environ["HOME"], "CGTeam")
        elif platform.system() == "Darwin":
            CGMaya_config.tmpStorageDir = '/tmp'
            CGMaya_config.sysStorageDir = os.path.join(os.environ["HOME"], "Library", "Preferences", "CGTeam")

        if not os.path.exists(CGMaya_config.sysStorageDir):
            os.mkdir(CGMaya_config.sysStorageDir)
        CGMaya_config.logger = CGMaya_logger.Logger(service, 'CGMaya', 'main')
        CGMaya_config.logger.info("tmpStorageDir = %s\r" % CGMaya_config.tmpStorageDir)
        CGMaya_config.logger.info("sysStorageDir = %s\r" % CGMaya_config.sysStorageDir)

        self.CGMayaMenu = CGMayaMenu(service)
        cmds.scriptJob(event=['quitApplication', self.onQuit])

    def __del__(self):
        self.CGMayaMenu.close()
        del CGMaya_config.logger
        del self.CGMayaMenu

    def onQuit(self):
        self.CGMayaMenu.close()
        del CGMaya_config.logger
        del self.CGMayaMenu
