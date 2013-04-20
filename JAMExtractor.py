#!/usr/bin/python

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

def extract(path, verbose):
    def uint32(offset):
        if bytesAre == "str":
            return ord(fileData[offset]) + (ord(fileData[offset+1]) * 256) + (ord(fileData[offset+2]) * 65536) + (ord(fileData[offset+3]) * 16777216)
        else:
            return fileData[offset] + (fileData[offset+1] * 256) + (fileData[offset+2] * 65536) + (fileData[offset+3] * 16777216)
    
    def listFolders(offset, number, folderPath):
        #List of folder to build.
        folderList = []
        #Read in data for the total number of folder.
        for _ in range(number):
            #Add ascii bytes to the end of the path until we hit a null byte.
            name = folderPath
            for b in fileData[offset:offset+12]:
                if b == 0 or b == b"\x00":
                    break
                if bytesAre == "str":
                    name += b
                else:
                    name += chr(b)
            position = uint32(offset + 12)
            if verbose:
                print("READING: " + name + "  OFFSET: " + str(position))
            #Add the folder data to the array to return.
            folderList.append([name, position])
            #Skip the offset forward for the next folder.
            offset += 16
        return folderList

    def listFiles(offset, number, folderPath):
        #List of files to build.
        fileList = []
        #Read in data for the total number of files.
        for _ in range(number):
            #Add ascii bytes to the end of the path until we hit a null byte.
            name = folderPath + os.sep
            for b in fileData[offset:offset+12]:
                if b == 0 or b == b"\x00":
                    break
                if bytesAre == "str":
                    name += b
                else:
                    name += chr(b)
            #Add the file data to the array to return.
            position = uint32(offset + 12)
            size = uint32(offset + 16)
            if verbose:
                print("READING: " + name + "  OFFSET: " + str(position) + "  SIZE: " + str(size))
            fileList.append([name, position, size])
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
    
    #Check if this version of Python treats bytes as int or str
    bytesAre = type(b'a'[0]).__name__    

    #Open the file and read it in.
    with open(path, "rb") as f:
        fileData = f.read()
    
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
        outFolder = path[:-4]
    else:
        outFolder = path
    
    #Move the old folder out of the way if it exists.
    if os.path.exists(outFolder):
        #Move to the first name not taken.
        i = 1
        while os.path.exists(outFolder + "_" + str(i) + "_bak"):
            i += 1
        renameFolder = outFolder + "_" + str(i) + "_bak"
        print("NOTE: Existing extraction found.\nMOVING: " + outFolder + " -> " + renameFolder)
        os.rename(outFolder, renameFolder)
        
        #Check that the file was moved out of the way.
        if os.path.exists(outFolder):
            #File still exists, something went wrong.
            print("ERROR: Failed to move old extraction folder out of the way, files not extracted.")
            return False

    os.makedirs(outFolder)   
    
    #Create all the folders we need to extract to.
    for a in folderList:
        if a[0] == "":
            continue
        if not os.path.exists(outFolder + a[0]):
            if verbose:
                print("WRITING: " + a[0])
            os.makedirs(outFolder + a[0])
    
    #Loop through the list of files, saving them.
    for a in fileList:
        if verbose:
            print("WRITING: " + a[0] + "  SIZE: " + str(a[2]))
        with open(outFolder + a[0], "wb") as f:
            f.write(fileData[a[1]:a[1]+a[2]])
    
    print("COMPLETE: " + str(len(fileList)) + " files extracted.\nOUTPUT: " + outFolder)
    return True

def build(path, verbose):
    def writeUint32(i = 0, position = -1):
        #Keep it possible.
        if i > 4294967295:
            i = 4294967295
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
        #Write 12 bytes for the name.
        for i in range(12):
            if i < len(s):
                fileData.append(ord(s[i]))
            else:
                fileData.append(0)
    
    def updateFolder(s):
        #Update the pointer to the folder.
        for a in folderList:
            if a[0] == s:
                writeUint32(len(fileData), a[1])
                break
    
    print("Building, please wait.")
    
    #Start the byte array.
    fileData = bytearray(b"LJAM")
    #Create lists to store file and folder pointers to update later.
    folderList = []
    fileList = []
    
    for currentdir, dirlist, filelist in os.walk(path):
        #Filter out files and folder with names that are too long for the format.
        for i in reversed(range(len(filelist))):
            if len(filelist[i]) > 12:
                if verbose:
                    print("SKIPPING: " + filelist[i] + "  (Name too long.)")
                del filelist[i]
        for i in reversed(range(len(dirlist))):
            if len(dirlist[i]) > 12:
                if verbose:
                    print("SKIPPING: " + dirlist[i] + "  (Name too long.)")
                del dirlist[i]
        
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
            if verbose:
                print("READING: " + a[0][len(path):])
        
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
            if verbose:
                print("READING: " + a[0][len(path):])
    
    #Append the files and update pointers.
    for a in fileList:
        start = len(fileData)
        writeUint32(start, a[1])
        with open(a[0], "rb") as f:
            fBytes = f.read()
            size = len(fBytes)
            if verbose:
                print("APPENDING: " + a[0][len(path):] + "  OFFSET:" + str(start) + "  SIZE:" + str(size))
            writeUint32(size, a[2])
            fileData.extend(fBytes)
    
    #Create the output file.
    outFile = path + ".JAM"
    
    #Move the old file out of the way if it exists.
    if os.path.exists(outFile):
        #Move to the first name not taken.
        i = 1
        while os.path.exists(outFile + "." + str(i) + ".bak"):
            i += 1
        renameFile = outFile + "." + str(i) + ".bak"
        print("NOTE: Existing archive found.\nMOVING " + outFile + " -> " + renameFile)
        os.rename(outFile, renameFile)
        
        #Check that the file was moved out of the way.
        if os.path.exists(outFile):
            #File still exists, something went wrong.
            print("ERROR: Failed to move old archive out of the way, archive not written.")
            return False
    
    #Write the archive.
    with open(outFile, "wb") as f:
        f.write(fileData)
    
    print("COMPLETE: Achive built.\nOUTPUT: " + outFile)
    
    return True

#Detect if executable or not.
fileName = sys.argv[0].split(os.sep).pop()
if fileName[-3:] == ".py" or fileName[-4:] == ".pyw":
    runCommand = "python " + fileName
else:
    runCommand = fileName

#Preprocess arguments.
fileList = []
verbose = False
for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    if arg == "--verbose":
        verbose = True
    else:
        fileList.append(arg)

#Process files/folders arrordingly or display message.
if len(fileList) > 0:
    for i in fileList:
        if os.path.isfile(i):
            extract(i, verbose)
        elif os.path.isdir(i):
            build(i, verbose)
else:
    print("JAM Extractor 1.0.2\nCOPYRIGHT (C) 2012-2013: JrMasterModelBuilder\n\nThis program will extract JAM archives to an adjacent folder and build new JAM archives from folders.\n\nUSAGE (Extract and Build):\n" + runCommand + " <FILE_OR_FOLDER_PATHS>\n")
