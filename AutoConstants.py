# Author : Vinayak Wagh
# Date   : 11/8/2019


ANDROID_DEVICES = "adb devices"
GET_EVENT = "getevent"
SEND_EVENT = "sendevent"
TOOL_EVENT_CODE = "0001"
TOUCH_EVENT_CODE = "0003"
PHYSICAL_DEVICE_X = "0035"
PHYSICAL_DEVICE_Y = "0036"
EMULATOR_X = "0000"
EMULATOR_Y = "0001"
WINDOW_DUMPSYS = "dumpsys window windows"
WINDOW_SIZE = "wm size"
SERVER_STATUS_COMMAND = "service call window 3"
SERVER_STOP_COMMAND = "service call window 2"
SERVER_START_COMMAND = "service call window 1 i32 4939"
TCP_FORWARD = "forward tcp"
LOCALHOST = "127.0.0.1"
DUMP_COMMAND = "DUMP"
IMG_CLUSTER_COUNT = 4
SCREENCAP_COMMAND = "/system/bin/screencap -p /storage/sdcard0/snaps.png"
