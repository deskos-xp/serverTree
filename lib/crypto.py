#! /usr/bin/env python3
import sys,os


import colors
color=colors.colors()

from Crypto.Cipher import AES

class theCryptKeeper:
    def adjuster(self,key,charLen):
        keyLen=charLen-len(key)
        keyPad=chr(keyLen)
        key+=(keyLen*keyPad)
        return key

    def adjustKey(self,key):
        if len(key) < 16:
            key=self.adjuster(key,16)
        elif  16 < len(key) < 24:
            key=self.adjuster(key,24)
        elif 24 < len(key) < 32:
            key=self.adjuster(key,32)
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
        multi=int((os.stat(file).st_size/16)-1)
        counter=0
        with open(file,'rb') as data:
            odata=open(ofile,"wb")
            while True:
                dt=data.read(16)
                if not dt:
                    break
                plaintext=cipher.decrypt(dt)
                if counter == multi:
                    endChar=plaintext[-1]
                    plaintext=plaintext[:-endChar]
                odata.write(plaintext)
                counter+=1

"""
keeper=theCryptKeeper()
key=keeper.adjustKey("sixteen   1234567 1234567")
ec=keeper.encrypt(key,"tarball.tgz","t.tmp")
keeper.decrypt(key,"t.tmp","tarball.tgz.tmp")
"""
