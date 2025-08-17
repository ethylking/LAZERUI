from spectramaker import*
from devices_control import*
sm = Spectramaker()
oscilloscope = None

sm.motor.connect()
sm.wavemeter.connect()
sm.energymeter.__init__
for i in range(3, 7):
    try:
        sm.energymeter.connect(i)
        sm.energymeter.is_connected = True
        break
    except Exception as e:
        print(f"Failed to connect to COM{i}: {str(e)}")
    
          

sm.calibrate()