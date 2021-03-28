#coding=utf-8
import os
import logging
import logging.config
import time

import CGMaya_config


class Logger:
    def __init__(self, service, logFileName, loggerName):
        self.service = service
        self.userName = ''
        self.projectName = ''
        logname = logFileName + '.log'
        logFileDir = os.path.join(CGMaya_config.sysStorageDir, 'log')
        if not os.path.isdir(logFileDir):
            os.mkdir(logFileDir)

        self.logFilePath = os.path.join(logFileDir, logname)
        self.logger = logging.getLogger(loggerName)
        self.logger.setLevel(CGMaya_config.logLevel)

        self.file_handler = logging.handlers.RotatingFileHandler(self.logFilePath,
                            maxBytes=CGMaya_config.logMaxBytes, backupCount=CGMaya_config.logBackupCount)

        self.file_handler.setLevel(CGMaya_config.logFileLevel)
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(CGMaya_config.logConsoleLevel)

        formatter = logging.Formatter('%(asctime)s-%(name)s-%(levelname)s::%(message)s')
        self.file_handler.setFormatter(formatter)
        self.console_handler.setFormatter(formatter)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
        self.logger.info(u"CGMaya Begin--------------------------------------------------------------")
        self.logger.info(u"logFilePath =%s\r" % self.logFilePath)
        #self.logger.removeHandler(file_handler)
        #self.logger.removeHandler(console_handler)

    def __del__(self):
        self.logger.info(u"CGMaya End--------------------------------------------------------------")

    def get(self):
        return self.logger

    def set(self, loggerName):
        self.logger = logging.getLogger(loggerName)
        self.logger.addHandler(self.file_handler)
        self.logger.addHandler(self.console_handler)
        return self.logger

    def setUserName(self, userName):
        self.UserName = userName

    def info(self, str1):
        self.logger.info(str1)

    def waring(self, str1):
        self.logger.waring(str1)

    def debug(self, str1):
        self.logger.debug(str1)

    def error(self, str1):
        self.logger.error(str1)

    def server(self, projectName, taskName, taskID, action):
        self.service.userActionLog(self.UserName, projectName, taskName, taskID, action)

