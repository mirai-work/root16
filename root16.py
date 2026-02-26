import pyxel
import random

# --- 定数 ---
SCREEN_SIZE = 128
UI_PANEL_HEIGHT = 48
WORLD_SIZE = 256
STATE_TITLE, STATE_PLAY, STATE_CLEAR, STATE_GAMEOVER, STATE_ENDING, STATE_TUTORIAL = range(6)

# --- 迷路データ ---
MAZE_DATA = {
    1: [[1,1,0,0,0,0,1,1],[1,0,0,0,0,0,0,1],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[1,0,0,0,0,0,0,1],[1,1,0,0,0,0,1,1]],
    2: [[1,1,0,0,0,0,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,0,0,1,1,0,0,1],[1,0,0,1,1,0,0,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,1,0,0,0,0,1,1]],
    3: [[0,0,0,1,1,0,0,0],[0,1,0,0,0,0,1,0],[0,0,0,0,0,0,0,0],[1,0,0,1,1,0,0,1],[1,0,0,1,1,0,0,1],[0,0,0,0,0,0,0,0],[0,1,0,0,0,0,1,0],[0,0,0,1,1,0,0,0]],
    4: [[1,0,0,0,0,0,0,1],[0,0,1,1,1,1,0,0],[0,1,0,0,0,0,1,0],[0,1,0,1,1,0,1,0],[0,1,0,1,1,0,1,0],[0,1,0,0,0,0,1,0],[0,0,1,1,1,1,0,0],[1,0,0,0,0,0,0,1]],
    5: [[0,0,0,0,0,0,0,0],[0,1,0,1,0,1,0,0],[0,0,0,0,0,0,0,0],[0,1,0,1,0,1,0,0],[0,0,0,0,0,0,0,0],[0,1,0,1,0,1,0,0],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0]]
}

