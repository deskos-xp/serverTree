#! /usr/bin/env python3
#scan a directory -- create an xml manifest of its contents -- zip the xml manifest and the directory up into an archive -- send to a remote server
#NoGuiLinux

from xml.etree.ElementTree import Element as element, SubElement as subElement, Comment as comment, tostring
import os, hashlib
import pwd,grp
import base64,paramiko
import zipfile,shutil,argparse
import subprocess as sp
import xattr,posix1e

#plugins
import sys
sys.path.insert(0,os.path.realpath('./lib'))
import colors
from archiveLib import tarball
from crypto import theCryptKeeper as tck
color=colors.colors()
from ssh import ssh
from manifestGen import docGen
from archiveLib import zipUp
from archiveLib import cpioShell 
from depCheck import checkDep
import aesCfbLib
import chacha20
import eLattice
class run:
    #do a depency checking run
    dep=checkDep()
    dep.getDeps()
    dep.dep()
    dep.determine()

    host="127.0.0.1"
    port=22
    username=""
    password=""
    keyFile=""
    src=""
    zipName=""
    dst=""
    forcePassword=None
    tarball=False
    cpio=False
    tarball_compression="gz"
    compModes=['xz','gz','bz2']
    tarballMessage=''
    encrypt=''
    decrypt=''
    delpromptYes=False
    delpromptNo=False
    emode='cbc'
    DECRYPT_ERR=color.errors+"some internal error occurred, and '{}' could not be decrypted... please check your mode!"+color.end
    MODEUNSUPPORTED="'{}' : mode is unsupported"
    def pathExpand(self,path):
        return os.path.realpath(os.path.expanduser(path))

    def zipnameMod(self):
        if self.tarball == True:
            ext=".tar."+self.tarball_compression
        elif self.cpio == True:
            ext=".cpio"
        else:
            ext=".zip"
        if self.zipName == "":
            if self.src[len(self.src)-1] == "/":
                self.src=self.src[0:len(self.src)-1]
            self.zipName=os.path.split(self.src)[1]+ext
        else:
            if os.path.splitext(self.zipName)[1] == "":
                self.zipName+=ext
   
    def dstMod(self):
        if self.dst == "":
            self.dst=os.path.join(self.pathExpand('~'),self.zipName)
        else:
            self.dst=os.path.join(self.pathExpand(self.dst),self.zipName)

    def delPrompt(self):
        breakStates=['y','n']
        stupidCounter=0
        stupidTimeout=10
        if self.tarball == True:
            archive = "tarball"
        elif self.cpio == True:
            archive = "cpio-archive"
        else:
            archive = "zipfile"

        ERR_FailToDelete=color.errors+"something went wrong and '{}' was not successfully deleted{}".format(self.zipName,color.end)
        if os.path.split(self.dst)[0] != self.pathExpand("."):
            if self.delpromptYes == True:
                user='y'
            elif self.delpromptNo == True:
                user='n'
            else:
                inputString=color.question+"do you wish to delete the generated "+archive+" in the current directory?"+color.end+" : "
                user=input(inputString)
                print(color.message+"="*os.get_terminal_size().columns+color.end)
            while user not in breakStates:
                stupidCounter+=1
                if stupidCounter <= stupidTimeout:
                    user=input(color.question+"[ {}{}{}/{}{}{} ] do you wish to delete the generated {} in the current directory? [{}y/n{}] : ".format(color.start,stupidCounter,color.end.color.stop,stupidTimeout,color.end,archive,color.stop,color.end))
                else:
                    print("{}the user apparently cannot read... not deleting the residue!{}".format(color.errors,color.end))
                    break
            if user == 'y':
                os.remove(os.path.join(self.pathExpand("."),self.zipName))
                try:
                    if not os.path.exists(os.path.join(self.pathExpand("."),self.zipName)):
                        print("{}the residual {} '{}' was successfully deleted!{}".format(color.errors,archive,self.zipName,color.end))
                    else:
                        print(ERR_FailToDelete)
                except IOError as message:
                    print(ERR_FailToDelete)
                    exit(message)
                except OSError as message:
                    print(ERR_FailToDelete)
                    exit(message)
            else:
                print("{}user chose to keep the residual {}!{}".format(color.errors,archive,color.end))
    def checkTarballCompMode(self):
        if self.tarball_compression not in self.compModes:
            exit(color.errors+"'{}' not available for tarballing".format(self.tarball_compression)+color.end)
        else:
            #i would prefer the message be displayed in a different location, so saving the string for later
            self.tarballMessage=color.message+"'{}' is using '{}' for compression.".format(self.zipName,self.tarball_compression)+color.end
            
    def main(self):
        success=False
        #temporary instantiation, since aes libs do not remove old files
        AES_RUN=False
        if self.decrypt != '':
            if os.path.exists(self.zipName):
                if self.emode == 'cbc':
                    try:
                        cipher=tck()
                        key=cipher.adjustKey(self.decrypt)
                        cipher.decrypt(key,self.zipName,os.path.splitext(self.zipName)[0])
                        os.remove(self.zipName)
                        success=True
                    except:
                        print(self.DECRYPT_ERR.format(self.zipName))
                        if os.path.exists(os.path.splitext(self.zipName)[0]):
                            os.remove(os.path.splitext(self.zipName)[0])
                        exit(1)
                elif self.emode == 'cfb':
                    try:
                        cipher=aesCfbLib.aesFile()
                        cipher.key=self.decrypt
                        cipher.decryptFile(self.zipName)
                        os.remove(self.zipName)
                        success=True
                    except:
                        print(self.DECRYPT_ERR.format(self.zipName))
                        if os.path.exists(os.path.splitext(self.zipName)[0]):
                            os.remove(os.path.splitext(self.zipName)[0])
                        exit(1)
                elif self.emode == 'chacha20':
                    try:
                        cipher=chacha20.chacha20()
                        cipher.dataFile=os.path.splitext(self.zipName)[0]
                        cipher.key=self.decrypt
                        cipher.decryptFile()
                        success=True
                    except:
                        print(self.DECRYPT_ERR.format(self.zipName))
                        if os.path.exists(os.path.splitext(self.zipName[0])):
                            os.remove(os.path.splitext(self.zipName)[0])
                        exit(1)
                elif self.emode == 'lattice':
                    try:
                        cipher=eLattice.modes()
                        cipher.key=self.decrypt
                        cipher.theLatticeD(self.zipName,os.path.splitext(self.zipName)[0])
                        success=True
                    except:
                        print(self.DECRYPT_ERR.format(self.zipName))
                        if os.path.exists(os.path.splitext(self.zipName[0])):
                            os.remove(os.path.splitext(self.zipName)[0])
                        exit(1)
                else:
                    exit(self.MODEUNSUPPORTED.format(self.emode))
                if success == True:
                    exit(color.start+"archive decrypted!"+color.end)
            else:
                exit(color.errors+"archive does not exist"+color.end)
        if self.username == "":
            exit(color.errors+"username cannot be blank!"+color.end)
        if self.host == "":
            exit(color.errors+"hostname cannot be blank!"+color.end)
        if self.keyFile == "" and self.forcePassword == None:
            exit(color.errors+"keyFile cannot be blank!"+color.end)           
        if self.src == "":
            exit(color.errors+"src directory cannot be blank!"+color.end)
        if not 1 < self.port < 65535:
            exit(color.errors+"port must be within 1-65535!"+color.end)
         
        self.zipnameMod()
        if self.tarball == True:
            #would have put this later for better grouping, but since this is technically an error check
            #it would better be here
            self.checkTarballCompMode()

        #perform any necessary expansions 
        self.keyFile=self.pathExpand(self.keyFile)
        self.src=self.pathExpand(self.src)
        src=self.src
        if os.path.isdir(src):
            gen=docGen()
            gen.verbose=True
            gen.genXml(src)
            if self.tarball == True:
                tar=tarball()
                tar.compression=self.tarball_compression
                tar.oPath=self.zipName
                tar.SRC=src
                tar.tarbit()
                print(self.tarballMessage)
            elif self.cpio == True:
                arch=cpioShell()
                arch.oFile=self.zipName
                arch.SRC=src
                arch.createArchive() 
            else:
                Zip=zipUp()
                Zip.oPath=self.zipName
                Zip.SRC=src
                Zip.zipper()
            if self.encrypt != '':
                if self.emode == 'cbc':
                    ec=tck()
                    key=ec.adjustKey(self.encrypt)
                    ec.encrypt(key,self.zipName,newZipName)
                    newZipName=self.zipName+".aes"
                    AES_RUN=True
                elif self.emode =='cfb':
                    ec=aesCfbLib.aesFile()
                    ec.key=self.encrypt
                    ec.encryptFile(self.zipName)
                    newZipName=self.zipName+".aes"
                    AES_RUN=True
                elif self.emode == 'chacha20':
                    ec=chacha20.chacha20()
                    ec.key=self.encrypt
                    ec.dataFile=self.zipName
                    ec.encryptFile()
                    newZipName=ec.oDataFile
                elif self.emode == "lattice":
                    newZipName=self.zipName+".lat"
                    cipher=eLattice.modes()
                    cipher.key=self.encrypt
                    cipher.theLatticeE(self.zipName,newZipName)
                else:
                    exit(self.MODEUNSUPPORTED.format(self.emode))
                if AES_RUN == True:
                    #this is run for modules that do not remove self.zipname automatically
                    os.remove(self.zipName)
                self.zipName=newZipName
            self.dstMod()
            send=ssh()
            send.host=self.host
            send.forcePassword=self.forcePassword
            send.password=self.password
            send.port=self.port
            send.username=self.username
            send.keyFile=self.keyFile
            client=send.client()
            print('{}SRC{} -> {}\n{}DST{} -> {}@{}:{}'.format(color.start,color.end,self.zipName,color.stop,color.end,self.username,self.host,self.dst))
            send.transfer(client,self.zipName,self.dst,mode="put")
            send.clientClose(client)
            self.delPrompt()
        else:
            exit("src directory provided is not a directory!")
           
            
    def cmdline(self):
        parser=argparse.ArgumentParser()
        parser.add_argument("-d","--dst")
        parser.add_argument("-z","--zipname")
        parser.add_argument("-H","--host")
        parser.add_argument("-p","--port")
        parser.add_argument("-P","--password")
        parser.add_argument("-k","--rsa-keyfile")
        parser.add_argument("-s","--src")
        parser.add_argument("-u","--username")
        parser.add_argument("-F","--force-password")
        parser.add_argument("-t","--tarball",action="store_true")
        parser.add_argument("-m","--tarball-compression")
        parser.add_argument("-e","--encrypt-archive")
        parser.add_argument("--encrypt-mode",help="cfb, cbc, chacha20, or lattice")
        parser.add_argument("--decrypt")
        parser.add_argument("--delprompt-bypass-yes",action="store_true")
        parser.add_argument("--delprompt-bypass-no",action="store_true")
        parser.add_argument("-c","--cpio",action="store_true")
        options=parser.parse_args()

        if options.dst:
            self.dst=options.dst
        if options.tarball:
            self.tarball=options.tarball
            if options.tarball_compression:
                self.tarball_compression=options.tarball_compression
        elif options.cpio:
            self.cpio=options.cpio
        if options.zipname:
            self.zipName=options.zipname
        if options.host:
            self.host=options.host
        if options.port:
            try:
                self.port=int(options.port)
            except:
                exit("it seems that the provided port number is not a number: '{}'".format(options.port))
        if options.rsa_keyfile:
            self.keyFile=options.rsa_keyfile
        if options.src:
            self.src=options.src
        if options.username:
            self.username=options.username
        if options.password:
            self.password=options.password
        
        if options.encrypt_archive:
            self.encrypt=options.encrypt_archive

        if options.encrypt_mode:
            self.emode=options.encrypt_mode
        else:
            self.emode="cbc"

        if options.decrypt:
            self.decrypt=options.decrypt
        if options.force_password:
            self.forcePassword=options.force_password
        else:
            self.forcePassword=None
        if options.delprompt_bypass_yes:
            self.delpromptYes=options.delprompt_bypass_yes
        if options.delprompt_bypass_no:
            self.delpromptNo=options.delprompt_bypass_no


Run=run()
Run.cmdline()
Run.main()
