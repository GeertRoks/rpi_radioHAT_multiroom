from enum import Enum
import gpio_config as gpio

class Sources(Enum):
    OFF = 0
    RADIO = 1
    SPOTIFY = 2

class SourceState:
    source_state = 0

    def __init__(self):
        self.off()

    def off(self):
        self.source_state = Sources.OFF
        # set Snapcast source to None
        gpio.GPIO.output(gpio.SPOTIFY_LED, gpio.GPIO.LOW)
        gpio.GPIO.output(gpio.RADIO_LED, gpio.GPIO.LOW)

    def radio(self):
        self.source_state = Sources.RADIO
        # set Snapcast source to Radio
        gpio.GPIO.output(gpio.SPOTIFY_LED, gpio.GPIO.LOW)
        gpio.GPIO.output(gpio.RADIO_LED, gpio.GPIO.HIGH)

    def spotify(self):
        self.source_state = Sources.SPOTIFY
        # set Snapcast source to Spotify
        gpio.GPIO.output(gpio.SPOTIFY_LED, gpio.GPIO.HIGH)
        gpio.GPIO.output(gpio.RADIO_LED, gpio.GPIO.LOW)

    def getState(self):
        return self.source_state

