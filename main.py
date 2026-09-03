import pygame
import math
import random
import config
from entities import update_enemy_size
from managers import generate_upgrade_options

screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
clock = pygame.time.Clock()
rankings = config.load_rankings()

def reset_game():
    global player, enemies, bullets, potions, loot_items, explosions, hit_effects, damage_rings
    global spawn_timer, shoot_timer, potion_timer
    global max_hp, player_hp, hp_regen, move_speed, pierce_count, bullet_count, bullet_speed, shoot_interval, fire_directions, split_count, enemy_speed_mult
    global bullet_type, base_explosion_radius, magnet_radius, magnet_radius_sq
    global bullet_count_upgrades, bullet_speed_upgrades, split_upgrades, player_size_upgrades
    global play_time, kill_count, kills_for_next_upgrade, player_level
    global is_upgrading, is_game_over, record_saved

    # 플레이어 기본 크기 30x30
    player = pygame.Rect(400, 300, 30, 30)
    enemies, bullets, potions, loot_items, explosions, hit_effects, damage_rings = [], [], [], [], [], [], []

    spawn_timer = shoot_timer = potion_timer = 0.0
    max_hp = player_hp = 100
    hp_regen = 0
    move_speed = 200.0
    enemy_speed_mult = 1.0
    pierce_count = bullet_count = 1
    bullet_speed = 400.0
    shoot_interval = 0.5
    fire_directions = 1
    split_count = 0

    bullet_type = 'PIERCE'
    base_explosion_radius = 90.0

    bullet_count_upgrades = bullet_speed_upgrades = split_upgrades = player_size_upgrades = 0
    magnet_radius = 100.0
    magnet_radius_sq = magnet_radius * magnet_radius

    play_time = 0.0
    kill_count = 0
    kills_for_next_upgrade = 20
    player_level = 1

    is_upgrading = is_game_over = record_saved = False

current_lang = 'KOR'
lang_button_rect = pygame.Rect(config.GAME_WIDTH - 90, 10, 80, 30)
upgrade_options, selected_option_index = [], 0

reset_game()

def add_kills_and_check_upgrade(amount):
    global kill_count, kills_for_next_upgrade, player_level, is_upgrading, upgrade_options, selected_option_index, max_hp, player_hp
    kill_count += amount
    if kill_count >= kills_for_next_upgrade:
        kills_for_next_upgrade = int(kills_for_next_upgrade * 1.3)
        player_level += 1
        max_hp += 5
        player_hp = min(max_hp, player_hp + 5)
        is_upgrading = True
        for loot in loot_items:
            loot["magnetized"] = True
        upgrade_options = generate_upgrade_options(bullet_count_upgrades, split_upgrades, bullet_speed_upgrades, player_size_upgrades)
        selected_option_index = 0

def apply_upgrade(upgrade_ids):
    for uid in upgrade_ids:
        apply_single_upgrade(uid)

def apply_single_upgrade(upgrade_id):
    global pierce_count, bullet_count, bullet_speed, shoot_interval, fire_directions, max_hp, player_hp, hp_regen, move_speed, split_count, enemy_speed_mult
    global magnet_radius, magnet_radius_sq, bullet_count_upgrades, bullet_speed_upgrades, split_upgrades, player_size_upgrades, player

    if upgrade_id == 1: pierce_count += 1
    elif upgrade_id == 2 and bullet_count_upgrades < 5:
        bullet_count += 2; bullet_count_upgrades += 1
    elif upgrade_id == 3: shoot_interval *= 0.9
    elif upgrade_id == 4: fire_directions += 1
    elif upgrade_id == 5: max_hp += 10; player_hp += 10
    elif upgrade_id == 6: hp_regen += 1
    elif upgrade_id == 8: magnet_radius *= 1.10; magnet_radius_sq = magnet_radius**2
    elif upgrade_id == 10: move_speed = min(500.0, move_speed * 1.20)
    elif upgrade_id == 11 and split_upgrades < 4:
        split_count += 1; split_upgrades += 1
    elif upgrade_id == 12: enemy_speed_mult *= 0.90
    elif upgrade_id == 13 and bullet_speed_upgrades < 3:
        bullet_speed *= 1.30; bullet_speed_upgrades += 1
    elif upgrade_id == 14 and player_size_upgrades < 2:
        # [신규] 캐릭터 크기 20% 축소 (중심점 유지)
        old_center = player.center
        new_w = max(10, int(player.width * 0.8))
        new_h = max(10, int(player.height * 0.8))
        player = pygame.Rect(0, 0, new_w, new_h)
        player.center = old_center
        player_size_upgrades += 1

