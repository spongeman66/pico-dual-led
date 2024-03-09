from machine import Pin, Timer
from sys import print_exception


class DualLED:
    """
    This represents a single LED with 3 wires.
    Common Cathode (negative)
    Red wire (Positive through a resistor turns RED on)
    Green wire (Positive through a resistor turns GREEN on)

    uses the async compatible Timer to blink LEDs
    """
    COLORS = ['RED', 'GREEN']
    DEFAULT_FREQ = 3.0

    def __init__(self, gpio_0, gpio_1, primary_color, freq=None):
        """
        gpio_0        - GPIO number for RED color output
        gpio_1        - GPIO number for GREEN color output
        primary_color - 'RED' or 'GREEN', primary color to use when generic ON/BLINKING, etc.
        freq          - frequency to blink LED. self.DEFAULT_FREQ if not specified.
                        Can be passed in to each blinky method
        """
        self.gpio_0 = gpio_0
        self.gpio_1 = gpio_1
        self.primary_color = primary_color.upper()
        self.freq = freq or self.DEFAULT_FREQ
        self.primary_led = None
        self.secondary_led = None
        self.timer = None
        self.tick_count = 0
        self.color_map = dict()
        self.state = None
        self.__led_0 = None
        self.__led_1 = None
        self.setup_control(self.primary_color)
        self.off()

    def set_primary_color(self, color):
        color = color.upper()
        if color not in self.COLORS:
            raise ValueError(f"primary color must be one of {self.COLORS} not {color}")
        self.primary_color = color
        if self.primary_color == self.COLORS[0]:
            self.primary_led, self.secondary_led = self.__led_0, self.__led_1
        else:
            self.primary_led, self.secondary_led = self.__led_1, self.__led_0

    def setup_control(self, primary_color):
        self.__led_0 = Pin(self.gpio_0, Pin.OUT, value=0)
        self.__led_1 = Pin(self.gpio_1, Pin.OUT, value=0)
        self.color_map = {
            self.COLORS[0]: self.__led_0,
            self.COLORS[1]: self.__led_1
        }
        self.set_primary_color(primary_color)
        
    def stop_timer(self):
        if self.timer:
            self.timer.deinit()
            del self.timer
            self.timer = None
        self.tick_count = 0

    def led_for_color(self, color=None):
        """
        reads the color and if None, returns primary led, secondary, color
        if matches self.COLORS[0] (normally RED)   returns __led_0, __led_1, color
        if matches self.COLORS[1] (normally GREEN) returns __led_1, __led_0, color
        """
        if not color:
            return self.primary_led, self.secondary_led, self.primary_color
        if color.upper() not in self.COLORS:
            raise ValueError(f"color must be None or one of {self.COLORS} not {color}")
        pos = self.COLORS.index(color.upper())
        other = (pos + 1) % 2
        return self.color_map[self.COLORS[pos]], self.color_map[self.COLORS[other]], color.upper()

    def off(self):
        """
        Turn both off
        """
        self.stop_timer()
        self.__led_0.value(0)
        self.__led_1.value(0)
        self.state = 'OFF'

    def on(self, color=None):
        """
        Turn primary on, secondary off
        Or turn selected color on, other color off
        """
        self.stop_timer()
        p, s, c = self.led_for_color(color)
        s.value(0)
        p.value(1)
        self.state = f"ON:{c}"

    def toggle(self, color=None):
        self.stop_timer()
        p, s, c = self.led_for_color(color)
        if self.state != 'OFF':
            self.off()
        else:
            self.on(c)

    def get_state(self):
        """
        read current state of LEDs
        return on/off status of each LED, and the current action state (on/off/blinking, etc.)
        """
        state = {'STATE': self.state}
        state.update({
            c: k.value() for c, k in self.color_map.items()})
        return state

    def restore_state(self, **kwargs):
        """
        from the state string, restore the LED function
        :param kwargs: must have a state or STATE parameter other values are ignored
        """
        try:
            state = [
                v for k, v in kwargs.items()
                if k.lower() == 'state'][0].split(':')
            if state[0] == 'OFF':
                self.off()
            elif state[0] == 'ON':
                # self.state = f"ON:{c}"
                self.on(state[1])
            elif state[0] == 'BLINK':
                # self.state = f"BLINK:{c}:{freq}Hz"
                self.blink(freq=state[-1][:-2], color=state[1])
            elif state[0] == 'COUNT':
                # self.state = f"COUNT:{c}:{number}:{freq}Hz"
                self.count_number(state[2], freq=state[-1][:-2], color=state[1])
                pass
            elif state[0] == 'ALTERNATE':
                # self.state = f'ALTERNATE::{freq}Hz'
                self.alternate_colors(freq=state[-1][:-2])
                pass
        except Exception as e:
            print_exception(e)

    def blink(self, freq=None, color=None):
        """
        blink the LED
        freq - Times to blink per second
        color - defaults to primary, but can override by setting color
        """
        freq = freq or self.freq
        freq = float(freq)
        self.stop_timer()
        self.off()
        to_blink, _, c = self.led_for_color(color)
        self.state = f"BLINK:{c}:{freq}Hz"

        def toggle_blinker(_t):
            to_blink.toggle()    
        
        self.timer = Timer()
        # need a * 2 on the frequency because we Toggle at the frequency rather than on half - off half
        self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=toggle_blinker)

    def alternate_colors(self, freq=None):
        """
        Primary On, Secondary Off, then toggle both periodically
        freq - (frequency) times per second to alternate
        """
        freq = freq or self.freq
        freq = float(freq)
        self.stop_timer()
        self.on()  # Primary set to on, secondary off
        self.state = f'ALTERNATE::{freq}Hz'

        def __toggle_both(_t):
            self.secondary_led.toggle()
            self.primary_led.toggle()
        
        self.timer = Timer()
        # need a * 2 on the frequency because we Toggle at the frequency rather than on half off half
        self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=__toggle_both)

    def count_number(self, number, freq=None, color=None):
        """
        blinks the LED in the default or chosen Color for
        number - (count) times to blink before a pause
        freq   - Times per second rate.
        color  - Primary color, or selected color will be used for counting
        
        After the number of flashes has occurred,
        a pause of 4 * the period (1/freq) and then the count starts over

        Example:
        number = 2
        Blink-Blink Pause, Blink-Blink Pause, etc.
        """
        freq = freq or self.freq
        freq = float(freq)
        number = int(number)
        self.off()  # Turn both colors off

        to_blink, _, c = self.led_for_color(color)
        self.state = f"COUNT:{c}:{number}:{freq}Hz"
        
        def __start_count(_t):
            self.stop_timer()
            self.tick_count = 0
            self.timer = Timer()
            self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=__toggle_with_count)
        
        def __toggle_with_count(_t):
            to_blink.toggle()
            if to_blink.value():  # True implies 1 == ON 0 == OFF
                self.tick_count += 1
            else:
                # since led is off, check our tick_count
                if self.tick_count >= number:
                    # kill our current timer
                    self.stop_timer()
                    # start a NEW one shot timer to kick it off again
                    self.timer = Timer()
                    self.timer.init(mode=Timer.ONE_SHOT, period=int(4000/freq), callback=__start_count)

        __start_count(None)  # Kick off the action
