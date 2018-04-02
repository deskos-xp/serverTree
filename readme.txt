#cpio archive format now added
-c,--cpio

#aes encryption now provided

-e,--encrypt-archive $password -> encrypts the archive before sending the data over the ssh connection with the .aes extension
--decrypt $password -z $zipname -> will decrypt the archive provided by -z using the password provided to --decrypt

#now contains the ability to tarball with xz, gz, and bz2.

#paramiko uses an sftp/scp client to perform filetransfers 

#a python3 script to:
scan a directory -> create an xml manifest of its contents -> zip the xml manifest and the directory up into an archive -> send to a remote server expecting a zipfile


#if id_rsa fails, attempt password authentication, if given password is provided with the -P option

#complete utility with all modules built in
#includes cmdline utility
serverTree.py

#useage

#get help menu
python3 serverTree.py -h

#general useage
python serverTree.py -u carl -k ~/.ssh/id_rsa -s ~/Documents/ -d /home/remote/Downloads -z try.zip 
#-d applies to the remote host only
#-z will take a filename with, or without, the zip extension and ensure the extension is added if needed
#-u is the remote server user
#-h is help

#expanded general useage
python serverTree.py -u carl -k ~/.ssh/id_rsa -s ~/Documents/resume -d /home/carl/Downloads -z try.zip -H 192.168.1.9 -p 22

#in the event that you do not have rsa keys set up in openssh, you can use the -F, or --force-password $PASSWORD, option to skip using the rsa key

#a brief video on the tool's operation can be on youtube at:
https://youtu.be/JPgqb_Jnl5Q
# an update videoon the tool's useage can be found at
https://youtu.be/R4Xy94Dp_6g
#best of luck,
NoGuiLinux

#example xml entry
<?xml version="1.0"?>
<file name="resume-10262017v1.pdf" num="6">
  <allocation>
    <fname>resume-10262017v1.pdf</fname>
    <fsize>52877</fsize>
  </allocation>
  <integ>
    <value>3cb4c85d94ea03b17a123e75144c71425829c042a60cfaff61eca0b7489ba12ce1c28811095d8286dcb4231cdbd18ef56dc31fcd535580ae6c57c36b43d65902</value>
    <hash>sha512</hash>
  </integ>
  <owners>
    <uid>1000</uid>
    <user>carl</user>
    <gid>1000</gid>
    <group>carl</group>
  </owners>
  <controls>
    <permissions>0644</permissions>
    <ftype>Regular file</ftype>
    <lsattr>--------------e----</lsattr>
    <facl>
      <acl num="0">user::rw-</acl>
      <acl num="1">group::r--</acl>
      <acl num="2">other::r--</acl>
    </facl>
  </controls>
</file>


#encryption mode implementation now adds the --encrpt-mode option supporting three different modes of encryption
#chacha20,cfb,cbc,lattice
#lattice utilizes cfb and chacha20 in a double cascade
#to decrypt lattice, you will either have develop your own tool to perform the decryption, or use my eLattice.py module, under lib/, which can be used as a standalone library, should you so choose for your own projects.

think of lattice like the depiction below
cc20=chacha20
cfb=aes cfb mode

==============
cfb |cc20|cfb 
==============
cc20|cfb |cc20
==============
data|data|data

#here is an example of useage

	python serverTree.py -u $USER -k ~/.ssh/id_rsa -d /home/carl/Downloads -s ~/Documents/resume --encrypt-mode chacha20 -e $PASSWORD
	python serverTree.py --decrypt $PASSWORD --encrypt-mode chacha20 -z resume.zip.cc20
