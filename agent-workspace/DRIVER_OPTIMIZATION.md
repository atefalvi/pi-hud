# Driver Optimization

## Source driver

Use the existing ST7735S driver from `pi-rack-hud` as the starting point.

Place it at:

```text
src/pi_hud/drivers/st7735s.py
```

## Required cleanup

The previous repo had a possible docs/code pin mismatch. Confirm and make pins configurable.

Config must support:

```ini
[display]
rotation = 270
x_offset = 24
y_offset = 0
dc_pin = 23
rst_pin = 24
bl_pin = 18
spi_port = 0
spi_cs = 0
spi_speed_hz = 24000000
```

## Performance goals

- Avoid full redraws when screen content is unchanged.
- Cache fonts.
- Cache static screen backgrounds.
- Render pinned alert once and reuse until changed.
- Normal screen refresh every 2 seconds.
- Power checks every 10 seconds.
- Avoid pulling in numpy.
- Keep SPI chunking.
- Keep safe cleanup on exit.

## Driver improvements

1. Keep `display(image)` as the high-level API.
2. Add `display_if_changed(image)` using a cheap frame hash.
3. Add explicit `clear()` method.
4. Add `set_backlight(state)` method.
5. Preserve chunked SPI writes.
6. Make recovery log errors but do not infinite-loop.
7. Validate image size and mode.
8. Keep GPIO cleanup targeted to pins used by the display only.

## Pseudocode

```python
class DisplayManager:
    def __init__(self, driver, renderer):
        self.driver = driver
        self.renderer = renderer
        self.last_frame_hash = None

    def show(self, frame):
        frame_hash = hash(frame.tobytes())
        if frame_hash == self.last_frame_hash:
            return
        self.driver.display(frame)
        self.last_frame_hash = frame_hash
```
