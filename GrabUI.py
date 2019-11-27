# Author : Vinayak Wagh
# Date   : 11/8/2019


import AutoConstants

import subprocess
import socket
import re
import os


class Widget:
    def __init__(self, action, level, line):
        self.action = action
        self.level = level
        self.line = line
        self.children = []

        self.class_name = None
        self.widget_id = None
        self.widget_text = None
        self.left = 0
        self.top = 0
        self.width = 0
        self.height = 0

        self.x = None
        self.y = None

    def get_level(self):
        return self.level

    def set_widget_x(self, value):
        self.x = value

    def get_widget_x(self):
        return self.x

    def set_widget_y(self, value):
        self.y = value

    def get_widget_y(self):
        return self.y

    def set_widget_left(self, value):
        self.left = value

    def get_widget_left(self):
        return self.left

    def set_widget_top(self, value):
        self.top = value

    def get_widget_top(self):
        return self.top

    def set_widget_width(self, value):
        self.width = value

    def get_widget_width(self):
        return self.width

    def set_widget_height(self, value):
        self.height = value

    def get_widget_height(self):
        return self.height

    def set_widget_id(self, value):
        self.widget_id = value

    def get_widget_id(self):
        return self.widget_id

    def set_widget_text(self, text):
        self.widget_text = text

    def get_widget_text(self):
        return self.widget_text

    def set_class_name(self, name):
        self.class_name = name

    def get_class_name(self):
        return self.class_name

    def get_children(self):
        return self.children

    def set_children(self, w):
        self.children.append(w)

    def touch(self):
        if self.x is None or self.y is None:
            return False
        return self.action.tap_on(self.x, self.y)

    def long_press(self):
        if self.x is None or self.y is None:
            return False
        return self.action.long_press(self.x, self.y)


