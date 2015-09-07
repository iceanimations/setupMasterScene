'''
Created on Aug 28, 2015

@author: qurban.ali
'''
import pymel.core as pc
from PyQt4.QtGui import QMessageBox
import utilities as utils
reload(utils)
import imaya
reload(imaya)

cacheFilePath = "R:/Pipe_Repo/Users/Qurban/extras/onions_rig_onions_geo_set_cache.xml"

env_matte_set = None
env_vis_set = None
rsIncandescent = None
env_layer = None

class Manager(object):
    def __init__(self, parent=None, group=None):
        super(Manager, self).__init__()
        self.parentWin = parent
        self.group = group
        self.meshes = []
        
        self.setMeshes()
        
    def setStatus(self, msg):
        if self.parentWin:
            self.parentWin.setStatus(msg)
            
    def setMeshes(self):
        self.setStatus('Extracting %s meshes'%self.group.name().capitalize())
        meshes = self.group.getChildren()
        badMeshes = []
        for mesh in meshes:
            if type(mesh) == pc.nt.Transform:
                meshShape = mesh.getShape(ni=True)
                if not meshShape:
                    meshShape = pc.ls(mesh, type='mesh', dag=True)
                    if not meshShape:
                        badMeshes.append(mesh)
                self.meshes.append(mesh)
        if badMeshes:
            s = 'es' if len(badMeshes) > 1 else ''
            self.setStatus('Warning: Shape node not found for %s mesh%s'%(len(badMeshes), s))
            for i, mesh in enumerate(badMeshes):
                self.setStatus('%s: %s'%(i+1, mesh.name()))
            
class EnvManager(Manager):
    def __init__(self, parent=None, envGroup=None, envLights=None, charLights=None):
        super(EnvManager, self).__init__(parent, envGroup)
        
        self.lightsGroup = envLights
        self.envLights = []
        self.charLights = []
        if charLights:
            for light in charLights.getChildren():
                self.charLights.append(light)
        
        self.setEnvLights()
        
    def setEnvLights(self):
        if self.lightsGroup:
            for light in self.lightsGroup.getChildren():
                self.envLights.append(light)
                
    def setupParameterSets(self):
        global env_matte_set
        global env_vis_set
        try:
            # create Redshift mesh parameter set
            if self.meshes:
                utils.createRedshiftMeshParameterSet([], 'Env_Smooth_Set')
                
                #TODO: How to identify the lights?
                #TODO: Put the identified lights in a group named env_lights
                
                env_matte_set = utils.createRedshiftMatteParameterSet(self.meshes, 'Env_Matte_Set')
                env_vis_set = utils.createRedshiftVisibilityParameterSet(self.meshes, 'Env_Vis_Set')
        except Exception as ex:
            self.setStatus('Warning: '+str(ex))
            
    def createEnvLayers(self):
        global rsIncandescent
        global env_layer
        if self.meshes or self.envLights:
            # create env layer
            env_layer = pc.createRenderLayer(self.meshes + self.envLights, name="Env", noRecurse=True, makeCurrent=True)
            # hide char lights
            if self.charLights:
                pc.select(self.charLights[0].firstParent())
                pc.mel.HideSelectedObjects()
            # turn char related aovs off
            for aov in pc.ls(type=pc.nt.RedshiftAOV):
                if aov.aovType.get() == 'Puzzle Matte':
                    pc.editRenderLayerAdjustment(aov.enabled)
                    aov.enabled.set(0)
            # create env_occ layer
            env_occ = pc.duplicate(env_layer, name='Env_Occ', inputConnections=True)[0]
            pc.editRenderLayerGlobals(currentRenderLayer=env_occ)
            # create rsAmbient_occ and rsIncandescent
            rsIncandescent = imaya.createShadingNode('RedshiftIncandescent')
            rsAmbientOcc = pc.shadingNode("RedshiftAmbientOcclusion", asShader=True)
            rsAmbientOcc.outColor.connect(rsIncandescent.color, f=True)
            rsAmbientOcc.maxDistance.set(15)
            rsAmbientOcc.numSamples.set(64)
            pc.rename(rsIncandescent, 'AO_Shader')
            pc.mel.hookShaderOverride(env_occ, "", rsIncandescent)
            # turn off all the aovs
            for aov in pc.ls(type=pc.nt.RedshiftAOV):
                pc.editRenderLayerAdjustment(aov.enabled)
                aov.enabled.set(0)
                
    def createMtlOverride(self):
        # create material override for env meshes on contact shadow to assing AO_Shader
        if rsIncandescent:
            sg = rsIncandescent.outColor.outputs()[0]
            pc.sets(sg, e=True, fe=self.meshes)
        for aov in pc.ls(pc.nt.RedshiftAOV):
            pc.editRenderLayerAdjustment(aov.enabled)
            aov.enabled.set(0)

