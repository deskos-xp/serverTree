#! /usr/bin/python3
import os,paramiko,sys
import colors
color=colors.colors()
class ssh:
    keyFile=""
    host="127.0.0.1"
    port=22
    username=""
    password=""
    forcePassword=None
    def printTotals(self,transferred, toBeTransferred):
        displayString=color.transfer+"Transferred [Bytes]: {0}/{1} - {2}".format(color.start+str(transferred)+color.end,color.stop+str(toBeTransferred)+color.end,color.stop+str(round(100*(transferred/toBeTransferred),2))+color.end )+color.end
        #for me, i like to not see a whole bunch of Transfered...yadeeyada text, asside from the filesystem based info
        #so backspace over previous display string, and print the new string
        #talk about automation
        print(displayString,end=str(len(displayString)*'\b'))

    def client(self):
        Client=paramiko.SSHClient()
        Client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if self.forcePassword == None:
            try:
                if os.path.exists(os.path.realpath(os.path.expanduser(self.keyFile))):
                    Client.connect(self.host,port=self.port,username=self.username,key_filename=self.keyFile)
                else:
                    Client.connect(self.host,port=self.port,username=self.username,password=self.password)
            except:
                Client.connect(self.host,port=self.port,username=self.username,password=self.password)
        else:
            try:
                Client.connect(self.host,port=self.port,username=self.username,password=self.forcePassword)
            except:
                exit(color.errors+"something went wrong and forcePassword could not be used!"+colors.end)
        return Client

    def transfer(self,client,src=None,dest=None,mode="put"):
        sftp_client=client.open_sftp()
        if src != None:
            if dest != None:
                if mode == "put":
                    sftp_client.put(src,dest,callback=self.printTotals)
                elif mode == "get":
                    sftp_client.get(src,dest,callback=self.printTotals)
                else:
                    exit("invalid mode")
                print("-"*os.get_terminal_size().columns)
            else:
                print("dest cannot be blank")
        else:
            print("src cannot be blank")
   
    def clientClose(self,client):
        client.close()

