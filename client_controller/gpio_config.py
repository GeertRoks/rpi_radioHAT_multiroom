import RPi.GPIO as GPIO

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

    def getSourceSelectState(self):
        return {"radio": GPIO.input(self.SRC_SEL_RADIO), "spotify": GPIO.input(self.SRC_SEL_SPOTIFY) }

    def getRadioBtnState(self):
        return GPIO.input(self.RADIO_BTN)

    def setRadioLed(self, state):
        GPIO.output(self.RADIO_LED, state)

    def setSpotifyLed(self, state):
        GPIO.output(self.SPOTIFY_LED, state)
