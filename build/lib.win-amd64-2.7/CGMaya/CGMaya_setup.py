#coding=utf-8
import os
import sys
import shutil

print sys.argv
if len(sys.argv) == 3:
	srcPath = sys.argv[1]
	destPath = sys.argv[2]

	destPath1 = os.path.join(destPath, 'CGMaya')
	if not os.path.exists(destPath1):
		os.mkdir(destPath1)
	fileList = os.listdir(srcPath)
	for file in fileList:
		filePath = srcPath + '/' + file
		destFile = destPath1 + '/' + file
		if os.path.isdir(filePath):
			shutil.copytree(filePath, destFile)
		else:
			shutil.copy(filePath, destFile)

	bakNums = 1
	print destPath + 'userSetup.mel'
	if os.path.exists(destPath + 'userSetup.mel'):
		while os.path.exists(destPath + 'userSetup' + str(bakNums) + '.mel'):
			bakNums = bakNums + 1
		shutil.copy(destPath + 'userSetup.mel', destPath + 'userSetup' + str(bakNums) + '.mel')
	shutil.copy(srcPath + '/usersetup.mel', destPath + '/userSetup.mel')



