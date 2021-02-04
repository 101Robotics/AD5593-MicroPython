###############################################################
###                                                         ###
###            MicroPython AD5593 ADC/DAC/GPIO I2C          ###
###             Library created by Tristan Muller           ###
###                 https://101robotics.com                 ###
###    Inspired by the library  created for the PCF8574     ###
###     https://github.com/mcauser/micropython-pcf8574      ###
###                                                         ###
###############################################################

###############################################################
###                                                         ###
###                         CHANGELOG                       ###
###     18/05/2020: v0.1: Creation of th lib with ADC and   ###
###                 GPIO outputs capabilites                ###
###                                                         ###
###############################################################

### Keywords :
AD5593_ALL = 0
AD5593_ADC = 1
AD5593_DAC = 2
AD5593_OUTPUT = 3
AD5593_INPUT  = 4

##### POINTER BYTE CONSTANTS :
### Mode bits :
AD5593_CONFIG_MODE  = 0b0000 << 4
AD5593_DAC_WRITE    = 0b0001 << 4
AD5593_ADC_READBACK = 0b0100 << 4
AD5593_DAC_READBACK = 0b0101 << 4
AD5593_GPIO_READBACK= 0b0110 << 4
AD5593_REG_READBACK = 0b0111 << 4

### Control Register : (Descriptions from the datasheet)
AD5593_NOP           = 0b0000 # No operation
AD5593_ADC_SEQ_REG   = 0b0010 # Selects ADC for conversion (1 byte blank and 1 for the 8 I/Os)
AD5593_GP_CONTR_REF  = 0b0011 # DAC and ADC control register
AD5593_ADC_PIN_CONF  = 0b0100 # Selects which pins are ADC inputs
AD5593_DAC_PIN_CONF  = 0b0101 # Selects which pins are DAC outputs
AD5593_PULLDOWN_CONF = 0b0110 # Selects which pins have an 85kOhms pull-down resistor to GND
AD5593_LDAC_MODE     = 0b0111 # Selects the operation of the load DAC
AD5593_GPIO_W_CONF   = 0b1000 # Selects which pins are general-purpose outputs
AD5593_GPIO_W_DATA   = 0b1001 # Writes data to general-purpose outputs
AD5593_GPIO_R_CONF   = 0b1010 # Selects which pins are general-purpose inputs
AD5593_PWRDWN_REFCONF= 0b1011 # Powers down the DACs and enables/disables the reference
AD5593_OPENDRAIN_CONF= 0b1100 # Selects open-drain or push-pull for general-purpose outputs
AD5593_3_STATES_PINS = 0b1101 # Selects which pins are three-stated
AD5593_SOFT_RESET    = 0b1111 # Resets the AD5593R
AD5593_BLANK         = 0b00000000

