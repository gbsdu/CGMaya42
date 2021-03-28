import inspect
import maya.OpenMaya as OpenMaya
import maya.OpenMayaMPx as OpenMayaMPx
import maya.cmds as cmds
import maya.mel as mel
import os
import sys
import time

_kPluginName = "RWingForMaya"

pluginDir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
sys.path.append(pluginDir)
sys.path.append(os.path.join(pluginDir, "renderer"))

# Import modules for renderer, settings, material, lights and volumes
from renderer import (
    RWingRenderSettings,
    RWingRenderer)
import RWingRendererIO

from materials import (
    bump,
    blendbsdf,
    coating,
    conductor,
    dielectric,
    difftrans,
    diffuse,
    mask,
    mixturebsdf,
    phong,
    plastic,
    roughcoating,
    roughconductor,
    roughdielectric,
    roughdiffuse,
    roughplastic,
    thindielectric,
    twosided,
    ward,
    irawan,
    hk,
    dipole)

from textures import (
    checkerboard,
    dots,
    fbm,
    gridtexture,
    marble,
    wrinkled,
    windy,
    uv,
    wireframe,
    scale,
    wood,
    brick,
    mix)

from lights import (
    envmap,
    sunsky,
    arealight)

from volumes import (
    homogeneous,
    heterogeneous)

global rendererModules
global generalNodeModules
global materialNodeModules

rendererModules = [
    RWingRenderer]

generalNodeModules = [
    RWingRenderSettings]

materialNodeModules = [
    # materials
    bump,
    blendbsdf,
    coating,
    conductor,
    dielectric,
    difftrans,
    diffuse,
    mask,
    mixturebsdf,
    phong,
    plastic,
    roughcoating,
    roughconductor,
    roughdielectric,
    roughdiffuse,
    roughplastic,
    thindielectric,
    twosided,
    ward,
    irawan,
    hk,
    dipole,
    #textures
    checkerboard,
    dots,
    fbm,
    gridtexture,
    marble,
    wrinkled,
    windy,
    uv,
    wireframe,
    scale,
    wood,
    brick,
    mix,
    # lights
    envmap,
    sunsky,
    arealight,
    # volumes
    homogeneous,
    heterogeneous]

# Initialize the script plug-in
def initializePlugin(mobject):
    global rendererModules
    global generalNodeModules
    global materialNodeModules

    mplugin = OpenMayaMPx.MFnPlugin(mobject)

    # Load needed plugins
    try:
        if not cmds.pluginInfo( "objExport", query=True, loaded=True ):
            cmds.loadPlugin("objExport" )
        print( "%s - Loaded plugin       : %s" % (_kPluginName, 'objExport'))
    except:
            sys.stderr.write( "Failed to load objExport plugin\n" )
            raise

    try:
        if not cmds.pluginInfo( "OpenEXRLoader", query=True, loaded=True ):
            cmds.loadPlugin( "OpenEXRLoader" )
        print( "%s - Loaded plugin       : %s" % (_kPluginName, 'OpenEXRLoader'))
    except:
            sys.stderr.write( "Failed to load OpenEXRLoader plugin\n" )
            raise

    # Register general nodes
    try:
        for generalNodeModule in generalNodeModules:
            mplugin.registerNode( generalNodeModule.kPluginNodeName, 
                generalNodeModule.kPluginNodeId, 
                generalNodeModule.nodeCreator, 
                generalNodeModule.nodeInitializer, 
                OpenMayaMPx.MPxNode.kDependNode )
            print( "%s - Registered node     : %s" % (_kPluginName, generalNodeModule.kPluginNodeName))
    except:
            sys.stderr.write( "%s - Failed to register node: %s\n" % (_kPluginName, generalNodeModule.kPluginNodeName) )
            raise

    # Register Materials / Volumes / Lights
    try:
        for materialNodeModule in materialNodeModules:
            mplugin.registerNode( materialNodeModule.kPluginNodeName, 
                materialNodeModule.kPluginNodeId, 
                materialNodeModule.nodeCreator, 
                materialNodeModule.nodeInitializer, 
                OpenMayaMPx.MPxNode.kDependNode, 
                materialNodeModule.kPluginNodeClassify )

            RWingRenderer.registMaterialNodeType(materialNodeModule.kPluginNodeName)

            print( "%s - Registered material : %s" % (_kPluginName, materialNodeModule.kPluginNodeName) )
    except:
            sys.stderr.write( "%s - Failed to register node: %s\n" % (_kPluginName, materialNodeModule.kPluginNodeName) )
            raise

    # Register Renderer commands
    for rendererModule in rendererModules:
        try:
            mplugin.registerCommand( rendererModule.kPluginCmdName, rendererModule.cmdCreator )
            print( "%s - Registered command  : %s" % (_kPluginName, rendererModule.kPluginCmdName) )
        except:
            sys.stderr.write( "%s - Failed to register command: %s\n" % (_kPluginName, rendererModule.kPluginCmdName) )
            raise

    # Register Renderers
    for rendererModule in rendererModules:
        try:
            rendererModule.registerRenderer()
            print( "%s - Registered renderer : %s" % (_kPluginName, rendererModule.kPluginCmdName) )
        except:
            sys.stderr.write( "%s - Failed to register renderer: %s\n" % (_kPluginName, rendererModule.kPluginCmdName) )
            raise

# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    global rendererModules
    global materialNodeModules
    global generalNodeModules

    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    for rendererModule in rendererModules:
        try:
            cmds.renderer(rendererModule.kPluginCmdName, edit=True, unregisterRenderer=True)
        except:
            sys.stderr.write( "Failed to unregister renderer: %s\n" % _kPluginName )

        try:
            mplugin.deregisterCommand( _kPluginName )
        except:
            sys.stderr.write( "Failed to unregister command: %s\n" % _kPluginName )

    # Unregister materials
    try:
        for materialNodeModule in materialNodeModules:
            mplugin.deregisterNode( materialNodeModule.kPluginNodeId )
    except:
            sys.stderr.write( "Failed to deregister node: %s\n" % materialNodeModule.kPluginNodeName )
            raise

    # Unregister general nodes
    try:
        for generalNodeModule in generalNodeModules:
            mplugin.deregisterNode( generalNodeModule.kPluginNodeId )
    except:
            sys.stderr.write( "Failed to deregister node: %s\n" % generalNodeModule.kPluginNodeName )
            raise

