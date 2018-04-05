#! /usr/bin/env bash
#NoGuiLinux

function getDeps(){
	CONFIG="$1"
	if test "$2" == "" ; then
		xmllint --format --xpath '/resolv/install/text()' "$CONFIG" | sed s/'  '/''/g | tr '\n' ' ' 
	elif test "$2" == "remove" ; then
		xmllint --format --xpath '/resolv/remove/text()' "$CONFIG" | sed s/'  '/''/g | tr '\n' ' ' 
	else
		printf "that getDeps mode is unsupported" "\n"
		exit 1
	fi
}

function helper(){
cat << EOF
syntax:
see install commands:
	./$0 base_os DEMO
run install commands:
	./$0 base_os
where base_os can be:
	fedora
	ubuntu
EOF
}
function fail(){
	echo "something went wrong"
	exit 1
}
function ubuntu(){
	"$DEMO" apt-get install `getDeps ubuntu-deps.xml`
	if test $? != "0" ; then
		fail
	fi
	"$DEMO" pip3 install `getDeps python-deps.xml`
	if test $? != "0" ; then
		fail
	fi
}
function fedora(){
	"$DEMO" yum install `getDeps fedora-deps.xml`
	if test $? != "0" ; then
		fail
	fi
	"$DEMO" yum remove `getDeps fedora-deps.xml remove`
	if test $? != "0" ; then
		fail
	fi
	"$DEMO" pip3 install `getDeps python-deps.xml`
	if test $? != "0" ; then
		fail
	fi
}
function install_deps(){
	if test "$2" == "DEMO" ; then
		DEMO="echo"
	else
		DEMO=""
	fi
	OS="$1"
	if test "`whoami`" == "root" ; then
		if test "$OS" == "ubuntu" ; then
			ubuntu
		elif test "$OS" == "fedora" ; then
			fedora		
		else
			printf "'%s' : not supported as of yet\n" "$OS"
			helper
		fi
	else
		echo "user is not root!"
	fi
}
install_deps "$1" "$2"
