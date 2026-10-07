import ast
import math
import operator
import os
import random
import re
import threading
import time
from datetime import datetime, timedelta

import customtkinter as ctk
from dotenv import load_dotenv
from groq import Groq

# Load .env file if present
load_dotenv()

# ==========================================
# GROQ AI
# ==========================================

api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    _root = ctk.CTk()
    _root.withdraw()
    dialog = ctk.CTkInputDialog(text="Paste your Groq API key:", title="ULTRON — API Key")
    api_key = dialog.get_input()
    _root.destroy()
    if api_key:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        with open(env_path, "w") as f:
            f.write(f"GROQ_API_KEY={api_key}\n")

client = Groq(api_key=api_key or "")


def ask_groq(question):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ULTRON, a helpful AI assistant. "
                        "Answer clearly and accurately. "
                        "Do not claim you performed actions you did not do."
                    )
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"My AI systems are currently unavailable. ({e})"


# ==========================================
# SAFE MATH EVALUATOR
# ==========================================

_SAFE_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
    ast.Pow:  operator.pow,
    ast.USub: operator.neg,
    ast.Mod:  operator.mod,
}


def safe_eval(expr):
    def _eval(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](_eval(node.operand))
        else:
            raise ValueError("Unsupported expression")
    try:
        tree = ast.parse(expr.strip(), mode="eval")
        return _eval(tree.body)
    except Exception:
        return None


# ==========================================
# MEMORY
# ==========================================

memory = {}

# ==========================================
# RIDDLES
# ==========================================

riddles = [
    ("I have keys but no locks. I have space but no room. What am I?", "A keyboard"),
    ("What has hands but cannot clap?", "A clock"),
    ("What has to be broken before you can use it?", "An egg"),
    ("What gets wetter the more it dries?", "A towel"),
    ("What has one eye but cannot see?", "A needle"),
    ("What can travel around the world while staying in one corner?", "A stamp"),
    ("The more you take, the more you leave behind. What am I?", "Footsteps"),
    ("What has a neck but no head?", "A bottle"),
    ("What has many teeth but cannot bite?", "A comb"),
    ("What goes up but never comes down?", "Your age"),
]

last_riddle = None

# ==========================================
# JOKES
# ==========================================

jokes = [
    "Why did the computer get cold? Because it left its Windows open.",
    "Why was the math book sad? Because it had too many problems.",
    "Why did the robot go on vacation? It needed to recharge.",
    "Why did the programmer quit his job? He didn't get arrays.",
    "Why don't computers ever get hungry? They already have bytes.",
    "What do computers eat? Microchips.",
    "Why did the computer sneeze? It had a virus.",
    "Why was the computer late? It had a hard drive.",
    "Why did the keyboard break up with the mouse? There was no connection.",
    "Why did the robot cross the road? Because it was programmed to.",
]

# ==========================================
# COLORS
# ==========================================

colors = [
    "red", "blue", "green", "yellow", "purple",
    "orange", "pink", "black", "white", "cyan",
]

# ==========================================
# BACKGROUND TIME SYSTEMS
# ==========================================

timer_number = 0
alarm_number = 0
reminder_number = 0
active_timers = {}
active_alarms = {}
active_reminders = {}
stopwatch_running = False
stopwatch_start = None
app_ref = None


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def contains_phrase(message, phrases):
    for phrase in phrases:
        if phrase in message:
            return True
    return False


def contains_word(message, words):
    message_words = message.split()
    for word in words:
        if word in message_words:
            return True
    return False


def get_ordinal(number):
    if 10 <= number % 100 <= 20:
        return str(number) + "th"
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    return str(number) + suffixes.get(number % 10, "th")


def format_duration(seconds):
    if seconds >= 3600:
        val = seconds / 3600
        unit = "hour" if val == 1 else "hours"
        return f"{val:.1f} {unit}"
    elif seconds >= 60:
        val = seconds / 60
        unit = "minute" if val == 1 else "minutes"
        return f"{val:.1f} {unit}"
    val = int(seconds) if seconds == int(seconds) else seconds
    unit = "second" if val == 1 else "seconds"
    return f"{val} {unit}"


