import os
import sys
import math
import random
import pygame as pg
import random

# 授業の指定通り、実行スクリプトのディレクトリに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 画面サイズの設定
WIDTH, HEIGHT = 800, 600
 

def get_dummy_surface(w: int, h: int, color: tuple) -> pg.Surface:
    """キャラクター用のダミー画像（画像ファイルがない場合の代用）"""
    surface = pg.Surface((w, h))
    surface.fill(color)
    return surface


def draw_moon_progress_bar(screen: pg.Surface, moon_radius: float, first_moon_radius: float, end_moon_radius: float) -> None:
    """満月(制限時間)の進行状況を右側のバーで表示する関数"""
    bar_x: int = WIDTH - 42 # 右から42pxの位置
    bar_y: int = 100 # 上から100pxの位置
    bar_w: int = 18 # バーの幅
    bar_h: int = 400 # バーの高さ

    # 満月の進行状況の計算
    if end_moon_radius <= first_moon_radius:
        progress = 1.0
    else:
        progress = (moon_radius - first_moon_radius) / (end_moon_radius - first_moon_radius) # 全体の時間分の経過時間(進捗度)
        progress = max(0.0, min(1.0, progress))

    # 進行状況に応じてバーの塗りつぶし部分の高さを計算
    fill_h: int = int(bar_h * progress)
    fill_y: int = bar_y + (bar_h - fill_h)

    # バーの背景と枠を描画
    pg.draw.rect(screen, (35, 35, 50), (bar_x, bar_y, bar_w, bar_h))
    pg.draw.rect(screen, (180, 180, 200), (bar_x - 3, bar_y - 3, bar_w + 6, bar_h + 6), 2)

    # 進行状況に応じてバーの色を変える
    if fill_h > 0:
        if progress < 0.5:
            fill_color = (90, 180, 90)
        elif progress < 0.85:
            fill_color = (240, 190, 70)
        else:
            fill_color = (230, 80, 70)

        # 塗りつぶし部分を描画（枠の内側に収まるように調整）
        pg.draw.rect(screen, fill_color, (bar_x + 3, fill_y + 3, bar_w - 6, max(0, fill_h - 6)))


class PerspectiveBackground:
    """奥行きのある虹の道と、正面に広がる宇宙、満月を描画・管理するクラス"""
    def __init__(self):
        self.scroll_y = 0
        self.road_base_speed = 4

        self.cx = WIDTH // 2
        self.cy = HEIGHT // 2 + 80  
        # 地平線（虹の道の始まり）のY座標
        self.horizon_y = int(self.cy)
        
        # 星の初期設定（中心を下げたので、新しい中心から放射状に広がる）
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

    def draw(self, screen: pg.Surface, moon_radius: int):
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
    """プレイヤー（おじいさん / おばあさん）"""
    def __init__(self):
        super().__init__()
        self.normal_image = pg.image.load("fig/grandfather.png").convert_alpha()
        self.normal_image = pg.transform.scale(self.normal_image, (60, 60))
        
        # キャラクターごとの性能パラメータ (色, 足の速さ)
        self.features = {
            "ojiisan": {"image_name": "grandfather.png", "speed": 5},
            "obaasan": {"image_name": "grandmother.png", "speed": 15},
        }
        self.current_char = "ojiisan"  # 初期キャラはおじいさん
        
        # 選択されたキャラクターの見た目と速度を適用
        self.apply_character()
        
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 80)
        self.stun_image = self.normal_image.copy()
        self.stun_image.fill((255, 100, 100), special_flags=pg.BLEND_MULT)

        self.image = self.normal_image
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, (HEIGHT - 80))
        self.speed = 20

        # ★ろっく担当：スタン時間を管理する変数
        self.stun_timer = 0

    def apply_character(self):
        """現在のキャラクター設定に合わせて画像と速度を更新する"""
        data = self.features[self.current_char]
        image_name = data["image_name"]

        candidates = [image_name, os.path.join("fig", image_name)]
        loaded_image = None
        for path in candidates:
            if os.path.exists(path):
                try:
                    loaded_image = pg.image.load(path).convert_alpha()
                    break
                except Exception:
                    loaded_image = None

        if loaded_image is None:
            loaded_image = get_dummy_surface(60, 60, (200, 200, 200))

        self.normal_image = pg.transform.scale(loaded_image, (60, 60))
        self.stun_image = self.normal_image.copy()
        self.stun_image.fill((255, 100, 100), special_flags=pg.BLEND_MULT)
        self.image = self.normal_image
        self.speed = data["speed"]

    def switch_character(self):
        """Sキー入力で操作キャラクターを交互に切り替える"""
        if self.current_char == "ojiisan":
            self.current_char = "obaasan"
        else:
            self.current_char = "ojiisan"
        
        self.apply_character()

    
    def update(self, key_lst: list):
        if key_lst[pg.K_LEFT]: self.rect.x -= self.speed
        if key_lst[pg.K_RIGHT]: self.rect.x += self.speed
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
   #言弾として吹き出す文字画像リスト
    word_list = ["だめ.png", "月に.png", "戻ら.png", "ないで.png", "おいて.png", "行か.png", "ないで.png", "帰ら.png", "ないで.png", "止まって.png", "待って.png", "お願い.png"]
    #言弾として吹き出すときの音声
    voice_list = ["だめ.wav", "月に.wav", "戻ら.wav", "ないでよ.wav", "おいて.wav", "行か.wav", "ないで.wav", "帰ら.wav", "ないでよ.wav", "止まって.wav", "待って.wav", "お願い.wav"]
    next_index = 0

    def __init__(self, player_center):
        super().__init__()
        # 初期サイズ
        self.base_size = 80
        # 画像と音声ファイルのロードを試みる
        self.raw_image = None
        self.sound = None

