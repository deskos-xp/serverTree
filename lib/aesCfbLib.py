from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import os

string="one two three"
key='one two four    '
iv=os.urandom(16)


class aesCFB:
    key=b''
    def fixKey(self):
        if type(self.key) == type(str()):
            self.key=self.key.encode()
        if len(self.key) < 16:
            self.key+=b' '*(16-len(self.key))
        elif 16 < len(self.key) < 24:
            self.key+=b' '*(24-len(self.key))
        elif 24 < len(self.key) < 32:
            self.key+=b' '*(32-len(self.key))
        else:
            print('key is longer than 32 bytes... truncating... unfortunately...')
            self.key=self.key[:32]

    def encrypt(self,plaintext):
        cipherText=''
        iv=os.urandom(16)
        cipher=AES.new(self.key,AES.MODE_CFB,iv)
        cipherText=cipher.encrypt(plaintext)
        return iv+cipherText

    def decrypt(self,cipherText):
        plainText=''
        iv=cipherText[:16]
        cipherText=cipherText[16:]
        cipher=AES.new(self.key,AES.MODE_CFB,iv)
        plainText=cipher.decrypt(cipherText)
        return plainText

#this acts like cbc, except that cbc uses cobe-block chaining with the iv's, i think, not too sure, still getting the hang of aes
#regardless, instead of slurping the file, and risking lock up due to too much memory useage, this read blocksize in bytes of input data
#and encrypt that specific chunk with its own randomly generated IV
#decryption follows a similar pattern, except that it be blocksize+iv_size_in_bytes being 16
#the smaller the blocksize, the more iv's, the more processing overhead to decrypt each chunk
class aesFile:        
    key=b''
    block_size=128
    def encryptFile(self,fname):
        cipher=aesCFB()
        cipher.key=self.key
        cipher.fixKey()
        ofile=open(fname+'.aes','wb')
        with open(fname,'rb') as idata:
            while True:
                data=idata.read(self.block_size)
                if not data:
                    break
                ofile.write(cipher.encrypt(data))
        ofile.close()

    def decryptFile(self,fname):
        cipher=aesCFB()
        cipher.key=self.key
        cipher.fixKey()
        ofile=open(os.path.splitext(fname)[0],'wb')
        with open(fname,'rb') as idata:
            while True:
                data=idata.read(self.block_size+16)
                if not data:
                    break
                ofile.write(cipher.decrypt(data))
        ofile.close()

#example code
'''
cipher=aesFile()
cipher.key='there\'s a rumbly in ma\' tumbly'
cipher.block_size=512
cipher.encryptFile('listener.py')
cipher.decryptFile('listener.py.aes')
'''
