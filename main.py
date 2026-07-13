import os
import sys
import math
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
        self.road_base_speed = 4  # 虹の道の基本スクロール速度

        self.cx = WIDTH // 2
        self.cy = HEIGHT // 2 + 80  # ★前より80px下に下げてプレイヤーに近づけました
        self.horizon_y = self.cy     # 地平線のy座標も同期
        
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
        
        self.road_near_width = 600     # 画面下部での道路の幅
        self.road_far_width = 20       # 地平線での道路の幅

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
    """プレイヤー（おじいさん / おばあさん）"""
    def __init__(self):
        super().__init__()
        
        # キャラクターごとの性能パラメータ (色, 足の速さ)
        self.features = {
            "ojiisan": {"color": (0, 255, 0), "speed": 10},     # おじいさん: 緑色、速度10
            "obaasan": {"color": (255, 105, 180), "speed": 15}  # おばあさん: ピンク、速度15（足が速い）
        }
        self.current_char = "ojiisan"  # 初期キャラはおじいさん
        
        # 選択されたキャラクターの見た目と速度を適用
        self.apply_character()
        
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 80)

    def apply_character(self):
        """現在のキャラクター設定に合わせて画像と速度を更新する"""
        data = self.features[self.current_char]
        self.image = get_dummy_surface(60, 60, data["color"])
        self.speed = data["speed"]

    def switch_character(self):
        """Sキー入力で操作キャラクターを交互に切り替える"""
        if self.current_char == "ojiisan":
            self.current_char = "obaasan"
        else:
            self.current_char = "ojiisan"
        
        self.apply_character()

    def update(self, key_lst):
        # 左右の移動速度(self.speed)はキャラクターごとに変化します
        if key_lst[pg.K_LEFT]: self.rect.x -= self.speed
        if key_lst[pg.K_RIGHT]: self.rect.x += self.speed
        
        if self.rect.left < 100: self.rect.left = 100
        if self.rect.right > 700: self.rect.right = 700


class Kotodama(pg.sprite.Sprite):
    """プレイヤーが発射する言弾（奥行きへ進むプレイヤー弾）"""
    def __init__(self, player_center, color):
        super().__init__()
        self.base_size = 24
        self.color = color  # 発射したキャラクターの色を引き継ぐ
        self.image = get_dummy_surface(self.base_size, self.base_size, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = player_center
        
        # 画面中央（地平線）を目標地点にする
        self.target_x = WIDTH // 2
        self.target_y = HEIGHT // 2
        
        # 発射された位置のY座標を記憶（比率計算用）
        self.start_y = player_center[1]
        
        # 浮動小数点で正確に追跡するための座標
        self.ex = float(self.rect.centerx)
        self.ey = float(self.rect.centery)
        
        # 1フレームあたりに目的地（奥）へ近づく割合（速度）
        self.speed_ratio = 0.04

    def update(self):
        # 目的地（画面中央の奥）に向かって一定割合で近づく（イージング）
        self.ex += (self.target_x - self.ex) * self.speed_ratio
        self.ey += (self.target_y - self.ey) * self.speed_ratio
        
        # 現在の「奥への進み具合」を0.0（手前）〜1.0（一番奥）で計算
        total_dist_y = self.start_y - self.target_y
        current_dist_y = self.ey - self.target_y
        t = current_dist_y / total_dist_y  # 手前にいるほど1.0、奥に行くほど0.0に近づく
        
        # 奥に行くほどサイズを小さくする（最小でも元の40%の大きさに）
        scale = max(0.4, t)
        new_size = int(self.base_size * scale)
        
        # 画像と判定範囲（rect）のサイズ・位置を更新
        self.image = pg.transform.scale(get_dummy_surface(self.base_size, self.base_size, self.color), (new_size, new_size))
        self.rect = self.image.get_rect()
        self.rect.center = (int(self.ex), int(self.ey))
        
        # 地平線（中央）に十分近づいたら消滅
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
            self.rect.y -= 0.1
            
        scale = max(0.4, (self.rect.y - (HEIGHT // 2)) / (HEIGHT - (HEIGHT // 2) - 200))
        new_size = int(30 * scale)
        if new_size > 5:
            self.image = pg.transform.scale(get_dummy_surface(30, 30, (255, 120, 180)), (new_size, new_size))
            self.rect = self.image.get_rect(center=self.rect.center)

        if self.rect.left < 320 or self.rect.right > 480:
            self.vx *= -1


def main():
    pg.init()
    pg.display.set_caption("かぐや姫 引き留めろ！（オール奥行きVer）")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    background = PerspectiveBackground()

    player = Player()
    kaguya = Kaguya()
    kotodamas = pg.sprite.Group()  # 弾のグループ名を言弾(kotodamas)に統一

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
                # 【なかむらさん担当】Sキーが押されたら操作キャラクターを変更
                if event.key == pg.K_s:
                    player.switch_character()

                # スペースキーが押されたら、現在のキャラクターの色に応じた言弾を発射
                if event.key == pg.K_SPACE:
                    current_color = player.features[player.current_char]["color"]
                    kotodamas.add(Kotodama(player.rect.center, current_color))

        key_lst = pg.key.get_pressed()
        player.update(key_lst)
        kaguya.update()
        kotodamas.update() 

        if pg.sprite.spritecollide(kaguya, kotodamas, True):
            print("【ゲームクリア】かぐや姫を引き留めました！")
            pg.quit()
            sys.exit()

        if moon_radius >= 350:
            print("【ゲームオーバー】かぐや姫は月へ帰ってしまいました。")
            pg.quit()
            sys.exit()

        kotodamas.draw(screen)  
        screen.blit(kaguya.image, kaguya.rect)
        screen.blit(player.image, player.rect)

        pg.display.update()
        tmr += 1
        clock.tick(60)

if __name__ == "__main__":
    main()