#! /usr/bin/env python3
#NoGuiLinux
import sys
#like the orginal capsule, but with a bit of a change
#encrypted block sizes are NOT static, their sizes are stored in the keyfile with their corresponding keys
try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Hash import HMAC,SHA512
except:
    from Crypto.Cipher import AES
    from Crypto.Hash import HMAC,SHA512

import sqlite3,os,base64
import random,hashlib

class capsule:
    ifile=''
    ofile=''
    keyfile=''
    db={}
    userKey=''
    keyfile_bs=256
    blkSize=(1024,20480)
    badhmac="HMAC sums do not match!\n    stored HMAC: {}\n calculated HMAC: {}"
    nohmac="Warning! there is no HMAC available to test against"
    def DB(self):
        db=sqlite3.connect(self.keyfile)
        cursor=db.cursor()
        self.db={'db':db,'cursor':cursor}

    def mkTable(self):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''
        create table if not exists
        keys ( key text, blockSize text,rowid INTEGER PRIMARY KEY AUTOINCREMENT );
        '''
        cursor.execute(sql)
        sql='''
        create table if not exists hmac ( shasum text, rowid INTEGER PRIMARY KEY AUTOINCREMENT );
        '''
        cursor.execute(sql)
        db.commit()

    def insertValues(self,key,blockSize):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''
        insert into keys (key,blockSize) values ("{}","{}");
        '''.format(key,blockSize)
        cursor.execute(sql)
        db.commit()

    def genKeyBlkSz(self):
        key=base64.b64encode(os.urandom(32))
        blockSize=random.randint(self.blkSize[0],self.blkSize[1])
        return {'key':key,'bs':blockSize}
    
    def aesE(self,key,chunk):
        iv=os.urandom(16)
        cipher=AES.new(base64.b64decode(key),AES.MODE_CFB,iv)
        data=iv+cipher.encrypt(chunk)
        return data
    
    def adjustKey(self,key):
        if len(key) < 32:
            key=key+' '*(32-len(key))
        if len(key) > 32:
            key=key[:32]
        if type(key) == type(str()):
            key=key.encode()
        return key

    def encryptKeyFile(self,keyfile):
        with open(keyfile,'rb') as idata, open(os.path.splitext(keyfile)[0]+".eke","wb") as odata:
            while True:
                data=idata.read(self.keyfile_bs)
                if not data:
                    break
                key=base64.b64encode(self.adjustKey(self.userKey))
                odata.write(self.aesE(key,data))
        os.remove(keyfile)
    
    def insertHMAC(self,hmac):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''
        insert into hmac (shasum) values ("{}");
        '''.format(base64.b64encode(hmac).decode())
        cursor.execute(sql)
        db.commit()
    def getHMAC(self):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''
        select shasum from hmac where rowid=1;
        '''
        cursor.execute(sql)
        result=cursor.fetchone()
        if result == None:
            print(self.nohmac)
        else:
            result=result[0]
        return result

    def verifyHMAC(self,file,hsum=None):
        fhsum=base64.b64encode(self.generateHMAC(file)).decode()
        if hsum == None:
            rhsum=self.getHMAC()
        else:
            rhsum=hsum
        if fhsum != rhsum:
            print(self.badhmac.format(fhsum,rhsum))
    
    def generateHMAC(self,file):
        hmac=HMAC.new(self.adjustKey(self.userKey),digestmod=SHA512)
        with open(file,'rb') as idata:
            while True:
                data=idata.read(self.keyfile_bs)
                if not data:
                    break
                hmac.update(data)
        return hmac.digest()

    def encryptMain(self):
        counter=0
        encryptRm=[self.ifile]
        if os.path.exists(self.keyfile):
            os.remove(self.keyfile)
        self.DB()
        self.mkTable()
        with open(self.ifile,'rb') as idata, open(self.ofile,'wb') as odata:
            while True:
                block=self.genKeyBlkSz()
                blockS=block['bs']
                data=idata.read(blockS)
                if not data:
                    break
                d=self.aesE(block['key'],data)
                self.insertValues(block['key'].decode(),len(d))
                odata.write(d)
                if ( counter % 100 ) == 0:
                    self.db['db'].commit()
                counter+=1
        hmac=self.generateHMAC(self.ofile)
        self.insertHMAC(hmac)
        self.db['db'].commit()
        self.db['db'].close()
        self.encryptKeyFile(self.keyfile)
        
        kfHmac=self.generateHMAC(os.path.splitext(self.keyfile)[0]+".eke")
        with open(self.ofile,'rb') as idata, open(self.ofile+'.tmp','wb') as odata:
            odata.write(kfHmac)
            while True:
                data=idata.read(8176)
                if not data:
                    break
                odata.write(data)
        os.remove(self.ofile)
        os.rename(self.ofile+".tmp",self.ofile)
        
        for file in encryptRm:
            os.remove(file)


    def getRows(self):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''select count(rowid) as count from keys;'''
        cursor.execute(sql)
        return cursor.fetchone()

    def getKeyBlkSz(self,rowid):
        db=self.db['db']
        cursor=self.db['cursor']
        sql='''
        select key,blockSize from keys where rowid={};
        '''.format(rowid)
        cursor.execute(sql)
        return cursor.fetchone()
    
    def aesD(self,key,chunk):
        iv=chunk[:16]
        cipherText=chunk[16:]
        cipher=AES.new(base64.b64decode(key),AES.MODE_CFB,iv)
        plaintext=cipher.decrypt(cipherText)
        return plaintext

    def decryptKeyFile(self,keyfile):
        with open(keyfile,'rb') as idata, open(os.path.splitext(keyfile)[0]+'.key','wb') as odata:
            while True:
                data=idata.read(self.keyfile_bs+16)
                if not data:
                    break
                key=self.adjustKey(self.userKey)
                odata.write(self.aesD(base64.b64encode(key),data))
        os.remove(keyfile)

    def decryptMain(self):
        decryptRm=[self.ofile,self.keyfile]
        #get the keyfile hmac and verify it
        kfHmac=b''
        with open(self.ofile,'rb') as idata, open(self.ofile+".tmp",'wb') as odata:
            kfHmac=idata.read(64)
            while True:
                data=idata.read(8176)
                if not data:
                    break
                odata.write(data)
        os.remove(self.ofile)
        os.rename(self.ofile+".tmp",self.ofile)
        self.verifyHMAC(os.path.splitext(self.keyfile)[0]+".eke",base64.b64encode(kfHmac).decode())
        #begin remainder of decryption run
        self.decryptKeyFile(os.path.splitext(self.keyfile)[0]+".eke")
        self.DB() 
        rows=self.getRows()
        db=self.db['db']
        cursor=self.db['cursor']
        self.verifyHMAC(self.ofile)
        counter=1
        if rows != None:
            rows=rows[0]
            with open(self.ofile,'rb') as idata, open(self.ifile,'wb') as odata:
                while True:
                    block=self.getKeyBlkSz(counter)
                    if block != None:
                        bs=block[1]
                        key=block[0].encode()
                        data=idata.read(int(bs))
                        if not data:
                            break
                        d=self.aesD(key,data)
                        odata.write(d)
                    else:
                        break
                    counter+=1
        self.db['db'].close()
        for file in decryptRm:
            os.remove(file)



#'''
def main():
    #example useage code
    helper='''
        ./capsule2.py $password $infile $mode
        $mode:
            e - encrypt
            d - decrypt
        '''
    if len(sys.argv) == 4:
        a=capsule()
        datExt='.ap2'
        keyExt='.key'
        a.ifile=sys.argv[2]
        a.keyfile=a.ifile+keyExt
        a.ofile=a.ifile+datExt
        a.userKey=sys.argv[1]
        if sys.argv[3] == 'e':
            if not os.path.exists(a.ifile):
                exit("file does not exist: '{}'".format(a.ifile))
            a.encryptMain()
        elif sys.argv[3] == 'd':
            if not os.path.exists(a.ofile):
                exit("data file does not exist: '{}'".format(a.ofile))
            if not os.path.exists(os.path.splitext(a.keyfile)[0]+".eke"):
                exit("key file does not exist: '{}'".format(os.path.splitext(a.keyfile)[0]+'.eke'))
            a.decryptMain()
        else:
            print(helper)
    else:
        print(helper)

if __name__ == '__main__':
    main()
#'''
