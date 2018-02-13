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
sys.path.insert(0,os.path.realpath('./plugins'))
import colors
from archiveLib import tarball
color=colors.colors()

class ssh:
    keyFile=""
    host="127.0.0.1"
    port=22
    username=""
    password=""
    forcePassword=None
    def printTotals(self,transferred, toBeTransferred):
        displayString=color.transfer+"Transferred [Bytes]: {0}/{1} - {2}".format(color.start+str(transferred)+color.end,color.stop+str(toBeTransferred)+color.end,color.stop+str(round(100*(transferred/toBeTransferred),2))+color.end )+color.end
        #for me, i like to not see a whole bunch of Transfered...yadeeyada text, asside from the filesystem based info
        #so backspace over previous display string, and print the new string
        #talk about automation
        print(displayString,end=str(len(displayString)*'\b'))

    def client(self):
        Client=paramiko.SSHClient()
        Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.forcePassword == None:
            try:
                if os.path.exists(os.path.realpath(os.path.expanduser(self.keyFile))):
                    Client.connect(self.host,port=self.port,username=self.username,key_filename=self.keyFile)
                else:
                    Client.connect(self.host,port=self.port,username=self.username,password=self.password)
            except:
                Client.connect(self.host,port=self.port,username=self.username,password=self.password)
        else:
            try:
                Client.connect(self.host,port=self.port,username=self.username,password=self.forcePassword)
            except:
                exit(color.errors+"something went wrong and forcePassword could not be used!"+colors.end)
        return Client

    def transfer(self,client,src=None,dest=None,mode="put"):
        sftp_client=client.open_sftp()
        if src != None:
            if dest != None:
                if mode == "put":
                    sftp_client.put(src,dest,callback=self.printTotals)
                elif mode == "get":
                    sftp_client.get(src,dest,callback=self.printTotals)
                else:
                    print("invalid mode")
            else:
                print("dest cannot be blank")
        else:
            print("src cannot be blank")
   
    def clientClose(self,client):
        client.close()

class docGen:
    manifest="manifest.xml"
    verbose=False
    integType="sha512"
    def integrity(self,fname):
        obj=hashlib.sha512()
        with open(fname,"rb") as file:
            while True:
                data=file.read(1024)
                if not data:
                    break
                obj.update(data)
        return [obj.hexdigest(),self.integType]

    def fsize(self,fname):
        return str(os.stat(fname).st_size)

    def getUserGroup(self,fname):
        gid=os.stat(fname).st_gid
        uid=os.stat(fname).st_uid
        group=grp.getgrgid(gid)[0]
        user=pwd.getpwuid(uid)[0]
        return (str(user),str(uid),str(group),str(gid))

    def getPermissions(self,fname):
        return str(oct(os.stat(fname)[0]))[4:]

    def getFileType(self,fname):
        num=str(oct(os.stat(fname)[0]))[2:4]
        types={"01":"FIFO","02":"character device","40":"Directory","60":"block device","10":"Regular file","12":"symbolic link","14":"socket","17":"bit mask for the file type bitfields"}
        keys=[key for key in types.keys()]
        if num in keys:
            return types[num]
        else:
            return num

    def lsAttr(self,fname):
        cmd='lsattr "'+fname+'" | cut -f 1 -d" "'
        process=sp.Popen(cmd,shell=True,stdout=sp.PIPE)
        out,err = process.communicate()
        return out.decode().rstrip("\n")

    def lsAttr2(self,fname,node):
        if len(xattr.list(fname)) > 0:
            attr2Top=subElement(node,'getfattr')
            for xat in xattr.list(fname):
                if xat != b"":
                    attr2=subElement(attr2Top,'attr')
                    attr2.text=xat.decode()
                    attr2Val=subElement(attr2Top,'value')
                    attr2Val.text=xattr.get(fname,xat).decode()
        #this function will be used to get extended attributes as used by the setfattr command

    def getfacl(self,fname,node):
        faclTop=subElement(node,"facl")
        acl=[el for el in posix1e.ACL(file=fname).to_any_text().decode().split("\n")]
        for counter,lien in enumerate(acl):
            if lien != "":
                facl=subElement(faclTop,'acl',num=str(counter))
                facl.text=lien

    def getFSType(self,fname,node):
        cmd='df --output=fstype /home/carl | tail -n 1'
        data=sp.Popen(cmd,shell=True,stdout=sp.PIPE)
        stdout,err=data.communicate()
        fstype=subElement(node,"fstype")
        fstype.text=stdout.decode().rstrip("\n")


    def genXml(self,dir='.'):
        path=os.path.realpath(dir)
        dirStrip=os.path.dirname(path)
        top = element("Directory",dpath=os.path.basename(path))
        counter=0
        dircounter=0
        for root,dirname,fnames in os.walk(path):
            dirs=subElement(top,'dir',num=str(dircounter),dpath=root.strip(dirStrip))
            counter=0
            dircounter+=1
            if root.strip(dirStrip) != '':
                names=subElement(dirs,'dirname')
                names.text=root.strip(dirStrip)
            for fname in fnames:
                fpath=os.path.join(root,fname)
                if os.path.exists(fpath):
                    if self.verbose == True:
                        print(color.start+fpath+color.end)
                    names=subElement(dirs,'file',num=str(counter),name=fname)
                    allocation=subElement(names,'allocation')
                    subNames=subElement(allocation,'fname')
                    subNames.text=fname
                    nameStat=subElement(allocation,'fsize')
                    nameStat.text=self.fsize(fpath)
                    #info concerning integrity
                    integrity=self.integrity(fpath)
                    integ=subElement(names,'integ')
                    value=subElement(integ,"value")
                    value.text=integrity[0]
                    integT=subElement(integ,"hash")
                    integT.text=integrity[1]
                    #info concerning ownership
                    own=subElement(names,"owners")
                    owners=self.getUserGroup(fpath)
                    uid=subElement(own,"uid")
                    uid.text=owners[1]
                    user=subElement(own,"user")
                    user.text=owners[0]
                    gid=subElement(own,"gid")
                    gid.text=owners[3]
                    group=subElement(own,"group")
                    group.text=owners[2]
                    #info concerning how the file is used 
                    fsdata=subElement(names,"controls")
                    permissions=subElement(fsdata,"permissions")
                    permissions.text=self.getPermissions(fpath)
                    ftype=subElement(fsdata,"ftype")
                    ftype.text=self.getFileType(fpath)
                    lsattr=subElement(fsdata,"lsattr")
                    lsattr.text=self.lsAttr(fpath)
                    self.getFSType(fpath,fsdata)
                    self.lsAttr2(fpath,fsdata)
                    self.getfacl(fpath,fsdata)
                    #do file integreity check and record
                    counter+=1    
                else:
                    print(color.error+'path {} is a broken symlink'.format(fpath)+color.end)
        file=open(self.manifest,"wb")
        file.write(tostring(top))

