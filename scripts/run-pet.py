#!/usr/bin/env python3
"""Run a PetHatch pet as a tiny macOS desktop companion."""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

try:
    import Quartz
    from AppKit import (
        NSApp,
        NSApplication,
        NSApplicationActivationPolicyAccessory,
        NSBackingStoreBuffered,
        NSBezierPath,
        NSColor,
        NSEvent,
        NSFloatingWindowLevel,
        NSFont,
        NSForegroundColorAttributeName,
        NSFontAttributeName,
        NSImage,
        NSMakePoint,
        NSMakeRect,
        NSMenu,
        NSMenuItem,
        NSScreen,
        NSStatusWindowLevel,
        NSString,
        NSView,
        NSWindow,
        NSWindowStyleMaskBorderless,
    )
    from Foundation import NSData, NSObject, NSTimer
except Exception as exc:  # pragma: no cover - platform guard
    print(f"error: PetHatch runner requires macOS PyObjC/AppKit: {exc}", file=sys.stderr)
    raise SystemExit(1)

try:
    from PIL import Image
except Exception as exc:  # pragma: no cover - dependency guard
    print(f"error: PetHatch runner requires Pillow: {exc}", file=sys.stderr)
    raise SystemExit(1)


SIZE_PRESETS = {
    "small": (168, 180, 112),
    "medium": (220, 232, 150),
}
FRAME_INTERVALS = {
    "idle": 1.6,
    "running-right": 0.35,
    "running-left": 0.35,
    "waving": 0.8,
    "jumping": 0.7,
    "failed": 1.1,
    "waiting": 1.2,
    "running": 0.8,
    "review": 1.0,
}
TICK_INTERVAL = 0.25


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ns_image_from_pil(image: Image.Image) -> NSImage:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    data = buffer.getvalue()
    ns_data = NSData.dataWithBytes_length_(data, len(data))
    return NSImage.alloc().initWithData_(ns_data)


def load_animations(pet_dir: Path, pet: dict) -> dict[str, list[NSImage]]:
    sheet_path = pet_dir / pet["spritesheet"]["path"]
    sheet = Image.open(sheet_path).convert("RGBA")
    cell_w = int(pet["spritesheet"]["cellWidth"])
    cell_h = int(pet["spritesheet"]["cellHeight"])
    animations: dict[str, list[NSImage]] = {}
    for animation in pet["animations"]:
        row = int(animation["row"])
        frames = int(animation["frames"])
        images = []
        for col in range(frames):
            crop = sheet.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            images.append(ns_image_from_pil(crop))
        animations[animation["name"]] = images
    return animations


def event_to_animation(pet: dict, event_name: str) -> str:
    event = pet.get("events", {}).get(event_name, {})
    return event.get("animation", "idle")


def matched_rule(pet: dict, elapsed_minutes: float, quota_remaining: float) -> dict | None:
    mode_priority = {"soft": 1, "medium": 2, "hard": 3}
    matches = []
    for rule in pet.get("behavior", {}).get("rules", []):
        trigger = rule.get("trigger", {})
        metric = trigger.get("metric")
        operator = trigger.get("operator")
        value = trigger.get("value")
        if not isinstance(value, (int, float)):
            continue
        current = None
        if metric == "codingSessionMinutes":
            current = elapsed_minutes
        elif metric == "quotaRemainingFraction":
            current = quota_remaining
        if current is None:
            continue
        if (
            (operator == ">=" and current >= value)
            or (operator == "<=" and current <= value)
            or (operator == ">" and current > value)
            or (operator == "<" and current < value)
            or (operator == "==" and current == value)
        ):
            matches.append((mode_priority.get(rule.get("mode"), 0), float(value), rule))
    if not matches:
        return None
    return sorted(matches, key=lambda item: (item[0], item[1]))[-1][2]


def input_idle_seconds() -> float:
    return float(
        Quartz.CGEventSourceSecondsSinceLastEventType(
            Quartz.kCGEventSourceStateCombinedSessionState,
            Quartz.kCGAnyInputEventType,
        )
    )