class CharManager(Manager):
    def __init__(self, parent=None, charGroup=None, char_lights=None, env_lights=None):
        super(CharManager, self).__init__(parent, charGroup)
        
        self.char_visibility_set = None
        
        self.lightsGroup = char_lights
        self.charLights = []
        self.envLights = []
        if env_lights:
            for light in env_lights.getChildren():
                self.envLights.append(light)
        
        self.setCharLights()
        
    def setCharLights(self):
        if self.lightsGroup:
            for light in self.lightsGroup.getChildren():
                self.charLights.append(light)
                
    def setupParameterSets(self):
        try:
            utils.createRedshiftMeshParameterSet(self.meshes, 'Char_Smooth_Set')
            utils.createRedshiftMatteParameterSet(self.meshes, 'Char_Matte_Set')
            self.char_visibility_set = utils.createRedshiftVisibilityParameterSet(self.meshes, 'Char_Vis_Set')
        except Exception as ex:
            self.setStatus('Warning: '+str(ex))
        
    def createDeformedShapeNodes(self):
        for mesh in self.meshes:
            self.setStatus('Applying to <b>%s</b>'%mesh.name())
            try:
                imaya.applyCache(mesh, cacheFilePath)
                imaya.deleteCache(mesh)
            except Exception as ex:
                self.setStatus('Warning: %s'%str(ex))
                
    def createObjectIds(self):
        pc.select(self.meshes)
        utils.createRedshiftAOVs()
        
    def createCharLayers(self):
        # override enable env_matte_set
        if env_layer:
            char_layer = pc.duplicate(env_layer, name='Char', inputConnections=True)[0]
            pc.editRenderLayerGlobals(currentRenderLayer=char_layer)
            # show charLights which was hidden in env and env_occ layers
            if self.charLights:
                pc.select(self.charLights[0].firstParent())
                pc.mel.ShowSelectedObjects()
            pc.editRenderLayerMembers(char_layer, self.meshes, noRecurse=True)
            if env_matte_set:
                pc.editRenderLayerAdjustment(env_matte_set.matteEnable)
                env_matte_set.matteEnable.set(1)
                pc.editRenderLayerAdjustment(env_matte_set.matteAlpha)
                env_matte_set.matteAlpha.set(0)
            # turn puzzle matte aovs on
            for aov in pc.ls(type=pc.nt.RedshiftAOV):
                if aov.aovType.get() == 'Puzzle Matte':
                    pc.editRenderLayerAdjustment(aov.enabled)
                    aov.enabled.set(1)
            # create shadow layer
            shadow_layer = pc.duplicate(char_layer, name='Shadow', inputConnections=True)[0]
            pc.editRenderLayerGlobals(currentRenderLayer=shadow_layer)
            if self.char_visibility_set:
                pc.editRenderLayerAdjustment(self.char_visibility_set.primaryRayVisible)
                # turn the primary visibility off for the characters
                self.char_visibility_set.primaryRayVisible.set(0)
            # turn the env_matte on for shadow
            if env_matte_set:
                pc.editRenderLayerAdjustment(env_matte_set.matteEnable)
                env_matte_set.matteEnable.set(1)
                # enable the shadow and affect_alpha on env_matte_set for shadow
                pc.editRenderLayerAdjustment(env_matte_set.matteShadowEnable)
                env_matte_set.matteShadowEnable.set(1)
                pc.editRenderLayerAdjustment(env_matte_set.matteShadowAffectsAlpha)
                env_matte_set.matteShadowAffectsAlpha.set(1)
                pc.editRenderLayerAdjustment(env_matte_set.matteAlpha)
                env_matte_set.matteAlpha.set(1)
            # turn cast shadows off
            if env_vis_set:
                pc.editRenderLayerAdjustment(env_vis_set.shadowCaster)
                env_vis_set.shadowCaster.set(0)
            # turn all the aovs Off
            for aov in pc.ls(type=pc.nt.RedshiftAOV):
                pc.editRenderLayerAdjustment(aov.enabled)
                aov.enabled.set(0)
            # create the contact shadow layer
            contact_layer = pc.duplicate(shadow_layer, name='ContactShadow', inputConnections=True)[0]
            pc.editRenderLayerGlobals(currentRenderLayer=contact_layer)
            # hide env and char lights
            if self.charLights:
                pc.select(self.charLights[0].firstParent())
                pc.mel.HideSelectedObjects()
            if self.envLights:
                pc.select(self.envLights[0].firstParent())
                pc.mel.HideSelectedObjects()
            # disable the env_matte for contact shadow
            if env_matte_set:
                pc.editRenderLayerAdjustment(env_matte_set.matteEnable)
                env_matte_set.matteEnable.set(0)
            if env_vis_set:
                pc.editRenderLayerAdjustment(env_vis_set.aoCaster)
                env_vis_set.aoCaster.set(0)