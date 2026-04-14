import sys
import os
# Add the project root to sys.path to allow imports
sys.path.append(os.getcwd())

import random
from src.engine.data_models import FighterProfile, FighterStats, Move, StatusEffect
from src.engine.combat_engine import CombatManager
from src.engine.data_manager import DataManager

def run_simulation():
    dm = DataManager()
    
    # 1. Setup Alexander (Fire)
    p1 = dm.create_default_fighter("Alexander")
    fire_move = Move(
        name="Llama Infernal", 
        type="Magico", 
        cost=20, 
        base_damage=30, 
        element="Fuego",
        effect=StatusEffect(name="Quemado", type="dot", value=10, duration=3)
    )
    p1.moves = [fire_move]
    p1.hp = 200
    p1.max_hp = 200
    p1.stats.poder = 20
    
    # 2. Setup Bot (Poison)
    p2 = dm.create_default_fighter("Bot Venenoso")
    poison_move = Move(
        name="Nube Tóxica", 
        type="Magico", 
        cost=15, 
        base_damage=5, 
        element="Veneno",
        effect=StatusEffect(name="Envenenado", type="dot", value=8, duration=5)
    )
    p2.moves = [poison_move]
    p2.hp = 250
    p2.max_hp = 250
    p2.stats.velocidad = 25 # Bot goes first
    
    # 3. Start Combat
    engine = CombatManager([p1], [p2])
    engine.initialize_combat()
    
    # 4. Run 10 Turns
    for turn in range(1, 11):
        print(f"\n--- TURNO {turn} ---")
        
        # Player 2 (Bot) Move
        engine.process_move(p2, p1, p2.moves[0])
        
        # Player 1 (Alexander) Move
        if p1.hp > 0:
            engine.process_move(p1, p2, p1.moves[0])
            
        print(f"ESTADO: Alexander HP: {int(p1.hp)} | Bot HP: {int(p2.hp)}")
        
        if p1.hp <= 0 or p2.hp <= 0:
            winner = "Alexander" if p1.hp > 0 else "Bot Venenoso"
            print(f"\n¡COMBATE TERMINADO! Ganador: {winner}")
            break

if __name__ == "__main__":
    run_simulation()