class AD5593:
    def __init__(self, i2c, address=0x11,advance=0):
        self._i2c = i2c
        self._address = address
        self._data = bytearray(3)
        self._advance = advance
        if i2c.scan().count(address) == 0:
            raise OSError('AD5593 not found at I2C address {:#x}'.format(address))


    def OUTPUT(self,pin):
        pin = self.validate_pin(pin)
        reg = self._read(AD5593_REG_READBACK | AD5593_GPIO_W_CONF,2)
        self._data[0] = AD5593_CONFIG_MODE | AD5593_GPIO_W_CONF
        self._data[1] = reg[0]
        self._data[2] = reg[1] | (1 << (pin))
        self._write()

    def ADC(self,pin,range=1):
        pin = self.validate_pin(pin)
        reg = self._read(AD5593_REG_READBACK | AD5593_ADC_PIN_CONF,2)
        self._data[0] = AD5593_CONFIG_MODE | AD5593_ADC_PIN_CONF
        self._data[1] = reg[0]
        self._data[2] = reg[1] | (1 << (pin))
        self._write()

        if self._advance == 0:
            #reg = self._read(AD5593_REG_READBACK | AD5593_ADC_SEQ_REG,2)
            #self._data[0] = AD5593_CONFIG_MODE | AD5593_ADC_SEQ_REG
            #self._data[1] = reg[0] | (1 << 1) # Activate repetition
            #self._data[2] = reg[1] | (1 << (pin))
            #self._write()

            reg = self._read(AD5593_REG_READBACK | AD5593_PWRDWN_REFCONF,2)
            self._data[0] = AD5593_CONFIG_MODE | AD5593_PWRDWN_REFCONF
            self._data[1] = reg[0] | (1 << 1) # Activate Vref
            self._data[2] = reg[1]
            self._write()

            if range == 2 :
                reg = self._read(AD5593_REG_READBACK | AD5593_GP_CONTR_REF,2)
                self._data[0] = AD5593_CONFIG_MODE | AD5593_GP_CONTR_REF
                self._data[1] = reg[0]
                self._data[2] = reg[1] | (1<<5) # Range 2x Vref
                self._write()
            else:
                reg = self._read(AD5593_REG_READBACK | AD5593_GP_CONTR_REF,2)
                self._data[0] = AD5593_CONFIG_MODE | AD5593_GP_CONTR_REF
                self._data[1] = reg[0]
                self._data[2] = reg[1] & ~(1 << (5))# Range 2x Vref
                self._write()

    def analogRead(self, pin, average=1):
        pin = self.validate_pin(pin)
        reg = self._read(AD5593_REG_READBACK | AD5593_ADC_SEQ_REG,2)
        self._data[0] = AD5593_CONFIG_MODE | AD5593_ADC_SEQ_REG
        self._data[1] = reg[0] | (1 << 1) # Activate repetition
        self._data[2] = (1 << (pin))
        self._write()

        self._i2c.writeto(self._address, AD5593_ADC_READBACK)
        values = list(range(average))
        for x in list(range(average)):
            msg = self._i2c.readfrom(self._address,2)
            values[x] = int(((msg[0] & 0x0F) << 8 ) + msg[1])
        return int(sum(values)/len(values))

    def getVref(self):
        mask = 0b00100000
        reg = self._read(AD5593_REG_READBACK | AD5593_GP_CONTR_REF,2)
        return 2.5*(((reg[1]&mask)>>5)+1)

    def setVref(self, activate):
        if activate:
            reg = self._read(AD5593_REG_READBACK | AD5593_PWRDWN_REFCONF,2)
            self._data[0] = AD5593_CONFIG_MODE | AD5593_PWRDWN_REFCONF
            self._data[1] = reg[0] | (1 << 1) # Activate Vref
            self._data[2] = reg[1]
            self._write()
        else:
            reg = self._read(AD5593_REG_READBACK | AD5593_PWRDWN_REFCONF,2)
            self._data[0] = AD5593_CONFIG_MODE | AD5593_PWRDWN_REFCONF
            self._data[1] = reg[0] & ~(1  << 1) # Activate Vref
            self._data[2] = reg[1]
            self._write()

    def readVoltage(self, pin, average=3):
        pin = self.validate_pin(pin)
        vref = self.getVref()
        value = self.analogRead(pin,average)
        return  (value/4096)*(vref)

    def digitalWrite(self, pin, value=0):
        pin = self.validate_pin(pin)
        reg = self._read(AD5593_REG_READBACK | AD5593_GPIO_W_DATA,2)
        self._data[0] = AD5593_CONFIG_MODE | AD5593_GPIO_W_DATA
        self._data[1] = AD5593_BLANK
        if value:
            self._data[2] = reg[1] | (1 << (pin)) # 1
        else:
            self._data[2] = reg[1] & ~(1 << (pin)) # 0
        self._write()

    def toggle(self, pin):
        pin = self.validate_pin(pin)
        reg = self._read(AD5593_REG_READBACK | AD5593_GPIO_W_DATA,2)
        self._data[0] = AD5593_CONFIG_MODE | AD5593_GPIO_W_DATA
        self._data[1] = AD5593_BLANK
        self._data[2] = reg[1] ^ (1 << (pin))
        self._write()

    def powerAll(self, state):
        if state: #Powering up
            reg = self._read(AD5593_REG_READBACK | AD5593_PWRDWN_REFCONF,2)
            self._data[0] = AD5593_CONFIG_MODE | AD5593_PWRDWN_REFCONF
            self._data[1] = reg[0] & ~(1  << 2) # Activate Vref
            self._data[2] = reg[1]
            self._write()
        else: # Powering down
            reg = self._read(AD5593_REG_READBACK | AD5593_PWRDWN_REFCONF,2)
            self._data[0] = AD5593_CONFIG_MODE | AD5593_PWRDWN_REFCONF
            self._data[1] = reg[0] | (1  << 2)
            self._data[2] = reg[1]
            self._write()

    def reset(self):
        self._data[0] = AD5593_CONFIG_MODE | AD5593_SOFT_RESET
        self._data[1] = 0x0D
        self._data[2] = 0xAC
        self._write()

    def validate_pin(self, pin):
        # pin valid range 0..7
        if not 0 <= pin <= 7:
            raise ValueError('Invalid pin {}. Use 0-7.'.format(pin))
        return pin

    def readRegister(self,reg):
        return bin(self._read(reg,2))

    def writeRegister(self, reg, msb, lsb):
        self._data[0] = reg
        self._data[1] = msb
        self._data[2] = lsb
        self._write()

    def readValues(self):
        return self._i2c.readfrom(self._address,2)

    def _read(self,reg=AD5593_BLANK,nbBytes=2):
        self._i2c.writeto(self._address, reg)
        return self._i2c.readfrom(self._address,nbBytes)

    def _write(self):
        self._i2c.writeto(self._address, self._data)
