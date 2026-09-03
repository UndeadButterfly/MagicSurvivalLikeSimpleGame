import pygame
import math
import random
import platform
import os

# 초기화
pygame.init()
pygame.font.init()

# 화면 확장: 800(게임 화면) + 200(오른쪽 패널) = 1000 x 600
GAME_WIDTH = 800
UI_PANEL_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH + UI_PANEL_WIDTH
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# --- [한글 폰트 설정] ---
def get_korean_font(size):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            return pygame.font.SysFont("malgungothic", size)
        elif os_name == "Darwin":
            return pygame.font.SysFont("applegothic", size)
        else:
            return pygame.font.SysFont("nanumgothic", size)
    except:
        return pygame.font.SysFont(None, size)

font = get_korean_font(16)
bold_font = get_korean_font(18)
title_font = get_korean_font(32)

# --- [랭킹 파일 입출력] ---
RANKING_FILE = "rankings.txt"

def load_rankings():
    ranks = []
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        level = int(parts[0])
                        kills = int(parts[1])
                        ptime = float(parts[2])
                        stats_str = parts[3] if len(parts) > 3 else ""
                        ranks.append({"level": level, "kills": kills, "time": ptime, "stats": stats_str})
        except Exception as e:
            print(f"랭킹 로드 실패: {e}")
    ranks.sort(key=lambda x: (x["kills"], x["time"]), reverse=True)
    return ranks

def save_rankings(ranks):
    try:
        with open(RANKING_FILE, "w", encoding="utf-8") as f:
            for r in ranks:
                f.write(f"{r['level']},{r['kills']},{r['time']:.2f},{r['stats']}\n")
    except Exception as e:
        print(f"랭킹 저장 실패: {e}")

rankings = load_rankings()

def reset_game():
    global player, enemies, bullets, potions, loot_items, explosions, hit_effects, damage_rings
    global spawn_timer, shoot_timer, potion_timer
    global max_hp, player_hp, hp_regen, move_speed, pierce_count, bullet_count, bullet_speed, shoot_interval, fire_directions, split_count, enemy_speed_mult
    global has_explosion, explosion_radius, explosion_upgrade_count, magnet_radius
    global play_time, kill_count, kills_for_next_upgrade, player_level
    global is_upgrading, is_game_over, record_saved

    # 캐릭터 크기: 30x30
    player = pygame.Rect(400, 300, 30, 30)
    enemies = []
    bullets = []
    potions = []
    loot_items = []
    explosions = []
    hit_effects = []
    damage_rings = []

    spawn_timer = 0
    shoot_timer = 0
    potion_timer = 0

    max_hp = 100
    player_hp = 100
    hp_regen = 0
    move_speed = 200.0
    enemy_speed_mult = 1.0
    pierce_count = 1
    bullet_count = 1
    bullet_speed = 400.0  # 기본 투사체 속도
    shoot_interval = 0.5
    fire_directions = 1
    split_count = 0

    has_explosion = False
    # 캐릭터 크기(30)의 5배 = 지름 150 (반경 75)
    explosion_radius = 75.0
    explosion_upgrade_count = 0  # 폭발 범위 증가 선택 횟수 제한 (최대 3회)
    magnet_radius = 100.0

    play_time = 0.0
    kill_count = 0
    kills_for_next_upgrade = 20
    player_level = 1

    is_upgrading = False
    is_game_over = False
    record_saved = False

current_lang = 'KOR'
lang_button_rect = pygame.Rect(GAME_WIDTH - 90, 10, 80, 30)
upgrade_options = []
selected_option_index = 0

reset_game()

def add_kills_and_check_upgrade(amount):
    global kill_count, kills_for_next_upgrade, player_level, is_upgrading, upgrade_options, selected_option_index
    kill_count += amount
    if kill_count >= kills_for_next_upgrade:
        kills_for_next_upgrade *= 2
        player_level += 1
        is_upgrading = True

        for loot in loot_items:
            loot["magnetized"] = True

        upgrade_options = generate_upgrade_options()
        selected_option_index = 0

