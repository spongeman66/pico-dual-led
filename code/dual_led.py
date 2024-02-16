from machine import Pin, Timer

class DualLED:
    """
    This represents a single LED with 3 wires.
    Common Cathode (negative)
    Red wire (Positive through a resistor turns RED on)
    Green wire (Positive through a resistor turns GREEN on)
    For the LED I purchased, when both wires are energized, ONLY the RED LED is seen

    Used for controlling both the Armed and the Signal LEDs
    """
    LOG = False
    COLORS = ['RED', 'GREEN']

    def __init__(self, red_pin, green_pin, primary_color, log_title = ""):
        """
        red_pin - GPIO pin for RED color output
        green_pin - GPIO pin for GREEN color output
        primary_color - 'RED' or 'GREEN', primary color to use when ON/BLINKING, etc.
        log_title - When logging, this will be prepended
        """
        self.red_pin = red_pin
        self.green_pin = green_pin
        self.primary_color = primary_color.upper()
        self.primary_led = None
        self.secondary_led = None
        self.timer = None
        self.tick_count = None
        self.color_map = dict()
        if primary_color not in self.COLORS:
            raise ValueError(f"primary color must be 'RED' or 'GREEN' not {primary_color}")

        self.log_title = f"{self.primary_color}-{log_title}:" if log_title else f"{self.primary_color}:"
        self.setup_control()
        self.off()
        
    def setup_control(self):
        self.red_led = Pin(self.red_pin, Pin.OUT, value=0)
        self.green_led = Pin(self.green_pin, Pin.OUT, value=0)
        self.color_map = {
            self.COLORS[0]: self.red_led,
            self.COLORS[1]: self.green_led
        }
        if self.primary_color == 'RED':
            self.primary_led, self.secondary_led = self.red_led, self.green_led
        else:
            self.primary_led, self.secondary_led = self.green_led, self.red_led
        
    def logit(self, message):
        if self.LOG:
            print(f"{self.log_title}{message}")

    def stop_timer(self):
        if self.timer:
            self.timer.deinit()
            self.timer = None
        self.tick_count = None

    def led_for_color(self, color=None):
        """
        reads the color and if None, returns primary, secondary
        if red, returns red, green
        if green, retruns green, red
        """
        if not color:
            return self.primary_led
        color_pos = self.COLORS.index(color.upper())
        return self.color_map[self.COLORS[color_pos]]

    def off(self):
        """
        Turn both red and green off
        """
        self.stop_timer()
        self.red_led.value(0)
        self.green_led.value(0)

    def on(self):
        """
        Turn primary on, secondary off
        """
        self.stop_timer()
        self.secondary_led.value(0)
        self.primary_led.value(1)

    def get_state(self):
        """
        read current state of LEDs
        return primary then secondary state
        """
        return self.primary_led.value(), self.secondary_led.value()

    def red_on(self):
        """
        implies Green off
        """
        self.stop_timer()
        self.green_led.value(0)
        self.red_led.value(1)
        
    def green_on(self):
        """
        implies Red off
        """
        self.stop_timer()
        self.red_led.value(0)
        self.green_led.value(1)
    
    def get_red_green_state(self):
        """
        read current state of LEDs
        return red then green state
        """
        return self.red_led.value(), self.green_led.value()

    def blink(self, freq=2, color=None):
        """
        blink the LED
        freq - Times to blink per second
        color - defaults to primary, but can override by setting to 'RED' or 'GREEN'
        """
        to_blink = self.led_for_color(color)
        self.stop_timer()
        self.off()

        def toggle_blinker(t):
            to_blink.toggle()    
        
        self.timer = Timer()
        # need a * 2 on the frequency because we Toggle at the frequency rather than on half off half
        self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=toggle_blinker)

    def alternate_colors(self, freq=5):
        """
        Primary On, Secondary Off, then toggle both periodically
        freq - (frequency) times per second to alternate
        """
        self.stop_timer()
        self.on()  # Primary set to on, secondary off
        def toggle_both(t):
            self.secondary_led.toggle()
            self.primary_led.toggle()
        
        self.timer = Timer()
        # need a * 2 on the frequency because we Toggle at the frequency rather than on half off half
        self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=toggle_both)

    def blink_number(self, number, freq=2, color=None):
        """
        blinks the LED in the default or chosen Color for
        number - (count) times at the
        freq - Times per second rate.
        
        After the number of flashes has occurred,
            a pause of 4 * the period (1/freq) and then the count starts over 
        
        """
        self.off()  # Turn both colors off

        led_to_blink = self.led_for_color(color)
        
        def __start_count(t):
            self.stop_timer()
            self.tick_count = 0
            self.timer = Timer()
            self.timer.init(mode=Timer.PERIODIC, freq=freq * 2, callback=__toggle_with_count)
        
        def __toggle_with_count(t):
            led_to_blink.toggle()
            if led_to_blink.value():  # True implies 1 == ON 0 == OFF
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
