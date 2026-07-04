"""Render the physical HUD screens as 160x80 PIL images, following the
DataDreamer Observatory mockups (dark surface, hairline rules, ember accent,
state-coloured rails/badges). No hardware here — pure Pillow."""
from PIL import Image, ImageDraw

from .drivers.st7735s import ST7735S

W, H = 160, 80

# design tokens (RGB)
BG = (5, 7, 10)
TEXT_1 = (237, 239, 243)
TEXT_2 = (168, 177, 189)
TEXT_3 = (133, 142, 153)
BORDER = (31, 38, 47)
ACCENT = (255, 92, 56)
SUCCESS = (62, 207, 142)
WARNING = (245, 184, 61)
DANGER = (240, 86, 74)
INFO = (92, 167, 255)

# message type -> rail/accent colour
_STATE = {
    "success": SUCCESS, "info": INFO, "note": INFO,
    "warning": WARNING, "caution": ACCENT,
    "error": DANGER, "critical": DANGER,
}
_GLYPH = {
    "success": "OK", "info": "i", "note": "i", "warning": "!",
    "caution": "!", "error": "x", "critical": "!!",
}


def state_color(type: str):
    return _STATE.get(type, INFO)


def _font(size, bold=True):
    return ST7735S.font(size, bold)


def _clamp(draw, text, font, max_w):
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…" if text else ""


def _canvas():
    img = Image.new("RGB", (W, H), BG)
    return img, ImageDraw.Draw(img)


def render_normal(metrics: dict, badges: list, colors: dict) -> Image.Image:
    """metrics: hostname/cpu_percent/ram_percent/temp_c. colors: level colour
    per metric key (temp/cpu/ram). badges: list of (label, rgb)."""
    img, d = _canvas()
    host = _clamp(d, metrics["hostname"], _font(13), 110)
    d.text((6, 2), host, font=_font(13), fill=TEXT_1)

    temp = metrics.get("temp_c")
    temp_txt = f"{round(temp)}°" if temp is not None else "--°"
    tw = d.textlength(temp_txt, font=_font(12))
    d.text((W - 16 - tw, 3), temp_txt, font=_font(12), fill=colors["temp"])
    d.ellipse((W - 10, 6, W - 5, 11), fill=ACCENT)  # live dot

    _bar(d, 24, metrics["cpu_percent"], "CPU", colors["cpu"])
    _bar(d, 42, metrics["ram_percent"], "RAM", colors["ram"])

    _badge_pile(d, badges)
    return img


def _bar(d, y, pct, label, color):
    pct = max(0, min(100, pct or 0))
    d.text((6, y - 1), label, font=_font(10), fill=TEXT_2)
    x0, x1 = 34, 118
    d.rounded_rectangle((x0, y, x1, y + 9), radius=4, outline=BORDER, fill=(22, 27, 34))
    fill_w = int((x1 - x0 - 2) * pct / 100)
    if fill_w > 0:
        d.rounded_rectangle((x0 + 1, y + 1, x0 + 1 + fill_w, y + 8), radius=3, fill=color)
    d.text((124, y - 1), f"{round(pct)}%", font=_font(10), fill=color)


