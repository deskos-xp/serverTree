#! /usr/bin/env python3
import sys,os

try:
    #plugins
    sys.path.insert(0,".")
    import colors
    color=colors.colors()
except:
    print("WARN: colors lib could not be imported")

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
key=keeper.adjustKey("sixteen")
ec=keeper.encrypt(key,"tarball.tgz","t.tmp")
keeper.decrypt(key,"t.tmp","tarball.tgz.tmp")
"""