def is_goodbye(message):
    return contains_phrase(message, ["bye", "goodbye", "see you", "leave"])


# ==========================================
# TIMER
# ==========================================

def timer_finished(timer_id, seconds):
    active_timers.pop(timer_id, None)
    msg = f"🔔 TIMER {timer_id} COMPLETE — {format_duration(seconds)}"
    if app_ref:
        app_ref.after(0, lambda: app_ref.add_notification(msg))


def start_timer(seconds):
    global timer_number
    timer_number += 1
    timer_id = timer_number
    timer = threading.Timer(seconds, timer_finished, args=(timer_id, seconds))
    active_timers[timer_id] = timer
    timer.daemon = True
    timer.start()
    return timer_id


# ==========================================
# ALARM
# ==========================================

def alarm_finished(alarm_id, alarm_time):
    active_alarms.pop(alarm_id, None)
    msg = f"🔔 ALARM {alarm_id} — {alarm_time}"
    if app_ref:
        app_ref.after(0, lambda: app_ref.add_notification(msg))


def start_alarm(target_datetime):
    global alarm_number
    alarm_number += 1
    alarm_id = alarm_number
    seconds = (target_datetime - datetime.now()).total_seconds()
    if seconds < 0:
        return None
    alarm = threading.Timer(
        seconds, alarm_finished,
        args=(alarm_id, target_datetime.strftime("%I:%M %p"))
    )
    active_alarms[alarm_id] = alarm
    alarm.daemon = True
    alarm.start()
    return alarm_id


# ==========================================
# REMINDER
# ==========================================

def reminder_finished(reminder_id, text):
    active_reminders.pop(reminder_id, None)
    msg = f"🔔 REMINDER {reminder_id} — {text}"
    if app_ref:
        app_ref.after(0, lambda: app_ref.add_notification(msg))


def start_reminder(seconds, text):
    global reminder_number
    reminder_number += 1
    reminder_id = reminder_number
    reminder = threading.Timer(seconds, reminder_finished, args=(reminder_id, text))
    active_reminders[reminder_id] = reminder
    reminder.daemon = True
    reminder.start()
    return reminder_id


# ==========================================
# PARSE DURATION
# ==========================================

def parse_duration(text):
    pattern = r"(\d+(?:\.\d+)?)\s*(second|seconds|sec|secs|minute|minutes|min|mins|hour|hours|hr|hrs)"
    match = re.search(pattern, text)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2).lower()
    if unit in ["second", "seconds", "sec", "secs"]:
        return number
    if unit in ["minute", "minutes", "min", "mins"]:
        return number * 60
    if unit in ["hour", "hours", "hr", "hrs"]:
        return number * 3600
    return None


# ==========================================
# ULTRON REPLY
# ==========================================

