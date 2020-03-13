# corrected_bristol_wavemeter
Reads the bristol wavemeter and uses the bristol fiber optic switch to correct for wavemeter drift by comparing to a stable laser. 

When the main code is run, the GUI can be launched with
wm.launch_gui()

Streaming of values to a ZMQ socket can be included with
wm.launch_gui(publish=True)