# 画像ファイル名と音声ファイル名をリストから取得
        index = Grandmother.next_index
        Grandmother.next_index += 1
        word = Grandmother.word_list[index]
        voice = Grandmother.voice_list[index]

        # 画像ファイルを探す
        for path in (word, os.path.join("img", word)):
            if os.path.exists(path):
                try:
                    self.raw_image = pg.image.load(path).convert_alpha()
                    break
                except Exception:
                    self.raw_image = None

        # 音声ファイルを探す
        for path in (voice, os.path.join("voice", voice)):
            if os.path.exists(path):
                try:
                    self.sound = pg.mixer.Sound(path)
                    self.sound.play()
                    break
                except Exception:
                    self.sound = None

        if self.raw_image is None:
            surf = pg.Surface((self.base_size, self.base_size), pg.SRCALPHA)
            pg.draw.circle(surf, (255, 255, 0, 255), (self.base_size // 2, self.base_size // 2), self.base_size // 2)
            self.image = surf
        else:
            self.image = pg.transform.smoothscale(self.raw_image, (self.base_size, self.base_size))

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
        new_size = max(1, int(self.base_size * scale))

        # 画像をスケールして丸くマスク（透過）する
        if self.raw_image is not None:
            try:
                scaled = pg.transform.smoothscale(self.raw_image, (new_size, new_size))
                # マスク: 中心が白(255)で外側が透明(0)のサーフェス
                mask = pg.Surface((new_size, new_size), pg.SRCALPHA)
                mask.fill((255, 255, 255, 0))
                pg.draw.circle(mask, (255, 255, 255, 255), (new_size // 2, new_size // 2), new_size // 2)
                # アルファを掛けて丸くする
                scaled.blit(mask, (0, 0), special_flags=pg.BLEND_RGBA_MULT)
                self.image = scaled
            except Exception:
                surf = pg.Surface((new_size, new_size), pg.SRCALPHA)
                pg.draw.circle(surf, (255, 255, 0, 255), (new_size // 2, new_size // 2), new_size // 2)
                self.image = surf
        else:
            surf = pg.Surface((new_size, new_size), pg.SRCALPHA)
            pg.draw.circle(surf, (255, 255, 0, 255), (new_size // 2, new_size // 2), new_size // 2)
            self.image = surf

        self.rect = self.image.get_rect()
        self.rect.center = (int(self.ex), int(self.ey))

        if current_dist_y < 10:
            self.kill()


class Kaguya(pg.sprite.Sprite):
    """かぐや姫"""
    def __init__(self):
        super().__init__()
        self.original_image = pg.image.load("fig/kaguya.png").convert_alpha()
        self.rect = self.original_image.get_rect()
        self.vx = 6 
        self.target_y = (HEIGHT // 2) + 60
        self.rect.center = (WIDTH // 2, HEIGHT - 200)
        self.base_size = 20
        self.size_modifier = 1.0
        self.image = pg.transform.scale(self.original_image, (self.base_size, self.base_size))

    def change_size(self, multiplier: float) -> None:
        """
        サイズ倍率を変更する（1.0より大きければ拡大、小さければ縮小）
        大きさが変わっているけど、近づいたり離れたりを表現するために使用
        """
        self.size_modifier *= multiplier

    def update(self):
        self.rect.x += self.vx

        if random.random() < 0.02:
            # スピードをランダムに変化させる
            self.vx = random.randint(2, 6)

        scale = max(0.4, (self.rect.y - (HEIGHT // 2)) / (HEIGHT - (HEIGHT // 2) - 200))
        # 奥行きのスケールに、サイズ倍率（size_modifier）を掛け合わせる
        new_size = int(self.base_size * scale * self.size_modifier)
        # new_size = int(30 * scale)
        if new_size > 5:
            self.image = pg.transform.scale(self.original_image, (new_size, new_size))
            self.rect = self.image.get_rect(center=self.rect.center)

        if self.rect.left < 320:
            self.rect.left = 320
            self.vx *= -1
        if self.rect.right > 460:
            self.rect.right = 460
            self.vx *= -1

class StoryDisplay:
    """画面左上に物語のあらすじを流すクラス"""
    def __init__(self):
        self.texts = [
            "Kaguya is about to go back to the moon.",
            "Grandfather must stop Kaguya from leaving Earth.",
            "Finish this game before the moon comes!",
            "左右キー:移動、スペース:射撃、Sキー:キャラ変更"
        ]
        self.font = pg.font.SysFont("ms-gothic", 24)
        self.color = (255, 255, 255)

        self.line_idx = 0
        self.char_count = 0
        self.timer = 0

    def update(self):
        if self.timer % 5 == 0: 
            if self.line_idx < len(self.texts):
                if self.char_count < len(self.texts[self.line_idx]):
                    self.char_count += 1
                elif self.line_idx < len(self.texts) - 1:
                    self.line_idx += 1
                    self.char_count = 0
        self.timer += 1
    def draw(self, screen):
        for i in range(self.line_idx + 1):
            limit = self.char_count if i == self.line_idx else len(self.texts[i])
            text_surf = self.font.render(self.texts[i][:limit], True, self.color)
            screen.blit(text_surf, (20, 20 + i * 30))

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
    pg.display.set_caption("Back to the Moon")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    background = PerspectiveBackground()
    story = StoryDisplay()
    remaining_font = pg.font.SysFont("ms-gothic", 24)

    player = Player()
    kaguya = Kaguya()

    grannies = pg.sprite.Group()
    

    # ★ろっく担当：隕石グループ
    meteors = pg.sprite.Group()

    first_moon_radius = 20 # 背景の月の初期サイズ
    moon_radius = first_moon_radius # 背景の月の現在サイズ
    end_moon_radius = 400 # 背景の月の最大サイズ（ゲームオーバーになるサイズ）
    tmr = 0 # ゲーム全体のタイマー変数

    clear_target_hits = 5 # クリアに必要な当てる回数
    hit_counter = 0 # 当たった回数カウンタ
    hit_reset_tmr = 1 # 当たった回数のリセット用タイマー変数
    hit_tmr = 0 # 当たった際のhit_reset_tmrを保存する変数
    hit_reset_tmr_threshold = 180 # 当たった回数のリセット用タイマーの閾値
    
    # BGM を初期化して再生
    try:
        pg.mixer.init()
        pg.mixer.music.load("BGM/Back To The Moon.mp3")
        pg.mixer.music.set_volume(0.4)
        pg.mixer.music.play(-1)
    except Exception:
        print("BGMを再生できませんでした。ファイルパスやサウンド設定を確認してください。")

    while True:
        background.update()
        
        if tmr % 3 == 0 and moon_radius < end_moon_radius:
            moon_radius += 0.25 # 月のサイズを徐々に大きくする（ゲームの制限時間を表す）

        background.draw(screen, moon_radius)
        draw_moon_progress_bar(screen, moon_radius, first_moon_radius, end_moon_radius)

        story.update() #あらすじを更新
        story.draw(screen)

        remaining_count = max(0, len(Grandmother.word_list) - Grandmother.next_index)
        remaining_text = remaining_font.render(f"残り言弾: {remaining_count}", True, (255, 255, 255))
        screen.blit(remaining_text, (20, 140))

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            if event.type == pg.KEYDOWN:
                # スタン中は弾を撃てないようにする
                if event.key == pg.K_SPACE and player.stun_timer == 0:
                    if Grandmother.next_index < len(Grandmother.word_list):
                        grannies.add(Grandmother(player.rect.center))
                # 【なかむらさん担当】Sキーが押されたら操作キャラクターを変更
                if event.key == pg.K_s:
                    player.switch_character()

        # ★ろっく担当：一定時間ごとに隕石を出す
        # 数字を小さくすると隕石が多くなる
        if tmr > 0 and tmr % 500 == 0:
            for _ in range(1):
                meteors.add(Meteor())

        key_lst = pg.key.get_pressed()

        player.update(key_lst)
        kaguya.update()
        grannies.update()
        meteors.update()

        # 言弾がかぐや姫に当たったらゲームクリア
        if pg.sprite.spritecollide(kaguya, grannies, True):
            hit_counter += 1
            kaguya.change_size(1.2) 
            hit_tmr = hit_reset_tmr
            if hit_counter >= clear_target_hits:
                print("【ゲームクリア】かぐや姫を引き留めました！")
                pg.quit()
                sys.exit()
                
        # ★ろっく担当：隕石がかぐや姫に当たったらゲームオーバー
        if pg.sprite.spritecollide(kaguya, meteors, False):
            print("【ゲームオーバー】隕石がかぐや姫に当たってしまいました。")
            pg.mixer.music.stop()
            pg.quit()
            sys.exit()

        # ★ろっく担当：隕石がおじいさんに当たったらスタン
        if pg.sprite.spritecollide(player, meteors, True):
            player.stun(120)
            print("【スタン】おじいさんが隕石に当たりました。しばらく動けません。")
        
        if hit_reset_tmr - hit_tmr > hit_reset_tmr_threshold: # 指定された時間弾が当たらなければ当たった回数カウンタが減る
            hit_counter -= 1
            kaguya.change_size(0.8)
            if hit_counter <= 0:
                hit_counter = 0
                hit_reset_tmr = 1 
                hit_tmr = 0
            else: # 当たった回数カウンタが0でなければもう一度リセット用タイマーが動く
                hit_reset_tmr = 1 
                hit_tmr = 1
            print("かぐや姫は遠ざかった")
            #かぐや姫に引き留めたときBGM停止


        if moon_radius >= end_moon_radius:
            print("【ゲームオーバー】かぐや姫は月へ帰ってしまいました。")
            #かぐや姫に月に帰ったときBGM停止
            pg.mixer.music.stop()
            pg.quit()
            sys.exit()

        meteors.draw(screen)
        grannies.draw(screen)
        screen.blit(kaguya.image, kaguya.rect)
        screen.blit(player.image, player.rect)

        pg.display.update()
        tmr += 1
        if hit_tmr:
            hit_reset_tmr += 1
        clock.tick(60)


if __name__ == "__main__":
    main()