#coding=utf-8

import os
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

import CGMaya_config
import CGMaya_common
import CGMaya_setup


class loginWindow(QtCGMaya.QDialog):
    def __init__(self, service, CGMenu, parent=CGMaya_common.maya_main_window()):
        super(loginWindow, self).__init__(parent)
        self.CGMenu = CGMenu
        self.CGMenu.menu.setEnable(False)
        self.service = service
        #cmds.nameCommand('RCMayaLogin', annotation='RCMaya Login', command='python("onLogin()")')
        #cmds.hotkey(k='Return', name='RCMayaLogin')

        result, message = service.getAllTeams()
        CGMaya_config.logger.set("login")
        if not result:
            CGMaya_config.logger.error('myGetAllTeams Error, CGServer API Server is down\r')
            QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(), u"错误信息", message, QtCGMaya.QMessageBox.Yes)
            return
        self.teamList = message
        self.errorFlag = False
        self.setup_ui()

    def setup_ui(self):
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'用户登录')
            self.teamLabel = QtCGMaya.QLabel(u'团队', self)
            self.nameLabel = QtCGMaya.QLabel(u'帐号', self)
            self.passLabel = QtCGMaya.QLabel(u'密码', self)
            # if self.errorFlag:
            #     self.errorLabel = QtCGMaya.QLabel(u'错误信息', self)
            self.button1 = QtCGMaya.QPushButton(u'登录', self)
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.setWindowTitle(u'User Login')
            self.teamLabel = QtCGMaya.QLabel(u'TeamName', self)
            self.nameLabel = QtCGMaya.QLabel(u'UserName', self)
            self.passLabel = QtCGMaya.QLabel(u'Password', self)
            # if self.errorFlag:
            #     self.errorLabel = QtCGMaya.QLabel(u'Error', self)
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
        # if self.errorFlag:
        #     self.errorText = QtCGMaya.QLineEdit('', self)
        #     self.errorText.setStyleSheet("color: red;")
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
        # if self.errorFlag:
        #     self.layout.addWidget(self.errorerrorTextLabel, 3, 0, 1, 1)
        #     self.layout.addWidget(self.errorText, 3, 1, 1, 6)
        self.row_Hbox1.setLayout(self.layout)

        self.row_Hbox2 = QtCGMaya.QGroupBox()
        self.layout = QtCGMaya.QGridLayout()
        self.layout.addWidget(self.button1, 0, 0)
        self.layout.addWidget(self.button2, 0, 1)
        self.row_Hbox2.setLayout(self.layout)

        self.main_layout.addWidget(self.row_Hbox1, 0, 0, 3, 1)
        self.main_layout.addWidget(self.row_Hbox2, 4, 0, 1, 1)
        self.setLayout(self.main_layout)

        self.setGeometry(0, 0, 500, 200)
        #self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onTeamSelect(self, n):
        pass

    def onLogin(self):
        teamName = self.teamList[self.teamBox.currentIndex()]['name']
        message = self.service.login(self.nameText.text(), self.passText.text(), teamName)
        #CGMaya_config.logger.info("login = %b, %s\r" % (result, message))
        if len(message) > 0:
            CGMaya_config.logger.error('login Error: : %s(%s, %s, %s)\r' % (message, teamName,
                                                            self.nameText.text(), self.passText.text()))
            QtCGMaya.QMessageBox.information(CGMaya_common.maya_main_window(),
                                             u"错误信息", message, QtCGMaya.QMessageBox.Yes)
            #self.errorFlag = True
            #self.errorText.setText(message)
            return
        CGMaya_config.teamName = teamName
        CGMaya_config.userName = self.nameText.text()
        CGMaya_config.password = self.passText.text()
        CGMaya_config.logger.info("login Success...\r")
        CGMaya_config.logger.setUserName(CGMaya_config.userName)
        CGMaya_config.logger.server('', '', '', CGMaya_config.CGMaya_Action_LoginSucessful)
        self.CGMenu.menu.setEnable(True)
        self.CGMenu.menuLogin()
        self.close()
        CGMaya_config.selectedProjectName = ''
        if not CGMaya_config.storageDir or not CGMaya_config.assetStorageDir or \
                    not os.path.exists(CGMaya_config.storageDir) or not os.path.exists(CGMaya_config.assetStorageDir):
            win = CGMaya_setup.setupWindow(self.service)
            win.show()

    def onCancel(self):
        self.CGMenu.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        self.CGMenu.menu.setEnable(True)
        event.accept()


class aboutWindow(QtCGMaya.QDialog):
    def __init__(self, service, menu, parent=CGMaya_common.maya_main_window()):
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
        #textFont = QtGui.QFont("song", 14, QtGui.QFont.Normal)
        message = u'视觉云（北京）科技有限公司\nCopyright @2016-2020\n版本 ：' + CGMaya_config.softwareVersion
        self.copyRightLabel = QtCGMaya.QLabel(message, self)
        #self.copyRightLabel.setFont(textFont)
        self.copyRightLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.copyRightLabel, 0, 1, 3, 1)

        if CGMaya_config.isLogin:
            temaInfo = self.service.getTeamInfo(CGMaya_config.teamName)
            self.teamLabel = QtCGMaya.QLabel(u'团队: ' + CGMaya_config.teamName +
                                             '(' + temaInfo['alias'] + ')', self)
            #self.teamLabel.setFont(textFont)
            self.teamLabel.setAlignment(QtCore.Qt.AlignCenter)
            self.userLabel = QtCGMaya.QLabel(u'用户: ' + CGMaya_config.userName +
                                            '(' + CGMaya_config.userAlias + ')', self)
            #self.userLabel.setFont(textFont)
            self.userLabel.setAlignment(QtCore.Qt.AlignCenter)

            self.layout.addWidget(self.teamLabel, 4, 1, 1, 1)
            self.layout.addWidget(self.userLabel, 5, 1, 1, 1)
            line = 6
        else:
            line = 4

        if CGMaya_config.lang == 'zh':
            self.button2 = QtCGMaya.QPushButton(u'关闭', self)
        else:
            self.button2 = QtCGMaya.QPushButton(u'Close', self)

        self.layout.addWidget(self.button2, line, 1, 1, 1)
        self.button2.clicked.connect(self.onClose)

        self.row_Hbox.setLayout(self.layout)
        self.main_layout.addWidget(self.row_Hbox)


        self.setLayout(self.main_layout)
        if CGMaya_config.lang == 'zh':
            self.setWindowTitle(u'关于插件CGMaya')
        else:
            self.setWindowTitle(u'About CGMaya')
        self.setGeometry(0, 0, 500, 200)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtCGMaya.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def onClose(self):
        self.menu.setEnable(True)
        self.close()

    def closeEvent(self, event):
        # do stuff
        self.menu.setEnable(True)
        event.accept() # let the window close