def get_base_upgrades():
    upgrades = [
        {"id": 1, "text_kor": "관통력 +1", "text_eng": "Pierce +1"},
        {"id": 2, "text_kor": "개수 +2", "text_eng": "Bullet Count +2"},
        {"id": 3, "text_kor": "공격 간격 -10%", "text_eng": "Cooldown -10%"},
        {"id": 4, "text_kor": "공격 방향 +1", "text_eng": "Direction +1"},
        {"id": 5, "text_kor": "최대 체력 +10", "text_eng": "Max HP +10"},
        {"id": 6, "text_kor": "초당 체력회복 +1", "text_eng": "HP Regen +1"},
        {"id": 8, "text_kor": "전리품 획득 범위 +10%", "text_eng": "Magnet Range +10%"},
        {"id": 10, "text_kor": "이동속도 +20%", "text_eng": "Move Speed +20%"},
        {"id": 11, "text_kor": "적중 시 분열 +1", "text_eng": "Bullet Split +1"},
        {"id": 12, "text_kor": "적 이동속도 -10%", "text_eng": "Enemy Speed -10%"},
        {"id": 13, "text_kor": "투사체 속도 +30%", "text_eng": "Bullet Speed +30%"}
    ]
    if not has_explosion:
        upgrades.append({"id": 7, "text_kor": "폭발 데미지 추가 (범위 5배)", "text_eng": "Add Explosion (5x Size)"})
    elif explosion_upgrade_count < 3:
        # 폭발 습득 후 최대 3번만 등장 가능
        upgrades.append({"id": 9, "text_kor": f"폭발 범위 +50% ({explosion_upgrade_count}/3)", "text_eng": f"Explosion Area +50% ({explosion_upgrade_count}/3)"})
    return upgrades

def generate_upgrade_options():
    avail = get_base_upgrades()
    options = []
    
    for _ in range(min(3, len(avail))):
        if random.random() < 0.30 and len(avail) >= 2:
            sampled = random.sample(avail, 2)
            for item in sampled:
                if item in avail:
                    avail.remove(item)
            options.append({
                "is_dual": True,
                "ids": [sampled[0]["id"], sampled[1]["id"]],
                "text_kor": f"[세트] {sampled[0]['text_kor']} + {sampled[1]['text_kor']}",
                "text_eng": f"[SET] {sampled[0]['text_eng']} + {sampled[1]['text_eng']}"
            })
        else:
            item = random.choice(avail)
            avail.remove(item)
            options.append({
                "is_dual": False,
                "ids": [item["id"]],
                "text_kor": item["text_kor"],
                "text_eng": item["text_eng"]
            })
    return options

def apply_upgrade(upgrade_ids):
    for uid in upgrade_ids:
        apply_single_upgrade(uid)

def apply_single_upgrade(upgrade_id):
    global pierce_count, bullet_count, bullet_speed, shoot_interval, fire_directions, max_hp, player_hp, hp_regen, move_speed, split_count, enemy_speed_mult
    global has_explosion, explosion_radius, explosion_upgrade_count, magnet_radius

    if upgrade_id == 1:
        pierce_count += 1
    elif upgrade_id == 2:
        bullet_count += 2  # 개수 2씩 증가 상향
    elif upgrade_id == 3:
        shoot_interval *= 0.9
    elif upgrade_id == 4:
        fire_directions += 1
    elif upgrade_id == 5:
        max_hp += 10
        player_hp += 10
    elif upgrade_id == 6:
        hp_regen += 1
    elif upgrade_id == 7:
        has_explosion = True
    elif upgrade_id == 8:
        magnet_radius *= 1.10
    elif upgrade_id == 9:
        if explosion_upgrade_count < 3:
            explosion_radius *= 1.50  # 폭발 범위 +50%
            explosion_upgrade_count += 1
    elif upgrade_id == 10:
        move_speed *= 1.20
    elif upgrade_id == 11:
        split_count += 1
    elif upgrade_id == 12:
        enemy_speed_mult *= 0.90
    elif upgrade_id == 13:
        bullet_speed *= 1.30  # 투사체 속도 +30%

