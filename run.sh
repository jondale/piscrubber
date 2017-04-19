#!/bin/bash

HOME=/home/pi/piscrubber
LOG="${HOME}/piscrubber.log"

exec &> $LOG

cd $HOME

while :
do
  sudo ./piscrubber.py
done

