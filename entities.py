import pygame

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