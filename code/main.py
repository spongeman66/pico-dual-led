import machine
from time import sleep
from machine import Pin
from dual_led import DualLED

class BlueYellowDualLED(DualLED):
    """
    Example class if your colors are not Red/Green
    """
    COLORS = ['BLUE', 'YELLOW']  # or whatever you want.


def show_state(led):
    print(f"state => {led.get_state()}")

if __name__=="__main__":
    # Hard Wired Pins
    LED_RED_GPIO = 13  # Output, Normally Low: RED LED 0 == Off, 1 == On
    LED_GRN_GPIO = 14  # Output, Normally Low: GREEN LED 0 == Off, 1 == On

    LED_BLU_GPIO = 16   # Output, Normally Low: BLUE LED 0 == Off, 1 == On
    LED_YEL_GPIO = 19   # Output, Normally Low: YELLOW LED 0 == Off, 1 == On

    print("Running Self test code on GPIO")
    print(f"({DualLED.COLORS[0]}={LED_RED_GPIO}, {DualLED.COLORS[1]}={LED_GRN_GPIO})")
    print(f"({BlueYellowDualLED.COLORS[0]}={LED_BLU_GPIO}, {BlueYellowDualLED.COLORS[1]}={LED_YEL_GPIO})")
    try:
        b_y = BlueYellowDualLED(LED_BLU_GPIO, LED_YEL_GPIO, 'BLUE')
        r_g = DualLED(LED_RED_GPIO, LED_GRN_GPIO, DualLED.COLORS[1])

        r_g.alternate_colors()
        show_state(r_g)
        b_y.alternate_colors()
        show_state(b_y)
        sleep(5)

        r_g.alternate_colors(freq=3)
        show_state(r_g)
        b_y.alternate_colors(freq=3)
        show_state(b_y)
        sleep(5)

        r_g.on('RED')
        show_state(r_g)
        b_y.on('BLUE')
        show_state(b_y)
        sleep(2)

        r_g.on('GREEN')
        show_state(r_g)
        b_y.on('YELLOW')
        show_state(b_y)
        sleep(2)

        r_g.blink(color='RED')
        b_y.blink(color='YELLOW')
        show_state(r_g)
        show_state(b_y)
        sleep(5)

        # Default colors
        r_g.on()
        show_state(r_g)
        b_y.on()
        show_state(b_y)
        sleep(2)

        r_g.off()
        b_y.off()
        sleep(1)

        r_g.blink(freq=5, color=DualLED.COLORS[1])
        show_state(r_g)
        sleep(5)

        r_g.off()
        show_state(r_g)
        sleep(1)

        # Step through setting the primary color
        for led_color in r_g.COLORS:
            print(f"setting primary color: {led_color}")
            r_g.set_primary_color(led_color)
            r_g.on()
            show_state(r_g)
            sleep(1)

            r_g.off()
            show_state(r_g)
            sleep(1)

            r_g.blink()
            show_state(r_g)
            sleep(5)

            r_g.off()
            show_state(r_g)
            sleep(1)

            for n in range(4):
                r_g.count_number(n+1)
                show_state(r_g)
                sleep(6 + n)
                r_g.off()
                sleep(1)

            r_g.off()

    except KeyboardInterrupt:
        machine.reset()
