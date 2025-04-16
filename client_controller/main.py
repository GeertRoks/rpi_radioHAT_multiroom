from dotenv import load_dotenv

from gpio_config import GPIO_Config
from radio import Radio


# Load environment variables from .env file
load_dotenv()

# setup the Radio
radio = Radio()

# setup GPIO
gpio = GPIO_Config()

# register hardware events
gpio.addBtnEvent(gpio.RADIO_BTN, radio.radio_button_event)
gpio.addSourceSwitchEvent(gpio.SRC_SEL_RADIO, radio.source_switch_event)
gpio.addSourceSwitchEvent(gpio.SRC_SEL_SPOTIFY, radio.source_switch_event)

# main loop
radio.run(gpio)
