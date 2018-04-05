#! /usr/bin/env python3
#NoGuiLinux
#eh, kind of broke a promise, here, this module/plugin requires eLattice and capsule,whoops

import eLattice,capsule,os

class lc:
    ifileE=''
    ifileD=''
    key=''
    
    def encryptMain(self):
        cipherL=eLattice.modes()
        cipherL.key=self.key
        cipherL.theLatticeE(self.ifileE,self.ifileE+".lat")

        cipherC=capsule.capsule()
        cipherC.oPath="."
        cipherC.ifile=self.ifileE+".lat"
        cipherC.userKey=self.key
        cipherC.encryptMain()

    def decryptMain(self):
        cipherC=capsule.capsule()
        cipherC.oPath='.'
        cipherC.ifile=os.path.splitext(self.ifileD)[0]
        cipherC.userKey=self.key
        cipherC.decryptMain()

        cipherL=eLattice.modes()
        cipherL.key=self.key
        cipherL.theLatticeD(os.path.splitext(self.ifileD)[0],'test.txt')
'''
#example useage code
LC=lc()
LC.ifileE='test.txt'
LC.ifileD='test.txt.lat.cap'
LC.key='topple this mountain range'
LC.encryptMain()
LC.decryptMain()
'''
