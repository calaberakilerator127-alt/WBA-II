import sys
import os
sys.path.append(os.getcwd())

import pygame
from src.engine.data_manager import DataManager
from src.engine.combat_engine import CombatManager
from src.engine.data_models import Move, StatusEffect

def run_automated_demo():
    print("\n--- [DEMO] INICIANDO PRUEBA DE SISTEMA PROFESIONAL ---")
    dm = DataManager()
    
    # 1. Registro y Login
    print("\n[PASO 1] Creando cuenta de prueba...")
    user = dm.register("TesterPro", "1234")
    if not user: 
        print("La cuenta ya existe, logueando...")
        user = dm.login("TesterPro", "1234")
    
    fighter = user.fighters[0] if user.fighters else dm.create_default_fighter("Alexander")
    if not user.fighters: user.fighters.append(fighter)
    print(f"Luchador inicial: {fighter.name} (Lv.{fighter.level})")

    # 2. Gimnasio (Entrenamiento)
    print("\n[PASO 2] Entrenando en el Gimnasio...")
    print(f"XP Actual: {fighter.xp} | Estamina: {fighter.estamina}")
    # Simular 3 sesiones de entrenamiento exitosas
    for i in range(3):
        dm.add_xp(user, fighter, 20)
        fighter.estamina -= 10
    print(f"Resultado: Nivel {fighter.level} alcanzado. Puntos de stat: {fighter.stat_points}")

    # 3. Mejora de Stats
    print("\n[PASO 3] Mejorando estadísticas...")
    print(f"Fuerza Base: {fighter.stats.fuerza}")
    dm.assign_stat(user, fighter, "fuerza")
    dm.assign_stat(user, fighter, "fuerza")
    print(f"Fuerza Final: {fighter.stats.fuerza} | Puntos restantes: {fighter.stat_points}")

    # 4. Laboratorio (Compra de Habilidad Especial)
    print("\n[PASO 4] Comprando 'Nova Carmesí' (Fuego)...")
    db = dm.load_database()
    fire_move_data = db["magic_attacks"]["Fuego"][4] # Nova Carmesí (Rank 5)
    # Ignorar costo para el demo
    user.brawels += 500 
    res = dm.buy_move(user, fighter, fire_move_data)
    print(f"Mensaje de la tienda: {res['message']}")
    print(f"Movimientos actuales: {[m.name for m in fighter.moves]}")

    # 5. Combate Real (Alexander vs Bot Metal)
    print("\n[PASO 5] Iniciando Combate de Estabilidad...")
    p2 = dm.create_default_fighter("Master Metal")
    metal_move = Move(
        name="Piel de Acero", 
        type="Magico", cost=20, base_damage=0, 
        element="Metal", 
        effect=StatusEffect(name="Espinas", type="thorns", value=0.5, duration=3)
    )
    p2.moves = [metal_move]
    
    engine = CombatManager([fighter], [p2])
    engine.initialize_combat()
    
    # Turno 1: Metal activa espinas
    print("\n--- TURNO 1 ---")
    engine.process_move(p2, fighter, p2.moves[0])
    
    # Turno 2: Alexander ataca y sufre espinas
    print("\n--- TURNO 2 ---")
    engine.process_move(fighter, p2, fighter.moves[-1]) # Usa Nova Carmesí
    
    print(f"\n[DEMO COMPLETO] Alexander HP: {int(fighter.hp)} | Master Metal HP: {int(p2.hp)}")
    print("--- PRUEBA FINALIZADA CON ÉXITO ---")

if __name__ == "__main__":
    run_automated_demo()