class PetView(NSView):
    def initWithController_(self, controller):
        self = self.initWithFrame_(NSMakeRect(0, 0, controller.window_width, controller.window_height))
        self.controller = controller
        self.drag_start = None
        return self

    def isFlipped(self):  # noqa: N802 - AppKit selector
        return False

    def drawRect_(self, rect):  # noqa: N802 - AppKit selector
        width = self.controller.window_width
        pet_size = self.controller.pet_size
        frame = self.controller.current_frame()
        image_rect = NSMakeRect((width - pet_size) / 2, 56, pet_size, pet_size)
        frame.drawInRect_(image_rect)

        message = self.controller.message
        title = self.controller.title
        bubble = NSMakeRect(8, 8, width - 16, 44)
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bubble, 14, 14)
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.88).setFill()
        path.fill()
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.12).setStroke()
        path.stroke()

        title_attrs = {
            NSFontAttributeName: NSFont.boldSystemFontOfSize_(11),
            NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.08, 1),
        }
        message_attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(10),
            NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.32, 1),
        }
        NSString.stringWithString_(title).drawInRect_withAttributes_(NSMakeRect(18, 33, width - 36, 16), title_attrs)
        NSString.stringWithString_(message).drawInRect_withAttributes_(NSMakeRect(18, 16, width - 36, 15), message_attrs)

    def mouseDown_(self, event):  # noqa: N802 - AppKit selector
        self.drag_start = event.locationInWindow()

    def mouseDragged_(self, event):  # noqa: N802 - AppKit selector
        if self.drag_start is None:
            return
        mouse = NSEvent.mouseLocation()
        self.window().setFrameOrigin_(NSMakePoint(mouse.x - self.drag_start.x, mouse.y - self.drag_start.y))

    def rightMouseDown_(self, event):  # noqa: N802 - AppKit selector
        menu = NSMenu.alloc().initWithTitle_("PetHatch")
        menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Next State", "nextState:", ""))
        menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Reset Session", "resetSession:", ""))
        menu.addItem_(NSMenuItem.separatorItem())
        menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit Xiaochai", "quit:", ""))
        for item in menu.itemArray():
            item.setTarget_(self.controller)
        NSMenu.popUpContextMenu_withEvent_forView_(menu, event, self)


