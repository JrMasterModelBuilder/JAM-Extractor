"""
    JAM Extractor - LEGO Racers JAM extractor.

    Copyright (C) 2012-2013 JrMasterModelBuilder

    You accept full responsibility for how you use this program.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import sys

def extract(path):
    def uint32(offset):
        return fileData[offset] + (fileData[offset+1] * 256) + (fileData[offset+2] * 65536) + (fileData[offset+3] * 16777216)
    
    def listFolders(offset, number, folderPath):
        #List of folder to build.
        folderList = []
        #Read in data for the total number of folder.
        for i in range(number):
            #Add ascii bytes to the end of the path until we hit a null byte.
            name = folderPath
            for b in fileData[offset:offset+12]:
                if b == 0:
                    break
                name += chr(b)
            #Add the folder data to the array to return.
            folderList.append([name, uint32(offset + 12)])
            #Skip the offset forward for the next folder.
            offset += 16
        return folderList

    def listFiles(offset, number, folderPath):
        #List of files to build.
        fileList = []
        #Read in data for the total number of files.
        for i in range(number):
            #Add ascii bytes to the end of the path until we hit a null byte.
            name = folderPath + os.sep
            for b in fileData[offset:offset+12]:
                if b == 0:
                    break
                name += chr(b)
            #Add the file data to the array to return.
            fileList.append([name, uint32(offset + 12), uint32(offset + 16)])
            #Skip the offset forward for the next file.
            offset += 20
        return fileList
    
    def recurse(foldersList):
        folderList.extend(foldersList)
        for f in foldersList:
            #How many files are there?
            totalFiles = uint32(f[1])
            if totalFiles == 0:
                #That place has only folders, run this function again for the folders in that folder.
                recurse(listFolders(f[1]+8, uint32(f[1]+4), f[0] + os.sep))
            else:
                #That place has files, add them to the list to extract.
                fileList.extend(listFiles(f[1]+4, uint32(f[1]), f[0]))
                #This place may also have folders. Find place where folder count exists after file list ends.
                folderCountPos = totalFiles * 20 + f[1] + 4
                folderCount = uint32(folderCountPos)
                if folderCount > 0:
                    recurse(listFolders(folderCountPos + 4, folderCount, f[0] + os.sep))
    
    
    #Open the file and read it in.
    f = open(path, "rb")
    fileData = f.read()
    f.close()
    
    if len(fileData) < 4 or fileData[0:4] != b"LJAM":
        print("ERROR: Not a JAM file.")
        return False
    
    print("Extracting, please wait.")
    
    #Recurse through, creating a list of all the files.
    folderList = []
    fileList = []
    recurse([["", 4]])
    
    #Create output path from input path.
    if path[-4:].lower() == ".jam":
        outFolder = path[:-4] + "_JAM"
    else:
        outFolder = path + "_JAM"
    
    #Create the first non-existant folder to extract to.
    if os.path.exists(outFolder):
        i = 1
        while os.path.exists(outFolder + "_" + str(i)):
            i += 1
        outFolder = outFolder + "_" + str(i)
    
    os.makedirs(outFolder)
    
    #Create all the folders we need to extract to.
    for a in folderList:
        if a[0] == "":
            continue
        if not os.path.exists(outFolder + a[0]):
            os.makedirs(outFolder + a[0])
    
    #Loop through the list of files, saving them.
    for a in fileList:
        f = open((outFolder + a[0]), "wb")
        f.write(fileData[a[1]:a[1]+a[2]])
        f.close()
    
    print("COMPLETE: " + str(len(fileList)) + " files extracted.")
    return True

def build(path):
    def writeUint32(i = 0, position = -1):
        if i > 4294967295:
            i = 4294967295 #Keep it possible.
        a = [0, 0, 0, 0]
        #Roll it over to the next place until the end giving what's left to the first number.
        while i >= 16777216:
            a[3] += 1
            i -= 16777216
        while i >= 65536:
            a[2] += 1
            i -= 65536
        while i >= 256:
            a[1] += 1
            i -= 256
        a[0] = i
        #If position not set, add it to the end.
        if position < 0:
            fileData.extend(a)
        else:
            fileData[position:position+4] = a
    
    def writeName(s):
        for i in range(12):
            if i < len(s):
                fileData.append(ord(s[i]))
            else:
                fileData.append(0)
    
    def updateFolder(s):
        for a in folderList:
            if a[0] == s:
                writeUint32(len(fileData), a[1])
    
    print("Building, please wait.")
    
    #Start the byte array.
    fileData = bytearray(b"LJAM")
    #Create lists to store file and folder pointers to update later.
    folderList = []
    fileList = []
    
    for currentdir, dirlist, filelist in os.walk(path):
        #Update pointer to this folder if listed earlier.
        updateFolder(currentdir)
        #Write the number of files.
        writeUint32(len(filelist))
        #Lists files.
        for filename in filelist:
            #Write to index, remembering where to update pointers later.
            a = [currentdir + os.sep + filename, 0, 0]
            writeName(filename)
            a[1] = len(fileData)
            writeUint32()
            a[2] = len(fileData)
            writeUint32()
            fileList.append(a)
        #Write the number of folders.
        writeUint32(len(dirlist))
        #Lists directories.
        for subdirname in dirlist:
            #Write to index, remembering where to update pointers later.
            a = [currentdir + os.sep + subdirname, 0]
            writeName(subdirname)
            a[1] = len(fileData)
            writeUint32()
            folderList.append(a)
    
    #Append the files and update pointers.
    for a in fileList:
        writeUint32(len(fileData), a[1])
        f = open(a[0], "rb")
        fBytes = f.read()
        writeUint32(len(fBytes), a[2])
        fileData.extend(fBytes)
        f.close()
    
    #Save the first non-existant file.
    outFile = path
    i = 1
    if os.path.exists(outFile + ".JAM"):
        while os.path.exists(outFile + "_" + str(i) + ".JAM"):
            i += 1
        outFile = outFile + "_" + str(i) + ".JAM"
    else:
        outFile = outFile + ".JAM"
    
    f = open(outFile, "wb")
    f.write(fileData)
    f.close()
    
    print("COMPLETE: Achive built. " + outFile)
    
    return True

#Detect if executable or not.
fileName = sys.argv[0].split(os.sep).pop()
if fileName[-3:] == ".py" or fileName[-4:] == ".pyw":
    runCommand = "python " + fileName
else:
    runCommand = fileName

#Determine if the first argument is a file or a folder and process it.
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        path = sys.argv[i]
        if os.path.isfile(path):
            extract(path)
        if os.path.isdir(path):
            build(path)
else:
    print("JAM Extractor 1.0.1\nCOPYRIGHT (C) 2012-2013: JrMasterModelBuilder\n\nThis program will extract JAM archives to an adjacent folder and build new JAM archives from folders.\n\nUSAGE (Extract and Builder):\n" + runCommand + " <FILE_OR_FOLDER_PATH>\n")

