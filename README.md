# corrected_bristol_wavemeter
Reads the bristol wavemeter and uses the bristol fiber optic switch to correct for wavemeter drift by comparing to a stable laser. The code is currently configured to correct using an 852 nm laser locked to a hyperfine transition of the Cs D2 line. The code is compatible with linux only. 

When the main code is run, the GUI can be launched with
wm.launch_gui()

Streaming of values to a ZMQ socket can be included with
wm.launch_gui(publish=True)
