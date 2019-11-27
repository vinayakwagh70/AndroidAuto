# About AndroidAuto
Test Automation Framework for Android Devices in Python.
This framework is portable across all the Android Devices. No need of customization.

# Things In Progress (TO DO): 
1. Improve performance of collecting UI Dump
2. Improve performance of doing screen comparison

# Sample code to get started
```
from Android import Make

d = Make().device()
```

# Click on x, y co-ordinates
```
d.tap_on(100, 200)
```

# Long Press on x, y co-ordinates
```
d.long_press(100, 200)
```

# Swipe from source (x1, y1) to destination (x2, y2)
```
d.swipe(100, 200, 100, 400)
```

# Drag Item from source (x1, y1) to destination (x2, y2)
```
d.hold_and_drag(100, 200, 100, 400)
```

# Get current window name (Activity Name)
```
print d.get_current_window_name()
```

# See if Item with provided property (widget_id OR widget_text OR widget_class_name) exists or not, & perform operation on it
```
w = d.fetch_widget(widget_text='Ok')
if w:
    print "Item Found. Clicking on Item"
    w.touch()
else:
    print "Item Not Found"
```


# See if Item with provided property (widget_id OR widget_text OR widget_class_name) exists or not (cannot perform operation on it)
```
w = d.find_widget(widget_text='Ok')
if w:
    print "Item Found"
    # Cannot do w.touch() here
else:
    print "Item Not Found"
```


# Find UI Item quickly using find_widget_ex() method, which is same as find_widget(), but produces output quicker
```
w = d.find_widget_ex(widget_text='Ok')
if w:
    print "Item Found"
    # Cannot do w.touch() here
else:
    print "Item Not Found"
```