class UI:
    def __init__(self, device=None, action=None):
        self.device = device
        self.action = action

        self.command = 'adb -s ' + self.device + ' '
        self.command_shell = 'adb -s ' + self.device + ' shell '

        self.view_server = False

        self.widget = None
        self.dump_data = ''
        self.communication_status = False

    def start_server(self):
        if self.view_server:
            return True
        server_status = subprocess.Popen(self.command_shell + AutoConstants.SERVER_STATUS_COMMAND, shell=False,
                                         stdout=subprocess.PIPE)
        server_status = server_status.stdout.read()
        status = re.match(r'^Result: Parcel.+(\d+).+(\d+).+\r\r\n', server_status).groups()[1]
        if status == '1':
            self.view_server = True
            return True
        elif status == '0':
            server_status = subprocess.Popen(self.command_shell + AutoConstants.SERVER_START_COMMAND, shell=False,
                                             stdout=subprocess.PIPE)
            server_status = server_status.stdout.read()
            status = re.match(r'^Result: Parcel.+(\d+).+(\d+).+\r\r\n', server_status).groups()[1]
            if status == '1':
                self.view_server = True
                return True
        return False

    def receive_dump(self):
        if self.start_server():
            client_socket = None
            self.dump_data = ''
            self.communication_status = False
            for local_port in range(6000, 7000):
                subprocess.Popen(self.command + AutoConstants.TCP_FORWARD + ':' + str(local_port) + ' tcp:4939',
                                 shell=False, stdout=subprocess.PIPE).stdout.read()

                try:
                    # Create Socket to connect to Android ViewServer
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((AutoConstants.LOCALHOST, local_port))

                    hash_id = self.action.get_current_window_hash()
                    if hash_id is not None:
                        client_socket.sendall(AutoConstants.DUMP_COMMAND + ' %s\n' % hash_id)
                        client_socket.settimeout(10)

                        while True:
                            received_dump = client_socket.recv(32 * 4096)
                            self.dump_data = self.dump_data + received_dump
                            if (received_dump.endswith('\nDONE.\n') or received_dump.endswith(
                                    'DONE.\n') or received_dump.endswith('\nDONE.\nDONE\n') or received_dump.endswith(
                                    'DONE.\nDONE\n')):
                                self.communication_status = True
                                client_socket.close()
                                break
                            if received_dump == '':
                                raise socket.error("Socket Closed")
                        if self.communication_status:
                            break
                except socket.error:
                    if client_socket is not None:
                        client_socket.close()
                        self.communication_status = False
                        self.view_server = False
                if not self.start_server():
                    self.communication_status = False

    def initial_parse(self):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            current_bound = self.action.get_current_window_bounds()

            level = -1
            new_level = -1
            self.widget = None

            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    new_level = len(line) - len(line.lstrip())
                    if self.widget is None:
                        # print "Root"
                        level = new_level
                        self.widget = Widget(self.action, new_level, line)
                    elif new_level > level:
                        # print str(new_level) + " is Child of " + str(level)
                        level = new_level
                        self.add_widget(new_level - 1, self.widget, Widget(self.action, new_level, line))
                    elif new_level == level:
                        # print str(new_level) + " is Sibling of  " + str(level)
                        self.add_widget(new_level - 1, self.widget, Widget(self.action, new_level, line))
                    elif new_level < level:
                        # print str(new_level) + " is Child of  " + str(new_level - 1)
                        level = new_level
                        self.add_widget(new_level - 1, self.widget, Widget(self.action, new_level, line))
            return self.widget

        return None

    def collect_and_parse_dump(self):
        self.receive_dump()
        return self.initial_parse()

    def add_widget(self, level_number=0, widget_root=None, w=None):
        if widget_root.get_level() == level_number:
            widget_root.set_children(w)
            return True
        children = widget_root.get_children()
        if len(children) != 0:
            self.add_widget(level_number, children[len(children) - 1], w)
        return False

    def find_widget_by_text_ex(self, widget_text):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', line)
                    if regex is not None:
                        if widget_text == regex.groupdict()['text']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_class_name_ex(self, name):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    regex = re.search(r'(?P<class_name>\S+)@\d+', line)
                    if regex is not None:
                        if name == regex.groupdict()['class_name']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_id_ex(self, widget_id):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', line)
                    if regex is not None:
                        if widget_id == regex.groupdict()['id_value']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_id_text_ex(self, widget_id, widget_text):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', line)
                    text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', line)
                    if id_regex is not None and text_regex is not None:
                        if widget_id == id_regex.groupdict()['id_value'] and \
                                widget_text == text_regex.groupdict()['text']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_id_class_ex(self, widget_id, name):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', line)
                    class_regex = re.search(r'(?P<class_name>\S+)@\d+', line)
                    if id_regex is not None and class_regex is not None:
                        if widget_id == id_regex.groupdict()['id_value'] and \
                                name == class_regex.groupdict()['class_name']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_text_class_ex(self, widget_text, name):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', line)
                    class_regex = re.search(r'(?P<class_name>\S+)@\d+', line)
                    if text_regex is not None and class_regex is not None:
                        if widget_text == text_regex.groupdict()['text'] and \
                                name == class_regex.groupdict()['class_name']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_id_text_class_ex(self, widget_id, widget_text, name):
        # Everything is good, then parse the ui dump
        if self.communication_status and self.dump_data != '':
            for line in self.dump_data.split('\n'):
                if line == '' or line == 'DONE' or line == 'DONE.':
                    break
                visibility_regex = re.search(r'\s+getVisibility\(\)=\d+,(?P<visibility>\S+) ', line)
                if visibility_regex is not None and visibility_regex.groupdict()['visibility'] == 'VISIBLE':
                    id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', line)
                    text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', line)
                    class_regex = re.search(r'(?P<class_name>\S+)@\d+', line)
                    if id_regex is not None and text_regex is not None and class_regex is not None:
                        if widget_id == id_regex.groupdict()['id_value'] and \
                                widget_text == text_regex.groupdict()['text'] and \
                                name == class_regex.groupdict()['class_name']:
                            return True
            return False
        else:
            print "Error In Collecting UI Dump"
            return False

    def find_widget_by_class_name(self, widget_root, name):
        if widget_root is not None:
            regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if regex is not None:
                if name == regex.groupdict()['class_name']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_class_name(item, name):
                    return True
        return None

    def find_widget_by_id(self, widget_root, widget_id):
        if widget_root is not None:
            regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if regex is not None:
                if widget_id == regex.groupdict()['id_value']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_id(item, widget_id):
                    return True
        return None

    def find_widget_by_text(self, widget_root, widget_text):
        if widget_root is not None:
            regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if regex is not None:
                if widget_text == regex.groupdict()['text']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_text(item, widget_text):
                    return True
        return None

    def find_widget_by_id_text(self, widget_root, widget_id, widget_text):
        if widget_root is not None:
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if id_regex is not None and text_regex is not None:
                if widget_id == id_regex.groupdict()['id_value'] and widget_text == text_regex.groupdict()['text']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_id_text(item, widget_id, widget_text):
                    return True
        return None

    def find_widget_by_id_class(self, widget_root, widget_id, name):
        if widget_root is not None:
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if id_regex is not None and class_regex is not None:
                if widget_id == id_regex.groupdict()['id_value'] and name == class_regex.groupdict()['class_name']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_id_class(item, widget_id, name):
                    return True
        return None

    def find_widget_by_text_class(self, widget_root, widget_text, name):
        if widget_root is not None:
            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if text_regex is not None and class_regex is not None:
                if widget_text == text_regex.groupdict()['text'] and name == class_regex.groupdict()['class_name']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_text_class(item, widget_text, name):
                    return True
        return None

    def find_widget_by_id_text_class(self, widget_root, widget_id, widget_text, name):
        if widget_root is not None:
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if id_regex is not None and text_regex is not None and class_regex is not None:
                if widget_id == id_regex.groupdict()['id_value'] and widget_text == text_regex.groupdict()['text'] \
                        and name == class_regex.groupdict()['class_name']:
                    return True

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                if self.find_widget_by_id_text_class(item, widget_id, widget_text, name):
                    return True
        return None

    def parse_all_by_text(self, widget_root, widget_text, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_text = None
            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_text == w_text:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_text(item, widget_text, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_id(self, widget_root, widget_id, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_id = None
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_id == w_id:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_id(item, widget_id, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_class(self, widget_root, widget_class_name, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            cls_name = None
            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_class_name == cls_name:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_class(item, widget_class_name, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_id_text(self, widget_root, widget_id, widget_text, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_id = None
            w_text = None
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_id == w_id and widget_text == w_text:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_id_text(item, widget_id, widget_text, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_text_class(self, widget_root, widget_text, widget_class_name, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_text = None
            cls_name = None
            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_text == w_text and widget_class_name == cls_name:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_text_class(item, widget_text, widget_class_name, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_id_class(self, widget_root, widget_id, widget_class_name, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_id = None
            cls_name = None
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_id == w_id and widget_class_name == cls_name:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_id_class(item, widget_id, widget_class_name, current_left, current_top)
                if w is not None:
                    return w
        return None

    def parse_all_by_id_text_class(self, widget_root, widget_id, widget_text, widget_class_name, left=0, top=0):
        current_left = left
        current_top = top
        if widget_root is not None:
            w_width = 0
            w_height = 0
            w_id = None
            w_text = None
            cls_name = None
            id_regex = re.search(r'\s+mID=\d+,(?P<id_value>\S+) ', widget_root.line)
            if id_regex is not None:
                w_id = id_regex.groupdict()['id_value']
                widget_root.set_widget_id(w_id)

            text_regex = re.search(r'\s+text:mText=\d+,(?P<text>.+) getEllipsize', widget_root.line)
            if text_regex is not None:
                w_text = text_regex.groupdict()['text']
                widget_root.set_widget_text(w_text)

            class_regex = re.search(r'(?P<class_name>\S+)@\d+', widget_root.line)
            if class_regex is not None:
                cls_name = class_regex.groupdict()['class_name']
                widget_root.set_class_name(cls_name)

            m_left_regex = re.search(r'\s+layout:mLeft=\d+,(?P<mLeft>\S+) ', widget_root.line)
            if m_left_regex is not None:
                m_left = int(m_left_regex.groupdict()['mLeft'])
                current_left = m_left + current_left
                widget_root.set_widget_left(current_left)

            m_top_regex = re.search(r'\s+layout:mTop=\d+,(?P<mTop>\S+) ', widget_root.line)
            if m_top_regex is not None:
                m_top = int(m_top_regex.groupdict()['mTop'])
                current_top = m_top + current_top
                widget_root.set_widget_top(current_top)

            width_regex = re.search(r'\s+layout:getWidth\(\)=\d+,(?P<width>\S+) ', widget_root.line)
            if width_regex is not None:
                w_width = int(width_regex.groupdict()['width'])
                widget_root.set_widget_width(w_width)

            height_regex = re.search(r'\s+layout:getHeight\(\)=\d+,(?P<height>\S+) ', widget_root.line)
            if height_regex is not None:
                w_height = int(height_regex.groupdict()['height'])
                widget_root.set_widget_height(w_height)

            # Calculate X Co-ordinate: parent.mLeft+self.mLeft+(self.width/2)
            widget_root.set_widget_x(current_left + int(w_width / 2))

            # Calculate Y Co-ordinate: parent.mTop+self.mTop+(self.height/2)
            widget_root.set_widget_y(current_top + int(w_height / 2))

            if widget_id == w_id and widget_text == w_text and widget_class_name == cls_name:
                return widget_root

        children = widget_root.get_children()
        if len(children) != 0:
            for item in widget_root.get_children():
                w = self.parse_all_by_id_text_class(item, widget_id, widget_text, widget_class_name, current_left,
                                                    current_top)
                if w is not None:
                    return w
        return None