def _badge_pile(d, badges):
    if not badges:
        return
    n = len(badges)
    gap, m = 6, 8
    total = W - 2 * m - gap * (n - 1)
    bw = total // n
    x = m
    y0, y1 = H - 15, H - 3
    for label, color in badges:
        _mix = tuple(int(c * 0.28 + BG[i] * 0.72) for i, c in enumerate(color))
        d.rounded_rectangle((x, y0, x + bw, y1), radius=6, outline=color, fill=_mix)
        d.ellipse((x + 6, (y0 + y1) // 2 - 2, x + 10, (y0 + y1) // 2 + 2), fill=color)
        tw = d.textlength(label, font=_font(9))
        d.text((x + (bw + 8 - tw) // 2, y0 + 2), label, font=_font(9), fill=TEXT_1)
        x += bw + gap


def render_alert(type: str, title: str, message: str | None, pinned: bool,
                 footer_left: str = "", footer_right: str = "clear") -> Image.Image:
    img, d = _canvas()
    color = state_color(type)
    d.rectangle((0, 0, 8, H), fill=color)  # rail
    bx = 14

    # top: type label + PIN badge
    glyph = _GLYPH.get(type, "i")
    d.text((bx, 4), f"{glyph}  {type.upper()}", font=_font(10), fill=color)
    if pinned:
        pin_txt = "PIN"
        pw = d.textlength(pin_txt, font=_font(9))
        d.rounded_rectangle((W - 8 - pw - 8, 3, W - 6, 15), radius=6, outline=color)
        d.text((W - 8 - pw - 4, 4), pin_txt, font=_font(9), fill=color)

    d.text((bx, 18), _clamp(d, title, _font(15), W - bx - 6), font=_font(15), fill=TEXT_1)

    if message:
        _wrap(d, message, bx, 38, W - bx - 6, _font(10), TEXT_2, max_lines=2)

    # footer
    d.text((bx, H - 12), _clamp(d, footer_left, _font(9), 100), font=_font(9), fill=TEXT_3)
    if footer_right:
        rw = d.textlength(footer_right, font=_font(9))
        d.text((W - 6 - rw, H - 12), footer_right, font=_font(9), fill=TEXT_3)
    return img


def _wrap(d, text, x, y, max_w, font, color, max_lines=2):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines:
        lines[-1] = _clamp(d, lines[-1], font, max_w)
    for i, line in enumerate(lines[:max_lines]):
        d.text((x, y + i * 12), line, font=font, fill=color)


def render_queue(total: int, groups: list) -> Image.Image:
    """groups: list of (label, count, rgb). No bottom badge pile."""
    img, d = _canvas()
    d.text((6, 2), f"{total} pending", font=_font(13), fill=TEXT_1)
    d.ellipse((W - 10, 6, W - 5, 11), fill=ACCENT)
    y = 24
    for label, count, color in groups[:3]:
        d.rounded_rectangle((6, y, 11, y + 16), radius=3, fill=color)
        d.text((18, y + 2), label, font=_font(11), fill=TEXT_1)
        cnt = str(count)
        cw = d.textlength(cnt, font=_font(11))
        d.text((W - 10 - cw, y + 2), cnt, font=_font(11), fill=color)
        y += 19
    return img


def render_message(m: dict) -> Image.Image:
    """Pick the right screen for an active message row (dict-like)."""
    md = m.get("metadata") or {}
    # any message with a previous/updated pair gets the change-line screen
    # (DNS updates, config changes, version bumps, ...)
    if md.get("previous_value") and md.get("updated_value"):
        label = md.get("record_type", "")
        body = f"{label} {md['previous_value']} → {md['updated_value']}".strip()
        return render_alert(m["type"], m["title"], body, bool(m["pinned"]),
                            footer_left=md.get("host") or m["source"])
    return render_alert(m["type"], m["title"], m.get("message"), bool(m["pinned"]),
                        footer_left=m["source"])


def render_colorcheck() -> Image.Image:
    """Labeled color bars for panel calibration. Each bar's label names the
    color it SHOULD be — if 'RED' looks blue, flip the bgr setting."""
    img, d = _canvas()
    bars = [("RED", (255, 0, 0)), ("GRN", (0, 255, 0)), ("BLU", (0, 0, 255)),
            ("EMBR", ACCENT), ("WHT", (255, 255, 255))]
    bw = W // len(bars)
    for i, (label, color) in enumerate(bars):
        x = i * bw
        d.rectangle((x, 14, x + bw - 1, H), fill=color)
        d.text((x + 2, 2), label, font=_font(9), fill=color)
    return img


def render_boot(text="pi-hud") -> Image.Image:
    img, d = _canvas()
    d.text((6, 28), text, font=_font(16), fill=TEXT_1)
    d.text((6, 50), "starting…", font=_font(10), fill=TEXT_3)
    return img