running = True
while running:
    dt = clock.tick(60) / 1000.0

    # 1. 이벤트 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if lang_button_rect.collidepoint(event.pos):
                current_lang = 'ENG' if current_lang == 'KOR' else 'KOR'

        if is_game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                reset_game()

        if is_upgrading and not is_game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                selected_option_index = (selected_option_index - 1) % len(upgrade_options)
            elif event.key == pygame.K_DOWN:
                selected_option_index = (selected_option_index + 1) % len(upgrade_options)
            elif event.key == pygame.K_SPACE:
                chosen_upgrade = upgrade_options[selected_option_index]
                apply_upgrade(chosen_upgrade["ids"])
                is_upgrading = False

    if is_game_over:
        if not record_saved:
            stats_summary = f"HP:{max_hp}|SPD:{int(move_speed)}|INT:{shoot_interval:.2f}|Prc:{pierce_count}|Splt:{split_count}"
            rankings.append({"level": player_level, "kills": kill_count, "time": play_time, "stats": stats_summary})
            rankings.sort(key=lambda x: (x["kills"], x["time"]), reverse=True)
            save_rankings(rankings)
            record_saved = True

    # --- [메인 게임 업데이트] ---
    if not is_game_over and not is_upgrading:
        play_time += dt

        if hp_regen > 0:
            player_hp = min(max_hp, player_hp + hp_regen * dt)

        # 플레이어 이동
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        player.x += dx * move_speed * dt
        player.y += dy * move_speed * dt
        player.clamp_ip(pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT))

        # 적 생성
        spawn_interval = max(0.2, 1.0 - (play_time / 60.0) * 0.4)
        spawn_amount = 1 + int(play_time / 15.0)

        spawn_timer += dt
        if spawn_timer >= spawn_interval:
            spawn_timer = 0
            for _ in range(spawn_amount):
                angle = random.uniform(0, math.pi * 2)
                ex = player.centerx + math.cos(angle) * 500
                ey = player.centery + math.sin(angle) * 500

                is_elite = random.random() < 0.1
                if is_elite:
                    dir_x = player.centerx - ex
                    dir_y = player.centery - ey
                    dist = math.hypot(dir_x, dir_y)
                    vx = (dir_x / dist) * 200 if dist > 0 else 200
                    vy = (dir_y / dist) * 200 if dist > 0 else 0
                    enemies.append({"rect": pygame.Rect(ex, ey, 24, 24), "hp": 10, "is_elite": True, "vx": vx, "vy": vy})
                else:
                    enemies.append({"rect": pygame.Rect(ex, ey, 16, 16), "hp": 1, "is_elite": False, "vx": 0, "vy": 0})

        # 포션 생성
        potion_timer += dt
        if potion_timer >= 10.0:
            potion_timer = 0
            px = random.randint(50, GAME_WIDTH - 50)
            py = random.randint(50, SCREEN_HEIGHT - 50)
            potions.append(pygame.Rect(px, py, 15, 15))

        # 적 공격력 공식 적용 (초기 1, 10초마다 +1 증가)
        time_damage_bonus = int(play_time / 10.0)
        base_normal_damage = 1 + time_damage_bonus
        base_elite_damage = 5 + time_damage_bonus

        # 적 이동 및 피격 충돌
        for enemy in enemies[:]:
            if enemy["is_elite"]:
                enemy["rect"].x += enemy["vx"] * enemy_speed_mult * dt
                enemy["rect"].y += enemy["vy"] * enemy_speed_mult * dt
            else:
                dir_x = player.centerx - enemy["rect"].centerx
                dir_y = player.centery - enemy["rect"].centery
                dist = math.hypot(dir_x, dir_y)
                if dist > 0:
                    enemy["rect"].x += (dir_x / dist) * 100 * enemy_speed_mult * dt
                    enemy["rect"].y += (dir_y / dist) * 100 * enemy_speed_mult * dt

            # 캐릭터와 충돌 시 데미지
            if player.colliderect(enemy["rect"]):
                damage = base_elite_damage if enemy["is_elite"] else base_normal_damage
                player_hp -= damage
                damage_rings.append({"x": player.centerx, "y": player.centery, "radius": 15, "timer": 0.2})
                enemies.remove(enemy)
                if player_hp <= 0:
                    player_hp = 0
                    is_game_over = True

        # 전리품 이동 및 수집
        for loot in loot_items[:]:
            dist_to_player = math.hypot(player.centerx - loot["x"], player.centery - loot["y"])
            is_magnetized = loot.get("magnetized", False) or (dist_to_player <= magnet_radius)

            if is_magnetized:
                if dist_to_player > 0:
                    speed = 600 if loot.get("magnetized", False) else 350
                    loot["x"] += ((player.centerx - loot["x"]) / dist_to_player) * speed * dt
                    loot["y"] += ((player.centery - loot["y"]) / dist_to_player) * speed * dt

                if dist_to_player < 20:
                    add_kills_and_check_upgrade(loot["value"])
                    loot_items.remove(loot)

        # 포션 획득
        for potion in potions[:]:
            if player.colliderect(potion):
                player_hp = min(max_hp, player_hp + 50)
                potions.remove(potion)

        # 총알 발사
        shoot_timer += dt
        if shoot_timer >= shoot_interval and enemies:
            shoot_timer = 0
            sorted_enemies = sorted(enemies, key=lambda e: math.hypot(e["rect"].centerx - player.centerx, e["rect"].centery - player.centery))
            target_enemies = sorted_enemies[:fire_directions]

            for target in target_enemies:
                dir_x = target["rect"].centerx - player.centerx
                dir_y = target["rect"].centery - player.centery
                dist = math.hypot(dir_x, dir_y)
                if dist > 0:
                    base_angle = math.atan2(dir_y, dir_x)
                    for b_idx in range(bullet_count):
                        angle_offset = (b_idx - (bullet_count - 1) / 2) * 0.15
                        final_angle = base_angle + angle_offset
                        bullets.append({
                            "rect": pygame.Rect(player.centerx, player.centery, 8, 8),
                            "vx": math.cos(final_angle) * bullet_speed,
                            "vy": math.sin(final_angle) * bullet_speed,
                            "pierce": pierce_count,
                            "can_split": True,
                            "hit_enemies": []
                        })

        # 총알 이동 및 적중 이펙트 / 폭발 처리
        for bullet in bullets[:]:
            bullet["rect"].x += bullet["vx"] * dt
            bullet["rect"].y += bullet["vy"] * dt

            for enemy in enemies[:]:
                if enemy["rect"] not in bullet["hit_enemies"] and bullet["rect"].colliderect(enemy["rect"]):
                    bullet["hit_enemies"].append(enemy["rect"])
                    bullet["pierce"] -= 1

                    bx, by = bullet["rect"].centerx, bullet["rect"].centery

                    # 적중 파티클 이펙트 추가
                    for _ in range(5):
                        hit_effects.append({
                            "x": bx, "y": by,
                            "vx": random.uniform(-100, 100),
                            "vy": random.uniform(-100, 100),
                            "timer": 0.15
                        })

                    # 분열 로직
                    if bullet.get("can_split", False) and split_count > 0:
                        split_num = split_count + 1
                        other_enemies = [e for e in enemies if e != enemy]
                        other_enemies.sort(key=lambda e: math.hypot(e["rect"].centerx - bx, e["rect"].centery - by))

                        for s_i in range(split_num):
                            if s_i < len(other_enemies):
                                target_e = other_enemies[s_i]
                                tx = target_e["rect"].centerx - bx
                                ty = target_e["rect"].centery - by
                                dist = math.hypot(tx, ty)
                                split_angle = math.atan2(ty, tx) if dist > 0 else (math.pi * 2 / split_num) * s_i
                            else:
                                split_angle = (math.pi * 2 / split_num) * s_i

                            bullets.append({
                                "rect": pygame.Rect(bx, by, 6, 6),
                                "vx": math.cos(split_angle) * bullet_speed * 0.85,
                                "vy": math.sin(split_angle) * bullet_speed * 0.85,
                                "pierce": 1,
                                "can_split": False,  # 분열 투사체는 추가 분열 불가
                                "hit_enemies": [enemy["rect"]]
                            })

                    # 폭발 로직 (분열된 투사체도 포함하여 적중할 때마다 발생)
                    if has_explosion:
                        explosions.append({"x": bx, "y": by, "radius": explosion_radius, "timer": 0.1})
                        for near_enemy in enemies:
                            e_dist = math.hypot(near_enemy["rect"].centerx - bx, near_enemy["rect"].centery - by)
                            if e_dist <= explosion_radius:
                                near_enemy["hp"] -= 1

                    enemy["hp"] -= 1

                    # 적 처치 처리 (경험치 드랍률 50%)
                    dead_enemies = [e for e in enemies if e["hp"] <= 0]
                    for d_enemy in dead_enemies:
                        if d_enemy in enemies:
                            ex, ey = d_enemy["rect"].centerx, d_enemy["rect"].centery
                            is_elite = d_enemy["is_elite"]
                            kill_value = 5 if is_elite else 1

                            add_kills_and_check_upgrade(kill_value)
                            enemies.remove(d_enemy)

                            if random.random() < 0.50:
                                loot_items.append({"x": ex, "y": ey, "value": kill_value, "is_elite": is_elite, "magnetized": False})

                    if bullet["pierce"] <= 0:
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break

        # 이펙트 타이머 업데이트
        for exp in explosions[:]:
            exp["timer"] -= dt
            if exp["timer"] <= 0:
                explosions.remove(exp)

        for eff in hit_effects[:]:
            eff["timer"] -= dt
            eff["x"] += eff["vx"] * dt
            eff["y"] += eff["vy"] * dt
            if eff["timer"] <= 0:
                hit_effects.remove(eff)

        for ring in damage_rings[:]:
            ring["timer"] -= dt
            ring["radius"] += 80 * dt
            if ring["timer"] <= 0:
                damage_rings.remove(ring)

    # --- [그리기] ---
    screen.fill((30, 30, 30))

    # 플레이어 및 체력바
    pygame.draw.rect(screen, (0, 255, 0), player)
    
    hp_bar_width = 40
    hp_bar_height = 6
    hp_ratio = max(0, player_hp / max_hp)
    hp_bar_x = player.centerx - hp_bar_width // 2
    hp_bar_y = player.top - 12
    pygame.draw.rect(screen, (80, 80, 80), (hp_bar_x, hp_bar_y, hp_bar_width, hp_bar_height))
    pygame.draw.rect(screen, (255, 50, 50), (hp_bar_x, hp_bar_y, int(hp_bar_width * hp_ratio), hp_bar_height))

    # 적 그리기
    for enemy in enemies:
        color = (160, 32, 240) if enemy["is_elite"] else (255, 0, 0)
        pygame.draw.rect(screen, color, enemy["rect"])

    # 총알 그리기
    for bullet in bullets:
        color = (255, 255, 0) if bullet.get("can_split", False) else (255, 165, 0)
        pygame.draw.rect(screen, color, bullet["rect"])

    # 아이템 및 폭발 이펙트
    for potion in potions:
        pygame.draw.rect(screen, (0, 191, 255), potion)

    for loot in loot_items:
        color = (255, 105, 180) if loot["is_elite"] else (255, 215, 0)
        pygame.draw.circle(screen, color, (int(loot["x"]), int(loot["y"])), 5 if loot["is_elite"] else 3)

    for exp in explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    # 적중 이펙트 파티클
    for eff in hit_effects:
        pygame.draw.circle(screen, (255, 200, 50), (int(eff["x"]), int(eff["y"])), 2)

    # 피격 이펙트 링
    for ring in damage_rings:
        pygame.draw.circle(screen, (255, 0, 0), (int(ring["x"]), int(ring["y"])), int(ring["radius"]), 2)

    # --- [상단 핵심 UI] ---
    minutes = int(play_time) // 60
    seconds = int(play_time) % 60

    if current_lang == 'KOR':
        time_str = f"시간: {minutes:02d}:{seconds:02d}"
        kill_str = f"LV.{player_level} | 처치: {kill_count} (다음: {kills_for_next_upgrade})"
    else:
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        kill_str = f"LV.{player_level} | Kills: {kill_count} (Next: {kills_for_next_upgrade})"

    screen.blit(bold_font.render(time_str, True, (255, 255, 255)), (10, 10))
    screen.blit(bold_font.render(kill_str, True, (255, 255, 255)), (10, 32))

    # [한영 버튼]
    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), lang_button_rect, 2)
    btn_text = font.render(f"[{current_lang}]", True, (255, 255, 255))
    screen.blit(btn_text, (lang_button_rect.x + 15, lang_button_rect.y + 4))

    # --- [우측 분리 패널 (랭킹 + 캐릭터 스탯 현황)] ---
    panel_rect = pygame.Rect(GAME_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (20, 20, 25), panel_rect)
    pygame.draw.line(screen, (80, 80, 100), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

    # 1) 랭킹 표시
    rank_title_str = "랭킹 (Top 5)" if current_lang == 'KOR' else "RANKING"
    rank_title = bold_font.render(rank_title_str, True, (255, 215, 0))
    screen.blit(rank_title, (GAME_WIDTH + 15, 15))

    for idx, r in enumerate(rankings[:5]):
        rk_m, rk_s = int(r["time"]) // 60, int(r["time"]) % 60
        rank_item_str = f"{idx+1}. Lv.{r['level']} | {r['kills']}K ({rk_m:02d}:{rk_s:02d})"
        rank_text = font.render(rank_item_str, True, (200, 200, 200))
        screen.blit(rank_text, (GAME_WIDTH + 10, 45 + idx * 25))

    pygame.draw.line(screen, (60, 60, 80), (GAME_WIDTH + 10, 185), (GAME_WIDTH + UI_PANEL_WIDTH - 10, 185), 1)

    # 2) 캐릭터 실시간 스탯 현황
    stat_title_str = "캐릭터 스탯" if current_lang == 'KOR' else "CHARACTER STATS"
    stat_title = bold_font.render(stat_title_str, True, (100, 200, 255))
    screen.blit(stat_title, (GAME_WIDTH + 15, 195))

    curr_time_dmg = 1 + int(play_time / 10.0)
    stats_list = [
        f"체력: {int(player_hp)} / {max_hp}" if current_lang == 'KOR' else f"HP: {int(player_hp)} / {max_hp}",
        f"이동속도: {int(move_speed)}" if current_lang == 'KOR' else f"Speed: {int(move_speed)}",
        f"공격간격: {shoot_interval:.2f}초" if current_lang == 'KOR' else f"Cooldown: {shoot_interval:.2f}s",
        f"발사방향: {fire_directions}방향" if current_lang == 'KOR' else f"Directions: {fire_directions}",
        f"총알 개수: {bullet_count}개" if current_lang == 'KOR' else f"Bullets: {bullet_count}",
        f"투사체 속도: {int(bullet_speed)}" if current_lang == 'KOR' else f"B.Speed: {int(bullet_speed)}",
        f"관통력: {pierce_count}" if current_lang == 'KOR' else f"Pierce: {pierce_count}",
        f"분열 수: {split_count}" if current_lang == 'KOR' else f"Splits: {split_count}",
        f"폭발 범위: {int(explosion_radius*2)}" if current_lang == 'KOR' else f"Exp. Size: {int(explosion_radius*2)}",
        f"적 공격력: {curr_time_dmg}" if current_lang == 'KOR' else f"Enemy Dmg: {curr_time_dmg}",
    ]
    for idx, s_text in enumerate(stats_list):
        screen.blit(font.render(s_text, True, (220, 220, 220)), (GAME_WIDTH + 12, 225 + idx * 24))

    # 레이어 팝업 (레벨업)
    if is_upgrading and not is_game_over:
        overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title_str = "레벨 업! 강화 선택" if current_lang == 'KOR' else "LEVEL UP! Choose Option"
        title_text = title_font.render(title_str, True, (255, 215, 0))
        screen.blit(title_text, (GAME_WIDTH // 2 - title_text.get_width() // 2, 100))

        for idx, option in enumerate(upgrade_options):
            color = (255, 255, 0) if idx == selected_option_index else (255, 255, 255)
            prefix = "-> " if idx == selected_option_index else "   "
            opt_str = option["text_kor"] if current_lang == 'KOR' else option["text_eng"]
            
            if option["is_dual"]:
                color = (255, 180, 0) if idx == selected_option_index else (255, 215, 100)

            opt_text = font.render(prefix + opt_str, True, color)
            screen.blit(opt_text, (120, 220 + idx * 60))

    if is_game_over:
        overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        go_title = "게임 오버" if current_lang == 'KOR' else "GAME OVER"
        go_sub = "'R'키를 눌러 재시작" if current_lang == 'KOR' else "Press 'R' to Restart"

        go_text = title_font.render(go_title, True, (255, 50, 50))
        sub_text = font.render(go_sub, True, (255, 255, 255))

        screen.blit(go_text, (GAME_WIDTH // 2 - go_text.get_width() // 2, 220))
        screen.blit(sub_text, (GAME_WIDTH // 2 - sub_text.get_width() // 2, 300))

    pygame.display.flip()

pygame.quit()