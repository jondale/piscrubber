#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ${0} <device> [label]";
  exit 111;
fi

if [ -z "$2"]; then
    LABEL="USBDRIVE"
else
    LABEL=$2
fi 

DEVICE=$1
PARTMATCH="${1}*"
PARTITION="${1}1"

for n in $PARTMATCH ; do umount -f $n ; done
mkfs.exfat $PARTITION -n $LABEL

exit $? 
