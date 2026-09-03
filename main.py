import pygame
import math
import random
import platform

# 초기화
pygame.init()
pygame.font.init()

# 화면 확장: 800(게임 화면) + 200(오른쪽 랭킹 패널) = 1000 x 600
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

font = get_korean_font(20)
bold_font = get_korean_font(22)
title_font = get_korean_font(36)

# 랭킹 기록 저장용 리스트 [(kill_count, play_time), ...]
rankings = []

# 게임 전체 상태 Reset 함수
def reset_game():
    global player, enemies, bullets, potions, loot_items, explosions
    global spawn_timer, shoot_timer, potion_timer
    global max_hp, player_hp, hp_regen, move_speed, pierce_count, bullet_count, shoot_interval, fire_directions, split_count
    global has_explosion, explosion_radius, magnet_radius
    global play_time, kill_count, kills_for_next_upgrade, player_level
    global is_upgrading, is_game_over, record_saved

    player = pygame.Rect(400, 300, 30, 30)
    enemies = []
    bullets = []
    potions = []
    loot_items = []
    explosions = []

    spawn_timer = 0
    shoot_timer = 0
    potion_timer = 0

    max_hp = 100
    player_hp = 100
    hp_regen = 0
    move_speed = 200.0     # 플레이어 기본 이동 속도
    pierce_count = 1
    bullet_count = 1
    shoot_interval = 0.5
    fire_directions = 1
    split_count = 0        # 적중 시 분열 횟수

    has_explosion = False
    explosion_radius = 30.0
    magnet_radius = 100.0

    play_time = 0.0
    kill_count = 0
    kills_for_next_upgrade = 20
    player_level = 1       # 시작 레벨

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
        player_level += 1      # 레벨 증가
        is_upgrading = True
        
        # 레벨업 시 필드의 모든 전리품 강제 자석 수집 (플레이어에게 흡수)
        for loot in loot_items:
            loot["magnetized"] = True
            
        avail = get_available_upgrades()
        upgrade_options = random.sample(avail, min(3, len(avail)))
        selected_option_index = 0

def get_available_upgrades():
    upgrades = [
        {"id": 1, "text_kor": "1. 관통력 +1", "text_eng": "1. Pierce +1"},
        {"id": 2, "text_kor": "2. 개수 +1", "text_eng": "2. Bullet Count +1"},
        {"id": 3, "text_kor": "3. 공격 간격 -10%", "text_eng": "3. Cooldown -10%"},
        {"id": 4, "text_kor": "4. 공격 방향 +1", "text_eng": "4. Direction +1"},
        {"id": 5, "text_kor": "5. 최대 체력 +10", "text_eng": "5. Max HP +10"},
        {"id": 6, "text_kor": "6. 초당 체력회복 +1", "text_eng": "6. HP Regen +1"},
        {"id": 8, "text_kor": "8. 전리품 획득 범위 +10%", "text_eng": "8. Magnet Range +10%"},
        {"id": 10, "text_kor": "10. 이동속도 +20%", "text_eng": "10. Move Speed +20%"},
        {"id": 11, "text_kor": "11. 적중 시 분열 +1", "text_eng": "11. Bullet Split +1"}
    ]
    if not has_explosion:
        upgrades.append({"id": 7, "text_kor": "7. 폭발 데미지 추가", "text_eng": "7. Add Explosion Damage"})
    else:
        upgrades.append({"id": 9, "text_kor": "9. 폭발 범위 +20%", "text_eng": "9. Explosion Area +20%"})
    return upgrades

