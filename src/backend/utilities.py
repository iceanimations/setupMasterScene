'''
Created on Aug 28, 2015

@author: qurban.ali
'''
import pymel.core as pc
import sys
import imaya

sys.path.insert(0, r"R:\Pipe_Repo\Users\Hussain\utilities\loader\command\python")

import RedshiftAOVTools as rsTools
reload(rsTools)

def loadRedshift():
    if not pc.pluginInfo('redshift4maya', q=True, loaded=True):
        pc.loadPlugin('redshift4maya')
    if pc.getAttr('defaultRenderGlobals.currentRenderer') != 'redshift':
        pc.setAttr('defaultRenderGlobals.currentRenderer', 'redshift')

def createRedshiftMeshParameterSet(meshes, name):
    pc.select(meshes)
    node = pc.PyNode(pc.mel.redshiftCreateMeshParametersNode2())
    pc.rename(node, name)

def createRedshiftMatteParameterSet(meshes, name):
    pc.select(meshes)
    node = pc.PyNode(pc.mel.redshiftCreateMatteParametersNode2())
    node.matteEnable.set(0)
    pc.rename(node, name)
    return node

def createRedshiftVisibilityParameterSet(meshes, name):
    pc.select(meshes)
    node = pc.PyNode(pc.mel.redshiftCreateVisibilityNode2())
    pc.rename(node, name)
    return node
    
def createRedshiftAOVs():
    for func in [rsTools.addPasses, rsTools.addMaterialIDs, rsTools.addObjectIDs,
                    rsTools.correctObjectID,
                    rsTools.fixAOVPrefixes]:
        func()
    pc.setAttr("redshiftOptions.imageFilePrefix", "<Camera>/<RenderLayer>/<RenderLayer>_<AOV>/<RenderLayer>_<AOV>_", type="string")
    pc.setAttr("redshiftOptions.imageFormat", 1)
    pc.setAttr("defaultRenderGlobals.animation", 1)
    #pc.setAttr("defaultRenderGlobals.enableDefaultLight", 0)
    
def setResolution(res):
    pc.setAttr('defaultResolution.width', int(res[0]))
    pc.setAttr('defaultResolution.height', int(res[1]))
    pc.setAttr('defaultResolution.deviceAspectRatio', float(res[2]))
    
def turnMasterLayerOff():
    for layer in imaya.getRenderLayers():
        if layer.name().lower().startswith('default'):
            layer.renderable.set(0)
            break
        
def turnGIOff():
    pc.editRenderLayerAdjustment("redshiftOptions.primaryGIEngine")
    pc.editRenderLayerAdjustment("redshiftOptions.secondaryGIEngine")
    pc.setAttr("redshiftOptions.primaryGIEngine", 0)
    pc.setAttr("redshiftOptions.secondaryGIEngine", 0)