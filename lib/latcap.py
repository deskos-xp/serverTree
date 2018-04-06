#! /usr/bin/env python3
#NoGuiLinux
#eh, kind of broke a promise, here, this module/plugin requires eLattice and capsule,whoops

import eLattice,capsule,os

class lc:
    ifileE=''
    ifileD=''
    key=''
    block_size=4096
    def encryptMain(self):
        cipherL=eLattice.modes()
        cipherL.key=self.key
        cipherL.theLatticeE(self.ifileE,self.ifileE+".lat")

        cipherC=capsule.capsule()
        cipherC.oPath="."
        cipherC.ifile=self.ifileE+".lat"
        cipherC.block_size=self.block_size
        cipherC.userKey=self.key
        cipherC.encryptMain()

    def decryptMain(self):
        cipherC=capsule.capsule()
        cipherC.oPath='.'
        cipherC.block_size=self.block_size
        cipherC.userKey=self.key
        cipherC.ifile=os.path.splitext(self.ifileD)[0]
        cipherC.decryptMain()

        cipherL=eLattice.modes()
        cipherL.key=self.key
        ifileE=os.path.splitext(os.path.splitext(self.ifileD)[0])[0]
        cipherL.theLatticeD(os.path.splitext(self.ifileD)[0],ifileE)
'''
#example useage code
LC=lc()
LC.ifileE='test.txt'
LC.ifileD='php.zip.lat.cap'
LC.key='avalon'
#LC.encryptMain()
LC.decryptMain()
'''
