#! /usr/bin/env python3
#NoGuiLinux

#I develop each implementation with its own AES,ChaCha20 functions to allow for each unit to be used as a standalone lib
#a standalone lib to encrypt a file using randomly generated 32 byte long keys, stored in a keyfile, which is encrypted
#with the actual user key ; for this to work properly as a secure mode of transmission, the data is sent in one transmission
#the key file is sent in another transmission ; and for a third transmission the actual key to the key file
#the data contained within the *.cap file is useless without the keyfile (*.eke), which is useless without the actual user provided key
#the idea is to ensure that the blocks of data are encrypted with their own key AND nonce, so even if one block is compromised, the 
#remaining data blocks will still be safe

import sqlite3,os,base64
try:
    from Cryptodome.Cipher import AES,ChaCha20
except:
    from Crypto.Cipher import AES,ChaCha20

class capsule:
    ifile=''
    ofile=''
    oPath=''
    keyFile=''
    ext='.cap'
    block_size=128
    db=''

    key=''
    NOTFILE="'{}' is not a file!"
    NOEXIST="'{}' does not exist!"
    TRUNCATE="the key is too long... key will be truncated to 32 characters in length!"
    userKey=''

    def adjustKey(self,key):
        if len(key) < 32:
            key=key+' '*(32-len(key))
        if len(key) > 32:
            key=key[:32]
            print(self.TRUNCATE)
        if type(key) == type(str()):
            key=key.encode()
        return key

    def mkOfile(self):
        self.ofile=os.path.join(self.oPath,os.path.split(self.ifile+self.ext)[1])
        self.keyFile=os.path.join(self.oPath,os.path.split(self.ifile+".key")[1])
    
    def genRandomKey(self):
        rKey=base64.b64encode(os.urandom(32))
        return rKey
    
    def DB(self,decrypt=None):
        if os.path.exists(self.keyFile):
            if os.path.isfile(self.keyFile):
                if decrypt == None:
                    os.remove(self.keyFile)
            else:
                exit('keyFile "{}" exists but is not a file!'.format(self.keyFile))
        db=sqlite3.connect(self.keyFile)
        cursor=db.cursor()
        return {'db':db,'cursor':cursor}

    def mkKeysTable(self):
        sql='''
        create table if not exists
        keys(key text,id INTEGER PRIMARY KEY AUTOINCREMENT);
        '''
        self.db['cursor'].execute(sql)

    def insertKey(self,key):
        sql='''
        insert into keys(key) values
        ("{}");
        '''.format(key.decode())
        self.db['cursor'].execute(sql)
    def getKey(self,counter):
        sql='''
        select key from keys where id={};
        '''.format(counter)
        self.db['cursor'].execute(sql)
        key=self.db['cursor'].fetchone()
        return key[0]

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
    #need to write function to encrypt keyfile specifically
    def encKeyFile(self):
        key=self.userKey
        with open(self.keyFile,'rb') as idata, open(os.path.splitext(self.keyFile)[0]+".eke","wb") as odata:
            while True:
                data=idata.read(self.block_size)
                if not data:
                    break
                odata.write(self.aesE(data))
        os.remove(self.keyFile)
    #need to write function to decrypt keyfile specifically
    def decKeyFile(self):
        key=self.userKey
        with open(os.path.splitext(self.keyFile)[0]+".eke","rb") as idata, open(self.keyFile,'wb') as odata:
            while True:
                data=idata.read(self.block_size+16)
                if not data:
                    break
                odata.write(self.aesD(data))
        os.remove(os.path.splitext(self.keyFile)[0]+'.eke')

    def encryptMain(self):
        counter=1
        self.mkOfile()
        self.db=self.DB()
        self.mkKeysTable()
        with open(self.ifile,'rb') as idata, open(self.ofile,'wb') as odata:
            while True:
                data=idata.read(self.block_size)
                if not data:
                    break
                rKey=self.genRandomKey()
                self.insertKey(rKey)
                self.key=base64.b64decode(rKey)
                odata.write(self.aesE(data))
                ## this is where individual chunks will be encrypted with their own independent key using aes_cfb
                if (counter % 50) == 0:
                    self.db['db'].commit()
                counter+=1
        self.db['db'].commit()
        self.db['db'].close()
        #after this point is where the final section will occur, where the key file will be encrypted
        self.encKeyFile()
        #cleanup time
        os.remove(self.ifile)

    def decryptMain(self):
        #keyfile must be decrypted first
        self.decKeyFile()
        counter=1
        self.mkOfile()
        self.db=self.DB(decrypt=True)
        self.mkKeysTable()
        with open(self.ofile,'rb') as idata, open(self.ifile,'wb') as odata:
            while True:
                data=idata.read(self.block_size+16)
                if not data:
                    break
                #decryption of chunks time
                rKey=self.getKey(counter)
                self.key=base64.b64decode(rKey)
                odata.write(self.aesD(data))
                if (counter % 50) == 0:
                    self.db['db'].commit()
                counter+=1
        self.db['db'].commit()
        self.db['db'].close()
        #cleanup remaining files
        os.remove(self.ofile)
        os.remove(self.keyFile)

'''
#example useage code
enc=capsule()
enc.oPath='.'
enc.ifile='smb.conf'
enc.userKey='1S@vi0r2all'

try:
    enc.encryptMain()
except OSError as err:
    print(err)

try:
    enc.decryptMain()
except OSError as err:
    print(err)
'''
