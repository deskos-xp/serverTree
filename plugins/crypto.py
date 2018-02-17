#! /usr/bin/env python3
import sys,os

#plugins
sys.path.insert(0,".")
import colors
color=colors.colors()

from Crypto.Cipher import AES

class theCryptKeeper:
    def adjustKey(self,key):
        keyLen=16-len(key)
        keyPad=chr(keyLen)
        key=key+(keyLen*keyPad)
        return key
    
    def encrypt(self,key,file,ofile):
        cipher=AES.new(key)
        ciphertext=b''
        with open(file,'rb') as data, open(ofile,"wb") as odata:
            while True:
                dt=data.read(16)
                if not dt:
                    break
                if len(dt) < 16:
                    chunkLen=16-len(dt)
                    chunkPad=chr(chunkLen).encode()
                    dt=dt+(chunkLen*chunkPad)
                ciphertext=cipher.encrypt(dt)
                odata.write(ciphertext)
    
    
    def decrypt(self,key,file,ofile):
        cipher=AES.new(key)
        plaintext=b''
        with open(file,'rb') as data:
            while True:
                dt=data.read(16)
                if not dt:
                    break
                plaintext+=cipher.decrypt(dt)
            odata=open(ofile,"wb")
            endChar=plaintext[-1]
            odata.write(plaintext[:-endChar])

'''
keeper=theCryptKeeper()
key=keeper.adjustKey("sixteen")
ec=keeper.encrypt(key,"tarball.tgz","t.tmp")
keeper.decrypt(key,"t.tmp","tarball.tgz.tmp")
'''
