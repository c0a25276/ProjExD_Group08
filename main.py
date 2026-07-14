import os
import sys
import math
import random
import pygame as pg

# 授業の指定通り、実行スクリプトのディレクトリに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 画面サイズの設定
WIDTH, HEIGHT = 800, 600


# キャラクター用のダミー画像（画像ファイルがない場合の代用）
def get_dummy_surface(w, h, color):
    surface = pg.Surface((w, h))
    surface.fill(color)
    return surface


class PerspectiveBackground:
    """奥行きのある虹の道と、正面に広がる宇宙、満月を描画・管理するクラス"""
    def __init__(self):
        self.scroll_y = 0
        self.road_base_speed = 4

        self.cx = WIDTH // 2
        self.cy = HEIGHT // 2 + 80
        self.horizon_y = self.cy

        self.stars = []
        for i in range(120):
            angle = (i * 133.7) % (math.pi * 2)
            base_dist = (i * 43) % 500
            speed_factor = 0.5 + (i % 5) * 0.4

            self.stars.append({
                "angle": angle,
                "base_dist": base_dist,
                "speed_factor": speed_factor,
                "id": i
            })

        self.rainbow_colors = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
        ]

        self.road_near_width = 600
        self.road_far_width = 20

    def update(self):
        self.scroll_y += self.road_base_speed

    def draw(self, screen, moon_radius):
        # --- ① 宇宙（夜空と星）の描画 ---
        screen.fill((10, 10, 30))

        for s in self.stars:
            current_dist = (s["base_dist"] + self.scroll_y * s["speed_factor"]) % 500
            star_x = self.cx + math.cos(s["angle"]) * current_dist
            star_y = self.cy + math.sin(s["angle"]) * current_dist

            if 0 <= star_x < WIDTH and 0 <= star_y < HEIGHT:
                t = current_dist / 500.0
                size = max(1, int(1 + t * 3))
                brightness_offset = int(30 * (((s["id"] + int(self.scroll_y) // 10)) % 2))
                brightness = max(150, min(255, int(150 + t * 105) - brightness_offset))

                pg.draw.circle(screen, (brightness, brightness, brightness), (int(star_x), int(star_y)), size)

        # --- ② 満月の描画 ---
        if moon_radius > 0:
            pg.draw.circle(screen, (25, 25, 50), (self.cx, self.cy), moon_radius + 20)
            pg.draw.circle(screen, (50, 45, 45), (self.cx, self.cy), moon_radius + 10)
            pg.draw.circle(screen, (100, 95, 60), (self.cx, self.cy), moon_radius + 4)
            pg.draw.circle(screen, (255, 230, 150), (self.cx, self.cy), moon_radius)

        # --- ③ 奥行きのある虹の道の描画 ---
        for y in range(self.horizon_y, HEIGHT):
            t = (y - self.horizon_y) / (HEIGHT - self.horizon_y) if (HEIGHT - self.horizon_y) > 0 else 1
            current_road_width = self.road_far_width + t * (self.road_near_width - self.road_far_width)
            scroll_offset = (self.scroll_y * (1.0 + t * 2.0)) % 100
            road_left = (WIDTH - current_road_width) // 2
            stripe_width = current_road_width / len(self.rainbow_colors)

            for i, color in enumerate(self.rainbow_colors):
                stripe_x = road_left + i * stripe_width
                c = color

                if (t * 20 + self.scroll_y * 0.05) % 2 < 1.0:
                    c = tuple(min(255, val + 40) for val in color)

                pg.draw.rect(screen, c, (int(stripe_x), y, int(stripe_width) + 1, 1))

            if (y + scroll_offset) % int(30 * (1.0 + t)) < 2:
                pg.draw.line(screen, (50, 50, 50), (road_left, y), (road_left + current_road_width, y), 1)


class Player(pg.sprite.Sprite):
    """プレイヤー（おじいさん）"""
    def __init__(self):
        super().__init__()

        self.normal_image = get_dummy_surface(60, 60, (0, 255, 0))
        self.stun_image = get_dummy_surface(60, 60, (120, 120, 120))

        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 80)

        self.speed = 10

        # ★ろっく担当：スタン時間を管理する変数
        self.stun_timer = 0

    def update(self, key_lst):
        # ★ろっく担当：スタン中は動けない
        if self.stun_timer > 0:
            self.stun_timer -= 1

            # スタン中は点滅させる
            if self.stun_timer % 20 < 10:
                self.image = self.stun_image
            else:
                self.image = self.normal_image

            return

        self.image = self.normal_image

        if key_lst[pg.K_LEFT]:
            self.rect.x -= self.speed
        if key_lst[pg.K_RIGHT]:
            self.rect.x += self.speed

        if self.rect.left < 100:
            self.rect.left = 100
        if self.rect.right > 700:
            self.rect.right = 700

    def stun(self, duration=120):
        """隕石に当たった時、一定時間スタン状態にする"""
        self.stun_timer = duration


class Grandmother(pg.sprite.Sprite):
    """おじいさんが投げるおばあさん（奥行きへ進むプレイヤー弾）"""
    def __init__(self, player_center):
        super().__init__()

        self.base_size = 24
        self.image = get_dummy_surface(self.base_size, self.base_size, (255, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.center = player_center

        self.target_x = WIDTH // 2
        self.target_y = HEIGHT // 2

        self.start_y = player_center[1]

        self.ex = float(self.rect.centerx)
        self.ey = float(self.rect.centery)

        self.speed_ratio = 0.04

    def update(self):
        self.ex += (self.target_x - self.ex) * self.speed_ratio
        self.ey += (self.target_y - self.ey) * self.speed_ratio

        total_dist_y = self.start_y - self.target_y
        current_dist_y = self.ey - self.target_y
        t = current_dist_y / total_dist_y

        scale = max(0.4, t)
        new_size = int(self.base_size * scale)

        self.image = pg.transform.scale(
            get_dummy_surface(self.base_size, self.base_size, (255, 255, 0)),
            (new_size, new_size)
        )
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.ex), int(self.ey))

        if current_dist_y < 10:
            self.kill()


class Kaguya(pg.sprite.Sprite):
    """かぐや姫"""
    def __init__(self):
        super().__init__()
        self.image = get_dummy_surface(30, 30, (255, 120, 180))
        self.rect = self.image.get_rect()
        self.vx = 4
        self.target_y = (HEIGHT // 2) + 20
        self.rect.center = (WIDTH // 2, HEIGHT - 200)

    def update(self):
        self.rect.x += self.vx

        if self.rect.y > self.target_y:
            self.rect.y -= 1

        scale = max(0.4, (self.rect.y - (HEIGHT // 2)) / (HEIGHT - (HEIGHT // 2) - 200))
        new_size = int(30 * scale)

        if new_size > 5:
            self.image = pg.transform.scale(
                get_dummy_surface(30, 30, (255, 120, 180)),
                (new_size, new_size)
            )
            self.rect = self.image.get_rect(center=self.rect.center)

        if self.rect.left < 320 or self.rect.right > 480:
            self.vx *= -1


class Meteor(pg.sprite.Sprite):
    """★ろっく担当：落ちてくる隕石"""
    def __init__(self):
        super().__init__()

        # 隕石の初期位置
        self.x = random.randint(80, WIDTH - 80)
        self.y = random.randint(-150, -40)

        # 落下速度
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(4.0, 7.0)

        # サイズ
        self.base_size = random.randint(22, 36)

        # 回転
        self.angle = random.randint(0, 360)
        self.rot_speed = random.uniform(-6, 6)

        self.image = self.create_meteor_image(self.base_size)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def create_meteor_image(self, size):
        """隕石の画像を作る"""
        surface = pg.Surface((size, size), pg.SRCALPHA)

        # 炎っぽいしっぽ
        pg.draw.polygon(
            surface,
            (255, 100, 0, 150),
            [
                (size // 2, size),
                (size // 4, size // 2),
                (size // 2, 0),
                (size * 3 // 4, size // 2)
            ]
        )

        # 隕石本体
        pg.draw.circle(
            surface,
            (120, 120, 120),
            (size // 2, size // 2),
            size // 3
        )

        # 隕石の外側
        pg.draw.circle(
            surface,
            (255, 160, 40),
            (size // 2, size // 2),
            size // 3,
            3
        )

        return surface

    def update(self):
        self.x += self.vx
        self.y += self.vy

        self.angle += self.rot_speed

        # 下に行くほど少し大きくして、奥行き感を出す
        t = max(0, min(1, self.y / HEIGHT))
        new_size = int(self.base_size * (0.7 + t * 1.2))

        base_image = self.create_meteor_image(new_size)
        self.image = pg.transform.rotate(base_image, self.angle)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

        # 画面外に出たら消す
        if self.rect.top > HEIGHT or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


def main():
    pg.init()
    pg.display.set_caption("かぐや姫 引き留めろ！（オール奥行きVer）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    background = PerspectiveBackground()

    player = Player()
    kaguya = Kaguya()

    grannies = pg.sprite.Group()

    # ★ろっく担当：隕石グループ
    meteors = pg.sprite.Group()

    moon_radius = 20
    tmr = 0

    while True:
        background.update()

        if tmr % 3 == 0 and moon_radius < 400:
            moon_radius += 1

        background.draw(screen, moon_radius)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                # スタン中は弾を撃てないようにする
                if event.key == pg.K_SPACE and player.stun_timer == 0:
                    grannies.add(Grandmother(player.rect.center))

        # ★ろっく担当：一定時間ごとに隕石を出す
        # 数字を小さくすると隕石が多くなる
        if tmr > 0 and tmr % 300 == 0:
            for _ in range(3):
                meteors.add(Meteor())

        key_lst = pg.key.get_pressed()

        player.update(key_lst)
        kaguya.update()
        grannies.update()
        meteors.update()

        # 言弾がかぐや姫に当たったらゲームクリア
        if pg.sprite.spritecollide(kaguya, grannies, True):
            print("【ゲームクリア】かぐや姫を引き留めました！")
            
        # ★ろっく担当：隕石がかぐや姫に当たったらゲームオーバー
        if pg.sprite.spritecollide(kaguya, meteors, False):
            print("【ゲームオーバー】隕石がかぐや姫に当たってしまいました。")
            

        # ★ろっく担当：隕石がおじいさんに当たったらスタン
        if pg.sprite.spritecollide(player, meteors, True):
            player.stun(120)
            print("【スタン】おじいさんが隕石に当たりました。しばらく動けません。")

        if moon_radius >= 350:
            print("【ゲームオーバー】かぐや姫は月へ帰ってしまいました。")
            pg.quit()
            sys.exit()

        meteors.draw(screen)
        grannies.draw(screen)
        screen.blit(kaguya.image, kaguya.rect)
        screen.blit(player.image, player.rect)

        pg.display.update()
        tmr += 1
        clock.tick(60)


if __name__ == "__main__":
    main()