import time
import RPi.GPIO as GPIO

from states import Sources

class GPIO_Config:
    # Define GPIO ports
    SPOTIFY_LED = 17
    RADIO_LED = 27
    RADIO_BTN = 24
    SRC_SEL_RADIO = 22
    SRC_SEL_SPOTIFY = 23

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SPOTIFY_LED, GPIO.OUT)
        GPIO.setup(self.RADIO_LED, GPIO.OUT)
        GPIO.setup(self.RADIO_BTN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SRC_SEL_RADIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.SRC_SEL_SPOTIFY, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def __del__(self):
        GPIO.cleanup()

    def blinkLed(self, pin, repeat = 1, period = 0.1):
        delay = period/2
        for i in range(repeat):
            self.toggleLed(pin)
            time.sleep(delay)
            self.toggleLed(pin)
            if (i < repeat-1):
                time.sleep(delay)

    def toggleLed(self, pin):
        state = GPIO.input(pin)
        GPIO.output(pin, not state)

    def getSourceSelectState(self):
        source_states = {"radio": GPIO.input(self.SRC_SEL_RADIO), "spotify": GPIO.input(self.SRC_SEL_SPOTIFY) }
        match source_states:
            case {"radio": GPIO.HIGH, "spotify": GPIO.HIGH}:
                return Sources.OFF
            case {"radio": GPIO.LOW, "spotify": GPIO.HIGH}:
                return Sources.RADIO
            case {"radio": GPIO.HIGH, "spotify": GPIO.LOW}:
                return Sources.SPOTIFY
            case _:
                # TODO: write this to a log or handle as Error exception
                print("GPIO_Config.getSourceSelectState(): invalid source select")
                return Sources.OFF

    def addBtnEvent(self, channel, callback):
        GPIO.add_event_detect(channel, GPIO.FALLING, callback=callback, bouncetime=300)

    def addSourceSwitchEvent(self, channel, callback):
        GPIO.add_event_detect(channel, GPIO.BOTH, callback=callback, bouncetime=100)

    def setSourceSelectLeds(self, state):
        match state:
            case Sources.OFF:
                GPIO.output(self.RADIO_LED, GPIO.LOW)
                GPIO.output(self.SPOTIFY_LED, GPIO.LOW)
            case Sources.RADIO:
                GPIO.output(self.RADIO_LED, GPIO.HIGH)
                GPIO.output(self.SPOTIFY_LED, GPIO.LOW)
            case Sources.SPOTIFY:
                GPIO.output(self.RADIO_LED, GPIO.LOW)
                GPIO.output(self.SPOTIFY_LED, GPIO.HIGH)
