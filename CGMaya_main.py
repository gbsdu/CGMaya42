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
import CGMaya_assetCapture
import CGMaya_aniCapture
import CGMaya_checkin
import CGMaya_service

class CGMayaMenu():
    def __init__(self, service):
        self.service = service
        CGMaya_config.isLogin = False
        CGMaya_config.clipboard = QtCGMaya.QApplication.clipboard()
        self.init()

    def __del__(self):
        pass

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
        #
        # def callback_transferTexture(_):
        #     CGMaya_function.transferTexture(self.service)
        #
        # def callback_updateReference(_):
        #     CGMaya_function.updateReference(self.service)
        #
        # def callback_shotTransfer(_):
        #     win = CGMaya_dialog.shotTransferWindow(self.service)
        #     win.show()
        #
        # def callback_loadplugin(_):
        #     win = CGMaya_dialog.loadpluginWindow(self.service, self.menu)
        #     win.show()
        #
        # def callback_upLoadplugin(_):
        #     win = CGMaya_dialog.upLoadpluginWindow(self.service, self.menu)
        #     win.show()

        def callback_submitRender(_):
            win = CGMaya_submit.submitRenderWindow(self.service, self.menu)
            win.show()

        # def callback_exportFile(_):
        #     win = CGMaya_dialog.exportFileWindow(self.service, self.menu)
        #     win.show()

        # https://github.com/FXTD-ODYSSEY/MayaViewportCapture
        def callback_assetCapture(_):
            win = CGMaya_assetCapture.assetCaptureWindow(self.service)
            win.show()

        def callback_aniCapture(_):
            CGMaya_aniCapture.capture(self.service)
            pass
            # import sys
            # import capture_gui
            # sys.path.append(os.path.dirname(__file__) + '/capture_gui')
            # print(os.path.dirname(__file__) + '/capture_gui')
            # capture_gui.main()
            #
            # # from capture_gui.vendor.Qt import QtCore
            #
            # def callback(options):
            #     """Implement your callback here"""
            #
            #     print("Callback before launching viewer..")
            #     # Debug print all options for example purposes
            #     import pprint
            #     pprint.pprint(options)
            #     filename = oCtions['filename']
            #     print("Finished callback for video {0}".format(filename))

        def callback_assetCheckin(_):
            CGMaya_checkin.assetCheckin(self.service)
            pass

        def callback_aniCheckin(_):
            CGMaya_checkin.aniCheckin(self.service)
            pass

        def callback_exportFbx(_):
            CGMaya_export.exportFbx(self.service)


        # https://github.com/Strangenoise/SubstancePainterToMaya
        def callback_exportMeshToSubstancePainter(_):
            # CGMaya_export.exportMeshToSubstancePainter(self.service, CGMaya_dialog.maya_main_window())
            pass

        # https://github.com/cgbeige/MariMe
        def callback_exportMeshToMari(_):
            # CGMaya_export.exportMeshToMari(self.service, CGMaya_dialog.maya_main_window())
            pass

        def callback_exportAbcToHoudini(_):
            # CGMaya_export.exportAbcToHoudini(self.service, CGMaya_dialog.maya_main_window())
            pass

        def callback_exportAbcToMax(_):
            # CGMaya_export.exportAbcToMax(CGMaya_dialog.maya_main_window())
            pass

        def callback_setup(_):
            win = CGMaya_setup.setupWindow(self.service)
            win.show()

        def callback_about(_):
            win = CGMaya_login.aboutWindow(self.service, self.menu)
            win.show()

        # def callback_exportFile(_):
        #     win = CGMaya_dialog.exportFileWindow(self.service, self.menu)
        #     win.show()
        #
        # def callback_redshiftToRenderWingByTexture(_):
        #     CGMaya_function.redshiftToRenderWingByTexture()
        #
        # def callback_transferUV(_):
        #     win = CGMaya_dialog.transferWindow()
        #     win.show()



        # 插件主菜单配置参数
        #   type: 类型 0: 菜单项; 1: 分割线; 2: 子菜单
        #   initStatus: 初始状态
        #   loginStatus: 登录后状态
        #   openStatus:  文件打开后状态
        #   name_zh:  中文名
        #   name_en:  英文名
        #   command:  回调函数

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
                                'name_zh': u'资产截图', 'name_en': 'Asset ScreenShot', 'command': callback_assetCapture},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                                'name_zh': u'动画捕屏', 'name_en': 'Animation Capture', 'command': callback_aniCapture},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                              'name_zh': u'资产检查', 'name_en': 'AssetCheckin', 'command': callback_assetCheckin},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                              'name_zh': u'动画检查', 'name_en': 'AniCheckin', 'command': callback_aniCheckin},
                            {'type': 1, 'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                              'name_en': '', 'command': None},
                            {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                              'name_zh': u'导出FBX文件', 'name_en': 'ExportFBX', 'command': callback_exportFbx}
                    #         {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                    #             'name_zh': u'导出Mesh(OBJ->Substance', 'name_en': 'ExportMesh->Substance', 'command': callback_exportMeshToSubstancePainter},
                    #         {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                    #             'name_zh': u'导出Mesh->Mari', 'name_en': 'ExportMesh->Mari', 'command': callback_exportMeshToMari},
                    #         {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                    #             'name_zh': u'导出ABC文件->Houdini', 'name_en': 'ExportAbc->Houdini', 'command': callback_exportAbcToHoudini},
                    #         {'type': 0, 'initStatus': False, 'loginStatus': False, 'openStatus': True,
                    #             'name_zh': u'导出ABC文件->3DsMax', 'name_en': 'ExportAbc->3DMax', 'command': callback_exportAbcToMax}
                        ],
                     },
                    {'type': 1, 'initStatus': False, 'loginStatus': True, 'openStatus': True, 'name_zh': u'',
                        'name_en': '', 'command': None},
                    {'type': 0, 'initStatus': True, 'loginStatus': True, 'openStatus': True,
                        'name_zh': u'关于插件', 'name_en': 'About', 'command': callback_about}
                    ]
        # 初始化菜单
        CGMaya_config.menuTitle = CGMaya_config.menuTitle + '(' + CGMaya_config.softwareVersion + ')'
        self.menu = pmc.menu(CGMaya_config.menuTitle, parent=pmc.MelGlobals()['gMainWindow'])
        for menuItem in self.menuList:
            if menuItem['type'] == 0:
                menuItem['handle'] = pmc.menuItem(parent=self.menu, label=menuItem['name_zh'], command=menuItem['command'])
                menuItem['handle'].setEnable(menuItem['initStatus'])
            elif menuItem['type'] == 1:
                pmc.menuItem(divider=True)
            elif menuItem['type'] == 2:
                menuItem['handle'] = pmc.menuItem(parent=self.menu, label=menuItem['name_zh'], subMenu=True)
                menuItem['handle'].setEnable(menuItem['initStatus'])
                for subMenuItem in menuItem['child']:
                    if subMenuItem['type'] == 0:
                        subMenuItem['handle'] = pmc.menuItem(label=subMenuItem['name_zh'],
                                                          command=subMenuItem['command'])
                        menuItem['handle'].setEnable(subMenuItem['initStatus'])
                    else:
                        pmc.menuItem(divider=True)

                cmds.setParent('..', menu=True)

        CGMaya_common.readConfigFile(CGMaya_config.sysStorageDir)
        CGMaya_config.logger.info("CGMaya_config.myRootURL = %s\r" % CGMaya_config.myRootURL)
        if not CGMaya_config.myRootURL:
            QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(), u"错误信息", u"请在设置中输入社区入口点",
                                             QtCGMaya.QMessageBox.Yes)
            return
        status, message = self.service.testConnection()
        if not status:
            print('myGetAllTeams Error, CGServer API Server is down')
            CGMaya_config.logger.error('myGetAllTeams Error, CGServer API Server is down\r')
            return


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
                        elif subMenuItem['name_zh'] == u'资产截图':
                            subMenuItem['handle'].setEnable(True)
                        if subMenuItem['name_zh'] == u'动画检查':
                            subMenuItem['handle'].setEnable(False)
                        elif subMenuItem['name_zh'] == u'资产检查':
                            subMenuItem['handle'].setEnable(True)
        else:
            for menuItem in self.menuList:
                if menuItem['name_zh'] == u'引用资产' or menuItem['name_zh'] == u'导入资产':
                    menuItem['handle'].setEnable(True)
                elif menuItem['type'] == 2:
                    for subMenuItem in menuItem['child']:
                        if subMenuItem['name_zh'] == u'动画检查':
                            subMenuItem['handle'].setEnable(True)
                        elif subMenuItem['name_zh'] == u'资产检查':
                            subMenuItem['handle'].setEnable(False)

        #cmds.nameCommand('RCMayaLogin', annotation='RCMaya Login', command=callback_login)
        #cmds.hotkey(k='F5', alt=True, name='RCMayaLogin')

