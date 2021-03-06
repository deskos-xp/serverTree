#! /usr/bin/env python3
#NoGuiLinux
try:
    from Cryptodome.Cipher import ChaCha20
except:
    from Crypto.Cipher import ChaCha20
import os
#local import
import colors

color=colors.colors()
class chacha20:
    dataFile=''
    ext=".cc20"
    oDataFile=''
    key=''
    FILE_NOT_EXIST="'{}' does not exist..."

    def mkOdataName(self):
        self.oDataFile=self.dataFile+self.ext

    def adjustKey(self,key):
        if len(key) < 32:
            key=key+' '*(32-len(key))
        if type(key) == type(str()):
            key=key.encode()
        return key

    def encryptFile(self):
        self.mkOdataName()
        key=self.adjustKey(self.key)
        if not os.path.exists(self.dataFile):
            exit(color.errors+self.FILE_NOT_EXIST.format(self.dataFile)+color.end)
        with open(self.dataFile,'rb') as data, open(self.oDataFile,'wb') as odata:
            while True:
                d=data.read(128)
                if not d:
                    break
                cipher=ChaCha20.new(key=key)
                msg=cipher.nonce+cipher.encrypt(d)
                odata.write(msg)
            os.remove(self.dataFile)

    def decryptFile(self):
        self.mkOdataName()
        key=self.adjustKey(self.key)
        if not os.path.exists(self.oDataFile):
            exit(color.errors+self.FILE_NOT_EXIST.format(self.oDataFile)+color.end)
        with open(self.oDataFile,'rb') as data, open(self.dataFile,'wb') as odata:
            while True:
                d=data.read(128+8)
                if not d:
                    break
                nonce=d[:8]
                msg=d[8:]
                cipher=ChaCha20.new(key=key,nonce=nonce)
                odata.write(cipher.decrypt(msg))
            os.remove(self.oDataFile)


##example code for this module
'''
chacha=chacha20()
chacha.dataFile='test.tar.gz'
chacha.key='avalon'
chacha.encryptFile()
chacha.decryptFile()
'''
