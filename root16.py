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
    # 描画（簡略）
    # -----------------------------
    def draw(self):
        pyxel.cls(0)
        if self.state == STATE_TITLE:
            pyxel.text(30, 60, "ROUTE 16 ULTIMATE", 7)
            pyxel.text(35, 90, "PRESS SPACE OR A", 10)

        elif self.state == STATE_PLAY:
            pyxel.circ(self.px % 128, self.py % 128, 4, 7)

        elif self.state == STATE_GAMEOVER:
            pyxel.text(45, 60, "GAME OVER", 8)

App()