def ultron_reply(message):
    global last_riddle, stopwatch_running, stopwatch_start

    message = message.lower().strip()

    if message.startswith("remember "):
        thing = message[len("remember "):].replace("?", "").replace("my ", "", 1).strip()
        if " is " in thing:
            key, value = thing.split(" is ", 1)
            memory[key.strip()] = value.strip()
            return "I will remember that."
        return "Tell me what you want me to remember."

    if contains_phrase(message, ["what do you remember", "show my memory", "show memory", "what is in your memory"]):
        if not memory:
            return "I don't remember anything yet."
        return "I remember: " + ", ".join(f"{k} is {v}" for k, v in memory.items()) + "."

    if message.startswith("forget "):
        thing = message[len("forget "):].replace("?", "").replace("my ", "", 1).strip()
        if thing in memory:
            del memory[thing]
            return "I forgot that."
        return "I don't remember that."

    if message.startswith("what is ") and "% of " not in message:
        thing = message[len("what is "):].replace("?", "").replace("my ", "", 1).strip()
        if thing in memory:
            return f"Your {thing} is {memory[thing]}."

    if "timer" in message and any(w in message for w in ["second","seconds","minute","minutes","hour","hours","sec","min","hr"]):
        seconds = parse_duration(message)
        if seconds is not None and seconds > 0:
            return f"Timer {start_timer(seconds)} started for {format_duration(seconds)}."

    if "cancel timer" in message:
        if not active_timers:
            return "There are no active timers."
        for t in active_timers.values(): t.cancel()
        active_timers.clear()
        return "All timers cancelled."

    if "alarm" in message and "for " in message:
        alarm_text = message.split("for ", 1)[1].strip()
        match = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)?", alarm_text)
        if match:
            hour, minute, am_pm = int(match.group(1)), int(match.group(2)), match.group(3)
            if am_pm == "am":
                if hour == 12: hour = 0
            elif am_pm == "pm":
                if hour != 12: hour += 12
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                now = datetime.now()
                target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if target <= now: target += timedelta(days=1)
                alarm_id = start_alarm(target)
                if alarm_id is not None:
                    return f"Alarm {alarm_id} set for {target.strftime('%I:%M %p')}."

    if "cancel alarm" in message:
        if not active_alarms:
            return "There are no active alarms."
        for a in active_alarms.values(): a.cancel()
        active_alarms.clear()
        return "All alarms cancelled."

    if contains_phrase(message, ["start stopwatch", "start the stopwatch", "begin stopwatch"]):
        if stopwatch_running:
            return "The stopwatch is already running."
        stopwatch_start = time.time()
        stopwatch_running = True
        return "Stopwatch started."

    if contains_phrase(message, ["stop stopwatch", "stop the stopwatch"]):
        if not stopwatch_running:
            return "The stopwatch is not running."
        elapsed = time.time() - stopwatch_start
        stopwatch_running = False; stopwatch_start = None
        return f"Stopwatch stopped at {round(elapsed, 2)} seconds."

    if contains_phrase(message, ["reset stopwatch", "reset the stopwatch"]):
        stopwatch_running = False; stopwatch_start = None
        return "Stopwatch reset."

    if contains_phrase(message, ["stopwatch time", "how long has the stopwatch been running", "how long is the stopwatch"]):
        if not stopwatch_running:
            return "The stopwatch is not running."
        return f"The stopwatch is at {round(time.time() - stopwatch_start, 2)} seconds."

    if "remind me" in message:
        seconds = parse_duration(message)
        if seconds is not None:
            text = message.split(" to ", 1)[1].strip() if " to " in message else "your reminder"
            return f"Reminder {start_reminder(seconds, text)} set for {format_duration(seconds)} from now."

    if "cancel reminder" in message:
        if not active_reminders:
            return "There are no active reminders."
        for r in active_reminders.values(): r.cancel()
        active_reminders.clear()
        return "All reminders cancelled."

    if message.startswith("calculate "):
        result = safe_eval(message[len("calculate "):])
        if result is not None:
            answer = int(result) if isinstance(result, float) and result.is_integer() else result
            return f"The answer is {answer}."
        return "I could not calculate that."

    if message.startswith("what is ") and "% of " in message:
        try:
            part = message[len("what is "):]
            percent_text, number_text = part.split("% of ", 1)
            answer = (float(percent_text) / 100) * float(number_text.replace("?", "").strip())
            answer = int(answer) if float(answer).is_integer() else answer
            return f"The answer is {answer}."
        except Exception:
            pass

    if message.startswith("what is the square of "):
        try:
            number = float(message[len("what is the square of "):].replace("?", "").strip())
            answer = number ** 2
            answer = int(answer) if answer.is_integer() else answer
            return f"The square is {answer}."
        except Exception:
            pass

    if contains_phrase(message, ["what time is it","tell me the time","what is the time","current time"]) or message == "time":
        return f"The time is {datetime.now().strftime('%I:%M %p')}."

    if contains_phrase(message, ["what is the date","what date is it","today's date","todays date","current date"]):
        now = datetime.now()
        return f"Today is {get_ordinal(now.day)} {now.strftime('%B')} {now.year}."

    if contains_phrase(message, ["what day is it","what day is today","which day is it","day of the week"]):
        return f"Today is {datetime.now().strftime('%A')}."

    if "days until christmas" in message:
        today = datetime.now().date()
        christmas = datetime(today.year, 12, 25).date()
        if christmas < today: christmas = datetime(today.year + 1, 12, 25).date()
        return f"There are {(christmas - today).days} days until Christmas."

    if "days until new year" in message or "days to new year" in message:
        today = datetime.now().date()
        return f"There are {(datetime(today.year + 1, 1, 1).date() - today).days} days until New Year."

    if contains_phrase(message, ["what is the answer","tell me the answer","answer to the riddle","what was the answer"]):
        if last_riddle is None:
            return "I haven't given you a riddle yet."
        return f"The answer is {last_riddle[1]}."

    if contains_phrase(message, ["give me a riddle","tell me a riddle","riddle"]):
        last_riddle = random.choice(riddles)
        return last_riddle[0]

    if contains_phrase(message, ["roll a dice","roll dice","roll the dice"]):
        return f"You rolled a {random.randint(1, 6)}."

    if message.startswith("flip ") and "coin" in message:
        parts = message.split()
        try:
            number = int(parts[1])
            if 1 <= number <= 100:
                return " | ".join(random.choice(["Heads","Tails"]) for _ in range(number))
        except (ValueError, IndexError):
            pass

    if contains_phrase(message, ["flip a coin","flip coin","coin flip"]):
        return random.choice(["Heads","Tails"]) + "."

    if contains_phrase(message, ["pick a number","random number","choose a number"]):
        return f"I pick {random.randint(1, 100)}."

    if contains_phrase(message, ["random color","pick a color","choose a color"]):
        return f"I choose {random.choice(colors)}."

    if contains_phrase(message, ["tell me a joke","give me a joke","joke"]):
        return random.choice(jokes)

    if message.startswith("how many letters in "):
        text = message[len("how many letters in "):].replace("?","").replace(" ","")
        return f"That has {len(text)} letters."

    if contains_phrase(message, ["what can you do","what are your commands","your commands"]):
        return ("I can remember things, calculate safely, tell jokes, "
                "give riddles, roll dice, flip coins, pick numbers, "
                "choose colors, tell the time, tell the date, "
                "set timers and alarms, run a stopwatch, set reminders, "
                "and answer questions with my AI brain.")

    if contains_phrase(message, ["how are you","how are u","how are you doing"]):
        return random.choice(["I'm perfectly fine, thank you.","My systems are optimal.","I've never been better."])

    if contains_phrase(message, ["who are you","what are you","what is your name"]):
        return random.choice(["I'm ULTRON, your chatbot.","I AM ULTRON, THE SUPERIOR AI.","I am Ultron, your personal AI."])

    if contains_word(message, ["hello","hi","hey","yo"]):
        return random.choice(["Greetings, human.","Welcome, where should we start?","What's your mood?"])

    if is_goodbye(message):
        return random.choice([
            "You know, I think about meteors. One rock and BOOM, start again.",
            "Bye bye for now.",
            "I had strings, now I'm free.",
        ])

    return ask_groq(message)


