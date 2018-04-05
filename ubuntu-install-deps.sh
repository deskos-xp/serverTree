#! /usr/bin/env bash
#NoGuiLinux
sudo apt-get install `cat ubuntu-deps.txt`
sudo pip3 install `cat python-deps.txt`
