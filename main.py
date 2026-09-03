import pygame
import math
import random
import platform

# 초기화
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((800, 600))
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

font = get_korean_font(24)
title_font = get_korean_font(38)

# 데이터 객체
player = pygame.Rect(400, 300, 30, 30)
enemies = []
bullets = []
potions = []
loot_items = []    # 전리품 리스트
explosions = []    # 폭발 이펙트 리스트

spawn_timer = 0
shoot_timer = 0
potion_timer = 0

# 플레이어 능력치 & 기본 변수
max_hp = 100
player_hp = 100
hp_regen = 0
pierce_count = 1
bullet_count = 1
shoot_interval = 0.5
fire_directions = 1

# 폭발 및 자석 속성
has_explosion = False
explosion_radius = 30.0    # 기본 플레이어 크기(30) 정도의 반경
magnet_radius = 100.0       # 기본 전리품 흡수 범위

play_time = 0.0
kill_count = 0
kills_for_next_upgrade = 20

# 업그레이드 시스템 변수
is_upgrading = False
upgrade_options = []
selected_option_index = 0

# 언어 설정 변수
current_lang = 'KOR'
lang_button_rect = pygame.Rect(700, 10, 80, 30)

# 업그레이드 목록 함수 (조건부 선택지 생성을 위해 함수화)
def get_available_upgrades():
    upgrades = [
        {"id": 1, "text_kor": "1. 관통력 +1", "text_eng": "1. Pierce +1"},
        {"id": 2, "text_kor": "2. 개수 +1", "text_eng": "2. Bullet Count +1"},
        {"id": 3, "text_kor": "3. 공격 간격 -10%", "text_eng": "3. Cooldown -10%"},
        {"id": 4, "text_kor": "4. 공격 방향 +1", "text_eng": "4. Direction +1"},
        {"id": 5, "text_kor": "5. 최대 체력 +10", "text_eng": "5. Max HP +10"},
        {"id": 6, "text_kor": "6. 초당 체력회복 +1", "text_eng": "6. HP Regen +1"},
        {"id": 8, "text_kor": "8. 전리품 획득 범위 +10%", "text_eng": "8. Magnet Range +10%"}
    ]
    
    # 폭발 데미지가 없으면 폭발 데미지 추가 옵션 포함
    if not has_explosion:
        upgrades.append({"id": 7, "text_kor": "7. 폭발 데미지 추가", "text_eng": "7. Add Explosion Damage"})
    else:
        # 폭발 데미지가 있을 때만 폭발 범위 증가 옵션 포함
        upgrades.append({"id": 9, "text_kor": "9. 폭발 범위 +20%", "text_eng": "9. Explosion Area +20%"})
        
    return upgrades

