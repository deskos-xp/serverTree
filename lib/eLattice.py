#! /usr/bin/env python3
#NoGuiLinux
try:
    from Cryptodome.Cipher import AES, ChaCha20
except:
    from Crypto.Cipher import AES, ChaCha20
import os

class modes:
    key=''
    NOTFILE="'{}' is not a file!"
    NOEXIST="'{}' does not exist!"
    TRUNCATE="the key is too long... key will be truncated to 32 characters in length!"
    def adjustKey(self,key):
        if len(key) < 32:
            key=key+' '*(32-len(key))
        if len(key) > 32:
            key=key[:32]
            print(self.TRUNCATE)
        if type(key) == type(str()):
            key=key.encode()
        return key

    def ccE(self,chunk):
        key=self.adjustKey(self.key)
        cipher=ChaCha20.new(key=key)
        cipherText=cipher.nonce+cipher.encrypt(chunk)
        return cipherText

    def ccD(self,chunk):
        key=self.adjustKey(self.key)
        nonce=chunk[:8]
        msg=chunk[8:]
        cipher=ChaCha20.new(key=key,nonce=nonce)
        plainText=cipher.decrypt(msg)
        return plainText

    def aesE(self,chunk):
        key=self.adjustKey(self.key)
        cipherText=b''
        iv=os.urandom(16)
        cipher=AES.new(key,AES.MODE_CFB,iv)
        cipherText=cipher.encrypt(chunk)
        return iv+cipherText

    def aesD(self,chunk):
        key=self.adjustKey(self.key)
        iv=chunk[:16]
        msg=chunk[16:]
        cipher=AES.new(key,AES.MODE_CFB,iv)
        plaintext=cipher.decrypt(msg)
        return plaintext

    def eFile1(self,infile,outfile):
        num=0
        with open(infile,'rb') as data, open(outfile,'wb') as odata:
            while True:
                d=data.read(128)
                if not d:
                    break
                if (num % 2 ) == 0:
                    odata.write(self.ccE(d))
                else:
                    odata.write(self.aesE(d))
                num+=1

    def dFile1(self,infile,outfile):
        num=0
        with open(infile,'rb') as data, open(outfile,'wb') as odata:
            while True:
                if ( num % 2 ) == 0:
                    d=data.read(128+8)
                else:
                    d=data.read(128+16)
                
                if not d:
                    break
                if ( num % 2 ) == 0:
                    odata.write(self.ccD(d))
                else:
                    odata.write(self.aesD(d))
                num+=1

    def eFile2(self,infile,outfile):
        num=0
        with open(infile,'rb') as data, open(outfile,'wb') as odata:
            while True:
                d=data.read(128)
                if not d:
                    break
                if (num % 2 ) == 0:
                    odata.write(self.aesE(d))
                else:
                    odata.write(self.ccE(d))
                num+=1

    def dFile2(self,infile,outfile):
        num=0
        with open(infile,'rb') as data, open(outfile,'wb') as odata:
            while True:
                if ( num % 2 ) == 0:
                    d=data.read(128+16)
                else:
                    d=data.read(128+8)
                
                if not d:
                    break
                if ( num % 2 ) == 0:
                    odata.write(self.aesD(d))
                else:
                    odata.write(self.ccD(d))
                num+=1

    
    def theLatticeE(self,ifile,ofile):
        if os.path.exists(ifile):
            if os.path.isfile(ifile):
                self.eFile1(ifile,ofile+".tmp")
                self.eFile2(ofile+".tmp",ofile)
                notNeeded=(ofile+".tmp",ifile)
                for i in notNeeded:
                    os.remove(i)
            else:
                exit(self.NOTFILE.format(ifile))
        else:
            exit(self.NOEXIST.format(ifile))
    
    def theLatticeD(self,ifile,ofile):
        if os.path.exists(ifile):
            if os.path.isfile(ifile):
                self.dFile2(ifile,ofile+".tmp")
                self.dFile1(ofile+".tmp",ofile)
                notNeeded=(ofile+".tmp",ifile)
                for i in notNeeded:
                    os.remove(i)
            else:
                exit(self.NOTFILE.format(ifile))
        else:
            exit(self.NOEXIST.format(ifile))

#example code for useage
'''
tr=modes()
tr.key="password is test"
tr.theLatticeE('test.txt','test.txt.lat')
tr.theLatticeD('test.txt.lat','test.txt')
'''
