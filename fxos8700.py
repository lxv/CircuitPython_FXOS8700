# The MIT License (MIT)
#
# Copyright (c) 2017 Alex Vasylenko
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import ustruct

from adafruit_bus_device import i2c_device
from micropython import const

_REGISTER_STATUS       = const(0x00)
_REGISTER_WHO_AM_I     = const(0x0D)
_REGISTER_XYZ_DATA_CFG = const(0x0E)
_REGISTER_CTRL_REG1    = const(0x2A)
_REGISTER_CTRL_REG2    = const(0x2B)
_REGISTER_MCTRL_REG1   = const(0x5B)
_REGISTER_MCTRL_REG2   = const(0x5C)

class FXOS8700:
    def __init__(self, i2c):
        self._buffer = bytearray(16)
        self._i2c = i2c_device.I2CDevice(i2c, 0x1F)

        # Make sure we have the correct chip ID
        ok = self._read_register(_REGISTER_WHO_AM_I, 1)[0] == 0xC7
        if not ok:
            raise ValueError("Unable to find FXOS8700 at i2c address 0x1F")

        # Set to standby mode (required to make changes to this register)
        self._write_register_byte(_REGISTER_CTRL_REG1, 0)

        # Configure the accelerometer
        self._write_register_byte(_REGISTER_XYZ_DATA_CFG, 0)

        # High resolution
        self._write_register_byte(_REGISTER_CTRL_REG2, 0x02)
        # Active, Normal Mode, Low Noise, 100Hz in Hybrid Mode
        self._write_register_byte(_REGISTER_CTRL_REG1, 0x15)

        # Configure the magnetometer
        # - Hybrid Mode, Over Sampling Rate = 16
        self._write_register_byte(_REGISTER_MCTRL_REG1, 0x1F)
        # - Jump to reg 0x33 after reading 0x06
        self._write_register_byte(_REGISTER_MCTRL_REG2, 0x20)

    def _read_register(self, register, length):
        self._buffer[0] = register & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=1, stop=False)
            i2c.read_into(self._buffer, start=0, end=length)
            return self._buffer

    def _write_register_byte(self, register, value):
        self._buffer[0] = register & 0xFF
        self._buffer[1] = value & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=2)

    @property
    def acceleration(self):
        self._read_register(_REGISTER_STATUS, 13)
        accelDataX, accelDataY, accelDataZ = ustruct.unpack('>hhh', self._buffer[1:7])
        d = 9.80665 * 0.000244 / 4
        return (d * accelDataX, d * accelDataY, d * accelDataZ)
