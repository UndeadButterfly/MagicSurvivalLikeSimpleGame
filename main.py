import pygame
import math
import random
import platform
import os

# 초기화
pygame.init()
pygame.font.init()

GAME_WIDTH = 800
UI_PANEL_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH + UI_PANEL_WIDTH
SCREEN_HEIGHT = 600

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

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

RANKING_FILE = "rankings.txt"

def load_rankings():
    ranks = []
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        ranks.append({
                            "level": int(parts[0]),
                            "kills": int(parts[1]),
                            "time": float(parts[2]),
                            "stats": parts[3] if len(parts) > 3 else ""
                        })
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
    global bullet_type, base_explosion_radius, magnet_radius, magnet_radius_sq
    global bullet_count_upgrades, bullet_speed_upgrades, split_upgrades
    global play_time, kill_count, kills_for_next_upgrade, player_level
    global is_upgrading, is_game_over, record_saved

    player = pygame.Rect(400, 300, 30, 30)
    enemies = []
    bullets = []
    potions = []
    loot_items = []
    explosions = []
    hit_effects = []
    damage_rings = []

    spawn_timer = 0.0
    shoot_timer = 0.0
    potion_timer = 0.0

    max_hp = 100
    player_hp = 100
    hp_regen = 0
    move_speed = 200.0
    enemy_speed_mult = 1.0
    pierce_count = 1
    bullet_count = 1
    bullet_speed = 400.0
    shoot_interval = 0.5
    fire_directions = 1
    split_count = 0

    bullet_type = 'PIERCE'
    base_explosion_radius = 30.0 * 3.0

    bullet_count_upgrades = 0
    bullet_speed_upgrades = 0
    split_upgrades = 0

    magnet_radius = 100.0
    magnet_radius_sq = magnet_radius * magnet_radius

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
    global max_hp, player_hp
    
    kill_count += amount
    if kill_count >= kills_for_next_upgrade:
        kills_for_next_upgrade = int(kills_for_next_upgrade * 1.3)
        player_level += 1
        
        max_hp += 5
        player_hp = min(max_hp, player_hp + 5)
        
        is_upgrading = True

        for loot in loot_items:
            loot["magnetized"] = True

        upgrade_options = generate_upgrade_options()
        selected_option_index = 0

def get_base_upgrades():
    upgrades = [
        {"id": 1, "text_kor": "관통력 +1", "text_eng": "Pierce +1"},
        {"id": 3, "text_kor": "공격 간격 -10%", "text_eng": "Cooldown -10%"},
        {"id": 4, "text_kor": "공격 방향 +1", "text_eng": "Direction +1"},
        {"id": 5, "text_kor": "최대 체력 +10", "text_eng": "Max HP +10"},
        {"id": 6, "text_kor": "초당 체력회복 +1", "text_eng": "HP Regen +1"},
        {"id": 8, "text_kor": "전리품 획득 범위 +10%", "text_eng": "Magnet Range +10%"},
        {"id": 10, "text_kor": "이동속도 +20%", "text_eng": "Move Speed +20%"},
        {"id": 12, "text_kor": "적 이동속도 -10%", "text_eng": "Enemy Speed -10%"}
    ]

    if bullet_count_upgrades < 5:
        upgrades.append({"id": 2, "text_kor": f"개수 +2 ({bullet_count_upgrades}/5)", "text_eng": f"Bullet Count +2 ({bullet_count_upgrades}/5)"})

    if split_upgrades < 4:
        upgrades.append({"id": 11, "text_kor": f"적중 시 분열 +1 ({split_upgrades}/4)", "text_eng": f"Bullet Split +1 ({split_upgrades}/4)"})

    if bullet_speed_upgrades < 3:
        upgrades.append({"id": 13, "text_kor": f"투사체 속도 +30% ({bullet_speed_upgrades}/3)", "text_eng": f"Bullet Speed +30% ({bullet_speed_upgrades}/3)"})

    if bullet_type == 'PIERCE':
        upgrades.append({"id": 14, "text_kor": "탄종 변경: 폭발탄 (범위/데미지 관통 비례)", "text_eng": "Change Ammo: Explosive (Area/Dmg scale with Pierce)"})
    else:
        upgrades.append({"id": 15, "text_kor": "탄종 변경: 관통탄 (순수 관통 위주)", "text_eng": "Change Ammo: Piercing (Focus on Pierce)"})

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
    global bullet_type, magnet_radius, magnet_radius_sq
    global bullet_count_upgrades, bullet_speed_upgrades, split_upgrades

    if upgrade_id == 1:
        pierce_count += 1
    elif upgrade_id == 2:
        if bullet_count_upgrades < 5:
            bullet_count += 2
            bullet_count_upgrades += 1
    elif upgrade_id == 3:
        shoot_interval *= 0.9
    elif upgrade_id == 4:
        fire_directions += 1
    elif upgrade_id == 5:
        max_hp += 10
        player_hp += 10
    elif upgrade_id == 6:
        hp_regen += 1
    elif upgrade_id == 8:
        magnet_radius *= 1.10
        magnet_radius_sq = magnet_radius * magnet_radius
    elif upgrade_id == 10:
        move_speed *= 1.20
    elif upgrade_id == 11:
        if split_upgrades < 4:
            split_count += 1
            split_upgrades += 1
    elif upgrade_id == 12:
        enemy_speed_mult *= 0.90
    elif upgrade_id == 13:
        if bullet_speed_upgrades < 3:
            bullet_speed *= 1.30
            bullet_speed_upgrades += 1
    elif upgrade_id == 14:
        bullet_type = 'EXPLOSIVE'
    elif upgrade_id == 15:
        bullet_type = 'PIERCE'

