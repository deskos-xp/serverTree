#! /usr/bin/env python3
#NoGuiLinux

import os
import colors
import xml.etree.ElementTree as ET
color=colors.colors()

class checkDep:
    depList=[]
    notFound=[]
    PATH=os.environ['PATH'].split(':')
    depCfg="deps.xml"
    def getDeps(self):
        if os.path.exists(self.depCfg):
            cfg=ET.parse(self.depCfg)
            root=cfg.getroot()
            for node in root:
                self.depList.append(node.text)
        else:
            exit(color.errors+"missing dep cfg '{}'".format(self.depcfg)+color.end)

    def dep(self):
        for dep in self.depList:
            found=''
            for Bin in self.PATH:
                try:
                    file=os.path.join(Bin,dep)
                    found=os.stat(file)
                except:
                    pass
            if type(found) != type(os.stat('/')):
                self.notFound.append(dep)

    def determine(self):
        if len(self.notFound) > 0:
            for dep in self.notFound:
                print(color.errors+"missing dependency '{}'".format(dep)+color.end)
            exit(1)

#example useage
'''
a=checkDep()
a.getDeps()
a.dep()
a.determine()
'''