running = True
while running:
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if lang_button_rect.collidepoint(event.pos):
                current_lang = 'ENG' if current_lang == 'KOR' else 'KOR'
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not is_game_over: is_game_over = True
            # [신규] 게임 오버 상태 이벤트 처리
            if is_game_over:
                if event.key == pygame.K_r: reset_game()
                elif event.key == pygame.K_q: running = False  # Q 누르면 창 종료

            if not is_game_over and not is_upgrading:
                if event.key in (pygame.K_1, pygame.K_EXCLAIM): bullet_type = 'PIERCE'
                elif event.key in (pygame.K_2, pygame.K_AT): bullet_type = 'EXPLOSIVE'

        if is_upgrading and not is_game_over and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP: selected_option_index = (selected_option_index - 1) % len(upgrade_options)
            elif event.key == pygame.K_DOWN: selected_option_index = (selected_option_index + 1) % len(upgrade_options)
            elif event.key == pygame.K_SPACE:
                apply_upgrade(upgrade_options[selected_option_index]["ids"])
                is_upgrading = False

    if is_game_over and not record_saved:
        stats_summary = f"HP:{max_hp}|SPD:{int(move_speed)}|INT:{shoot_interval:.2f}|Prc:{pierce_count}|Splt:{split_count}"
        rankings.append({"level": player_level, "kills": kill_count, "time": play_time, "stats": stats_summary})
        rankings.sort(key=lambda x: (x["kills"], x["time"]), reverse=True)
        config.save_rankings(rankings)
        record_saved = True

    if not is_game_over and not is_upgrading:
        play_time += dt
        if hp_regen > 0: player_hp = min(max_hp, player_hp + hp_regen * dt)

        # [신규] Shift 키 입력을 감지하여 속도 절반 적용
        keys = pygame.key.get_pressed()
        current_speed = move_speed * 0.5 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else move_speed

        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx or dy:
            player.x += dx * current_speed * dt
            player.y += dy * current_speed * dt
            player.clamp_ip(pygame.Rect(0, 0, config.GAME_WIDTH, config.SCREEN_HEIGHT))

        px_c, py_c = player.centerx, player.centery

        # 스폰 및 속성 설정
        spawn_interval = max(0.2, 1.0 - (play_time / 60.0) * 0.4)
        spawn_amount = 1 + int(play_time / 15.0)
        base_enemy_hp = 1 + (player_level - 1)
        time_damage_bonus = int(play_time / 10.0)

        spawn_timer += dt
        if spawn_timer >= spawn_interval and len(enemies) < 250:
            spawn_timer = 0.0
            for _ in range(spawn_amount):
                angle = random.uniform(0, 6.28318)
                ex, ey = px_c + math.cos(angle) * 500, py_c + math.sin(angle) * 500
                rand_val = random.random()

                if rand_val < 0.05:
                    boss_hp = (base_enemy_hp + 9) * 5
                    enemies.append({"rect": pygame.Rect(ex, ey, 36, 36), "hp": boss_hp, "max_hp": boss_hp, "base_size": 36, "type": "BOSS", "damage": (5 + time_damage_bonus) * 5, "vx": 0, "vy": 0})
                elif rand_val < 0.15:
                    dist = math.hypot(px_c - ex, py_c - ey)
                    vx, vy = ((px_c - ex) / dist) * 200, ((py_c - ey) / dist) * 200
                    enemies.append({"rect": pygame.Rect(ex, ey, 24, 24), "hp": base_enemy_hp + 9, "max_hp": base_enemy_hp + 9, "base_size": 24, "type": "ELITE", "damage": 5 + time_damage_bonus, "vx": vx, "vy": vy})
                else:
                    enemies.append({"rect": pygame.Rect(ex, ey, 16, 16), "hp": base_enemy_hp, "max_hp": base_enemy_hp, "base_size": 16, "type": "NORMAL", "damage": 1 + time_damage_bonus, "vx": 0, "vy": 0})

        potion_timer += dt
        if potion_timer >= 10.0:
            potion_timer = 0.0
            potions.append(pygame.Rect(random.randint(50, config.GAME_WIDTH - 50), random.randint(50, config.SCREEN_HEIGHT - 50), 15, 15))

        # 적 이동
        i = 0
        while i < len(enemies):
            enemy = enemies[i]
            er = enemy["rect"]
            if enemy["type"] == "ELITE":
                er.x += enemy["vx"] * enemy_speed_mult * dt; er.y += enemy["vy"] * enemy_speed_mult * dt
            else:
                speed = 70 if enemy["type"] == "BOSS" else 100
                dist = math.hypot(px_c - er.centerx, py_c - er.centery)
                if dist > 0:
                    er.x += ((px_c - er.centerx) / dist) * speed * enemy_speed_mult * dt
                    er.y += ((py_c - er.centery) / dist) * speed * enemy_speed_mult * dt

            if player.colliderect(er):
                player_hp -= enemy["damage"]
                damage_rings.append({"x": px_c, "y": py_c, "radius": 15, "timer": 0.2})
                enemies.pop(i)
                if player_hp <= 0: player_hp = 0; is_game_over = True
            else: i += 1

        # 전리품 획득
        i = 0
        while i < len(loot_items):
            loot = loot_items[i]
            dist_sq = (px_c - loot["x"])**2 + (py_c - loot["y"])**2
            if loot.get("magnetized", False) or dist_sq <= magnet_radius_sq:
                dist = math.sqrt(dist_sq)
                if dist > 0:
                    sp = 600 if loot.get("magnetized", False) else 350
                    loot["x"] += ((px_c - loot["x"]) / dist) * sp * dt
                    loot["y"] += ((py_c - loot["y"]) / dist) * sp * dt
                if dist_sq < 400:
                    add_kills_and_check_upgrade(loot["value"])
                    loot_items.pop(i); continue
            i += 1

        for potion in potions[:]:
            if player.colliderect(potion):
                player_hp = min(max_hp, player_hp + 50)
                potions.remove(potion)

        # 사격
        shoot_timer += dt
        if shoot_timer >= shoot_interval and enemies:
            shoot_timer = 0.0
            sorted_e = sorted(enemies, key=lambda e: (e["rect"].centerx - px_c)**2 + (e["rect"].centery - py_c)**2)[:fire_directions]
            active_bullet_count = max(1, bullet_count // 2) if bullet_type == 'EXPLOSIVE' else bullet_count

            for target in sorted_e:
                base_angle = math.atan2(target["rect"].centery - py_c, target["rect"].centerx - px_c)
                for b_idx in range(active_bullet_count):
                    angle = base_angle + (b_idx - (active_bullet_count - 1) / 2) * 0.15
                    bullets.append({"rect": pygame.Rect(px_c, py_c, 8, 8), "vx": math.cos(angle) * bullet_speed, "vy": math.sin(angle) * bullet_speed, "pierce": pierce_count, "damage": 1 + pierce_count, "can_split": True, "hit_enemies": set()})

        # 총알 충돌
        current_exp_radius = base_explosion_radius * (1.0 + 0.10 * pierce_count)
        exp_sq = current_exp_radius**2
        exp_damage = 1 + pierce_count
        b_idx = 0

        while b_idx < len(bullets):
            bullet = bullets[b_idx]
            br = bullet["rect"]
            br.x += bullet["vx"] * dt; br.y += bullet["vy"] * dt

            if br.right < 0 or br.left > config.GAME_WIDTH or br.bottom < 0 or br.top > config.SCREEN_HEIGHT:
                bullets.pop(b_idx); continue

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
                            hit_effects.append({"x": bx, "y": by, "vx": random.uniform(-80, 80), "vy": random.uniform(-80, 80), "timer": 0.12})

                    if bullet.get("can_split", False) and split_count > 0:
                        split_num = split_count + 1
                        others = sorted([e for e in enemies if e != enemy], key=lambda e: (e["rect"].centerx - bx)**2 + (e["rect"].centery - by)**2)
                        for s_i in range(split_num):
                            angle = math.atan2(others[s_i]["rect"].centery - by, others[s_i]["rect"].centerx - bx) if s_i < len(others) else (6.28318 / split_num) * s_i
                            bullets.append({"rect": pygame.Rect(bx, by, 6, 6), "vx": math.cos(angle) * bullet_speed * 0.85, "vy": math.sin(angle) * bullet_speed * 0.85, "pierce": 1, "damage": 1, "can_split": False, "hit_enemies": set(bullet["hit_enemies"])})

                    if bullet_type == 'EXPLOSIVE':
                        if len(explosions) < 30: explosions.append({"x": bx, "y": by, "radius": current_exp_radius, "timer": 0.1})
                        for near in enemies:
                            if (near["rect"].centerx - bx)**2 + (near["rect"].centery - by)**2 <= exp_sq:
                                near["hp"] -= exp_damage; update_enemy_size(near)
                        enemy["hp"] -= 1
                    else:
                        enemy["hp"] -= bullet["damage"]
                        bullet["damage"] = max(1, bullet["damage"] - 1)

                    bullet["pierce"] -= 1
                    update_enemy_size(enemy)

                    if enemy["hp"] <= 0:
                        val = 25 if enemy["type"] == "BOSS" else (5 if enemy["type"] == "ELITE" else 1)
                        add_kills_and_check_upgrade(val)
                        enemies.pop(e_idx)
                        if random.random() < 0.50 and len(loot_items) < 150:
                            loot_items.append({"x": bx, "y": by, "value": val, "type": enemy["type"], "magnetized": False})
                    else: e_idx += 1

                    if bullet["pierce"] <= 0: bullet_destroyed = True; break
                else: e_idx += 1

            if bullet_destroyed: bullets.pop(b_idx)
            else: b_idx += 1

        explosions = [e for e in explosions if e["timer"] > 0]
        for exp in explosions: exp["timer"] -= dt

        hit_effects = [e for e in hit_effects if e["timer"] > 0]
        for eff in hit_effects:
            eff["timer"] -= dt; eff["x"] += eff["vx"] * dt; eff["y"] += eff["vy"] * dt

        damage_rings = [r for r in damage_rings if r["timer"] > 0]
        for ring in damage_rings:
            ring["timer"] -= dt; ring["radius"] += 80 * dt

    # Render
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (0, 255, 0), player)

    for e in enemies:
        c = (255, 215, 0) if e["type"] == "BOSS" else ((160, 32, 240) if e["type"] == "ELITE" else (255, 0, 0))
        pygame.draw.rect(screen, c, e["rect"])

    for b in bullets:
        c = (255, 80, 80) if bullet_type == 'EXPLOSIVE' else (255, 255, 0)
        pygame.draw.rect(screen, c, b["rect"])

    for p in potions: pygame.draw.rect(screen, (0, 191, 255), p)
    for l in loot_items: pygame.draw.circle(screen, (255, 215, 0) if l["type"] in ("BOSS", "NORMAL") else (255, 105, 180), (int(l["x"]), int(l["y"])), 8 if l["type"] == "BOSS" else 3)
    for exp in explosions: pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)
    for eff in hit_effects: pygame.draw.circle(screen, (255, 200, 50), (int(eff["x"]), int(eff["y"])), 2)
    for ring in damage_rings: pygame.draw.circle(screen, (255, 0, 0), (int(ring["x"]), int(ring["y"])), int(ring["radius"]), 2)

    # UI
    m, s = int(play_time) // 60, int(play_time) % 60
    time_str = f"시간: {m:02d}:{s:02d} | [1]:관통 [2]:폭발 | [ESC]:포기" if current_lang == 'KOR' else f"Time: {m:02d}:{s:02d} | [1]:Pierce [2]:Exp"
    kill_str = f"LV.{player_level} | 처치: {kill_count} (다음: {kills_for_next_upgrade})"
    screen.blit(config.bold_font.render(time_str, True, (255, 255, 255)), (10, 10))
    screen.blit(config.bold_font.render(kill_str, True, (255, 255, 255)), (10, 32))

    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    screen.blit(config.font.render(f"[{current_lang}]", True, (255, 255, 255)), (lang_button_rect.x + 15, lang_button_rect.y + 4))

    # 우측 정보 패널
    pygame.draw.rect(screen, (20, 20, 25), (config.GAME_WIDTH, 0, config.UI_PANEL_WIDTH, config.SCREEN_HEIGHT))
    screen.blit(config.bold_font.render("랭킹 (Top 5)", True, (255, 215, 0)), (config.GAME_WIDTH + 15, 10))
    for idx, r in enumerate(rankings[:5]):
        screen.blit(config.font.render(f"{idx+1}. Lv.{r['level']} | {r['kills']}K", True, (200, 200, 200)), (config.GAME_WIDTH + 10, 32 + idx * 22))

    screen.blit(config.bold_font.render("캐릭터 스탯", True, (100, 200, 255)), (config.GAME_WIDTH + 15, 150))
    disp_bc = max(1, bullet_count // 2) if bullet_type == 'EXPLOSIVE' else bullet_count

    stats = [
        f"탄종: {bullet_type}",
        f"체력: {int(player_hp)}/{max_hp}",
        f"초당 회복: +{hp_regen}/s",
        f"이동 속도: {int(move_speed)}",
        f"캐릭터 크기: {player.width}x{player.height}",
        f"공격 간격: {shoot_interval:.2f}s",
        f"발사 방향: {fire_directions}방향",
        f"발사 개수: {disp_bc}개",
        f"관통력: {pierce_count}",
        f"적중 분열: +{split_count}개",
        f"투사체 속도: {int(bullet_speed)}",
        f"폭발 범위: {int(current_exp_radius)}",
        f"획득 범위: {int(magnet_radius)}",
        f"적 속도율: {int(enemy_speed_mult * 100)}%"
    ]

    for idx, st in enumerate(stats):
        screen.blit(config.font.render(st, True, (220, 220, 220)), (config.GAME_WIDTH + 12, 175 + idx * 21))

    # 팝업 처리
    if is_upgrading and not is_game_over:
        overlay = pygame.Surface((config.GAME_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(180); overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        for idx, option in enumerate(upgrade_options):
            c = (255, 255, 0) if idx == selected_option_index else (255, 255, 255)
            screen.blit(config.font.render(option["text_kor"], True, c), (120, 220 + idx * 60))

    if is_game_over:
        overlay = pygame.Surface((config.GAME_WIDTH, config.SCREEN_HEIGHT))
        overlay.set_alpha(200); overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        screen.blit(config.title_font.render("GAME OVER", True, (255, 50, 50)), (config.GAME_WIDTH // 2 - 120, 200))
        # [신규] 안내 문구 변경
        screen.blit(config.bold_font.render("[R] 재시작  |  [Q] 게임 종료", True, (255, 255, 255)), (config.GAME_WIDTH // 2 - 110, 270))

    pygame.display.flip()

pygame.quit()