class PetController(NSObject):
    def initWithPetDir_pet_args_(self, pet_dir, pet, args):
        self = self.init()
        self.pet_dir = pet_dir
        self.pet = pet
        self.args = args
        self.window_width, self.window_height, self.pet_size = SIZE_PRESETS[args.size]
        self.animations = load_animations(pet_dir, pet)
        self.animation = event_to_animation(pet, "agent.idle")
        self.frame_index = 0
        self.started_at = time.monotonic()
        self.last_tick_at = self.started_at
        self.active_minutes = 0.0
        self.last_frame_at = 0.0
        self.last_event = "agent.idle"
        self.message = "休息中"
        self.title = f"{pet.get('displayName', pet.get('id', 'Pet'))} · idle"
        self.manual_events = ["agent.running", "session.long", "session.rest_suggested", "session.soft_strike", "agent.idle"]
        self.manual_index = 0
        self.manual_override_until = 0.0
        self.log_event("agent.idle", self.animation, self.message)
        return self

    def applicationDidFinishLaunching_(self, notification):  # noqa: N802 - AppKit selector
        screen = NSScreen.mainScreen().visibleFrame()
        x = self.args.x if self.args.x is not None else screen.size.width - self.window_width - 28
        y = self.args.y if self.args.y is not None else 72
        window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, self.window_width, self.window_height),
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        window.setOpaque_(False)
        window.setBackgroundColor_(NSColor.clearColor())
        window.setHasShadow_(False)
        window.setLevel_(NSStatusWindowLevel if self.args.pin else NSFloatingWindowLevel)
        window.setIgnoresMouseEvents_(False)
        window.setMovableByWindowBackground_(False)
        self.view = PetView.alloc().initWithController_(self)
        window.setContentView_(self.view)
        window.makeKeyAndOrderFront_(None)
        self.window = window
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(TICK_INTERVAL, self, "tick:", None, True)

    def elapsed_minutes(self) -> float:
        return self.active_minutes

    def current_frame(self):
        frames = self.animations.get(self.animation) or self.animations["idle"]
        return frames[self.frame_index % len(frames)]

    def set_event(self, event_name: str, message: str | None = None):
        self.last_event = event_name
        self.animation = event_to_animation(self.pet, event_name)
        self.frame_index = 0
        self.message = message or self.pet.get("events", {}).get(event_name, {}).get("threshold", "")
        self.log_event(event_name, self.animation, self.message)

    def log_event(self, event_name: str, animation: str, message: str):
        if self.args.log_events:
            elapsed = self.elapsed_minutes() if hasattr(self, "started_at") else 0
            print(f"{elapsed:.1f}m\t{event_name}\t{animation}\t{message}", flush=True)

    def update_active_time(self, now: float) -> bool:
        delta = max(0.0, now - self.last_tick_at)
        self.last_tick_at = now
        idle_seconds = input_idle_seconds()
        resting = idle_seconds >= self.args.rest_after
        if resting:
            if self.active_minutes and idle_seconds >= self.args.reset_after:
                self.active_minutes = 0.0
            return False
        self.active_minutes += delta / self.args.minute_seconds
        return True

    def node_title(self, rule: dict | None, active: bool) -> str:
        pet_name = self.pet.get("displayName", self.pet.get("id", "Pet"))
        if not active:
            return f"{pet_name} · rest"
        if not rule:
            return f"{pet_name} · focus"
        label = rule.get("label", "").replace(" min", "m")
        return f"{pet_name} · {label}"

    def update_state(self):
        if time.monotonic() < self.manual_override_until:
            return
        active = self.update_active_time(time.monotonic())
        if not active:
            event_name = "agent.idle"
            message = "检测到休息，计时暂停"
            rule = None
        else:
            rule = matched_rule(self.pet, self.elapsed_minutes(), self.args.quota_remaining)
            if rule:
                event_name = rule["event"]
                message = rule["message"]
            else:
                event_name = "agent.running"
                message = "正在陪你 coding"
        if rule:
            message = rule["message"]
        if event_name != self.last_event:
            self.set_event(event_name, message)
        self.title = self.node_title(rule, active)

    def tick_(self, timer):  # noqa: N802 - AppKit selector
        now = time.monotonic()
        if self.args.duration and now - self.started_at >= self.args.duration:
            NSApp.terminate_(None)
            return
        self.update_state()
        frame_interval = self.args.frame_interval or FRAME_INTERVALS.get(self.animation, 1.0)
        if now - self.last_frame_at >= frame_interval:
            self.last_frame_at = now
            frames = self.animations.get(self.animation) or self.animations["idle"]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.view.setNeedsDisplay_(True)

    def nextState_(self, sender):  # noqa: N802 - AppKit selector
        self.manual_index = (self.manual_index + 1) % len(self.manual_events)
        event_name = self.manual_events[self.manual_index]
        message = self.pet.get("events", {}).get(event_name, {}).get("threshold") or event_name
        self.manual_override_until = time.monotonic() + 6
        self.set_event(event_name, message)
        self.view.setNeedsDisplay_(True)

    def resetSession_(self, sender):  # noqa: N802 - AppKit selector
        self.started_at = time.monotonic()
        self.last_tick_at = self.started_at
        self.active_minutes = 0.0
        self.manual_override_until = 0.0
        self.set_event("agent.idle", "计时已重置")
        self.view.setNeedsDisplay_(True)

    def quit_(self, sender):  # noqa: N802 - AppKit selector
        NSApp.terminate_(None)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a PetHatch pet as a macOS desktop companion.")
    parser.add_argument("pet_dir", type=Path, help="Directory containing pet.json and spritesheet.webp.")
    parser.add_argument("--demo", action="store_true", help="Compress pet minutes so behavior changes quickly.")
    parser.add_argument("--minute-seconds", type=float, default=None, help="Seconds per pet minute. Default: 60, demo: 0.25.")
    parser.add_argument("--rest-after", type=float, default=None, help="Pause session after this many input-idle seconds. Default: 300, demo: 4.")
    parser.add_argument("--reset-after", type=float, default=None, help="Reset session after this many input-idle seconds. Default: 900, demo: 10.")
    parser.add_argument("--size", choices=sorted(SIZE_PRESETS), default="small", help="Desktop pet size.")
    parser.add_argument("--frame-interval", type=float, default=None, help="Override seconds between animation frames.")
    parser.add_argument("--quota-remaining", type=float, default=1.0, help="Quota remaining fraction for quota behavior demos.")
    parser.add_argument("--duration", type=float, default=0.0, help="Exit after this many seconds. Useful for smoke tests.")
    parser.add_argument("--log-events", action="store_true", help="Print event transitions to stdout.")
    parser.add_argument("--x", type=float, default=None, help="Initial window x position.")
    parser.add_argument("--y", type=float, default=None, help="Initial window y position.")
    parser.add_argument("--pin", action="store_true", help="Use a higher always-on-top level.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.minute_seconds = args.minute_seconds if args.minute_seconds is not None else (0.25 if args.demo else 60.0)
    args.rest_after = args.rest_after if args.rest_after is not None else (4.0 if args.demo else 300.0)
    args.reset_after = args.reset_after if args.reset_after is not None else (10.0 if args.demo else 900.0)
    pet_dir = args.pet_dir.expanduser().resolve()
    pet = load_json(pet_dir / "pet.json")

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    controller = PetController.alloc().initWithPetDir_pet_args_(pet_dir, pet, args)
    app.setDelegate_(controller)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