class zipUp:
    SRC=os.path.realpath(os.path.expanduser("~/Documents"))
    DST="tmp"
    oPath="default.zip"
    counter=1
    dirCounter=1
    manifest="manifest.xml"
    def prep(self):
        if not os.path.exists(self.DST):
            os.mkdir(self.DST)
        if not os.path.exists(os.path.join(self.DST,self.manifest)):
            shutil.copyfile(self.manifest,os.path.join(self.DST,self.manifest))
            #if manifest does not exist generate it

    def zipper(self):
        self.prep()
        if os.path.exists(self.SRC):
            if not os.path.exists(os.path.join(self.DST,os.path.split(self.SRC)[1])):
                shutil.copytree(self.SRC,os.path.join(self.DST,os.path.split(self.SRC)[1]))
            else:
                exit("Destination Dir '{}' Exists".format(self.DST))
        else:
            exit("Source Dir '{}' Does not Exist".format(self.SRC))
        
        try:
            zippy=zipfile.ZipFile(self.oPath,'w',zipfile.ZIP_DEFLATED)
            for root, dirname, fnames in os.walk(self.DST):
                for dir in dirname:
                    absolutePath=os.path.join(root,dir)
                    relativePath=absolutePath.replace(self.DST,os.path.splitext(self.oPath)[0])
                    zippy.write(absolutePath,relativePath)
                    print(color.dirs+"directory {}{} : {} added.".format(self.dirCounter,color.end,dir))
                    self.dirCounter+=1
                for fname in fnames:
                    if fname == self.manifest:
                        print(color.manifest+"file {} {}: manifest {} added.".format(self.counter,color.end,fname))
                    else:
                        print(color.files+"file {} {}: {} added.".format(self.counter,color.end,fname))
                    absolutePath=os.path.join(root,fname)
                    relativePath=absolutePath.replace(self.DST,os.path.splitext(self.oPath)[0])
                    zippy.write(absolutePath,relativePath)
                    self.counter+=1
            print(color.message+"{} created successfully.{}".format(self.oPath,color.end))
            print("{}Directories {}: {}\n{}Files{} : {}".format(color.message,color.end,self.dirCounter,color.message,color.end,self.counter))
        except IOError as message:
            exit(message)
        except OSError as message:
            exit(message)
        except zipfile.BadZipFile as message:
            exit(message)
        finally:
            zippy.close()
            shutil.rmtree(self.DST)
            os.remove(self.manifest)

class run:
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
    tarball_compression="gz"
    compModes=['xz','gz','bz2']
    tarballMessage=''
    def pathExpand(self,path):
        return os.path.realpath(os.path.expanduser(path))

    def zipnameMod(self):
        if self.tarball == True:
            ext=".tar."+self.tarball_compression
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
        else:
            archive = "zipfile"

        ERR_FailToDelete=color.errors+"something went wrong and '{}' was not successfully deleted{}".format(self.zipName,color.end)
        if os.path.split(self.dst)[0] != self.pathExpand("."):
            inputString=color.question+"do you wish to delete the generated "+archive+" in the current directory?"+color.end+" : "
            user=input(inputString)
            print(color.message+"="*len(inputString)+color.end)
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
                print("{}user chose to keep the residual {}.{}".format(color.errors,archive,color.end))
    def checkTarballCompMode(self):
        if self.tarball_compression not in self.compModes:
            exit(color.errors+"'{}' not available for tarballing".format(self.tarball_compression)+color.end)
        else:
            #i would prefer the message be displayed in a different location, so saving the string for later
            self.tarballMessage=color.message+"'{}' is using '{}' for compression.".format(self.zipName,self.tarball_compression)+color.end
            
    def main(self):
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

        self.dstMod()
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
            else:
                Zip=zipUp()
                Zip.oPath=self.zipName
                Zip.SRC=src
                Zip.zipper()
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
        options=parser.parse_args()

        if options.dst:
            self.dst=options.dst
        if options.tarball:
            self.tarball=options.tarball
            if options.tarball_compression:
                self.tarball_compression=options.tarball_compression
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
        if options.force_password:
            self.forcePassword=options.force_password
        else:
            self.forcePassword=None


Run=run()
Run.cmdline()
Run.main()
