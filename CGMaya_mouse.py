#coding=utf-8

import sys, os
from ctypes import *
import maya.cmds as cmds
import maya.mel as mel

import CGMaya_config


class mousePoint(object):
    def __init__(self):
        CGMaya_config.mouseCount = 0
        if cmds.draggerContext('Context', exists=True):
            cmds.deleteUI('Context')
        cmds.draggerContext('Context', pressCommand=self.onPress, dragCommand=self.onDrag,
                            releaseCommand=self.onRelease,
                            name='Context', space='world')
        cmds.setToolTo('Context')

    def onPress(self, *args):
        self.anchorPoint = cmds.draggerContext('Context', query=True, anchorPoint=True)
        CGMaya_config.mouseCount = CGMaya_config.mouseCount + 1
        #print 'mouseCount =', CGMaya_config.mouseCount

    def onDrag(self, *args):
        # pass
        self.dragPoint = cmds.draggerContext('Context', query=True, dragPoint=True)
        #print 'anchorPoint =', self.dragPoint

    def onRelease(self, *args):
        self.releasePoint = cmds.draggerContext('Context', query=True, dragPoint=True)
        #print ' releasePoint =', self.releasePoint




