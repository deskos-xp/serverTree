#! /usr/bin/env python3
import os,zipfile,shutil
import tarfile

import colors
color=colors.colors()

class tarball:
    SRC=os.path.realpath(os.path.expanduser("~/Documents"))
    DST="tmp"
    oPath="default.tgz"
    counter=1
    manifest="manifest.xml"
    compression='gz'
    def prep(self):
        if not os.path.exists(self.DST):
            os.mkdir(self.DST)
        if not os.path.exists(os.path.join(self.DST,self.manifest)):
            shutil.copyfile(self.manifest,os.path.join(self.DST,self.manifest))
            #if manifest does not exist generate it

    def tarbit(self):
        self.prep()
        if os.path.exists(self.SRC):
            if not os.path.exists(os.path.join(self.DST,os.path.split(self.SRC)[1])):
                shutil.copytree(self.SRC,os.path.join(self.DST,os.path.split(self.SRC)[1]))
            else:
                exit("Destination Dir '{}' Exists".format(self.DST))
        else:
            exit("Source Dir '{}' Does not Exist".format(self.SRC))
        
        try:
            tarry=tarfile.open(self.oPath,'w:'+self.compression)
            absolutePath=self.DST
            relativePath=absolutePath.replace(self.DST,os.path.splitext(self.oPath)[0])
                        
            for root, dirname, fnames in os.walk(self.DST):
                for fname in fnames:
                    if fname == self.manifest:
                        print(color.manifest+"file {} {}: manifest {} added.".format(self.counter,color.end,fname))
                    else:
                        print(color.files+"file {} {}: {} added.".format(self.counter,color.end,fname))
                    absolutePath=os.path.join(root,fname)
                    relativePath=absolutePath.replace(self.DST,os.path.splitext(self.oPath)[0])
                    tarry.add(absolutePath,relativePath)
                    self.counter+=1
            print(color.message+"{} created successfully.{}".format(self.oPath,color.end))
            print("{}Files{} : {}".format(color.message,color.end,self.counter))
            tarry.close()

        except IOError as message:
            exit(message)
        except OSError as message:
            exit(message)

        shutil.rmtree(self.DST)
        os.remove(self.manifest)

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
