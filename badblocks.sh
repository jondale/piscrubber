#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ${0} <device>";
  exit 111;
fi

DEVICE=$1
PARTMATCH="${1}*"

for n in $PARTMATCH ; do umount -f $n ; done
rm -f badblocks.log
touch badblocks.log
badblocks -s -o badblocks.log $DEVICE

if [[ -s badblocks.log ]] ; then
  exit 1
else
  exit 0
fi ; 
 
