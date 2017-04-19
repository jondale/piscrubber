#!/usr/bin/python

import threading
import time
import re
import os.path
from subprocess import call
import glib
import gobject
from pyudev import Context, Monitor
from pyudev.glib import MonitorObserver

import logging
logging.info("piscrubber")
logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

# ####### CONFIG ###################

scrub_path = "/usr/bin/scrub"
partition_path = "/home/pi/piscrubber/partition.sh"
format_path = "/home/pi/piscrubber/format.sh"
badblocks_path = "/home/pi/piscrubber/badblocks.sh"

# ####### CONFIG ###################


class DeviceScreen:
    lcd = None
    lcd_time = 0
    status = 0

    def __init__(self):
        import Adafruit_CharLCD as LCD
        self.lcd = LCD.Adafruit_CharLCDPlate()
        self.lcd.set_color(1, 1, 1)
        self.status = 1

    def off(self):
        if self.status != 0:
            self.lcd.set_color(0, 0, 0)
            self.status = 0

    def on(self):
        if self.status != 1:
            self.lcd.set_color(1, 1, 1)
            self.status = 1

    def say(self, line1=None, line2="", seconds=0):
        logger.info("say: {}\t{}".format(line1, line2))
        self.lcd.clear()
        self.on()
        if not line1:
            self.lcd.message("   (o)    (o)   \n      ^--^       ")
        else:
            msg = "{}\n{}".format(line1, line2)
            self.lcd.message(msg)
            self.lcd_time = seconds

    def step(self):
        if self.lcd_time > 0:
            self.lcd_time -= 1
            if self.lcd_time <= 0:
                self.lcd_time = 0
                self.say()


class DiskScrubber:
    logger = None
    device = None
    label = None
    lcd = None
    start_time = None
    last_time = None

    state = None
    seconds = 0

    def __init__(self):
        self.lcd = DeviceScreen()
        self.lcd.say()

    def scrub(self, device, label=None):
        logger.info("SCRUB CALL: {} {}".format(device, label))
        if not self.device:
            self.device = device
            self.label = label or device
            self.state = "INIT"
            self.seconds = 10
        elif self.device == device and not self.label:
            self.label = label

    def time_format(self, t):
            hours = int(t / 3600)
            minutes = int((t - (hours*3600)) / 60)
            seconds = int(t - (hours*3600) - (minutes*60))
            return "{}h {}m {}s".format(hours, minutes, seconds)

    def step(self):

        if not self.state or not self.device:
            self.lcd.step()
            return

        if not os.path.exists(self.device):
            self.lcd.say("DEVICE REMOVED")
            time.sleep(5)
            self.lcd.say()
            self.device = None
            self.state = None
            return

        if self.state == "INIT":
            self.seconds -= 1
            if self.seconds > 0:
                msg = "{} SECONDS".format(self.seconds)
                self.lcd.say(self.label, msg)
            else:
                self.lcd.say(self.label, "PREPARING...")
                self.state = "SCRUB1"
                self.start_time = time.time()
                self.last_time = time.time()
                return

        if self.state == "SCRUB1":
            # NNSA NAP-14.1-C
            self.lcd.say(self.label, "1: RANDOM")
            r = call([scrub_path, "-S", "-f", "-p", "random", self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("Pass 1: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "SCRUB2"
            return

        if self.state == "SCRUB2":
            self.lcd.say(self.label, "2: RANDOM")
            r = call([scrub_path, "-S", "-f", "-p", "random", self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("Pass 2: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "SCRUB3"
            return

        if self.state == "SCRUB3":
            self.lcd.say(self.label, "3: 0 + VERIFY")
            r = call([scrub_path, "-S", "-f", "-p", "verify", self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("Pass 3: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "SCRUB4"
            return

        if self.state == "SCRUB4":
            self.lcd.say(self.label, "4: PARTITION")
            time.sleep(10)
            r = call([partition_path, self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("PARTITION: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "SCRUB5"
            return

        if self.state == "SCRUB5":
            self.lcd.say(self.label, "5: FORMAT")
            time.sleep(10)
            r = call([format_path, self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("FORMAT: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "SCRUB6"
            return

        if self.state == "SCRUB6":
            self.lcd.say(self.label, "6: BLOCK TEST")
            time.sleep(10)
            r = call([badblocks_path, self.device])
            if r != 0:
                self.state = "FAILED"
                return
            pass_time = self.time_format(time.time() - self.last_time)
            self.last_time = time.time()
            total_time = self.time_format(time.time() - self.start_time)
            logger.info("BADBLOCKS: {}".format(pass_time))
            logger.info("Total: {}".format(total_time))
            self.state = "REMOVE"
            return

        if self.state == "REMOVE":
            self.lcd.on()
            t = self.time_format(time.time() - self.start_time)
            self.lcd.say("SCRUB COMPLETE", t)
            self.state = "REMOVE-FLASH-ON"
            return

        if self.state == "REMOVE-FLASH-ON":
            self.lcd.on()
            self.state = "REMOVE-FLASH-OFF"
            return

        if self.state == "REMOVE-FLASH-OFF":
            self.lcd.off()
            self.state = "REMOVE-FLASH-ON"
            return

        if self.state == "FAILED":
            self.state = "FAILED-CHECK"
            self.lcd.say("FAILED", "TRY AGAIN", 60)
            return

        if self.state == "FAILED-CHECK":
            return

        self.lcd.step()


def device_change(observer, device):
    if device.get("DEVTYPE") == "disk":
        path = device.get("DEVNAME")
        vendor = device.get("ID_VENDOR")
        model = device.get("ID_MODEL")
        label = "{} {}".format(vendor, model)

        logger.info("{}:\t{}\t{}".format(device.action, path, label))
        if device.action == "add":
            scrubber.scrub(path, label)


def start_listening():
    context = Context()
    monitor = Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')
    observer = MonitorObserver(monitor)
    observer.connect('device-event', device_change)
    monitor.start()
    gobject.threads_init()
    glib.MainLoop().run()


scrubber = DiskScrubber()

thread = threading.Thread(target=start_listening)
thread.daemon = True
thread.start()

while True:
    time.sleep(1)
    scrubber.step()
