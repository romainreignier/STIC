import atexit
import time
import laser_egismos
import pwmio
import async_button
import async_buzzer
import displayio
import rm3100
import seeed_xiao_nrf52840
import busio
import digitalio

try:
    from typing import Optional
except ImportError:
    pass

from . import invertingpwmio
from . import bluetooth
from . import pins
from .debug import logger


# Pin definitions

HAPPY = (("C6", 50.0), ("E6", 50.0), ("G6", 50.0), ("C7", 50.0))
BIP = (("A7", 50),)
BOP = (("C7", 50),)
SAD = (("G6", 100), ("C6", 200))


# noinspection PyAttributeOutsideInit
class Hardware:
    def __init__(self):
        logger.debug("Initialising hardware")
        import displayio
        displayio.release_displays()
        self._las_en_pin = digitalio.DigitalInOut(pins.LASER_EN)
        self._las_en_pin.switch_to_output(False)
        self._peripheral_enable_io = digitalio.DigitalInOut(pins.PERIPH_EN)
        self._peripheral_enable_io.switch_to_output(True)
        time.sleep(0.1)
        self.button_a = async_button.Button(pins.BUTTON_A, value_when_pressed=False, long_click_enable=True)
        self.button_b = async_button.Button(pins.BUTTON_B, value_when_pressed=False, long_click_enable=True)
        self.both_buttons = async_button.MultiButton(a=self.button_a, b=self.button_b)
        self.i2c = busio.I2C(scl=pins.SCL, sda=pins.SDA, frequency=4000000)
        self._drdy_io = digitalio.DigitalInOut(pins.DRDY)
        self._drdy_io.direction = digitalio.Direction.INPUT
        # noinspection PyTypeChecker
        self.magnetometer = rm3100.RM3100_I2C(self.i2c, drdy_pin=self._drdy_io, cycle_count=2000)
        self._uart = busio.UART(pins.TX, pins.RX, baudrate=9600)
        self._uart.reset_input_buffer()
        self._laser = laser_egismos.AsyncLaser(self._uart)
        if pins.BUZZER_B is None:
            self._pwm = pwmio.PWMOut(pins.BUZZER_A, variable_frequency=True)
        else:
            self._pwm = invertingpwmio.InvertingPWMOut(pins.BUZZER_A, pins.BUZZER_B)
        self.buzzer = async_buzzer.Buzzer(self._pwm)
        self._battery = seeed_xiao_nrf52840.Battery()
        self.accelerometer = seeed_xiao_nrf52840.IMU()
        self.bt = bluetooth.BluetoothServices()
        self._atexit_handler = self.deinit
        atexit.register(self._atexit_handler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()

    def laser_enable(self, value: bool) -> None:
        self._las_en_pin.value = value

    async def laser_on(self, value: bool) -> None:
        await self._laser.set_laser(value)

    async def laser_measure(self) -> float:
        self._laser.async_reader.s.read()  # clear the buffer
        return await self._laser.measure()

    def peripherals_enable(self, value: bool) -> None:
        self._peripheral_enable_io.value = value

    @property
    def batt_voltage(self) -> float:
        return self._battery.voltage

    def beep_happy(self):
        self.buzzer.play(HAPPY)

    def beep_shutdown(self):
        # noinspection PyTypeChecker
        self.buzzer.play(reversed(HAPPY))

    def beep_bip(self):
        self.buzzer.play(BIP)

    def beep_bop(self):
        self.buzzer.play(BOP)

    def beep_sad(self):
        self.buzzer.play(SAD)

    async def beep_wait(self):
        await self.buzzer.wait()

    def charge_status(self):
        return self._battery.charge_status

    def deinit(self):
        # release display
        displayio.release_displays()
        time.sleep(0.1)
        self._las_en_pin.value = False
        self.bt.deinit()
        self.accelerometer.deinit()
        self._battery.deinit()
        self._pwm.deinit()
        self._uart.deinit()
        self.i2c.deinit()
        self._drdy_io.deinit()
        try:
            self.button_b.deinit()
        except KeyError:
            pass
        try:
            self.button_a.deinit()
        except KeyError:
            pass
        self._peripheral_enable_io.value = False
        time.sleep(0.1)
        self._las_en_pin.deinit()
        self._peripheral_enable_io.deinit()
        atexit.unregister(self._atexit_handler)