def update_enemy_size(enemy):
    ratio = enemy["hp"] / enemy["max_hp"]
    scale = 1.0
    if ratio <= 0.30:
        scale = 0.8
    elif ratio <= 0.70:
        scale = 0.9

    new_size = int(enemy["base_size"] * scale)
    if enemy["rect"].width != new_size:
        center = enemy["rect"].center
        enemy["rect"].width = new_size
        enemy["rect"].height = new_size
        enemy["rect"].center = center

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

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not is_game_over:
                is_game_over = True

            if is_game_over and event.key == pygame.K_r:
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
        if dx != 0 or dy != 0:
            player.x += dx * move_speed * dt
            player.y += dy * move_speed * dt
            player.clamp_ip(pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT))

        px_c, py_c = player.centerx, player.centery

        # 적 생성
        spawn_interval = max(0.2, 1.0 - (play_time / 60.0) * 0.4)
        spawn_amount = 1 + int(play_time / 15.0)

        base_enemy_hp = 1 + (player_level - 1)

        spawn_timer += dt
        if spawn_timer >= spawn_interval and len(enemies) < 250:
            spawn_timer = 0.0
            for _ in range(spawn_amount):
                angle = random.uniform(0, 6.28318)
                ex = px_c + math.cos(angle) * 500
                ey = py_c + math.sin(angle) * 500

                is_elite = random.random() < 0.1
                if is_elite:
                    dir_x, dir_y = px_c - ex, py_c - ey
                    dist = math.hypot(dir_x, dir_y)
                    vx = (dir_x / dist) * 200 if dist > 0 else 200
                    vy = (dir_y / dist) * 200 if dist > 0 else 0
                    hp = base_enemy_hp + 9
                    enemies.append({
                        "rect": pygame.Rect(ex, ey, 24, 24),
                        "hp": hp,
                        "max_hp": hp,
                        "base_size": 24,
                        "is_elite": True,
                        "vx": vx,
                        "vy": vy
                    })
                else:
                    hp = base_enemy_hp
                    enemies.append({
                        "rect": pygame.Rect(ex, ey, 16, 16),
                        "hp": hp,
                        "max_hp": hp,
                        "base_size": 16,
                        "is_elite": False,
                        "vx": 0,
                        "vy": 0
                    })

        # 포션 생성
        potion_timer += dt
        if potion_timer >= 10.0:
            potion_timer = 0.0
            potions.append(pygame.Rect(random.randint(50, GAME_WIDTH - 50), random.randint(50, SCREEN_HEIGHT - 50), 15, 15))

        # 적 공격력
        time_damage_bonus = int(play_time / 10.0)
        base_normal_damage = 1 + time_damage_bonus
        base_elite_damage = 5 + time_damage_bonus

        # 적 이동 및 플레이어 충돌
        i = 0
        while i < len(enemies):
            enemy = enemies[i]
            er = enemy["rect"]
            if enemy["is_elite"]:
                er.x += enemy["vx"] * enemy_speed_mult * dt
                er.y += enemy["vy"] * enemy_speed_mult * dt
            else:
                dir_x = px_c - er.centerx
                dir_y = py_c - er.centery
                dist_sq = dir_x * dir_x + dir_y * dir_y
                if dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    er.x += (dir_x / dist) * 100 * enemy_speed_mult * dt
                    er.y += (dir_y / dist) * 100 * enemy_speed_mult * dt

            if player.colliderect(er):
                damage = base_elite_damage if enemy["is_elite"] else base_normal_damage
                player_hp -= damage
                damage_rings.append({"x": px_c, "y": py_c, "radius": 15, "timer": 0.2})
                enemies.pop(i)
                if player_hp <= 0:
                    player_hp = 0
                    is_game_over = True
            else:
                i += 1

        # 전리품 수집
        i = 0
        while i < len(loot_items):
            loot = loot_items[i]
            lx, ly = loot["x"], loot["y"]
            dx_l, dy_l = px_c - lx, py_c - ly
            dist_sq = dx_l * dx_l + dy_l * dy_l

            is_mag = loot.get("magnetized", False) or (dist_sq <= magnet_radius_sq)

            if is_mag:
                if dist_sq > 0:
                    dist = math.sqrt(dist_sq)
                    speed = 600 if loot.get("magnetized", False) else 350
                    loot["x"] += (dx_l / dist) * speed * dt
                    loot["y"] += (dy_l / dist) * speed * dt

                if dist_sq < 400:
                    add_kills_and_check_upgrade(loot["value"])
                    loot_items.pop(i)
                    continue
            i += 1

        # 포션 획득
        for potion in potions[:]:
            if player.colliderect(potion):
                player_hp = min(max_hp, player_hp + 50)
                potions.remove(potion)

        # 총알 발사
        shoot_timer += dt
        if shoot_timer >= shoot_interval and enemies:
            shoot_timer = 0.0
            sorted_enemies = sorted(enemies, key=lambda e: (e["rect"].centerx - px_c)**2 + (e["rect"].centery - py_c)**2)
            target_enemies = sorted_enemies[:fire_directions]

            for target in target_enemies:
                dir_x = target["rect"].centerx - px_c
                dir_y = target["rect"].centery - py_c
                if dir_x != 0 or dir_y != 0:
                    base_angle = math.atan2(dir_y, dir_x)
                    for b_idx in range(bullet_count):
                        angle_offset = (b_idx - (bullet_count - 1) / 2) * 0.15
                        final_angle = base_angle + angle_offset
                        bullets.append({
                            "rect": pygame.Rect(px_c, py_c, 8, 8),
                            "vx": math.cos(final_angle) * bullet_speed,
                            "vy": math.sin(final_angle) * bullet_speed,
                            "pierce": pierce_count,
                            "damage": 1 + pierce_count,  # 관통탄 초기 데미지: 1 + 관통력
                            "can_split": True,
                            "hit_enemies": set()
                        })

        # 총알 이동 및 충돌
        b_idx = 0

        # 폭발 탄종 스탯 계산: 관통력만큼 범위 +20%, 데미지 = 1 + pierce_count
        current_exp_radius = base_explosion_radius * (1.0 + 0.20 * pierce_count)
        exp_sq = current_exp_radius * current_exp_radius
        exp_damage = 1 + pierce_count

        while b_idx < len(bullets):
            bullet = bullets[b_idx]
            br = bullet["rect"]
            br.x += bullet["vx"] * dt
            br.y += bullet["vy"] * dt

            if br.right < 0 or br.left > GAME_WIDTH or br.bottom < 0 or br.top > SCREEN_HEIGHT:
                bullets.pop(b_idx)
                continue

            bullet_destroyed = False
            e_idx = 0

            while e_idx < len(enemies):
                enemy = enemies[e_idx]
                er = enemy["rect"]

                if id(er) not in bullet["hit_enemies"] and br.colliderect(er):
                    bullet["hit_enemies"].add(id(er))
                    
                    bx, by = br.centerx, br.centery

                    if len(hit_effects) < 100:
                        for _ in range(3):
                            hit_effects.append({
                                "x": bx, "y": by,
                                "vx": random.uniform(-80, 80),
                                "vy": random.uniform(-80, 80),
                                "timer": 0.12
                            })

                    # 분열 로직
                    if bullet.get("can_split", False) and split_count > 0:
                        split_num = split_count + 1
                        other_enemies = [e for e in enemies if e != enemy]
                        other_enemies.sort(key=lambda e: (e["rect"].centerx - bx)**2 + (e["rect"].centery - by)**2)

                        for s_i in range(split_num):
                            if s_i < len(other_enemies):
                                target_e = other_enemies[s_i]
                                tx = target_e["rect"].centerx - bx
                                ty = target_e["rect"].centery - by
                                split_angle = math.atan2(ty, tx) if (tx!=0 or ty!=0) else (6.28318 / split_num) * s_i
                            else:
                                split_angle = (6.28318 / split_num) * s_i

                            split_hit = set(bullet["hit_enemies"])
                            bullets.append({
                                "rect": pygame.Rect(bx, by, 6, 6),
                                "vx": math.cos(split_angle) * bullet_speed * 0.85,
                                "vy": math.sin(split_angle) * bullet_speed * 0.85,
                                "pierce": 1,
                                "damage": 1,
                                "can_split": False,
                                "hit_enemies": split_hit
                            })

                    # 탄종별 데미지 및 효과 처리
                    if bullet_type == 'EXPLOSIVE':
                        if len(explosions) < 30:
                            explosions.append({"x": bx, "y": by, "radius": current_exp_radius, "timer": 0.1})
                        for near_enemy in enemies:
                            edx = near_enemy["rect"].centerx - bx
                            edy = near_enemy["rect"].centery - by
                            if edx * edx + edy * edy <= exp_sq:
                                near_enemy["hp"] -= exp_damage
                                update_enemy_size(near_enemy)
                        
                        enemy["hp"] -= 1
                    else: # PIERCE 탄종
                        # 적중 시 현재 데미지 입히고, 관통 시 데미지 1 차감 (최소 1)
                        enemy["hp"] -= bullet["damage"]
                        bullet["damage"] = max(1, bullet["damage"] - 1)

                    bullet["pierce"] -= 1
                    update_enemy_size(enemy)

                    if enemy["hp"] <= 0:
                        ex, ey = er.centerx, er.centery
                        is_elite = enemy["is_elite"]
                        kill_val = 5 if is_elite else 1
                        add_kills_and_check_upgrade(kill_val)
                        enemies.pop(e_idx)

                        if random.random() < 0.50 and len(loot_items) < 150:
                            loot_items.append({"x": ex, "y": ey, "value": kill_val, "is_elite": is_elite, "magnetized": False})
                    else:
                        e_idx += 1

                    if bullet["pierce"] <= 0:
                        bullet_destroyed = True
                        break
                else:
                    e_idx += 1

            if bullet_destroyed:
                bullets.pop(b_idx)
            else:
                b_idx += 1

        # 이펙트 업데이트
        explosions = [exp for exp in explosions if exp["timer"] > 0]
        for exp in explosions:
            exp["timer"] -= dt

        hit_effects = [eff for eff in hit_effects if eff["timer"] > 0]
        for eff in hit_effects:
            eff["timer"] -= dt
            eff["x"] += eff["vx"] * dt
            eff["y"] += eff["vy"] * dt

        damage_rings = [ring for ring in damage_rings if ring["timer"] > 0]
        for ring in damage_rings:
            ring["timer"] -= dt
            ring["radius"] += 80 * dt

    # --- [그리기] ---
    screen.fill((30, 30, 30))

    pygame.draw.rect(screen, (0, 255, 0), player)
    
    hp_ratio = max(0, player_hp / max_hp)
    hp_bar_x = px_c - 20
    hp_bar_y = player.top - 12
    pygame.draw.rect(screen, (80, 80, 80), (hp_bar_x, hp_bar_y, 40, 6))
    pygame.draw.rect(screen, (255, 50, 50), (hp_bar_x, hp_bar_y, int(40 * hp_ratio), 6))

    for enemy in enemies:
        color = (160, 32, 240) if enemy["is_elite"] else (255, 0, 0)
        pygame.draw.rect(screen, color, enemy["rect"])

    for bullet in bullets:
        if bullet_type == 'EXPLOSIVE':
            color = (255, 80, 80) if bullet.get("can_split", False) else (255, 0, 0)
        else:
            color = (255, 255, 0) if bullet.get("can_split", False) else (255, 165, 0)
        pygame.draw.rect(screen, color, bullet["rect"])

    for potion in potions:
        pygame.draw.rect(screen, (0, 191, 255), potion)

    for loot in loot_items:
        color = (255, 105, 180) if loot["is_elite"] else (255, 215, 0)
        pygame.draw.circle(screen, color, (int(loot["x"]), int(loot["y"])), 5 if loot["is_elite"] else 3)

    for exp in explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    for eff in hit_effects:
        pygame.draw.circle(screen, (255, 200, 50), (int(eff["x"]), int(eff["y"])), 2)

    for ring in damage_rings:
        pygame.draw.circle(screen, (255, 0, 0), (int(ring["x"]), int(ring["y"])), int(ring["radius"]), 2)

    # UI 상단
    minutes = int(play_time) // 60
    seconds = int(play_time) % 60

    if current_lang == 'KOR':
        time_str = f"시간: {minutes:02d}:{seconds:02d} | [ESC]: 포기하기"
        kill_str = f"LV.{player_level} | 처치: {kill_count} (다음: {kills_for_next_upgrade})"
    else:
        time_str = f"Time: {minutes:02d}:{seconds:02d} | [ESC]: Give Up"
        kill_str = f"LV.{player_level} | Kills: {kill_count} (Next: {kills_for_next_upgrade})"

    screen.blit(bold_font.render(time_str, True, (255, 255, 255)), (10, 10))
    screen.blit(bold_font.render(kill_str, True, (255, 255, 255)), (10, 32))

    # [한영 버튼]
    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), lang_button_rect, 2)
    btn_text = font.render(f"[{current_lang}]", True, (255, 255, 255))
    screen.blit(btn_text, (lang_button_rect.x + 15, lang_button_rect.y + 4))

    # --- [우측 분리 패널] ---
    panel_rect = pygame.Rect(GAME_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (20, 20, 25), panel_rect)
    pygame.draw.line(screen, (80, 80, 100), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

    rank_title_str = "랭킹 (Top 5)" if current_lang == 'KOR' else "RANKING"
    screen.blit(bold_font.render(rank_title_str, True, (255, 215, 0)), (GAME_WIDTH + 15, 15))

    for idx, r in enumerate(rankings[:5]):
        rk_m, rk_s = int(r["time"]) // 60, int(r["time"]) % 60
        rank_item_str = f"{idx+1}. Lv.{r['level']} | {r['kills']}K ({rk_m:02d}:{rk_s:02d})"
        screen.blit(font.render(rank_item_str, True, (200, 200, 200)), (GAME_WIDTH + 10, 45 + idx * 25))

    pygame.draw.line(screen, (60, 60, 80), (GAME_WIDTH + 10, 185), (GAME_WIDTH + UI_PANEL_WIDTH - 10, 185), 1)

    stat_title_str = "캐릭터 스탯" if current_lang == 'KOR' else "CHARACTER STATS"
    screen.blit(bold_font.render(stat_title_str, True, (100, 200, 255)), (GAME_WIDTH + 15, 195))

    curr_time_dmg = 1 + int(play_time / 10.0)
    curr_enemy_hp = 1 + (player_level - 1)
    type_display = "관통탄" if bullet_type == 'PIERCE' else "폭발탄"
    initial_pierce_dmg = 1 + pierce_count
    
    stats_list = [
        f"탄종: {type_display}" if current_lang == 'KOR' else f"Ammo: {bullet_type}",
        f"체력: {int(player_hp)} / {max_hp}" if current_lang == 'KOR' else f"HP: {int(player_hp)} / {max_hp}",
        f"이동속도: {int(move_speed)}" if current_lang == 'KOR' else f"Speed: {int(move_speed)}",
        f"공격간격: {shoot_interval:.2f}초" if current_lang == 'KOR' else f"Cooldown: {shoot_interval:.2f}s",
        f"발사방향: {fire_directions}방향" if current_lang == 'KOR' else f"Directions: {fire_directions}",
        f"총알 개수: {bullet_count}개 ({bullet_count_upgrades}/5)" if current_lang == 'KOR' else f"Bullets: {bullet_count} ({bullet_count_upgrades}/5)",
        f"투사체 속도: {int(bullet_speed)} ({bullet_speed_upgrades}/3)" if current_lang == 'KOR' else f"B.Speed: {int(bullet_speed)} ({bullet_speed_upgrades}/3)",
        f"관통력: {pierce_count}" if current_lang == 'KOR' else f"Pierce: {pierce_count}",
        f"초기 데미지: {initial_pierce_dmg}" if current_lang == 'KOR' and bullet_type == 'PIERCE' else f"Init Dmg: {initial_pierce_dmg}" if bullet_type == 'PIERCE' else "",
        f"분열 수: {split_count} ({split_upgrades}/4)" if current_lang == 'KOR' else f"Splits: {split_count} ({split_upgrades}/4)",
        f"폭발 데미지: {exp_damage}" if current_lang == 'KOR' and bullet_type == 'EXPLOSIVE' else f"Exp. Dmg: {exp_damage}" if bullet_type == 'EXPLOSIVE' else "",
        f"적 체력: {curr_enemy_hp}" if current_lang == 'KOR' else f"Enemy HP: {curr_enemy_hp}",
        f"적 공격력: {curr_time_dmg}" if current_lang == 'KOR' else f"Enemy Dmg: {curr_time_dmg}",
    ]
    for idx, s_text in enumerate(stats_list):
        if s_text:
            screen.blit(font.render(s_text, True, (220, 220, 220)), (GAME_WIDTH + 12, 225 + idx * 24))

    # 레벨업 팝업
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