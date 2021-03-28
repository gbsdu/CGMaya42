import logging


myRootURL = "http://211.87.224.166:3600"
teamName = ''  #RC-Team
teamInfo = []
userToken = {}
userName = ''
password = ''
userRole = ''
userAlias = ''
myDAMURL = ''
lang = 'zh'

tmpStorageDir = ''
sysStorageDir = ''
storageDir = ''
assetStorageDir = ''
isLogin = False

config = None
ConfigFileName = 'CGMaya.ini'
teamConfigFileName = 'CGTeam.ini'
swapConfigFileName = 'CGSwap.ini'
ConfigFileName_user = ''

IPFSUrl = '192.168.1.2:5002'
softwareVersion = '4.00'

monthInfo = {}

logger = None
logMaxBytes = 10 * 1024
logBackupCount = 3
logLevel = logging.DEBUG
logFileLevel = logging.DEBUG
logConsoleLevel = logging.DEBUG


loggerFilePath = 'CGMayaLogger.log'


currentTask = {}
currentTaskName = ''
currentTaskID = ''
currentProject = {}
currentProjectName = ''

dynamicStorageFlag = True
workDir = "e:\\temp"

DLLFile_window = 'CGMaya/processMaya.dll'
DLLFile_Darwin = 'CGMaya/libMaya.so'
pidFileName = 'CGC.pid'

changeReferenceModelList = []

nukePath = 'C:/Program Files/Nuke9.0v1/Nuke9.0.exe'
nukeScriptPath = 'D:/CGNuke'

mariPath = 'C:/Program Files/Mari2.6v2/Bundle/bin/Mari2.6v2.exe'

fileID = ''

renderWingFlag = False

renderSettingsSave = None

block_size = 4 * 1024 * 1024

project_Dir = 'projects'
icon_Dir = 'icon'

CGMaya_Texture_Dir = 'texture'
CGMaya_Log_Dir = 'log'
CGMaya_Hdr_Dir = 'GeneralLighting'
CGMaya_Submit_Dir = 'submitFile'
CGMaya_Return_Dir = 'returnFile'
CGMaya_Light_Dir = 'light'
CGMaya_Shot_Dir = 'ShotDir'
CGMaya_Output_Dir = 'output'
CGMaya_Audio_Dir = 'AudioDir'
CGMaya_CacheFile_Dir = 'CacheFileDir'
CGMaya_AbcFile_Dir = 'AbcFileDir'
CGMaya_plugin_Dir = 'maya_plugin'
CGMaya_RenderWing_Dir = 'renderwing'
CGMaya_Tmp_Dir = 'tmp'

CGMaya_Action_LoginSucessful = 'loginSucessful'
CGMaya_Action_LoginFailed = 'loginFailed'
CGMaya_Action_Logout = 'logout'
CGMaya_Action_New = 'new'
CGMaya_Action_Open = 'open'
CGMaya_Action_Save = 'save'
CGMaya_Action_Submit = 'submit'
CGMaya_Action_SaveAs = 'saveAs'
CGMaya_Action_Replace = 'replace'
CGMaya_Action_Reference = 'reference'
CGMaya_Action_Import = 'import'
CGMaya_Action_LoadPlugin = 'loadplugin'
CGMaya_Action_UploadPlugin = 'uploadplugin'
CGMaya_Action_RenderJob = 'renderJob'
CGMaya_Action_SubmitRenderJob = 'submitRenderJob'
CGMaya_Action_ClearBuffer = 'clearBuffer'
CGMaya_Action_Setup = 'setup'
CGMaya_Action_About = 'about'
CGMaya_Action_UpdateSoftware = 'updateSoftware'

selectedProjectName = ''
refProjectName = 'Model'
parentProjectID = ''
sceneName = ''
assetExtFileName = ''
lightName = ''
lightAsset = {}
sceneName_suffix = 'ma'
project = {}
taskIndex = 0
currentAsset = ''

mouseCount = 0
saveFlag = False
loadFlag = True
versionURL = ''
assetDescription = ''
refCount = 1
refAssetIDList = []
assetID = ''
taskFileID = ''
lightRefFlag = False
lightFileFlag = False
currentShot = {}
lightRefFlag = True
singleOutputPath = ''

logFileExt = '.ini'
lockFileExt = '.lock'
iconLogFileExt = '.ini'
currentDialog = None

MariCommand = "C:/Program Files/Mari2.6v2/Bundle/bin/Mari2.6v2.exe"
MariObjFileName = 'e:/temp/mari.obj'

textureDirClass = True
# True: one model have TextureDir
# False: one Project have textureDir

IconFlag = False
IconWidth = 128
IconHeight = 128
movWidth = 640
movHeight = 480
movFileName = ''
layoutScale = '1'
layoutQuality = '100'
frameList = ''
defaultStartFrame = 101
defaultEndFrame = 201
singleFrame = ''

processMayaDLLPath = 'CGMaya/processMaya.dll'
processMayaDLL = None

clipboard = ''
specialMimeType = "application/x-qt-windows-mime;value=\"FileNameW\""


softInfo = {}
userPhotoInfo = {}
menuTitle = 'CGMenu'
stereoFlag = False
textureReadFlag = True

fileEXTNameList = ['.tif', '.jpg', '.bmp', '.png', '.exr', '.iff', '.JPG']

successfulReadMayaFile = True
currentDlg = None

camParaFileName = 'camPara.ini'