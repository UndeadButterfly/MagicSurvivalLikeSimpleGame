import pygame
import math
import random
import config
from entities import update_enemy_size
from managers import generate_upgrade_options

class GameState:
    def __init__(self):
        self.rankings = config.load_rankings()
        self.reset()

    def reset(self):
        self.player = pygame.Rect(400, 300, 30, 30)
        self.enemies, self.bullets, self.potions = [], [], []
        self.invincibility_items = []  # [신규] 무적 아이템 목록
        self.loot_items, self.explosions, self.hit_effects, self.damage_rings = [], [], [], []

        self.spawn_timer = self.shoot_timer = self.potion_timer = 0.0
        self.invincibility_item_timer = 0.0  # [신규] 무적 아이템 스폰 타이머
        self.invincible_timer = 0.0  # [신규] 플레이어 무적 지속 시간

        self.max_hp = self.player_hp = 100
        self.hp_regen = 0
        self.move_speed = 200.0
        self.enemy_speed_mult = 1.0
        self.pierce_count = self.bullet_count = 1
        self.bullet_speed = 400.0
        self.shoot_interval = 0.5
        self.fire_directions = 1
        self.split_count = 0
        self.bonus_damage = 0

        self.lasers = []  # [신규] 활성화된 레이저 목록 관리
        self.bullet_type = 'PIERCE'
        self.base_explosion_radius = 90.0

        self.bullet_count_upgrades = self.bullet_speed_upgrades = 0
        self.split_upgrades = self.player_size_upgrades = self.bullet_damage_upgrades = 0
        self.magnet_radius = 100.0
        self.magnet_radius_sq = self.magnet_radius ** 2

        self.play_time = 0.0
        self.kill_count = 0
        self.kills_for_next_upgrade = 20
        self.player_level = 1

        self.is_upgrading = self.is_game_over = self.record_saved = False
        self.upgrade_options = []
        self.selected_option_index = 0

    def add_kills_and_check_upgrade(self, amount):
        self.kill_count += amount
        if self.kill_count >= self.kills_for_next_upgrade:
            self.kills_for_next_upgrade = int(self.kills_for_next_upgrade * 1.3)
            self.player_level += 1
            self.max_hp += 5
            self.player_hp = min(self.max_hp, self.player_hp + 5)
            self.is_upgrading = True
            for loot in self.loot_items:
                loot["magnetized"] = True
            
            # [수정] bullet_type 전달하여 맞춤 선택지 생성
            self.upgrade_options = generate_upgrade_options(
                self.bullet_count_upgrades, self.split_upgrades,
                self.bullet_speed_upgrades, self.player_size_upgrades,
                self.bullet_damage_upgrades, self.bullet_type
            )
            self.selected_option_index = 0

    def apply_upgrade(self, upgrade_ids):
        for uid in upgrade_ids:
            self.apply_single_upgrade(uid)

    def apply_single_upgrade(self, upgrade_id):
        if upgrade_id == 1: self.pierce_count += 1
        elif upgrade_id == 2 and self.bullet_count_upgrades < 5:
            # [수정] 폭발탄은 증가량이 절반 (+1), 관통탄은 (+2)
            inc = 1 if self.bullet_type == 'EXPLOSIVE' else 2
            self.bullet_count += inc
            self.bullet_count_upgrades += 1
        elif upgrade_id == 3: self.shoot_interval *= 0.9
        elif upgrade_id == 4: self.fire_directions += 1
        elif upgrade_id == 5: self.max_hp += 10; self.player_hp += 10
        elif upgrade_id == 6: self.hp_regen += 1
        elif upgrade_id == 8: self.magnet_radius *= 1.10; self.magnet_radius_sq = self.magnet_radius**2
        elif upgrade_id == 10: self.move_speed = min(500.0, self.move_speed * 1.20)
        elif upgrade_id == 11 and self.split_upgrades < 4:
            self.split_count += 1; self.split_upgrades += 1
        elif upgrade_id == 12: self.enemy_speed_mult *= 0.90
        elif upgrade_id == 13 and self.bullet_speed_upgrades < 3:
            self.bullet_speed *= 1.30; self.bullet_speed_upgrades += 1
        elif upgrade_id == 14 and self.player_size_upgrades < 2:
            old_center = self.player.center
            new_w, new_h = max(10, int(self.player.width * 0.8)), max(10, int(self.player.height * 0.8))
            self.player = pygame.Rect(0, 0, new_w, new_h)
            self.player.center = old_center
            self.player_size_upgrades += 1
        elif upgrade_id == 15 and self.bullet_damage_upgrades < 4:
            self.bonus_damage += 1
            self.bullet_damage_upgrades += 1

    def update(self, dt):
        if self.is_game_over:
            if not self.record_saved:
                stats_summary = f"HP:{self.max_hp}|SPD:{int(self.move_speed)}|INT:{self.shoot_interval:.2f}|Prc:{self.pierce_count}|Splt:{self.split_count}"
                self.rankings.append({"level": self.player_level, "kills": self.kill_count, "time": self.play_time, "stats": stats_summary})
                self.rankings.sort(key=lambda x: (x["kills"], x["time"]), reverse=True)
                config.save_rankings(self.rankings)
                self.record_saved = True
            return

        if self.is_upgrading:
            return

        self.play_time += dt
        if self.hp_regen > 0:
            self.player_hp = min(self.max_hp, self.player_hp + self.hp_regen * dt)

        # 무적 타이머 감소
        if self.invincible_timer > 0:
            self.invincible_timer = max(0.0, self.invincible_timer - dt)

        # 이동 처리
        keys = pygame.key.get_pressed()
        spd = self.move_speed * 0.5 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else self.move_speed
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        if dx or dy:
            self.player.x += dx * spd * dt
            self.player.y += dy * spd * dt
            self.player.clamp_ip(pygame.Rect(0, 0, config.GAME_WIDTH, config.SCREEN_HEIGHT))

        px_c, py_c = self.player.centerx, self.player.centery

        # --- 레이저 발사 로직 ---
        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_interval and self.enemies:
            self.shoot_timer = 0.0
            sorted_e = sorted(self.enemies, key=lambda e: (e["rect"].centerx - px_c)**2 + (e["rect"].centery - py_c)**2)[:self.fire_directions]

            # 1) 레이저탄 처리
            if self.bullet_type == 'LASER':
                base_duration = 2.0 + (self.pierce_count - 1) * 1.5
                for target in sorted_e:
                    base_angle = math.atan2(target["rect"].centery - py_c, target["rect"].centerx - px_c)
                    for b_idx in range(self.bullet_count):
                        angle = base_angle + (b_idx - (self.bullet_count - 1) / 2) * 0.15
                        self.lasers.append({
                            "is_sub": False,
                            "angle": angle,
                            "duration": base_duration,
                            "max_duration": base_duration,
                            "damage": 1 + self.bonus_damage,
                            "hit_cooldowns": {},  # 적 ID별 다단히트 쿨다운 (0.1초 마다 데미지)
                            "can_split": True
                        })
            # 2) 일반 관통탄/폭발탄 처리
            else:
                for target in sorted_e:
                    base_angle = math.atan2(target["rect"].centery - py_c, target["rect"].centerx - px_c)
                    for b_idx in range(self.bullet_count):
                        angle = base_angle + (b_idx - (self.bullet_count - 1) / 2) * 0.15
                        base_dmg = 1 + self.pierce_count + self.bonus_damage
                        self.bullets.append({"rect": pygame.Rect(px_c, py_c, 8, 8), "vx": math.cos(angle) * self.bullet_speed, "vy": math.sin(angle) * self.bullet_speed, "pierce": self.pierce_count, "damage": base_dmg, "can_split": True, "hit_enemies": set()})

        # --- 레이저 업데이트 및 충돌 검사 ---
        l_idx = 0
        while l_idx < len(self.lasers):
            laser = self.lasers[l_idx]
            laser["duration"] -= dt
            if laser["duration"] <= 0:
                self.lasers.pop(l_idx)
                continue

            # 시작점 설정 (본체 레이저는 플레이어 중심, 분열 레이저는 생성된 원본 위치)
            lx, ly = (px_c, py_c) if not laser["is_sub"] else (laser["x"], laser["y"])
            laser_length = 800.0
            ex_end = lx + math.cos(laser["angle"]) * laser_length
            ey_end = ly + math.sin(laser["angle"]) * laser_length

            # 쿨다운 감쇠
            for eid in list(laser["hit_cooldowns"].keys()):
                laser["hit_cooldowns"][eid] -= dt
                if laser["hit_cooldowns"][eid] <= 0:
                    del laser["hit_cooldowns"][eid]

            # 적 충돌 검사 (선분-선분/선분-사각 단순 거리 연산)
            e_idx = 0
            while e_idx < len(self.enemies):
                enemy = self.enemies[e_idx]
                er = enemy["rect"]
                eid = id(er)

                # 레이저 선분과 적 중심점 간의 거리 계산
                cx, cy = er.centerx, er.centery
                # 점과 선분 사이의 거리 구하기
                dx, dy = ex_end - lx, ey_end - ly
                if dx == 0 and dy == 0:
                    dist = math.hypot(cx - lx, cy - ly)
                else:
                    t = max(0, min(1, ((cx - lx) * dx + (cy - ly) * dy) / (dx*dx + dy*dy)))
                    nx, ny = lx + t * dx, ly + t * dy
                    dist = math.hypot(cx - nx, cy - ny)

                # 적의 판정 범위를 고려한 타격 (반지름 이내)
                if dist <= (er.width / 2 + 5):
                    if eid not in laser["hit_cooldowns"]:
                        laser["hit_cooldowns"][eid] = 0.15  # 0.15초마다 연속 타격
                        enemy["hp"] -= laser["damage"]
                        update_enemy_size(enemy)

                        # [분열] 피격된 적을 중심으로 지속시간 절반의 레이저 분열
                        if laser.get("can_split", False) and self.split_count > 0:
                            split_num = self.split_count
                            sub_duration = laser["duration"] * 0.5  # 본체 남은 지속시간의 절반
                            if sub_duration > 0.2:  # 최소 지속시간 보장
                                others = sorted([e for e in self.enemies if e != enemy], key=lambda e: (e["rect"].centerx - cx)**2 + (e["rect"].centery - cy)**2)
                                for s_i in range(split_num):
                                    sub_angle = math.atan2(others[s_i]["rect"].centery - cy, others[s_i]["rect"].centerx - cx) if s_i < len(others) else laser["angle"] + (s_i + 1) * 0.5
                                    self.lasers.append({
                                        "is_sub": True,
                                        "x": cx, "y": cy,
                                        "angle": sub_angle,
                                        "duration": sub_duration,
                                        "max_duration": sub_duration,
                                        "damage": max(1, laser["damage"] // 2 + self.bonus_damage),
                                        "hit_cooldowns": {},
                                        "can_split": False
                                    })

                        if enemy["hp"] <= 0:
                            val = 75 if enemy["type"] == "SPECIAL_BOSS" else (25 if enemy["type"] == "BOSS" else (5 if enemy["type"] == "ELITE" else 1))
                            self.add_kills_and_check_upgrade(val)
                            self.enemies.pop(e_idx)
                            if random.random() < 0.50 and len(self.loot_items) < 150:
                                self.loot_items.append({"x": cx, "y": cy, "value": val, "type": enemy["type"], "magnetized": False})
                        else: e_idx += 1
                    else: e_idx += 1
                else: e_idx += 1
            l_idx += 1
        
        # 적 스폰 (스페셜 보스 추가)
        spawn_interval = max(0.2, 1.0 - (self.play_time / 60.0) * 0.4)
        spawn_amount = 1 + int(self.play_time / 15.0)
        base_enemy_hp = 1 + (self.player_level - 1) * 2
        time_damage_bonus = int(self.play_time / 10.0)

        self.spawn_timer += dt
        if self.spawn_timer >= spawn_interval and len(self.enemies) < 250:
            self.spawn_timer = 0.0
            for _ in range(spawn_amount):
                angle = random.uniform(0, 6.28318)
                ex, ey = px_c + math.cos(angle) * 500, py_c + math.sin(angle) * 500
                rand_val = random.random()

                # [신규] 스페셜 보스 (1% 확률) - 체력 3배, 공격력 3배
                if rand_val < 0.01:
                    s_boss_hp = (base_enemy_hp + 9) * 15
                    self.enemies.append({"rect": pygame.Rect(ex, ey, 48, 48), "hp": s_boss_hp, "max_hp": s_boss_hp, "base_size": 48, "type": "SPECIAL_BOSS", "damage": (5 + time_damage_bonus) * 15, "vx": 0, "vy": 0})
                elif rand_val < 0.05:
                    boss_hp = (base_enemy_hp + 9) * 5
                    self.enemies.append({"rect": pygame.Rect(ex, ey, 36, 36), "hp": boss_hp, "max_hp": boss_hp, "base_size": 36, "type": "BOSS", "damage": (5 + time_damage_bonus) * 5, "vx": 0, "vy": 0})
                elif rand_val < 0.15:
                    dist = math.hypot(px_c - ex, py_c - ey)
                    vx, vy = ((px_c - ex) / dist) * 200, ((py_c - ey) / dist) * 200
                    self.enemies.append({"rect": pygame.Rect(ex, ey, 24, 24), "hp": base_enemy_hp + 9, "max_hp": base_enemy_hp + 9, "base_size": 24, "type": "ELITE", "damage": 5 + time_damage_bonus, "vx": vx, "vy": vy})
                else:
                    self.enemies.append({"rect": pygame.Rect(ex, ey, 16, 16), "hp": base_enemy_hp, "max_hp": base_enemy_hp, "base_size": 16, "type": "NORMAL", "damage": 1 + time_damage_bonus, "vx": 0, "vy": 0})

        # 포션 생성
        self.potion_timer += dt
        if self.potion_timer >= 10.0:
            self.potion_timer = 0.0
            p_rect = pygame.Rect(random.randint(50, config.GAME_WIDTH - 50), random.randint(50, config.SCREEN_HEIGHT - 50), 15, 15)
            self.potions.append({"rect": p_rect, "timer": 120.0})

        # [신규] 무적 흰색 아이템 생성 (15초 주기로 30% 확률, 제한시간 60초)
        self.invincibility_item_timer += dt
        if self.invincibility_item_timer >= 15.0:
            self.invincibility_item_timer = 0.0
            if random.random() < 0.30:
                item_rect = pygame.Rect(random.randint(50, config.GAME_WIDTH - 50), random.randint(50, config.SCREEN_HEIGHT - 50), 15, 15)
                self.invincibility_items.append({"rect": item_rect, "timer": 60.0})

        # 포션 습득 및 소멸
        p_idx = 0
        while p_idx < len(self.potions):
            potion = self.potions[p_idx]
            potion["timer"] -= dt
            if potion["timer"] <= 0:
                self.potions.pop(p_idx)
            else:
                if self.player.colliderect(potion["rect"]):
                    self.player_hp = min(self.max_hp, self.player_hp + 50)
                    self.potions.pop(p_idx)
                else:
                    p_idx += 1

        # [신규] 무적 아이템 습득 및 소멸
        inv_idx = 0
        while inv_idx < len(self.invincibility_items):
            item = self.invincibility_items[inv_idx]
            item["timer"] -= dt
            if item["timer"] <= 0:
                self.invincibility_items.pop(inv_idx)
            else:
                if self.player.colliderect(item["rect"]):
                    self.invincible_timer = 5.0  # 5초 무적 적용
                    self.invincibility_items.pop(inv_idx)
                else:
                    inv_idx += 1

        # 적 이동 및 충돌
        i = 0
        while i < len(self.enemies):
            enemy = self.enemies[i]
            er = enemy["rect"]
            if enemy["type"] == "ELITE":
                er.x += enemy["vx"] * self.enemy_speed_mult * dt
                er.y += enemy["vy"] * self.enemy_speed_mult * dt
            else:
                speed = 50 if enemy["type"] == "SPECIAL_BOSS" else (70 if enemy["type"] == "BOSS" else 100)
                dist = math.hypot(px_c - er.centerx, py_c - er.centery)
                if dist > 0:
                    er.x += ((px_c - er.centerx) / dist) * speed * self.enemy_speed_mult * dt
                    er.y += ((py_c - er.centery) / dist) * speed * self.enemy_speed_mult * dt

            if self.player.colliderect(er):
                # 무적 상태가 아닐 때만 데미지 적용
                if self.invincible_timer <= 0:
                    self.player_hp -= enemy["damage"]
                    self.damage_rings.append({"x": px_c, "y": py_c, "radius": 15, "timer": 0.2})
                    if self.player_hp <= 0:
                        self.player_hp = 0
                        self.is_game_over = True
                self.enemies.pop(i)
            else: i += 1

        # 전리품
        i = 0
        while i < len(self.loot_items):
            loot = self.loot_items[i]
            dist_sq = (px_c - loot["x"])**2 + (py_c - loot["y"])**2
            if loot.get("magnetized", False) or dist_sq <= self.magnet_radius_sq:
                dist = math.sqrt(dist_sq)
                if dist > 0:
                    sp = 600 if loot.get("magnetized", False) else 350
                    loot["x"] += ((px_c - loot["x"]) / dist) * sp * dt
                    loot["y"] += ((py_c - loot["y"]) / dist) * sp * dt
                if dist_sq < 400:
                    self.add_kills_and_check_upgrade(loot["value"])
                    self.loot_items.pop(i); continue
            i += 1

        # 발사 처리 [수정]: 절반 나눗셈 없이 bullet_count 그대로 생성
        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_interval and self.enemies:
            self.shoot_timer = 0.0
            sorted_e = sorted(self.enemies, key=lambda e: (e["rect"].centerx - px_c)**2 + (e["rect"].centery - py_c)**2)[:self.fire_directions]

            for target in sorted_e:
                base_angle = math.atan2(target["rect"].centery - py_c, target["rect"].centerx - px_c)
                for b_idx in range(self.bullet_count):
                    angle = base_angle + (b_idx - (self.bullet_count - 1) / 2) * 0.15
                    base_dmg = 1 + self.pierce_count + self.bonus_damage
                    self.bullets.append({"rect": pygame.Rect(px_c, py_c, 8, 8), "vx": math.cos(angle) * self.bullet_speed, "vy": math.sin(angle) * self.bullet_speed, "pierce": self.pierce_count, "damage": base_dmg, "can_split": True, "hit_enemies": set()})

        # 총알 충돌
        current_exp_radius = self.base_explosion_radius * (1.0 + 0.10 * self.pierce_count)
        exp_sq = current_exp_radius**2
        exp_damage = 1 + self.pierce_count + self.bonus_damage
        b_idx = 0

        while b_idx < len(self.bullets):
            bullet = self.bullets[b_idx]
            br = bullet["rect"]
            br.x += bullet["vx"] * dt; br.y += bullet["vy"] * dt

            if br.right < 0 or br.left > config.GAME_WIDTH or br.bottom < 0 or br.top > config.SCREEN_HEIGHT:
                self.bullets.pop(b_idx); continue

            bullet_destroyed = False
            e_idx = 0

            while e_idx < len(self.enemies):
                enemy = self.enemies[e_idx]
                er = enemy["rect"]

                if id(er) not in bullet["hit_enemies"] and br.colliderect(er):
                    bullet["hit_enemies"].add(id(er))
                    bx, by = br.centerx, br.centery

                    if len(self.hit_effects) < 100:
                        for _ in range(3):
                            self.hit_effects.append({"x": bx, "y": by, "vx": random.uniform(-80, 80), "vy": random.uniform(-80, 80), "timer": 0.12})

                    if bullet.get("can_split", False) and self.split_count > 0:
                        split_num = self.split_count + 1
                        others = sorted([e for e in self.enemies if e != enemy], key=lambda e: (e["rect"].centerx - bx)**2 + (e["rect"].centery - by)**2)
                        for s_i in range(split_num):
                            angle = math.atan2(others[s_i]["rect"].centery - by, others[s_i]["rect"].centerx - bx) if s_i < len(others) else (6.28318 / split_num) * s_i
                            self.bullets.append({"rect": pygame.Rect(bx, by, 6, 6), "vx": math.cos(angle) * self.bullet_speed * 0.85, "vy": math.sin(angle) * self.bullet_speed * 0.85, "pierce": 1, "damage": 1 + self.bonus_damage, "can_split": False, "hit_enemies": set(bullet["hit_enemies"])})

                    if self.bullet_type == 'EXPLOSIVE':
                        if len(self.explosions) < 30: self.explosions.append({"x": bx, "y": by, "radius": current_exp_radius, "timer": 0.1})
                        for near in self.enemies:
                            if (near["rect"].centerx - bx)**2 + (near["rect"].centery - by)**2 <= exp_sq:
                                near["hp"] -= exp_damage; update_enemy_size(near)
                        enemy["hp"] -= 1
                    else:
                        enemy["hp"] -= bullet["damage"]
                        bullet["damage"] = max(1, bullet["damage"] - 1)

                    bullet["pierce"] -= 1
                    update_enemy_size(enemy)

                    if enemy["hp"] <= 0:
                        val = 75 if enemy["type"] == "SPECIAL_BOSS" else (25 if enemy["type"] == "BOSS" else (5 if enemy["type"] == "ELITE" else 1))
                        self.add_kills_and_check_upgrade(val)
                        self.enemies.pop(e_idx)
                        if random.random() < 0.50 and len(self.loot_items) < 150:
                            self.loot_items.append({"x": bx, "y": by, "value": val, "type": enemy["type"], "magnetized": False})
                    else: e_idx += 1

                    if bullet["pierce"] <= 0: bullet_destroyed = True; break
                else: e_idx += 1

            if bullet_destroyed: self.bullets.pop(b_idx)
            else: b_idx += 1

        self.explosions = [e for e in self.explosions if e["timer"] > 0]
        for exp in self.explosions: exp["timer"] -= dt

        self.hit_effects = [e for e in self.hit_effects if e["timer"] > 0]
        for eff in self.hit_effects:
            eff["timer"] -= dt; eff["x"] += eff["vx"] * dt; eff["y"] += eff["vy"] * dt

        self.damage_rings = [r for r in self.damage_rings if r["timer"] > 0]
        for ring in self.damage_rings:
            ring["timer"] -= dt; ring["radius"] += 80 * dt

    def get_stats_dict(self):
        current_exp_radius = self.base_explosion_radius * (1.0 + 0.10 * self.pierce_count)
        return {
            "bullet_type": self.bullet_type,
            "player_hp": self.player_hp,
            "max_hp": self.max_hp,
            "hp_regen": self.hp_regen,
            "move_speed": self.move_speed,
            "player_w": self.player.width,
            "player_h": self.player.height,
            "shoot_interval": self.shoot_interval,
            "fire_directions": self.fire_directions,
            "disp_bc": self.bullet_count,  # [수정] 스탯 표시도 현재 개수 그대로 표기
            "pierce_count": self.pierce_count,
            "bonus_damage": self.bonus_damage,
            "split_count": self.split_count,
            "bullet_speed": self.bullet_speed,
            "current_exp_radius": current_exp_radius,
            "magnet_radius": self.magnet_radius,
            "enemy_speed_mult": self.enemy_speed_mult
        }