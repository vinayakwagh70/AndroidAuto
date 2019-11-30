# Author : Vinayak Wagh
# Date   : 11/8/2019
import os


class Module:
    def __init__(self, device_actions=None, grab_ui=None):
        self.action = device_actions
        self.ui = grab_ui

    def tap_on(self, x, y):
        self.action.tap_on(x, y)

    def get_current_window_name(self):
        return self.action.get_current_window_name()

    def long_press(self, x, y, delay=2):
        self.action.long_press(x, y, delay)

    def swipe(self, x1, y1, x2, y2):
        self.action.swipe(x1, y1, x2, y2)

    def hold_and_drag(self, x1, y1, x2, y2):
        self.action.hold_and_drag(x1, y1, x2, y2)

    # Temp Function
    def get_current_window_hash(self):
        return self.action.get_current_window_hash()

    # Temp Function
    def get_current_window_bounds(self):
        return self.action.get_current_window_bounds()

    def find_widget(self, widget_id=None, widget_text=None, widget_class_name=None):
        widget = self.ui.collect_and_parse_dump()
        if widget is not None:
            if widget_class_name is not None and widget_id is None and widget_text is None:
                return self.ui.find_widget_by_class_name(widget, widget_class_name)
            elif widget_class_name is None and widget_id is not None and widget_text is None:
                return self.ui.find_widget_by_id(widget, widget_id)
            elif widget_class_name is None and widget_id is None and widget_text is not None:
                return self.ui.find_widget_by_text(widget, widget_text)
            elif widget_class_name is None and widget_id is not None and widget_text is not None:
                return self.ui.find_widget_by_id_text(widget, widget_id, widget_text)
            elif widget_class_name is not None and widget_id is not None and widget_text is None:
                return self.ui.find_widget_by_id_class(widget, widget_id, widget_class_name)
            elif widget_class_name is not None and widget_id is None and widget_text is not None:
                return self.ui.find_widget_by_text_class(widget, widget_text, widget_class_name)
            elif widget_class_name is not None and widget_id is not None and widget_text is not None:
                return self.ui.find_widget_by_id_text_class(widget, widget_id, widget_text, widget_class_name)
        print "Error In Collecting UI Dump"
        return None

    def fetch_widget(self, widget_id=None, widget_text=None, widget_class_name=None):
        widget = self.ui.collect_and_parse_dump()
        if widget is not None:
            bounds = self.action.get_current_window_bounds()
            if widget_class_name is None and widget_id is None and widget_text is not None:
                return self.ui.parse_all_by_text(widget, widget_text, bounds[0], bounds[1])
            elif widget_class_name is None and widget_id is not None and widget_text is None:
                return self.ui.parse_all_by_id(widget, widget_text, bounds[0], bounds[1])
            elif widget_class_name is not None and widget_id is None and widget_text is None:
                return self.ui.parse_all_by_class(widget, widget_text, bounds[0], bounds[1])
            elif widget_class_name is None and widget_id is not None and widget_text is not None:
                return self.ui.parse_all_by_id_text(widget, widget_id, widget_text, bounds[0], bounds[1])
            elif widget_class_name is not None and widget_id is None and widget_text is not None:
                return self.ui.parse_all_by_id_text(widget, widget_text, widget_class_name, bounds[0], bounds[1])
            elif widget_class_name is not None and widget_id is not None and widget_text is None:
                return self.ui.parse_all_by_id_class(widget, widget_id, widget_class_name, bounds[0], bounds[1])
            elif widget_class_name is not None and widget_id is not None and widget_text is not None:
                return self.ui.parse_all_by_id_text_class(widget, widget_id, widget_class_name, bounds[0], bounds[1])
        print "Error In Collecting UI Dump"
        return False

    def find_widget_ex(self, widget_id=None, widget_text=None, widget_class_name=None):
        self.ui.receive_dump()
        if widget_class_name is not None and widget_id is None and widget_text is None:
            return self.ui.find_widget_by_class_name_ex(widget_class_name)
        elif widget_class_name is None and widget_id is not None and widget_text is None:
            return self.ui.find_widget_by_id_ex(widget_id)
        elif widget_class_name is None and widget_id is None and widget_text is not None:
            return self.ui.find_widget_by_text_ex(widget_text)
        elif widget_class_name is None and widget_id is not None and widget_text is not None:
            return self.ui.find_widget_by_id_text_ex(widget_id, widget_text)
        elif widget_class_name is not None and widget_id is not None and widget_text is None:
            return self.ui.find_widget_by_id_class_ex(widget_id, widget_class_name)
        elif widget_class_name is not None and widget_id is None and widget_text is not None:
            return self.ui.find_widget_by_text_class_ex(widget_text, widget_class_name)
        elif widget_class_name is not None and widget_id is not None and widget_text is not None:
            return self.ui.find_widget_by_id_text_class_ex(widget_id, widget_text, widget_class_name)

    # Image Comparison
    def validate_image_pattern(self, img=None, start_reg=None, end_reg=None):
        if img is None or start_reg is None:
            print "Please provide Image file & start region to search"
            return False
        if os.path.exists(img):
            return self.ui.verify_pattern(img, start_reg, end_reg)
        print str(img) + " does not exist!!"
        return False