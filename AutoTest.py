# Author : Vinayak Wagh
# Date   : 11/8/2019

from Android import Make

d = Make().device()

# Click on X, y co-ordinates
d.tap_on(100, 200)

# Long Press on X, y co-ordinates
d.long_press(100, 200)

# Swipe from source to destination
d.swipe(100, 200, 100, 400)

# Drag Item from one place to another place
d.hold_and_drag(100, 200, 100, 400)

# Get current Window Name (Activity Name)
print d.get_current_window_name()

# See if Item with provided property is present or not, & perform operation on it
w = d.fetch_widget(widget_text='Import')
if w:
    print "Item Found. Clicking on Item"
    # Perform operation on item
    w.touch()
else:
    print "Item Not Found"

# See if Item with provided property is present or not (cannot perform operation on it)
w = d.find_widget(widget_text='Import')
if w:
    print "Item Found"
else:
    print "Item Not Found"
