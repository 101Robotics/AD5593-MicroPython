from machine import I2C
import ad5593
import pycom
import time

pycom.heartbeat(False)
pycom.rgbled(0x000100)

# configure the I2C bus
i2c = I2C(0, pins=('P9','P10'))
i2c = I2C(0, I2C.MASTER, baudrate=400000)
print(i2c.scan())

i2c.writeto(113,0b00000001)

AD = ad5593.AD5593(i2c, 0x11) # Addresse 0x11 = 17, optional : 1 for advanced mode (let you have more control)

### ADC/DAC/GPIO Operations :
print("Pins configuration")
AD.OUTPUT(2) # Digital Output on pin 0
AD.ADC(0,2) # ADC on pin 1 with a range of 2xVref =  2x2.5 = 5V (1 by default)
#AD.ADC(1,1)
#AD.ADC(2,1)

while True:
    print("Set I/O 0 ON")
    AD.digitalWrite(2,1) #Pin number, 1 or 0
    time.sleep(1)
    print("Toggle I/O 0")
    AD.toggle(2)
    print("Reading ADC I/O 1 with an average over 5 measurments (optional)")
    #print(AD.readVoltage(1,5)-AD.readVoltage(2,5))
    print(AD.analogRead(0,1))
    print(AD.readVoltage(0,1)) # Reading voltage on pin 0 with an average over 5 measurments
    AD.powerAll(1) #Powers down Vref, ADC and DACs
    time.sleep(1)
