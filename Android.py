# Author : Vinayak Wagh
# Date   : 11/8/2019
import subprocess
import sys

import AutoConstants
import DeviceActions
import DeviceConfig
import UserModule
import GrabUI


def get_device_id():
    devices = subprocess.Popen(AutoConstants.ANDROID_DEVICES, shell=False,
                               stdout=subprocess.PIPE).stdout.read().split()
    return (True, devices[4]) if len(devices) == 6 else (False, devices)


class Make:
    def __init__(self, index=None):
        self.index = index
        self.device_id = None

    def device(self):
        return_code, dev = get_device_id()
        if not return_code:
            if len(dev) == 4:
                print("You don't have any Android Device connected...Please connect device & try again")
                sys.exit(1)

        if self.index is None:
            if not return_code:
                if len(dev) > 6:
                    print(
                        "You have more than one Android Device connected...\\nIf you are using all the devices, "
                        "then don't forget to put them in DeviceConfig & use proper methods for initialization of "
                        "Main/Support DUTs: "
                        "\\nMake(index).device()")
                    self.device_id = dev[4]
                    print("For now, following Device is used as Main DUT: \\n" + str(dev[4]))
                elif dev is None:
                    print("adb devices returned None..Make sure your adb is running")
                    sys.exit(1)
            else:
                self.device_id = dev
                print("Created Instance of Default Device!!")

            action = DeviceActions.Actions(self.device_id)
            ui = GrabUI.UI(self.device_id, action)
        else:
            if DeviceConfig.devices_list[self.index] in dev:
                action = DeviceActions.Actions(DeviceConfig.devices_list[self.index])
                ui = GrabUI.UI(self.device_id, action)
                print("Created Instance of User Provided Device!!")
            else:
                print(
                    "Requested Device Number from DeviceConfig is not connected to machine...Please connect device & "
                    "try again")
                sys.exit(1)
        return UserModule.Module(action, ui)