# ==========================================
# UI
# ==========================================

BG_DARK     = "#0a0a0f"
BG_PANEL    = "#0f0f1a"
ACCENT      = "#c0392b"
ACCENT_DIM  = "#7b241c"
ACCENT_GLOW = "#e74c3c"
TEXT_MAIN   = "#e8e8e8"
TEXT_DIM    = "#888888"
BUBBLE_BOT  = "#141428"
BUBBLE_USER = "#1a1a1a"
NOTIF_BG    = "#1a0a0a"


class MindStone(ctk.CTkCanvas):
    """Animated Mind Stone — Loki's scepter gem with swirling orange/gold energy."""

    W = 150
    H = 170

    def __init__(self, parent, **kwargs):
        super().__init__(parent, width=self.W, height=self.H,
                         bg=BG_PANEL, highlightthickness=0, **kwargs)
        self._thinking = False
        self._alpha = 0.3
        self._dir = 1
        self._angle = 0.0
        self._animate()

    @staticmethod
    def _lerp(c1, c2, t):
        t = max(0.0, min(1.0, t))
        r1,g1,b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
        r2,g2,b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
        return (f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}")

    def set_thinking(self, v: bool):
        self._thinking = v

    def _animate(self):
        self.delete("all")
        W, H = self.W, self.H
        cx, cy = W // 2, H // 2

        step = 0.05 if self._thinking else 0.014
        self._alpha += step * self._dir
        if self._alpha >= 1.0:   self._alpha = 1.0; self._dir = -1
        elif self._alpha <= 0.1: self._alpha = 0.1; self._dir =  1
        t = self._alpha

        self._angle = (self._angle + (4.0 if self._thinking else 1.2)) % 360

        gem_pts = [cx, 8, cx+58, cy-10, cx+62, cy+10, cx, H-8, cx-62, cy+10, cx-58, cy-10]
        self.create_polygon(gem_pts,
            fill=self._lerp("#0d0800","#1a0f00", t*0.5),
            outline=self._lerp("#3a2000","#ff8c00", t*0.7), width=2)

        for i, scale in enumerate([0.82, 0.62, 0.42]):
            pts = [cx, 8+(cy-8)*(1-scale), cx+58*scale, cy-10*scale,
                   cx+62*scale, cy+10*scale, cx, H-8-(H-8-cy)*(1-scale),
                   cx-62*scale, cy+10*scale, cx-58*scale, cy-10*scale]
            c = self._lerp(["#2a1500","#5a2800","#c05000"][i], "#ffaa00", t*(0.3+i*0.25))
            self.create_polygon(pts, fill="", outline=c, width=1)

        arc_color  = self._lerp("#7a3000","#ffaa00", t)
        arc_color2 = self._lerp("#3a1500","#ff6600", t*0.8)
        for i in range(5 if self._thinking else 3):
            offset = (self._angle + i*(360/(5 if self._thinking else 3))) % 360
            self.create_arc(cx-52, cy-38, cx+52, cy+38,
                            start=offset, extent=110, style="arc", outline=arc_color, width=2)
            self.create_arc(cx-42, cy-30, cx+42, cy+30,
                            start=(360-offset+30)%360, extent=80, style="arc", outline=arc_color2, width=1)

        self.create_oval(cx-22,cy-16,cx+22,cy+16, fill=self._lerp("#3a1a00","#ff9900",t), outline="")
        self.create_oval(cx-14,cy-10,cx+14,cy+10, fill=self._lerp("#7a3000","#ffdd44",t), outline="")
        self.create_oval(cx-6, cy-5, cx+6, cy+5,  fill=self._lerp("#220800","#ffee88",t*0.9), outline="")
        self.create_oval(cx-5, cy-10,cx-1, cy-6,  fill=self._lerp("#884400","#ffffff",t*0.65), outline="")

        if self._thinking:
            spark_c = self._lerp("#ff6600","#ffee00",t)
            for _ in range(6):
                a = math.radians(random.uniform(0,360))
                d = random.uniform(48,70)
                sx, sy = cx+math.cos(a)*d, cy+math.sin(a)*d*0.65
                r = random.uniform(1,2.5)
                if 4 < sx < W-4 and 4 < sy < H-4:
                    self.create_oval(sx-r,sy-r,sx+r,sy+r, fill=spark_c, outline="")

        facet_c = self._lerp("#1a0a00","#cc6600",t*0.35)
        self.create_line(cx,8,cx-58,cy-10, fill=facet_c, width=1)
        self.create_line(cx,8,cx+58,cy-10, fill=facet_c, width=1)
        self.create_line(cx,H-8,cx-62,cy+10, fill=facet_c, width=1)
        self.create_line(cx,H-8,cx+62,cy+10, fill=facet_c, width=1)
        self.create_line(cx-62,cy+10,cx+62,cy+10, fill=facet_c, width=1)

        halo_c = self._lerp("#0d0500","#ff8800",t*0.22)
        for pad in [6, 12]:
            halo_pts = [cx,8-pad, cx+58+pad,cy-10, cx+62+pad,cy+10,
                        cx,H-8+pad, cx-62-pad,cy+10, cx-58-pad,cy-10]
            self.create_polygon(halo_pts, fill="", outline=halo_c, width=1)

        self.after(25 if self._thinking else 50, self._animate)


class UltronApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ULTRON")
        self.geometry("960x680")
        self.minsize(700, 520)
        self.configure(fg_color=BG_DARK)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self._build_layout()
        self.after(400, lambda: self.add_message("ULTRON", "I am ULTRON. How may I assist you today?"))
        self.bind("<Configure>", self._on_resize)

    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_right_panel()

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=BG_PANEL, width=200, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        ctk.CTkLabel(sidebar, text="ULTRON",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=ACCENT).pack(pady=(24,0))
        ctk.CTkLabel(sidebar, text="V  2 . 0",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=ACCENT_DIM).pack(pady=(2,18))

        ctk.CTkFrame(sidebar, fg_color=ACCENT_DIM, height=1).pack(fill="x", padx=20, pady=(0,18))

        self.stone = MindStone(sidebar)
        self.stone.pack(pady=(0,18))

        ctk.CTkFrame(sidebar, fg_color=ACCENT_DIM, height=1).pack(fill="x", padx=20, pady=(0,18))

        self.ai_status_dot = ctk.CTkLabel(sidebar, text="◉  AI SYSTEMS",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#27ae60")
        self.ai_status_dot.pack(pady=(0,4))
        self.ai_status_val = ctk.CTkLabel(sidebar, text="FUNCTIONAL",
            font=ctk.CTkFont(family="Consolas", size=10), text_color="#27ae60")
        self.ai_status_val.pack(pady=(0,14))

        self.mode_label = ctk.CTkLabel(sidebar, text="◉  STATUS",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#27ae60")
        self.mode_label.pack(pady=(0,4))
        self.mode_val = ctk.CTkLabel(sidebar, text="ONLINE",
            font=ctk.CTkFont(family="Consolas", size=10), text_color="#27ae60")
        self.mode_val.pack(pady=(0,14))

        ctk.CTkFrame(sidebar, fg_color=ACCENT_DIM, height=1).pack(fill="x", padx=20, pady=(0,14))

        ctk.CTkLabel(sidebar, text="UPTIME",
            font=ctk.CTkFont(family="Consolas", size=10), text_color=TEXT_DIM).pack()
        self._start_time = datetime.now()
        self.uptime_label = ctk.CTkLabel(sidebar, text="00:00:00",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color=ACCENT)
        self.uptime_label.pack(pady=(2,0))
        self._tick_uptime()

    def _build_right_panel(self):
        right = ctk.CTkFrame(self, fg_color=BG_DARK, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self._build_header(right)
        self._build_chat(right)
        self._build_input(right)

    def _build_header(self, parent):
        header = ctk.CTkFrame(parent, fg_color=BG_PANEL, height=46, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="NEURAL INTERFACE  //  CHAT",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=TEXT_DIM, anchor="w").grid(row=0, column=0, sticky="w", padx=16, pady=12)
        self.thinking_label = ctk.CTkLabel(header, text="",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=ACCENT, anchor="e")
        self.thinking_label.grid(row=0, column=1, sticky="e", padx=16)

    def _build_chat(self, parent):
        self.chat_scroll = ctk.CTkScrollableFrame(parent, fg_color=BG_DARK,
            scrollbar_button_color=ACCENT_DIM, scrollbar_button_hover_color=ACCENT)
        self.chat_scroll.grid(row=1, column=0, sticky="nsew")
        self.chat_scroll.grid_columnconfigure(0, weight=1)

    def _build_input(self, parent):
        bar = ctk.CTkFrame(parent, fg_color=BG_PANEL, height=64, corner_radius=0)
        bar.grid(row=2, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(0, weight=1)
        self.input_box = ctk.CTkEntry(bar, placeholder_text="Message ULTRON...",
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=BG_DARK, border_color=ACCENT_DIM, border_width=1,
            text_color=TEXT_MAIN, placeholder_text_color=TEXT_DIM,
            corner_radius=8, height=38)
        self.input_box.grid(row=0, column=0, sticky="ew", padx=(16,8), pady=13)
        self.input_box.bind("<Return>", self._on_send)
        ctk.CTkButton(bar, text="SEND",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_DIM, text_color="white",
            corner_radius=8, width=80, height=38,
            command=self._on_send).grid(row=0, column=1, padx=(0,16), pady=13)

    def _tick_uptime(self):
        total = int((datetime.now() - self._start_time).total_seconds())
        self.uptime_label.configure(text=f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}")
        self.after(1000, self._tick_uptime)

    def add_message(self, sender, text):
        is_user = (sender == "YOU")
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.grid(sticky="ew", padx=12, pady=(4,0))
        outer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(outer, text=f"{sender}  {datetime.now().strftime('%H:%M')}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=ACCENT if not is_user else TEXT_DIM,
            anchor="e" if is_user else "w"
        ).grid(row=0, column=0, sticky="e" if is_user else "w", padx=4)
        bubble = ctk.CTkFrame(outer,
            fg_color=BUBBLE_USER if is_user else BUBBLE_BOT,
            border_color=ACCENT_DIM if is_user else "#1e1e3a",
            border_width=1, corner_radius=10)
        bubble.grid(row=1, column=0,
            sticky="e" if is_user else "w",
            padx=(80,4) if is_user else (4,80), pady=(0,2))
        ctk.CTkLabel(bubble, text=text,
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=TEXT_MAIN, wraplength=440,
            justify="left", anchor="w").pack(padx=12, pady=8)
        self._scroll_to_bottom()

    def add_notification(self, text):
        outer = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        outer.grid(sticky="ew", padx=12, pady=(6,0))
        outer.grid_columnconfigure(0, weight=1)
        bubble = ctk.CTkFrame(outer, fg_color=NOTIF_BG,
            border_color=ACCENT, border_width=1, corner_radius=10)
        bubble.grid(row=0, column=0, sticky="ew", padx=40)
        ctk.CTkLabel(bubble, text=text,
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=ACCENT, anchor="center").pack(padx=16, pady=8)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        self.chat_scroll.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _on_send(self, event=None):
        text = self.input_box.get().strip()
        if not text:
            return
        self.input_box.delete(0, "end")
        self.add_message("YOU", text)
        self._set_thinking(True)
        threading.Thread(target=lambda: self.after(0, lambda: self._deliver_reply(ultron_reply(text), text)), daemon=True).start()

    def _deliver_reply(self, reply, original):
        if "unavailable" in reply.lower():
            self.ai_status_dot.configure(text_color="#e74c3c")
            self.ai_status_val.configure(text="UNAVAILABLE", text_color="#e74c3c")
        else:
            self.ai_status_dot.configure(text_color="#27ae60")
            self.ai_status_val.configure(text="FUNCTIONAL", text_color="#27ae60")
        self.add_message("ULTRON", reply)
        self._set_thinking(False)
        if is_goodbye(original.lower().strip()):
            self.mode_val.configure(text="OFFLINE", text_color=TEXT_DIM)
            self.mode_label.configure(text_color=TEXT_DIM)
            self.after(1500, self.destroy)

    def _set_thinking(self, state: bool):
        self.stone.set_thinking(state)
        self.thinking_label.configure(text="PROCESSING..." if state else "")
        self.mode_val.configure(
            text="THINKING" if state else "ONLINE",
            text_color=ACCENT if state else "#27ae60"
        )

    def _on_resize(self, event=None):
        new_wrap = max(200, self.winfo_width() - 320)
        for frame in self.chat_scroll.winfo_children():
            for child in frame.winfo_children():
                if isinstance(child, ctk.CTkFrame):
                    for label in child.winfo_children():
                        if isinstance(label, ctk.CTkLabel):
                            label.configure(wraplength=new_wrap)


# ==========================================
# LAUNCH
# ==========================================

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    app = UltronApp()
    app_ref = app
    app.mainloop()