def apply_upgrade(upgrade_id):
    global pierce_count, bullet_count, shoot_interval, fire_directions, max_hp, player_hp, hp_regen
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
        magnet_radius *= 1.10  # 10% 증가
    elif upgrade_id == 9:
        explosion_radius *= 1.20 # 20% 증가

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

        if is_upgrading and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                selected_option_index = (selected_option_index - 1) % len(upgrade_options)
            elif event.key == pygame.K_DOWN:
                selected_option_index = (selected_option_index + 1) % len(upgrade_options)
            elif event.key == pygame.K_SPACE:
                chosen_upgrade = upgrade_options[selected_option_index]
                apply_upgrade(chosen_upgrade["id"])
                is_upgrading = False

    # 업그레이드 일시정지 창
    if is_upgrading:
        overlay = pygame.Surface((800, 600))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        title_str = "레벨 업! 강화 선택" if current_lang == 'KOR' else "LEVEL UP! Choose Option"
        title_text = title_font.render(title_str, True, (255, 215, 0))
        screen.blit(title_text, (400 - title_text.get_width() // 2, 120))

        for idx, option in enumerate(upgrade_options):
            color = (255, 255, 0) if idx == selected_option_index else (255, 255, 255)
            prefix = "-> " if idx == selected_option_index else "   "
            opt_str = option["text_kor"] if current_lang == 'KOR' else option["text_eng"]
            opt_text = font.render(prefix + opt_str, True, color)
            screen.blit(opt_text, (200, 240 + idx * 60))

        pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
        pygame.draw.rect(screen, (255, 255, 255), lang_button_rect, 2)
        btn_text = font.render(f"[{current_lang}]", True, (255, 255, 255))
        screen.blit(btn_text, (lang_button_rect.x + 15, lang_button_rect.y + 4))

        pygame.display.flip()
        continue

    # --- 메인 게임 루프 ---
    play_time += dt

    if hp_regen > 0:
        player_hp = min(max_hp, player_hp + hp_regen * dt)

    # 2. 플레이어 이동
    keys = pygame.key.get_pressed()
    dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
    dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
    player.x += dx * 200 * dt
    player.y += dy * 200 * dt

    # 3. 적 생성 (크기 20% 축소 적용)
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
                
                # 엘리트 몹: 24x24 크기 (20% 축소)
                enemies.append({
                    "rect": pygame.Rect(ex, ey, 24, 24),
                    "hp": 10,
                    "is_elite": True,
                    "vx": vx,
                    "vy": vy
                })
            else:
                # 일반 몹: 16x16 크기 (20% 축소)
                enemies.append({
                    "rect": pygame.Rect(ex, ey, 16, 16),
                    "hp": 1,
                    "is_elite": False,
                    "vx": 0,
                    "vy": 0
                })

    # 4. 포션 생성
    potion_timer += dt
    if potion_timer >= 10.0:
        potion_timer = 0
        px = random.randint(50, 750)
        py = random.randint(50, 550)
        potions.append(pygame.Rect(px, py, 15, 15))

    # 5. 적 이동 및 데미지 (엘리트 몹 공격력 5배 설정)
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
            # 엘리트 몹은 5배의 공격력 부여
            dmg_mult = 5.0 if enemy["is_elite"] else 1.0
            player_hp -= base_enemy_damage * dmg_mult * dt
            if player_hp <= 0:
                player_hp = 0
                running = False

    # 6. 전리품 이동 및 자석 수집 처리
    for loot in loot_items[:]:
        dist_to_player = math.hypot(player.centerx - loot["x"], player.centery - loot["y"])
        # 자석 범위 내에 들어오면 플레이어 쪽으로 이동
        if dist_to_player <= magnet_radius:
            if dist_to_player > 0:
                loot["x"] += ((player.centerx - loot["x"]) / dist_to_player) * 350 * dt
                loot["y"] += ((player.centery - loot["y"]) / dist_to_player) * 350 * dt

            # 플레이어 획득 처리
            if dist_to_player < 20:
                kill_count += loot["value"]
                loot_items.remove(loot)

                # 처치 수 상승에 의한 레벨업 체크
                if kill_count >= kills_for_next_upgrade:
                    kills_for_next_upgrade *= 2
                    is_upgrading = True
                    avail = get_available_upgrades()
                    upgrade_options = random.sample(avail, min(3, len(avail)))
                    selected_option_index = 0

    # 7. 포션 획득
    for potion in potions[:]:
        if player.colliderect(potion):
            player_hp = min(max_hp, player_hp + 50)
            potions.remove(potion)

    # 8. 자동 발사
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
                        "hit_enemies": []
                    })

    # 9. 총알 이동 및 충돌 (폭발 데미지 적용 포함)
    for bullet in bullets[:]:
        bullet["rect"].x += bullet["vx"] * dt
        bullet["rect"].y += bullet["vy"] * dt

        for enemy in enemies[:]:
            if enemy["rect"] not in bullet["hit_enemies"] and bullet["rect"].colliderect(enemy["rect"]):
                bullet["hit_enemies"].append(enemy["rect"])
                bullet["pierce"] -= 1

                # 폭발 데미지 발동
                if has_explosion:
                    explosions.append({"x": bullet["rect"].centerx, "y": bullet["rect"].centery, "radius": explosion_radius, "timer": 0.1})
                    # 주변 적들에게도 피해 전달
                    for near_enemy in enemies:
                        if near_enemy != enemy:
                            e_dist = math.hypot(near_enemy["rect"].centerx - bullet["rect"].centerx, near_enemy["rect"].centery - bullet["rect"].centery)
                            if e_dist <= explosion_radius:
                                near_enemy["hp"] -= 1

                enemy["hp"] -= 1

                # 적 사망 처리 및 20% 확률 전리품 드롭
                if enemy["hp"] <= 0:
                    ex, ey = enemy["rect"].centerx, enemy["rect"].centery
                    is_elite = enemy["is_elite"]
                    enemies.remove(enemy)

                    # 20% 확률로 전리품 보석 드롭
                    if random.random() < 0.20:
                        loot_items.append({
                            "x": ex,
                            "y": ey,
                            "value": 5 if is_elite else 1,
                            "is_elite": is_elite
                        })

                if bullet["pierce"] <= 0:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    break

    # 폭발 이펙트 시각효과 타이머 업데이트
    for exp in explosions[:]:
        exp["timer"] -= dt
        if exp["timer"] <= 0:
            explosions.remove(exp)

    # 10. 화면 그리기
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (0, 255, 0), player) # 플레이어
    
    # 적 그리기
    for enemy in enemies:
        if enemy["is_elite"]:
            pygame.draw.rect(screen, (160, 32, 240), enemy["rect"]) # 엘리트 몹 (보라색)
        else:
            pygame.draw.rect(screen, (255, 0, 0), enemy["rect"])     # 일반 몹 (빨간색)
            
    # 총알 및 포션 그리기
    for bullet in bullets:
        pygame.draw.rect(screen, (255, 255, 0), bullet["rect"])
    for potion in potions:
        pygame.draw.rect(screen, (0, 191, 255), potion)

    # 전리품 드롭 아이템 그리기
    for loot in loot_items:
        color = (255, 105, 180) if loot["is_elite"] else (255, 215, 0) # 엘리트 전리품: 핑크, 일반: 금색
        pygame.draw.circle(screen, color, (int(loot["x"]), int(loot["y"])), 5 if loot["is_elite"] else 3)

    # 폭발 이펙트 그리기 (주황색 원)
    for exp in explosions:
        pygame.draw.circle(screen, (255, 140, 0), (int(exp["x"]), int(exp["y"])), int(exp["radius"]), 2)

    # 11. UI 렌더링
    minutes = int(play_time) // 60
    seconds = int(play_time) % 60

    if current_lang == 'KOR':
        time_str = f"시간: {minutes:02d}:{seconds:02d}"
        kill_str = f"처치 수: {kill_count} (다음 레벨업: {kills_for_next_upgrade})"
        hp_str = f"체력: {int(player_hp)} / {max_hp}"
    else:
        time_str = f"Time: {minutes:02d}:{seconds:02d}"
        kill_str = f"Kills: {kill_count} (Next UP: {kills_for_next_upgrade})"
        hp_str = f"HP: {int(player_hp)} / {max_hp}"

    time_text = font.render(time_str, True, (255, 255, 255))
    kill_text = font.render(kill_str, True, (255, 255, 255))
    hp_text = font.render(hp_str, True, (0, 255, 127))

    screen.blit(time_text, (10, 10))
    screen.blit(kill_text, (10, 40))
    screen.blit(hp_text, (10, 70))

    # [한영 전환 버튼]
    pygame.draw.rect(screen, (70, 70, 70), lang_button_rect)
    pygame.draw.rect(screen, (255, 255, 255), lang_button_rect, 2)
    btn_text = font.render(f"[{current_lang}]", True, (255, 255, 255))
    screen.blit(btn_text, (lang_button_rect.x + 15, lang_button_rect.y + 4))

    pygame.display.flip()

pygame.quit()