class app():
    def __init__(self):
        import sys
        reload(sys)
        sys.setdefaultencoding('utf-8')

        self.service = CGMaya_service.CGService()
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
        CGMaya_config.logger = CGMaya_logger.Logger(self.service, 'CGMaya', 'main')
        CGMaya_config.logger.info("tmpStorageDir = %s\r" % CGMaya_config.tmpStorageDir)
        CGMaya_config.logger.info("sysStorageDir = %s\r" % CGMaya_config.sysStorageDir)

        try:
            self.CGMayaMenu = CGMayaMenu(self.service)
        except AttributeError as e:
            print('err =', e)

        # cmds.scriptJob(event=['SceneOpened', self.processSceneOpened])
        # cmds.scriptJob(event=['quitApplication', self.onQuit])


    def __del__(self):
        self.CGMayaMenu.close()
        del CGMaya_config.logger
        del self.CGMayaMenu

    def processSceneOpened(self):
        if CGMaya_common.isDesktopClientOpenFile():
            # maya用命令行参数打开文件，并且由桌面客户端选中任务后交换信息文件存在（CGSwap.ini）
            # 读取配置参数，可能有冗余
            if not CGMaya_config.myRootURL:
                QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(), u"错误信息", u"请在设置中输入社区入口点",
                                                 QtCGMaya.QMessageBox.Yes)
                return
            status, message = self.service.testConnection()
            if not status:
                CGMaya_config.logger.error('myGetAllTeams Error, CGServer API Server is down\r')
                return
            message = self.service.login(CGMaya_config.userName, CGMaya_config.password, CGMaya_config.teamName)
            CGMaya_config.logger.info("login Success...\r")
            # print(CGMaya_config.userToken)
            CGMaya_config.logger.setUserName(CGMaya_config.userName)
            CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_LoginSucessful)
            self.CGMayaMenu.menu.setEnable(True)
            self.CGMayaMenu.menuLogin()
            if CGMaya_config.currentProjectTemplate == '3DShot':
                self.CGMayaMenu.menuOpen(False)
            else:
                self.CGMayaMenu.menuOpen(True)

            CGMaya_config.currentProject = self.service.getProjectInfo(CGMaya_config.currentProjectName)
            CGMaya_config.currentTask = self.service.getTaskInfo(CGMaya_config.currentTaskID)

    def onQuit(self):
        self.CGMayaMenu.close()
        del CGMaya_config.logger
        del self.CGMayaMenu


if __name__ == "__main__":
    app()