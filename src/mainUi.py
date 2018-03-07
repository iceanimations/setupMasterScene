'''
Created on Aug 27, 2015

@author: qurban.ali
'''

from uiContainer import uic
from PyQt4.QtGui import QMessageBox, QRadioButton, QFileDialog, qApp, QCheckBox
from PyQt4.QtCore import Qt
import qtify_maya_window as qtfy
import os
osp = os.path
import qutil
reload(qutil)
import msgBox
import cui
reload(cui)
import pymel.core as pc
#import backend
#reload(backend)
from backend import managers, utilities as utils
reload(managers)
reload(utils)
import imaya
reload(imaya)
import appUsageApp
reload(appUsageApp)
from collections import OrderedDict
import pymel.core as pc

import login
reload(login)
import auth.user as user

pathKey = 'setupMasterScene_shotsPathKey'
resolution_key = 'setupMasterScene_resolutionKey'
uiPath = osp.join(qutil.dirname(__file__, 2), 'ui')
title = 'Setup Master Scene'

Form, Base = uic.loadUiType(osp.join(uiPath, 'main.ui'))
class MainUi(Form, Base):
    def __init__(self, parent=qtfy.getMayaWindow()):
        super(MainUi, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        
        path = qutil.getOptionVar(pathKey)
        if path:
            self.lastPath = path
            self.shotsPathBox.setText(path)
        else:
            self.lastPath = ''
            
        self.cm = None
        
        self.resolutions = OrderedDict()
        self.resolutions['320x240'] = [320, 240, 1.333]
        self.resolutions['640x480'] = [640, 480, 1.333]
        self.resolutions['960x540'] = [960, 540, 1.777]
        self.resolutions['1280x720'] = [1280, 720, 1.777]
        self.resolutions['1920x1080'] = [1920, 1080, 1.777]

        self.resolutionBox.activated.connect(self.resolutionBoxActivated)
        self.startButton.clicked.connect(self.start)
        self.browseButton.clicked.connect(self.setShotsPath)
        self.addAssetsButton.clicked.connect(self.addAssets)
        self.fresnelButton.clicked.connect(self.customFeature_suntopFresnel)
        
        self.label.hide()
        self.shotsPathBox.hide()
        self.browseButton.hide()
        
        self.setupWindow()
        
        appUsageApp.updateDatabase('setupMasterScene')
        
    def isEnvOcc(self):
        return self.envOccButton.isChecked()
    
    def isContactShadow(self):
        return self.contactShadowButton.isChecked()
    
    def isOcc(self):
        return self.occButton.isChecked()
        
    def addAssets(self):
        if not user.user_registered():
            if not login.Dialog().exec_():
                return
        import addAssets
        reload(addAssets)
        addAssets.Window(self).show()
        
    def resolutionBoxActivated(self):
        qutil.addOptionVar(resolution_key, self.resolutionBox.currentText())
        
    def setupWindow(self):
        # load redshift
        try:
            utils.loadRedshift()
        except Exception as ex:
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
        # setup the resolution box
        self.resolutionBox.addItems(self.resolutions.keys())
        val = qutil.getOptionVar(resolution_key)
        if val:
            for i in range(self.resolutionBox.count()):
                text = self.resolutionBox.itemText(i)
                if text == val:
                    self.resolutionBox.setCurrentIndex(i)
                    break
    
    def getResolution(self):
        return self.resolutions[self.resolutionBox.currentText()]
        
    def setShotsPath(self):
        path = QFileDialog.getExistingDirectory(self, title, self.lastPath, QFileDialog.ShowDirsOnly)
        if path:
            self.shotsPathBox.setText(path)
            self.lastPath = path
            qutil.addOptionVar(pathKey, path)

    def closeEvent(self, event):
        self.deleteLater()

    def showMessage(self, **kwargs):
        return msgBox.showMessage(self, title=title, **kwargs)
    
    def setStatus(self, msg):
        if 'Warning:' in msg:
            msg = '<span style="color: orange;">'+ msg.replace('Warning:', '<b>Warning:</b>') + '<span>'
        self.statusBox.append(msg)
        qApp.processEvents()

    def getGroup(self, name):
        group = pc.ls(name)
        if group:
            if len(group) > 1:
                sb = cui.SelectionBox(self, [QRadioButton(x.name(), self) for x in group], msg='Multiple %s Groups found, please select one'%name.capitalize())
                if sb.exec_():
                    group = sb.getSelectedItems()
                else:
                    return
        else:
            return
        return pc.PyNode(group[0])
    
    def start(self):
        try:
            groupNames = []
            self.statusBox.clear()
            env = self.getGroup('environment')
            if not env:
                groupNames.append('environment')
            chars = self.getGroup('characters')
            if not chars:
                groupNames.append('characters')
            env_lights = self.getGroup('env_lights')
            if not env_lights:
                groupNames.append('Env_lights')
            char_lights = self.getGroup('char_lights')
            if not char_lights:
                groupNames.append('char_lights')
            if groupNames:
                btn = self.showMessage(msg='Could not find following groups\n'+
                                       ', '.join(groupNames),
                                       ques='Do you want to continue?',
                                       icon=QMessageBox.Question,
                                       btns=QMessageBox.Yes|QMessageBox.No)
                if btn == QMessageBox.Yes:
                    if not env_lights: env_lights = None
                    if not char_lights: char_lights = None
                    imaya.switchToMasterLayer()
                    if env:
                        em = managers.EnvManager(self, env, env_lights, char_lights)
                        self.setStatus('Creating Redshift Parameter Sets for environment')
                        em.setupParameterSets()
                    if chars:
                        self.cm = managers.CharManager(self, chars, char_lights, env_lights)
                        self.setStatus('Creating Redshift Parameters Sets for characters')
                        self.cm.setupParameterSets()
                        self.setStatus('Applying orbitrary cache to generate DeformedShape nodes')
                        self.cm.createDeformedShapeNodes()
                        self.setStatus('Creating object and material IDs')
                        self.cm.createObjectIds()
                    if env:
                        self.setStatus('Creating Environment layers')
                        em.createEnvLayers()
                    if chars:
                        self.setStatus('Creating character layers')
                        self.cm.createCharLayers()
                    if env:
                        self.setStatus('Creating material override for environment on Contact shadow layer')
                        em.createMtlOverride()
                    utils.setResolution(self.getResolution())
                    utils.turnMasterLayerOff()
                    self.setStatus('DONE...')
        except Exception as ex:
            self.showMessage(msg=str(ex), icon=QMessageBox.Critical)
        finally:
            self.setStatus('')
            
    def customFeature_suntopFresnel(self):
        if self.cm:
            self.setStatus('Creating suntop_fresnel layer')
            self.cm.customFeature_SuntopFresnel()
            self.setStatus('DONE...')
        else:
            self.showMessage(msg='This feature will only work right after creating other layers, without closing \'Setup Master Scene\'',
                             icon=QMessageBox.Information)