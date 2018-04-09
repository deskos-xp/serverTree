#! /usr/bin/env python3
#NoGuiLinux

#like the orginal capsule, but with a bit of a change
#encrypted block sizes are NOT static, their sizes are stored in the keyfile with their corresponding keys
try:
    from Cryptodome.Cipher import AES
except:
    from Crypto.Cipher import AES

import sqlite3,os,base64
import random

class capsule:
    ifile=''
    ofile=''
    keyfile=''
    db={}
    userKey=''
    keyfile_bs=256
    blkSize=(128,8176)
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
        self.db['db'].commit()
        self.db['db'].close()
        self.encryptKeyFile(self.keyfile)
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
        self.decryptKeyFile(os.path.splitext(self.keyfile)[0]+".eke")
        self.DB()
        rows=self.getRows()
        db=self.db['db']
        cursor=self.db['cursor']
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
#example useage code
a=capsule()
a.keyfile='smb.conf.key'
a.ifile='smb.conf'
a.ofile='smb.conf.cap2'
a.userKey='password 123'
a.encryptMain()
#a.decryptMain()
#'''
