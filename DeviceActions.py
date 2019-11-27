# Author : Vinayak Wagh
# Date   : 11/8/2019

import subprocess
import AutoConstants
import re
import time


class Actions:
    def __init__(self, device=None):
        self.device = device
        self.touch_dev = None
        self.x_range = None
        self.y_range = None
        self.width = None
        self.height = None
        self.windows = None
        self.current_focus = None

        self.tool_event_list = []
        self.touch_event_list = []

        self.touch_event_command = ''

        self.command = 'adb -s ' + self.device + ' '
        self.command_shell = 'adb -s ' + self.device + ' shell '
        self.window_command = self.command_shell + AutoConstants.WINDOW_DUMPSYS
        self.window_size_command = self.command_shell + AutoConstants.WINDOW_SIZE

        get_event = subprocess.Popen(self.command_shell + AutoConstants.GET_EVENT + ' -i', shell=False,
                                     stdout=subprocess.PIPE)
        add_devices = get_event.stdout.read()

        # Touch Events
        for add_device in re.compile(r'^add device .*\r?\n(?: .*\r?\n)+', re.MULTILINE).findall(add_devices):
            tool_event_check = False
            touch_event_check = False
            tool_event_key = None
            touch_event_key = None
            tool_event_value = None
            touch_event_value = None

            event_device, name = re.match(r'add device \d+: (\S+)(?:.*\r?\n)+?\s+name:\s+"(.*?)"', add_device).groups()

            for event_key, event_value in re.compile(r'^    (?:....? \(?([\da-f]{4})\)?): (.*\r?\n(?:     .*\r?\n)*)',
                                                     re.MULTILINE).findall(add_device):
                if event_key == AutoConstants.TOOL_EVENT_CODE:      # Tool Event Key is 0001
                    tool_event_check = True
                    tool_event_key = event_key
                    tool_event_value = event_value
                elif event_key == AutoConstants.TOUCH_EVENT_CODE:   # Touch Event Key is 0003
                    touch_event_check = True
                    touch_event_key = event_key
                    touch_event_value = event_value

            if tool_event_check and touch_event_check:
                self.touch_dev = event_device

                # Prepare Tool Event List
                tool_prop = tool_event_value.split()
                for tool in tool_prop:
                    self.tool_event_list.append([tool_event_key, tool])

                # Prepare Touch Event List
                for event in re.compile(
                        r'(?P<type>[\da-f]{4}) (?:[: ]+)?value -?\d+, min (?P<min>-?\d+), max (?P<max>-?\d+), fuzz -?\d+,? flat -?\d+(?:, resolution \d+)?[\r\n]+',
                        re.MULTILINE).finditer(touch_event_value):
                    event_dict = event.groupdict()
                    if event_dict['type'] == AutoConstants.PHYSICAL_DEVICE_X or \
                            event_dict['type'] == AutoConstants.EMULATOR_X:
                        self.x_range = [int(event_dict['min']), int(event_dict['max'])]
                    elif event_dict['type'] == AutoConstants.PHYSICAL_DEVICE_Y or \
                            event_dict['type'] == AutoConstants.EMULATOR_Y:
                        self.y_range = [int(event_dict['min']), int(event_dict['max'])]
                    else:
                        pass
                    self.touch_event_list.append([touch_event_key, event_dict['type']])
                break

        # Window Size
        wm_size = subprocess.Popen(self.window_size_command, shell=False, stdout=subprocess.PIPE)
        wm_size = wm_size.stdout.read()
        dimensions = re.compile(r'Physical size: (\d+)x(\d+)').findall(wm_size)
        self.width = dimensions[0][0]
        self.height = dimensions[0][1]

    def get_window(self):
        dump = subprocess.Popen(self.window_command, shell=False,
                                stdout=subprocess.PIPE)
        window_dump = dump.stdout.read()

        regexp = re.compile(
            r'Window #\d+[:\s\r\n]+Window\{(?P<hash>[a-f\d]{8}) u0 (?P<title>.*).*\}:?[\r\n]+(?P<attributes>(?:    .*[\r\n]+)+)',
            re.MULTILINE)
        self.windows = [m.groupdict() for m in regexp.finditer(window_dump)]

        self.current_focus = re.search('mCurrentFocus=Window\{(?P<hash>\S*) (?P<title2>\S*) (?P<title>\S*)\S+',
                                       window_dump).groupdict()

    def get_current_window_name(self):
        self.get_window()
        if self.current_focus:
            return self.current_focus['title']
        else:
            return None

    def get_current_window_hash(self):
        self.get_window()
        for window in self.windows:
            if window['hash'] == self.current_focus['hash']:
                return [window][0]['hash']
        return None

    def get_current_window_bounds(self):
        self.get_window()
        bound_list = []
        for window in self.windows:
            if window['hash'] == self.current_focus['hash']:
                for temp in re.compile(r'mShownFrame=\[([\d\.]+),([\d\.]+)\]\[([\d\.]+),([\d\.]+)\]').search(
                        [window][0]['attributes']).groups():
                    bound_list.append(int(float(temp)))
                return bound_list
        return None

    def translate_x_y(self, x, y):
        return (x * (int(self.x_range[1]) - int(self.x_range[0])) / int(self.width) + int(self.x_range[0]),
                y * int((self.y_range[1]) - int(self.y_range[0])) / int(self.height) + int(self.y_range[0]))

    def tool_events(self, value):
        for tool in self.tool_event_list:
            self.touch_event_command = self.touch_event_command + AutoConstants.SEND_EVENT + ' ' + self.touch_dev + ' ' + str(
                int(tool[0], 16)) + ' ' + str(int(tool[1], 16)) + ' ' + str(value) + ';'
        if value == 0:
            self.touch_event_command = self.touch_event_command + AutoConstants.SEND_EVENT + ' ' + self.touch_dev + ' 0 0 0;'

    def touch_events(self, x, y):
        for touch in self.touch_event_list:
            value = 1
            if touch[1] == AutoConstants.PHYSICAL_DEVICE_X or touch[1] == AutoConstants.EMULATOR_X:
                value = x
            elif touch[1] == AutoConstants.PHYSICAL_DEVICE_Y or touch[1] == AutoConstants.EMULATOR_Y:
                value = y

            self.touch_event_command = self.touch_event_command + AutoConstants.SEND_EVENT + ' ' + self.touch_dev + ' ' + str(
                int(touch[0], 16)) + ' ' + str(int(touch[1], 16)) + ' ' + str(value) + ';'

    def event_separator(self):
        self.touch_event_command = self.touch_event_command + AutoConstants.SEND_EVENT + ' ' + self.touch_dev + ' 0 2 0;'
        self.touch_event_command = self.touch_event_command + AutoConstants.SEND_EVENT + ' ' + self.touch_dev + ' 0 0 0;'

    def touch_down(self, x, y):
        x, y = self.translate_x_y(x, y)
        self.tool_events(1)
        self.touch_events(x, y)
        self.event_separator()

    def touch_up(self, x, y):
        x, y = self.translate_x_y(x, y)
        self.touch_events(x, y)
        self.event_separator()
        self.tool_events(0)

    def tap_on(self, x, y):
        self.touch_event_command = ''
        self.touch_down(x, y)
        self.touch_up(x, y)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()
        return True

    def long_press(self, x, y, delay=2):
        self.touch_event_command = ''
        self.touch_down(x, y)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()
        time.sleep(delay)
        self.touch_event_command = ''
        self.touch_up(x, y)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()
        return True

    def swipe(self, x1, y1, x2, y2):
        self.touch_event_command = ''
        self.touch_down(x1, y1)
        for i in range(1, 4):
            x, y = (x1 + (x2 - x1) * i / 4, y1 + (y2 - y1) * i / 4)
            self.touch_down(x, y)
        self.touch_up(x2, y2)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()

    def hold_and_drag(self, x1, y1, x2, y2):
        self.touch_event_command = ''
        self.touch_down(x1, y1)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()
        time.sleep(2)
        self.touch_event_command = ''
        for i in range(1, 4):
            x, y = (x1 + (x2 - x1) * i / 4, y1 + (y2 - y1) * i / 4)
            self.touch_down(x, y)
        self.touch_up(x2, y2)
        tap_event = subprocess.Popen(self.command_shell + self.touch_event_command, shell=False, stdout=subprocess.PIPE)
        tap_event.stdout.read()