def apply_upgrade(upgrade_id):
    global pierce_count, bullet_count, shoot_interval, fire_directions, max_hp, player_hp, hp_regen, move_speed, split_count
    global has_explosion, explosion_radius, magnet_radius

    if upgrade_id == 1:
        pierce_count += 1
    elif upgrade_id == 2:
        bullet_count += 1
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
        explosion_radius *= 1.20
    elif upgrade_id == 10:
        move_speed *= 1.20    # 이동속도 20% 증가
    elif upgrade_id == 11:
        split_count += 1       # 분열 횟수 증가

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
                apply_upgrade(chosen_upgrade["id"])
                is_upgrading = False

    # --- [게임 오버 처리 & 기록 저장] ---
    if is_game_over:
        if not record_saved:
            rankings.append((kill_count, play_time))
            # 처치수 내림차순, 플레이시간 내림차순 정렬
            rankings.sort(key=lambda x: (x[0], x[1]), reverse=True)
            record_saved = True

    # --- [메인 게임 업데이트] ---
    if not is_game_over and not is_upgrading:
        play_time += dt

        if hp_regen > 0:
            player_hp = min(max_hp, player_hp + hp_regen * dt)

        # 플레이어 이동 (업그레이드된 move_speed 적용)
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        player.x += dx * move_speed * dt
        player.y += dy * move_speed * dt
        player.clamp_ip(pygame.Rect(0, 0, GAME_WIDTH, SCREEN_HEIGHT)) # 게임 영역 제한

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

        # 적 이동 및 피격
        base_enemy_damage = 1 + (play_time / 30.0)
        for enemy in enemies:
            if enemy["is_elite"]:
                enemy["rect"].x += enemy["vx"] * dt
                enemy["rect"].y += enemy["vy"] * dt
            else:
                dir_x = player.centerx - enemy["rect"].centerx
                dir_y = player.centery - enemy["rect"].centery
                dist = math.hypot(dir_x, dir_y)
                if dist > 0:
                    enemy["rect"].x += (dir_x / dist) * 100 * dt
                    enemy["rect"].y += (dir_y / dist) * 100 * dt

            if player.colliderect(enemy["rect"]):
                dmg_mult = 5.0 if enemy["is_elite"] else 1.0
                player_hp -= base_enemy_damage * dmg_mult * dt
                if player_hp <= 0:
                    player_hp = 0
                    is_game_over = True

        # 전리품 이동 및 수집 (전체 흡수 플래그 처리 포함)
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
                            "vx": math.cos(final_angle) * 400,
                            "vy": math.sin(final_angle) * 400,
                            "pierce": pierce_count,
                            "can_split": True,  # 분열 가능한 총알 표시
                            "hit_enemies": []
                        })

        # 총알 이동 및 충돌
        for bullet in bullets[:]:
            bullet["rect"].x += bullet["vx"] * dt
            bullet["rect"].y += bullet["vy"] * dt

            for enemy in enemies[:]:
                if enemy["rect"] not in bullet["hit_enemies"] and bullet["rect"].colliderect(enemy["rect"]):
                    bullet["hit_enemies"].append(enemy["rect"])
                    bullet["pierce"] -= 1

                    # 적중 시 분열 로직 (자식 총알 생성)
                    if bullet.get("can_split", False) and split_count > 0:
                        split_num = split_count + 1
                        for s_i in range(split_num):
                            split_angle = (math.pi * 2 / split_num) * s_i
                            bullets.append({
                                "rect": pygame.Rect(bullet["rect"].centerx, bullet["rect"].centery, 6, 6),
                                "vx": math.cos(split_angle) * 350,
                                "vy": math.sin(split_angle) * 350,
                                "pierce": 1,
                                "can_split": False, # 자식 총알은 추가 분열 금지
                                "hit_enemies": [enemy["rect"]]
                            })

                    # 폭발 데미지
                    if has_explosion:
                        explosions.append({"x": bullet["rect"].centerx, "y": bullet["rect"].centery, "radius": explosion_radius, "timer": 0.1})
                        for near_enemy in enemies:
                            if near_enemy != enemy:
                                e_dist = math.hypot(near_enemy["rect"].centerx - bullet["rect"].centerx, near_enemy["rect"].centery - bullet["rect"].centery)
                                if e_dist <= explosion_radius:
                                    near_enemy["hp"] -= 1

                    enemy["hp"] -= 1

                    # 적 처치 처리
                    if enemy["hp"] <= 0:
                        ex, ey = enemy["rect"].centerx, enemy["rect"].centery
                        is_elite = enemy["is_elite"]
                        kill_value = 5 if is_elite else 1

                        add_kills_and_check_upgrade(kill_value)
                        enemies.remove(enemy)

                        if random.random() < 0.20:
                            loot_items.append({"x": ex, "y": ey, "value": kill_value, "is_elite": is_elite, "magnetized": False})

                    if bullet["pierce"] <= 0:
                        if bullet in bullets:
                            bullets.remove(bullet)
                        break

        for exp in explosions[:]:
            exp["timer"] -= dt
            if exp["timer"] <= 0:
                explosions.remove(exp)

    # --- [화면 그리기] ---
    screen.fill((30, 30, 30))

    # 게임 영역 객체 그리기
    pygame.draw.rect(screen, (0, 255, 0), player)

    for enemy in enemies:
        color = (160, 32, 240) if enemy["is_elite"] else (255, 0, 0)
        pygame.draw.rect(screen, color, enemy["rect"])

    for bullet in bullets:
        color = (255, 255, 0) if bullet.get("can_split", False) else (255, 165, 0)
        pygame.draw.rect(screen, color, bullet["rect"])

    for potion in potions:
        pygame.draw.rect(screen, (0, 191, 255), potion)

    for loot in loot_items:
        color = (255, 105, 180) if loot["is_elite"] else (255, 215, 0)
        pygame.draw.circle(screen, color, (int(loot["x"]), int(loot["y"])), 5 if loot["is_elite"] else 3)

    for exp in explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    # 메인 게임 UI (LV 추가)
    minutes = int(play_time) // 60
    seconds = int(play_time) % 60

    if current_lang == 'KOR':
        time_str = f"시간: {minutes:02d}:{seconds:02d}"
        kill_str = f"LV.{player_level} | 처치: {kill_count} (다음: {kills_for_next_upgrade})"
        hp_str = f"체력: {int(player_hp)} / {max_hp}"
    else:
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        kill_str = f"LV.{player_level} | Kills: {kill_count} (Next: {kills_for_next_upgrade})"
        hp_str = f"HP: {int(player_hp)} / {max_hp}"

    screen.blit(font.render(time_str, True, (255, 255, 255)), (10, 10))
    screen.blit(font.render(kill_str, True, (255, 255, 255)), (10, 35))
    screen.blit(font.render(hp_str, True, (0, 255, 127)), (10, 60))

    # [한영 버튼]
    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), lang_button_rect, 2)
    btn_text = font.render(f"[{current_lang}]", True, (255, 255, 255))
    screen.blit(btn_text, (lang_button_rect.x + 15, lang_button_rect.y + 4))

    # --- [오른쪽 랭킹 패널 영역] ---
    panel_rect = pygame.Rect(GAME_WIDTH, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT)
    pygame.draw.rect(screen, (15, 15, 20), panel_rect)
    pygame.draw.line(screen, (100, 100, 100), (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2)

    rank_title_str = "랭킹 (Top 5)" if current_lang == 'KOR' else "RANKING"
    rank_title = bold_font.render(rank_title_str, True, (255, 215, 0))
    screen.blit(rank_title, (GAME_WIDTH + 20, 20))

    # 상위 5개 기록 출력
    for idx, record in enumerate(rankings[:5]):
        rk_kills, rk_time = record
        rk_m, rk_s = int(rk_time) // 60, int(rk_time) % 60
        
        rank_item_str = f"{idx+1}. {rk_kills}Kills ({rk_m:02d}:{rk_s:02d})"
        rank_text = font.render(rank_item_str, True, (220, 220, 220))
        screen.blit(rank_text, (GAME_WIDTH + 15, 60 + idx * 35))

    # --- [팝업 레이어: 업그레이드 선택] ---
    if is_upgrading and not is_game_over:
        overlay = pygame.Surface((GAME_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title_str = "레벨 업! 강화 선택" if current_lang == 'KOR' else "LEVEL UP! Choose Option"
        title_text = title_font.render(title_str, True, (255, 215, 0))
        screen.blit(title_text, (GAME_WIDTH // 2 - title_text.get_width() // 2, 120))

        for idx, option in enumerate(upgrade_options):
            color = (255, 255, 0) if idx == selected_option_index else (255, 255, 255)
            prefix = "-> " if idx == selected_option_index else "   "
            opt_str = option["text_kor"] if current_lang == 'KOR' else option["text_eng"]
            opt_text = font.render(prefix + opt_str, True, color)
            screen.blit(opt_text, (200, 240 + idx * 60))

    # --- [팝업 레이어: 게임 오버] ---
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