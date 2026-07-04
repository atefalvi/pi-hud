"""ST7735S 160x80 SPI display driver.

Adapted from the pi-rack-hud driver. Improvements per DRIVER_OPTIMIZATION.md:
configurable pins, safe SPI chunking, targeted GPIO cleanup, cached fonts,
`display_if_changed()` frame hashing, explicit `clear()` / `set_backlight()`,
image validation, and bounded (non-looping) SPI recovery. No numpy.

Hardware imports (spidev, RPi.GPIO) are only available on the Pi; import them
lazily so the rest of the app can be imported/tested on a dev machine.
"""
import logging
import time
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

# --- command / bit constants ------------------------------------------------
_CMD_SWRESET, _CMD_SLPOUT = 0x01, 0x11
_CMD_INVON, _CMD_NORON, _CMD_DISPON = 0x21, 0x20, 0x29
_CMD_CASET, _CMD_RASET, _CMD_RAMWR = 0x2A, 0x2B, 0x2C
_CMD_MADCTL, _CMD_COLMOD = 0x36, 0x3A
_CMD_FRMCTR1, _CMD_FRMCTR2, _CMD_FRMCTR3, _CMD_INVCTR = 0xB1, 0xB2, 0xB3, 0xB4
_CMD_PWCTR1, _CMD_PWCTR2, _CMD_PWCTR3, _CMD_PWCTR4, _CMD_PWCTR5 = \
    0xC0, 0xC1, 0xC2, 0xC3, 0xC4
_CMD_VMCTR1 = 0xC5

_MADCTL_RGB, _MADCTL_MV, _MADCTL_MX, _MADCTL_MY = 0x00, 0x20, 0x40, 0x80
_COLMOD_16BIT = 0x05

_DISPLAY_WIDTH, _DISPLAY_HEIGHT = 80, 160  # native portrait
_MAX_SPI_CHUNK = 4096  # bytes per SPI transfer (kernel limit)

log = logging.getLogger("pi_hud.st7735s")


