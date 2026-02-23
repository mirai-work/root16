import pyxel
import random

# --- 定数 ---
SCREEN_SIZE = 128
WORLD_SIZE = 256
STATE_TITLE, STATE_TUTORIAL, STATE_PLAY, STATE_CLEAR, STATE_GAMEOVER, STATE_ENDING = range(6)

MAZE_DATA = {
    1: [[1,1,0,0,0,0,1,1],[1,0,0,0,0,0,0,1],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[0,0,0,1,1,0,0,0],[1,0,0,0,0,0,0,1],[1,1,0,0,0,0,1,1]],
    2: [[1,1,0,0,0,0,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,0,0,1,1,0,0,1],[1,0,0,1,1,0,0,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,1,0,0,0,0,1,1]],
    3: [[1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,1],[1,0,1,1,1,1,0,1],[1,0,1,0,0,1,0,1],[1,0,1,0,0,1,0,1],[1,0,1,1,1,1,0,1],[1,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1]],
    4: [[1,1,1,1,1,1,1,1],[1,0,0,0,0,0,0,1],[1,0,1,0,1,0,1,1],[0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0],[1,1,0,1,0,1,0,1],[1,0,0,0,0,0,0,1],[1,1,1,1,1,1,1,1]],
    5: [[1,0,1,0,1,0,1,0],[0,0,0,0,0,0,0,0],[1,0,1,1,1,1,0,1],[0,0,1,0,0,1,0,0],[0,0,1,0,0,1,0,0],[1,0,1,1,1,1,0,1],[0,0,0,0,0,0,0,0],[1,0,1,0,1,0,1,0]]
}

