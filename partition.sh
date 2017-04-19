#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: ${0} <device>";
  exit 111;
fi

DEVICE=$1
PARTMATCH="${1}*"
PARTITION="${1}1"

for n in $PARTMATCH ; do umount -f $n ; done

(
echo o # Create a new empty DOS partition table
echo n # Add a new partition
echo p # Primary partition
echo 1 # Partition number
echo   # First sector (Accept default: 1)
echo   # Last sector (Accept default: varies)
echo t # Set partition type
echo 7 # Partition type 7 (HPFS/NTFS/ExFAT)
echo w # Write changes
) | fdisk $DEVICE 

exit $? 