class App:
    def __init__(self):
        pyxel.init(SCREEN_SIZE, SCREEN_SIZE + 16 + UI_PANEL_HEIGHT, title="ROUTE 16 ULTIMATE")
        try:
            pyxel.image(0).load(0, 0, "sp-tuka-.png")
        except:
            pyxel.image(0).rect(0, 0, 128, 128, 1)
            pyxel.image(0).text(40, 60, "NO IMAGE FOUND", 7)
        self.init_sound()
        # マウスカーソルを非表示に変更
        pyxel.mouse(False)
        self.state = STATE_TITLE
        self.ready_to_start = False
        self.score, self.stage, self.total_time = 0, 1, 0
        self.trails, self.popups, self.ending_timer = [], [], 0
        self.input_lock, self.is_turbo_active = False, False 
        pyxel.run(self.update, self.draw)

    def init_sound(self):
        pyxel.sounds[0].set("a2c3e3g3a2c3e3g3", "p", "5", "v", 20)
        pyxel.sounds[1].set("a1a1e1e1a1a1g1g1", "s", "4", "n", 20)
        pyxel.sounds[2].set("c3e3g3c4", "p", "7", "v", 5)
        pyxel.sounds[3].set("f1e1d1c1", "n", "7", "f", 10)
        pyxel.sounds[4].set("g3a3b3c4", "p", "7", "v", 5)

    def check_input(self):
        dx, dy = 0, 0
        if pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP): dy = -1
        elif pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN): dy = 1
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT): dx = -1
        elif pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT): dx = 1
        mx, my = pyxel.mouse_x, pyxel.mouse_y
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and my > 144:
            if 20 <= mx <= 40 and 145 <= my <= 165: dy = -1
            if 20 <= mx <= 40 and 175 <= my <= 195: dy = 1
            if 5 <= mx <= 25 and 160 <= my <= 180: dx = -1
            if 35 <= mx <= 55 and 160 <= my <= 180: dx = 1
        dist = ((mx - 105)**2 + (my - 170)**2)**0.5
        turbo = pyxel.btn(pyxel.KEY_LSHIFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_A) or (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and dist < 16)
        self.is_turbo_active = turbo 
        return dx, dy, turbo

    def is_confirm_pressed(self):
        return pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_B) or (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_y < 144)

    def get_current_maze(self): return MAZE_DATA[min(self.stage, 5)]
    def get_wall(self, x, y):
        if x < 0 or y < 0 or x >= WORLD_SIZE or y >= WORLD_SIZE: return True
        return self.get_current_maze()[int((y % 64) // 8)][int((x % 64) // 8)] == 1

    def find_safe_pos(self, rx, ry):
        maze = self.get_current_maze(); candidates = []
        for ty in range(8):
            for tx in range(8):
                if maze[ty][tx] == 0: candidates.append((tx, ty))
        if candidates: tx, ty = random.choice(candidates); return rx * 64 + tx * 8 + 4, ry * 64 + ty * 8 + 4
        return rx * 64 + 32, ry * 64 + 32

    def init_stage(self):
        self.px, self.py = self.find_safe_pos(0, 0); self.fuel, self.power_timer = 100.0, 0
        self.trails, self.popups, self.items = [], [], []
        for rx in range(4):
            for ry in range(4):
                x, y = self.find_safe_pos(rx, ry); self.items.append({"x": x, "y": y, "t": "G"})
                if (rx + ry) % 3 == 0: xf, yf = self.find_safe_pos(rx, ry); self.items.append({"x": xf, "y": yf, "t": "F"})
                if (rx == 1 and ry == 2) or (rx == 3 and ry == 0): xp, yp = self.find_safe_pos(rx, ry); self.items.append({"x": xp, "y": yp, "t": "P"})
        self.enemies = []
        config = {1:(2, 0.5), 2:(2, 0.8), 3:(3, 0.6), 4:(4, 0.7), 5:(6, 0.75)}
        num, speed = config.get(self.stage, (6, 0.8))
        for _ in range(num):
            ex, ey = self.find_safe_pos(random.randint(0,3), random.randint(0,3))
            self.enemies.append({"x": ex, "y": ey, "dx": 0, "dy": 0, "active": True, "speed": speed})
        pyxel.play(0, [0, 1], loop=True)

    def update(self):
        if not pyxel.btn(pyxel.MOUSE_BUTTON_LEFT): self.input_lock = False
        if self.state == STATE_TITLE:
            if self.is_confirm_pressed() and not self.input_lock:
                if not self.ready_to_start: self.ready_to_start = True
                else: self.state = STATE_TUTORIAL; self.ready_to_start = False
                self.input_lock = True
        elif self.state == STATE_TUTORIAL:
            if self.is_confirm_pressed() and not self.input_lock:
                self.score, self.stage, self.total_time = 0, 1, 0
                self.init_stage(); self.state = STATE_PLAY; self.input_lock = True
        elif self.state == STATE_PLAY: self.update_play()
        elif self.state == STATE_CLEAR:
            if self.is_confirm_pressed() and not self.input_lock:
                if self.stage >= 5: self.state = STATE_ENDING; self.ending_timer = 0
                else: self.stage += 1; self.init_stage(); self.state = STATE_PLAY
                self.input_lock = True
        elif self.state == STATE_ENDING:
            self.ending_timer += 1
            if self.ending_timer > 60 and self.is_confirm_pressed() and not self.input_lock:
                self.state = STATE_TITLE; self.input_lock = True
        elif self.state == STATE_GAMEOVER:
            if self.is_confirm_pressed() and not self.input_lock:
                self.state = STATE_TITLE; self.input_lock = True

    def update_play(self):
        self.total_time += 1; dx_val, dy_val, turbo = self.check_input()
        if self.input_lock: dx_val, dy_val, turbo = 0, 0, False
        self.fuel -= 0.18 if turbo else 0.08
        if self.fuel <= 0: pyxel.stop(); pyxel.play(3, 3); self.state = STATE_GAMEOVER; self.input_lock = True
        if self.power_timer > 0: self.power_timer -= 1
        mv = (2.4 if turbo else 1.6) if self.stage == 2 else (2.1 if turbo else 1.3)
        if not self.get_wall(self.px + dx_val * mv, self.py): self.px += dx_val * mv
        if not self.get_wall(self.px, self.py + dy_val * mv): self.py += dy_val * mv
        for e in self.enemies:
            if not e["active"]: continue
            if e["dx"] == 0 and e["dy"] == 0 or random.random() < 0.05:
                e["dx"] = e["speed"] if self.px > e["x"] else -e["speed"]
                e["dy"] = e["speed"] if self.py > e["y"] else -e["speed"]
            if not self.get_wall(e["x"] + e["dx"], e["y"] + e["dy"]): e["x"] += e["dx"]; e["y"] += e["dy"]
            else: e["dx"], e["dy"] = random.choice([(e["speed"],0),(-e["speed"],0),(0,e["speed"]),(0,-e["speed"])])
            if abs(self.px - e["x"]) < 5 and abs(self.py - e["y"]) < 5:
                if self.power_timer > 0:
                    e["active"] = False; self.score += 500; self.popups.append({"x": e["x"], "y": e["y"], "txt": "DEFEAT!", "c": 10, "l": 20}); pyxel.play(2, 2)
                else: pyxel.stop(); pyxel.play(3, 3); self.state = STATE_GAMEOVER; self.input_lock = True
        for it in self.items[:]:
            if abs(self.px - it["x"]) < 5 and abs(self.py - it["y"]) < 5:
                if it["t"] == "G": self.score += 100; self.popups.append({"x": it["x"], "y": it["y"], "txt": "+100", "c": 10, "l": 20}); pyxel.play(2, 2)
                elif it["t"] == "F": self.fuel = min(100, self.fuel + 40); self.popups.append({"x": it["x"], "y": it["y"], "txt": "GAS UP", "c": 11, "l": 20}); pyxel.play(2, 4)
                elif it["t"] == "P": self.power_timer = 240; self.popups.append({"x": it["x"], "y": it["y"], "txt": "POWER!", "c": 12, "l": 20}); pyxel.play(2, 4)
                self.items.remove(it)
        for p in self.popups[:]:
            p["y"] -= 0.5; p["l"] -= 1
            if p["l"] <= 0: self.popups.remove(p)
        if len([i for i in self.items if i["t"] == "G"]) == 0: pyxel.stop(); pyxel.play(2, 4); self.state = STATE_CLEAR; self.input_lock = True

    def draw(self):
        pyxel.cls(0)
        if self.state == STATE_TITLE:
            pyxel.blt(0, 0, 0, 0, 0, 128, 128)
            self.draw_text_border(30, 40, "ROUTE 16 ULTIMATE", 7)
            self.draw_text_border(40, 55, "(C)M.Takahashi", 6)
            txt = "PUSH TO PREPARE" if not self.ready_to_start else "PUSH AGAIN TO GO!"
            self.draw_text_border(28, 100, txt, 10 if not self.ready_to_start else 14)
        elif self.state == STATE_TUTORIAL: self.draw_tutorial()
        elif self.state == STATE_PLAY:
            lx, ly = self.px % 64, self.py % 64
            if not (8 < lx < 56 and 8 < ly < 56): self.draw_radar()
            else: self.draw_zoom()
            self.draw_ui(); self.draw_vpad()
        elif self.state == STATE_CLEAR: self.draw_text_border(30, 50, f"STAGE {self.stage} CLEAR!", 10)
        elif self.state == STATE_ENDING:
            pyxel.blt(0, 0, 0, 0, 0, 128, 128)
            self.draw_text_border(30, 30, "MISSION COMPLETE!", pyxel.frame_count % 16)
            self.draw_text_border(30, 60, f"TOTAL SCORE: {self.score}", 10)
            self.draw_text_border(30, 75, f"TOTAL TIME: {self.total_time // 30}s", 7)
            if self.ending_timer > 60: self.draw_text_border(30, 110, "PUSH TO TITLE", 6)
        elif self.state == STATE_GAMEOVER: self.draw_text_border(45, 60, "GAME OVER", 8)

    def draw_tutorial(self):
        self.draw_text_border(42, 6, "HOW TO PLAY", 10)
        pyxel.text(5, 20, "PC:ARROW-KEY / SHIFT:TURBO", 7)
        pyxel.text(5, 28, "SP:V-PAD     / TURBO-BTN", 7)
        pyxel.text(5, 42, "$:GET ALL", 10); pyxel.text(45, 42, "F:FUEL UP", 11); pyxel.text(85, 42, "O:POWER UP", 12)
        pyxel.rectb(4, 55, 120, 18, 5)
        pyxel.text(8, 58, "CENTER=ZOOM / EDGE=RADAR-MAP", 6)
        pyxel.text(8, 65, "DONT HIT THE ENEMY CARS!", 8)
        pyxel.text(32, 80, "-- MOBILE PAD --", 6)
        pyxel.rectb(30, 92, 10, 10, 7); pyxel.text(33, 94, "U", 7)
        pyxel.rectb(30, 112, 10, 10, 7); pyxel.text(33, 114, "D", 7)
        pyxel.rectb(18, 102, 10, 10, 7); pyxel.text(21, 104, "L", 7)
        pyxel.rectb(42, 102, 10, 10, 7); pyxel.text(45, 104, "R", 7)
        pyxel.circb(95, 107, 10, 10); pyxel.text(85, 105, "TURBO", 10)
        self.draw_text_border(22, 134, "PUSH SCREEN TO START", pyxel.frame_count % 16)

    def draw_player_car(self, x, y, is_radar=False):
        if self.power_timer > 0: c = [7, 10, 12, 14][(pyxel.frame_count // 2) % 4]
        elif self.score >= 10000: c = [9, 10, 11, 12, 14][(pyxel.frame_count // 2) % 5]
        elif self.score >= 5000: c = 10
        else: c = 7 if is_radar else 8
        if is_radar: pyxel.rect(x-1, y-1, 3, 3, c)
        else:
            if self.is_turbo_active:
                for _ in range(3): pyxel.pset(x + random.randint(-10, -5), y + random.randint(-3, 3), random.choice([7, 10, 9]))
            pyxel.rect(x-6, y-3, 13, 7, 0); pyxel.rect(x-5, y-4, 11, 7, c); pyxel.rect(x-2, y-7, 5, 4, 1)

    def draw_enemy_car(self, x, y):
        pyxel.rect(x-5, y-4, 11, 7, 12); pyxel.rect(x-2, y-7, 5, 4, 1)
        lamp = 8 if (pyxel.frame_count // 4) % 2 else 12
        pyxel.pset(x-1, y-8, lamp)

    def draw_zoom(self):
        rx, ry = (self.px // 64)*64, (self.py // 64)*64
        maze = self.get_current_maze()
        for ty in range(8):
            for tx in range(8):
                if maze[ty][tx]: pyxel.rect(tx*16, ty*16, 14, 14, 5)
        for it in self.items:
            if rx <= it["x"] < rx+64 and ry <= it["y"] < ry+64: self.draw_item((it["x"]-rx)*2, (it["y"]-ry)*2, it["t"])
        for p in self.popups:
            if rx <= p["x"] < rx+64 and ry <= p["y"] < ry+64: pyxel.text((p["x"]-rx)*2-10, (p["y"]-ry)*2, p["txt"], p["c"])
        for e in self.enemies:
            if e["active"] and rx <= e["x"] < rx+64 and ry <= e["y"] < ry+64: self.draw_enemy_car((e["x"]-rx)*2, (e["y"]-ry)*2)
        self.draw_player_car((self.px%64)*2, (self.py%64)*2)

    def draw_radar(self):
        maze = self.get_current_maze()
        for ry in range(4):
            for rx in range(4):
                for ty in range(8):
                    for tx in range(8):
                        if maze[ty][tx]: pyxel.pset(rx*32+tx*4, ry*32+ty*4, 5)
        for it in self.items: pyxel.pset(it["x"]*0.5, it["y"]*0.5, 10 if it["t"]=="G" else 11)
        for e in self.enemies:
            if e["active"]: pyxel.pset(e["x"]*0.5, e["y"]*0.5, 12)
        self.draw_player_car(self.px*0.5, self.py*0.5, is_radar=True)

    def draw_ui(self):
        pyxel.rect(0, 128, 128, 16, 0); pyxel.line(0, 128, 128, 128, 7)
        pyxel.text(4, 133, f"ST:{self.stage}", 7); pyxel.text(28, 133, "F", 7)
        pyxel.rect(34, 134, 30, 4, 1); pyxel.rect(34, 134, self.fuel*0.3, 4, 11 if self.fuel > 30 else 8)
        pyxel.text(68, 133, f"T:{self.total_time // 30}s", 7); pyxel.text(98, 133, f"S:{self.score}", 10 if self.score >= 5000 else 7)

    def draw_vpad(self):
        pyxel.rect(0, 144, 128, UI_PANEL_HEIGHT, 1); pyxel.line(0, 144, 128, 144, 7)
        pyxel.rectb(20, 145, 20, 20, 7); pyxel.rectb(20, 175, 20, 20, 7); pyxel.rectb(5, 160, 20, 20, 7); pyxel.rectb(35, 160, 20, 20, 7)
        t_col = 10 if self.is_turbo_active else 7
        pyxel.circb(105, 170, 15, t_col); pyxel.text(95, 168, "TURBO", t_col)

    def draw_text_border(self, x, y, text, col):
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]: pyxel.text(x+ox, y+oy, text, 0)
        pyxel.text(x, y, text, col)

    def draw_item(self, x, y, t):
        if t == "G": pyxel.text(x-2, y-2, "$", 10)
        elif t == "F": pyxel.text(x-2, y-2, "F", 11)
        elif t == "P": pyxel.circb(x, y, 3, 12)

App()
