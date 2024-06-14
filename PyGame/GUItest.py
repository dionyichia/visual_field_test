# CamTracker GUI test
inp = int(input("For cam_v1 press '1', otherwise press '2: "))
print(inp)
if inp == 1:
    from camtracker import Setup

    # initialize setup
    setup = Setup()

    # run GUI
    tracker = setup.start()

else:
    from camtracker_v2 import Setup

    # initialize setup
    setup = Setup()

    # run GUI
    tracker = setup.start()