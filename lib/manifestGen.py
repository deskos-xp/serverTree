#! /usr/bin/python3

from xml.etree.ElementTree import Element as element, SubElement as subElement, Comment as comment, tostring
import os, hashlib
import pwd,grp
import base64,paramiko
import zipfile,shutil,argparse
import subprocess as sp
import xattr,posix1e
import colors

color=colors.colors()

class docGen:
    manifest="manifest.xml"
    verbose=False
    integType="sha512"
    supportedLFS=['ext4','ext3','btrfs','xfs']
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
        return fstype.text

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
                    fstype=self.getFSType(fpath,fsdata)
                    if fstype in self.supportedLFS:
                        lsattr=subElement(fsdata,"lsattr")
                        lsattr.text=self.lsAttr(fpath)
                    self.lsAttr2(fpath,fsdata)
                    self.getfacl(fpath,fsdata)
                    #do file integreity check and record
                    counter+=1    
                else:
                    print(color.error+'path {} is a broken symlink'.format(fpath)+color.end)
        file=open(self.manifest,"wb")
        file.write(tostring(top))