class App:
    def __init__(self):
        pyxel.init(SCREEN_SIZE, SCREEN_SIZE + 16, title="ROUTE 16 ULTIMATE")
        try:
            pyxel.image(0).load(0, 0, "sp-tuka-.png")
        except:
            pyxel.image(0).rect(0, 0, 128, 128, 1)

        self.state = STATE_TITLE
        self.score, self.stage, self.total_time = 0, 1, 0
        self.trails, self.popups = [], []
        pyxel.run(self.update, self.draw)

    # -----------------------------
    # 共通入力（SPACE or GAMEPAD A）
    # -----------------------------
    def decide_pressed(self):
        return pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.GAMEPAD1_BUTTON_A)

    # -----------------------------
    # 迷路関連
    # -----------------------------
    def get_current_maze(self):
        return MAZE_DATA[self.stage]

    def get_wall(self, x, y):
        if x < 0 or y < 0 or x >= WORLD_SIZE or y >= WORLD_SIZE:
            return True
        return self.get_current_maze()[int((y % 64) // 8)][int((x % 64) // 8)] == 1

    def find_safe_pos(self, rx, ry):
        maze = self.get_current_maze()
        while True:
            tx, ty = random.randint(0, 7), random.randint(0, 7)
            if maze[ty][tx] == 0:
                return rx * 64 + tx * 8 + 4, ry * 64 + ty * 8 + 4

    # -----------------------------
    # ステージ初期化
    # -----------------------------
    def init_stage(self):
        self.px, self.py = self.find_safe_pos(0, 0)
        self.fuel, self.power_timer = 100.0, 0
        self.trails, self.popups, self.items = [], [], []

        for rx in range(4):
            for ry in range(4):
                x, y = self.find_safe_pos(rx, ry)
                self.items.append({"x": x, "y": y, "t": "G"})
                if (rx + ry) % 3 == 0:
                    xf, yf = self.find_safe_pos(rx, ry)
                    self.items.append({"x": xf, "y": yf, "t": "F"})
                if (rx == 1 and ry == 2) or (rx == 3 and ry == 0):
                    xp, yp = self.find_safe_pos(rx, ry)
                    self.items.append({"x": xp, "y": yp, "t": "P"})

        self.enemies = []
        config = {1:(2,0.5),2:(2,0.8),3:(3,0.6),4:(4,0.7),5:(6,0.75)}
        num, speed = config[self.stage]

        for _ in range(num):
            ex, ey = self.find_safe_pos(random.randint(1,3), random.randint(1,3))
            self.enemies.append({"x": ex, "y": ey, "dx": 0, "dy": 0, "active": True, "speed": speed})

    # -----------------------------
    # 更新
    # -----------------------------
    def update(self):
        if self.state == STATE_TITLE:
            if self.decide_pressed():
                self.score, self.stage, self.total_time = 0, 1, 0
                self.state = STATE_TUTORIAL

        elif self.state == STATE_TUTORIAL:
            if self.decide_pressed():
                self.init_stage()
                self.state = STATE_PLAY

        elif self.state == STATE_PLAY:
            self.update_play()

        elif self.state == STATE_CLEAR:
            if self.decide_pressed():
                if self.stage >= 5:
                    self.state = STATE_ENDING
                    self.ending_timer = 0
                else:
                    self.stage += 1
                    self.init_stage()
                    self.state = STATE_PLAY

        elif self.state == STATE_ENDING:
            self.ending_timer += 1
            if self.ending_timer > 60 and self.decide_pressed():
                self.state = STATE_TITLE

        elif self.state == STATE_GAMEOVER:
            if self.decide_pressed():
                self.state = STATE_TITLE

    # -----------------------------
    # プレイ更新（ゲームパッド対応）
    # -----------------------------
    def update_play(self):
        self.total_time += 1

        turbo = pyxel.btn(pyxel.KEY_LSHIFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_B)

        self.fuel -= 0.18 if turbo else 0.08
        if self.fuel <= 0:
            self.state = STATE_GAMEOVER

        if self.power_timer > 0:
            self.power_timer -= 1

        mv = (2.4 if turbo else 1.6) if self.stage == 2 else (2.1 if turbo else 1.3)

        dx, dy = 0, 0

        up = pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_UP)
        down = pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_DOWN)
        left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
        right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT)

        if up: dy = -mv
        elif down: dy = mv
        if left: dx = -mv
        elif right: dx = mv

        if not self.get_wall(self.px + dx, self.py):
            self.px += dx
        if not self.get_wall(self.px, self.py + dy):
            self.py += dy

        # （以下、敵・アイテム処理は元コードと同じ）
        for e in self.enemies:
            if not e["active"]:
                continue
            if e["dx"] == 0 and e["dy"] == 0 or random.random() < 0.05:
                e["dx"] = e["speed"] if self.px > e["x"] else -e["speed"]
                e["dy"] = e["speed"] if self.py > e["y"] else -e["speed"]
            if not self.get_wall(e["x"] + e["dx"], e["y"] + e["dy"]):
                e["x"] += e["dx"]
                e["y"] += e["dy"]
            if abs(self.px - e["x"]) < 5 and abs(self.py - e["y"]) < 5:
                if self.power_timer > 0:
                    e["active"] = False
                    self.score += 500
                else:
                    self.state = STATE_GAMEOVER

        for it in self.items[:]:
            if abs(self.px - it["x"]) < 5 and abs(self.py - it["y"]) < 5:
                if it["t"] == "G":
                    self.score += 100
                elif it["t"] == "F":
                    self.fuel = min(100, self.fuel + 40)
                elif it["t"] == "P":
                    self.power_timer = 240
                self.items.remove(it)

        if len([i for i in self.items if i["t"] == "G"]) == 0:
            self.state = STATE_CLEAR

    # -----------------------------
    # 描画
    # -----------------------------
    def draw(self):
        pyxel.cls(0)
        if self.state == STATE_TITLE:
            pyxel.blt(0, 0, 0, 0, 0, 128, 128)
            self.draw_text_border(30, 40, "ROUTE  ULTIMATE", 7)
            self.draw_text_border(35, 100, "PUSH SPACE KEY", 10)
        elif self.state == STATE_TUTORIAL: self.draw_tutorial()
        elif self.state == STATE_PLAY:
            lx, ly = self.px % 64, self.py % 64
            if not (8 < lx < 56 and 8 < ly < 56): self.draw_radar()
            else: self.draw_zoom()
            self.draw_ui()
        elif self.state == STATE_CLEAR:
            self.draw_text_border(30, 50, f"STAGE {self.stage} CLEAR!", 10)
            self.draw_text_border(32, 90, "SPACE TO NEXT", 7)
        elif self.state == STATE_ENDING: self.draw_ending()
        elif self.state == STATE_GAMEOVER: self.draw_text_border(45, 60, "GAME OVER", 8)

    def draw_player_car(self, x, y):
        is_gold = self.score >= 5000
        c = 10 if is_gold else 8
        if self.power_timer > 0 and pyxel.frame_count % 2: c = 7
        pyxel.rect(x-6, y-3, 13, 7, 0) # 影
        pyxel.rect(x-5, y-4, 11, 7, c) # ボディ
        pyxel.rect(x-2, y-7, 5, 4, 1)  # 窓
        pyxel.pset(x-4, y-2, 10 if not is_gold else 7); pyxel.pset(x+4, y-2, 10 if not is_gold else 7)
        if is_gold:
            off = pyxel.frame_count % 15
            if off < 10: pyxel.line(x-5+off, y-4, x-3+off, y+1, 7)

    def draw_enemy_car(self, x, y):
        pyxel.rect(x-5, y-4, 11, 6, 1)
        pyxel.rect(x-5, y-5, 11, 2, 7)
        lamp = 8 if (pyxel.frame_count // 4) % 2 else 12
        pyxel.pset(x-2, y-6, lamp); pyxel.pset(x+2, y-6, 12 if lamp==8 else 8)
        pyxel.pset(x-5, y-2, 9); pyxel.pset(x+5, y-2, 9)

    def draw_zoom(self):
        rx, ry = (self.px // 64)*64, (self.py // 64)*64
        maze = self.get_current_maze()
        for t in self.trails:
            if rx <= t["x"] < rx+64 and ry <= t["y"] < ry+64:
                pyxel.pset((t["x"]-rx)*2, (t["y"]-ry)*2, 13 if t["life"] > 10 else 5)
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
            if e["active"]: pyxel.pset(e["x"]*0.5, e["y"]*0.5, 8)
        pyxel.rect(self.px*0.5-1, self.py*0.5-1, 3, 3, 10 if self.score >= 5000 else 7)

    def draw_ui(self):
        pyxel.rect(0, 128, 128, 16, 0)
        pyxel.line(0, 128, 128, 128, 7)
        # 各情報の座標を固定し、重なりを防止
        pyxel.text(4, 133, f"ST:{self.stage}", 7)    # ステージ
        pyxel.text(28, 133, "F", 7)                  # 燃料ラベル
        pyxel.rect(34, 134, 30, 4, 1)                # 燃料枠
        pyxel.rect(34, 134, self.fuel*0.3, 4, 11 if self.fuel > 30 else 8)
        pyxel.text(68, 133, f"T:{self.total_time // 30}s", 7) # タイム
        pyxel.text(98, 133, f"S:{self.score}", 10 if self.score >= 5000 else 7) # スコア

    def draw_tutorial(self):
        pyxel.rectb(5, 5, 118, 118, 7)
        pyxel.text(40, 12, "- MISSIONS -", 10)
        txt = [
            "1. COLLECT ALL COINS", "   IN EACH STAGE.", "",
            "2. WATCH FUEL BAR.", "   COLLECT 'F' TO REFILL.", "",
            "3. GET 'P' TO BECOME", "   INVINCIBLE!", "",
            "4. AVOID POLICE CARS.", "",
            "MOVE : ARROW KEYS", "TURBO: SHIFT KEY"
        ]
        for i, line in enumerate(txt): pyxel.text(12, 28 + i * 7, line, 7)
        if (pyxel.frame_count // 15) % 2: pyxel.text(32, 130, "PRESS SPACE KEY", 6)

    def draw_ending(self):
        pyxel.cls(0)
        self.draw_text_border(30, 30, "MISSION COMPLETE!", pyxel.frame_count % 16)
        pyxel.text(30, 60, f"TOTAL SCORE: {self.score}", 10)
        pyxel.text(30, 75, f"TOTAL TIME: {self.total_time // 30}s", 7)
        if self.ending_timer > 60: self.draw_text_border(30, 110, "PUSH SPACE TO TITLE", 6)

    def draw_text_border(self, x, y, text, col):
        for ox, oy in [(-1,0),(1,0),(0,-1),(0,1)]: pyxel.text(x+ox, y+oy, text, 0)
        pyxel.text(x, y, text, col)

    def draw_item(self, x, y, t):
        if t == "G": pyxel.text(x-2, y-2, "$", 10)
        elif t == "F": pyxel.text(x-2, y-2, "F", 11)
        elif t == "P": pyxel.circb(x, y, 3, 12)

App()