class ST7735S:
    _FONT_CACHE: dict = {}

    def __init__(self, dc=23, rst=24, bl=18, port=0, cs=0, speed_hz=24_000_000,
                 rotation=270, invert=False, x_offset=24, y_offset=0):
        import RPi.GPIO as GPIO  # lazy: Pi-only
        import spidev
        self._GPIO = GPIO

        self.orig_width, self.orig_height = _DISPLAY_WIDTH, _DISPLAY_HEIGHT
        self._hw_x_offset, self._hw_y_offset = x_offset, y_offset
        self._x_offset, self._y_offset = x_offset, y_offset
        self.width, self.height, self.rotation = self.orig_width, self.orig_height, 0
        self._dc, self._rst, self._bl = dc, rst, bl
        self._port, self._cs, self._speed = port, cs, speed_hz
        self._last_hash: Optional[int] = None

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in (dc, rst, bl):
            GPIO.setup(pin, GPIO.OUT)
        GPIO.output(bl, GPIO.LOW)

        self.spi = spidev.SpiDev()
        try:
            self.spi.open(port, cs)
            self.spi.max_speed_hz = speed_hz
            self.spi.mode = 0
            self.spi.lsbfirst = False
        except Exception:
            GPIO.cleanup([dc, rst, bl])
            raise

        self.reset()
        self.set_backlight(True)
        self._init_display(invert)
        self.set_rotation(rotation)
        self.clear()
        log.info("ST7735S ready rotation=%s offset=(%s,%s)", rotation, x_offset, y_offset)

    # --- context manager ---
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    # --- hardware control ---
    def reset(self):
        G = self._GPIO
        G.output(self._rst, G.HIGH); time.sleep(0.005)
        G.output(self._rst, G.LOW);  time.sleep(0.01)
        G.output(self._rst, G.HIGH); time.sleep(0.15)

    def set_backlight(self, state: bool):
        try:
            self._GPIO.output(self._bl, self._GPIO.HIGH if state else self._GPIO.LOW)
        except Exception:
            log.warning("backlight control failed", exc_info=True)

    def close(self):
        try:
            self.spi.close()
        except Exception:
            log.warning("SPI close failed", exc_info=True)
        try:
            self._GPIO.cleanup([self._dc, self._rst, self._bl])
        except Exception:
            log.warning("GPIO cleanup failed", exc_info=True)

    # --- SPI helpers ---
    def _cmd(self, command: int):
        try:
            self._GPIO.output(self._dc, self._GPIO.LOW)
            self.spi.xfer2([command & 0xFF])
        except Exception:
            log.error("command write failed", exc_info=True)
            self._recover()

    def _data(self, data: Union[bytes, bytearray, List[int]]):
        try:
            self._GPIO.output(self._dc, self._GPIO.HIGH)
            if isinstance(data, (bytes, bytearray)):
                # writebytes2 takes the buffer protocol directly and chunks
                # internally — xfer2 silently mangles large bytes payloads on
                # some py-spidev versions (symptom: panel shows static).
                self.spi.writebytes2(data)
            else:
                for i in range(0, len(data), _MAX_SPI_CHUNK):
                    self.spi.xfer2(data[i:i + _MAX_SPI_CHUNK])
        except Exception:
            log.error("data write failed", exc_info=True)
            self._recover()

    def _recover(self):
        """Best-effort one-shot recovery. Logs and returns; never loops.
        Guarded so failures inside recovery can't recurse back into it."""
        if getattr(self, "_recovering", False):
            return
        self._recovering = True
        log.warning("attempting SPI recovery")
        try:
            self.spi.close(); time.sleep(0.1)
            self.spi.open(self._port, self._cs)
            self.spi.max_speed_hz = self._speed
            self.reset()
            self._init_display(False)
            self.set_rotation(self.rotation)
            self._last_hash = None
            log.info("SPI recovery ok")
        except Exception:
            log.critical("SPI recovery failed", exc_info=True)
        finally:
            self._recovering = False

    # --- init / rotation ---
    def _init_display(self, invert: bool):
        self._cmd(_CMD_SWRESET); time.sleep(0.15)
        self._cmd(_CMD_SLPOUT);  time.sleep(0.5)
        self._cmd(_CMD_FRMCTR1); self._data([0x01, 0x2C, 0x2D])
        self._cmd(_CMD_FRMCTR2); self._data([0x01, 0x2C, 0x2D])
        self._cmd(_CMD_FRMCTR3); self._data([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])
        self._cmd(_CMD_INVCTR);  self._data([0x07])
        self._cmd(_CMD_PWCTR1);  self._data([0xA2, 0x02, 0x84])
        self._cmd(_CMD_PWCTR2);  self._data([0xC5])
        self._cmd(_CMD_PWCTR3);  self._data([0x0A, 0x00])
        self._cmd(_CMD_PWCTR4);  self._data([0x8A, 0x2A])
        self._cmd(_CMD_PWCTR5);  self._data([0x8A, 0xEE])
        self._cmd(_CMD_VMCTR1);  self._data([0x0E])
        self._cmd(_CMD_COLMOD);  self._data([_COLMOD_16BIT])
        self._cmd(_CMD_INVON if invert else _CMD_NORON)
        time.sleep(0.01)
        self._cmd(_CMD_DISPON); time.sleep(0.1)

    def set_rotation(self, rotation: int):
        rotation %= 360
        if rotation not in (0, 90, 180, 270):
            raise ValueError("rotation must be 0/90/180/270")
        madctl = _MADCTL_RGB
        if rotation == 0:
            madctl |= _MADCTL_MX | _MADCTL_MY
            self.width, self.height = self.orig_width, self.orig_height
            self._x_offset, self._y_offset = self._hw_x_offset, self._hw_y_offset
        elif rotation == 90:
            madctl |= _MADCTL_MY | _MADCTL_MV
            self.width, self.height = self.orig_height, self.orig_width
            self._x_offset, self._y_offset = self._hw_y_offset, self._hw_x_offset
        elif rotation == 180:
            self.width, self.height = self.orig_width, self.orig_height
            self._x_offset, self._y_offset = self._hw_x_offset, self._hw_y_offset
        else:  # 270
            madctl |= _MADCTL_MX | _MADCTL_MV
            self.width, self.height = self.orig_height, self.orig_width
            self._x_offset, self._y_offset = self._hw_y_offset, self._hw_x_offset
        self._cmd(_CMD_MADCTL); self._data([madctl])
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self.rotation = rotation

    def _set_window(self, x0, y0, x1, y1):
        x0 += self._x_offset; x1 += self._x_offset
        y0 += self._y_offset; y1 += self._y_offset
        self._cmd(_CMD_CASET); self._data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        self._cmd(_CMD_RASET); self._data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
        self._cmd(_CMD_RAMWR)

    # --- pixel conversion ---
    @staticmethod
    def _image_to_565(image: Image.Image) -> bytes:
        if image.mode != "RGB":
            image = image.convert("RGB")
        buf = bytearray()
        for r, g, b in image.getdata():
            c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
            buf.append(c >> 8); buf.append(c & 0xFF)
        return bytes(buf)

    # --- high-level API ---
    def display(self, image: Image.Image):
        """Blit a PIL image. Validates/resizes to the panel geometry."""
        if not isinstance(image, Image.Image):
            raise TypeError("display() expects a PIL.Image")
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))
        data = self._image_to_565(image)
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self._data(data)

    def display_if_changed(self, image: Image.Image) -> bool:
        """Blit only when the frame differs from the last one. Returns True if
        a write happened. Avoids constant redraws of static/pinned screens."""
        h = hash(image.tobytes())
        if h == self._last_hash:
            return False
        self.display(image)
        self._last_hash = h
        return True

    def clear(self, color: Tuple[int, int, int] = (0, 0, 0)):
        self.display(Image.new("RGB", (self.width, self.height), color))

    # candidate paths for the mono font, tried in order (bare name works on the
    # Pi via fontconfig; absolute paths cover dev machines).
    _FONT_PATHS = {
        True: ["DejaVuSansMono-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
               "/Library/Fonts/DejaVuSansMono-Bold.ttf",
               "/System/Library/Fonts/Menlo.ttc"],
        False: ["DejaVuSansMono.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/System/Library/Fonts/Menlo.ttc",
                "/Library/Fonts/DejaVuSansMono.ttf"],
    }

    @classmethod
    def font(cls, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        key = (size, bold)
        if key not in cls._FONT_CACHE:
            f = None
            for path in cls._FONT_PATHS[bold]:
                try:
                    f = ImageFont.truetype(path, size)
                    break
                except OSError:
                    continue
            cls._FONT_CACHE[key] = f or ImageFont.load_default()
        return cls._FONT_CACHE[key]
