import random
from typing import List, Tuple, Dict
from src.engine.data_models import FighterProfile, Move, StatusEffect

class CombatManager:
    """The brain of the turn-based combat system with support for 10 specialized elements."""
    def __init__(self, team1: List[FighterProfile], team2: List[FighterProfile]):
        self.team1 = team1
        self.team2 = team2
        self.turn_queue = []
        self.current_turn_idx = 0
        self.combat_history = [] 

    def initialize_combat(self, rounds=1, is_deathmatch=False):
        """Prepares the combat with multiple fighters and specific rules."""
        self.rounds = rounds
        self.current_round = 1
        self.is_deathmatch = is_deathmatch
        
        # Fresh start for teams
        self.active_f1_idx = 0
        self.active_f2_idx = 0
        
        for team in [self.team1, self.team2]:
            for f in team:
                f.status_effects = []
                if not self.is_deathmatch:
                    f.hp = f.max_hp
                    f.estamina = f.stats.estamina_max
                    f.energia = f.stats.energia_max
        
        self.combat_history = []
        # Track which fighters have participated/won for XP
        self.participation_p1 = set() 
        self.participation_p2 = set()
        
        print(f"\n--- COMBATE INICIADO: {rounds} RONDAS ---")

    def process_start_of_turn_effects(self, fighter: FighterProfile):
        """Processes Poison, Burn, Regen, etc. returns False if turn is skipped (Freeze)."""
        skip_turn = False
        remaining_effects = []
        
        for effect in fighter.status_effects:
            # 1. Damage Over Time
            if effect.type == "dot":
                damage = effect.value * effect.stacks
                fighter.hp -= damage
                print(f"[COMBAT] {fighter.name} sufre {int(damage)} de daño por {effect.name} (x{effect.stacks})")
            
            # 2. Regeneration
            elif effect.type == "regen":
                regen_val = effect.value * effect.stacks
                fighter.estamina = min(fighter.stats.estamina_max, fighter.estamina + regen_val)
                fighter.energia = min(fighter.stats.energia_max, fighter.energia + regen_val)
                print(f"[COMBAT] {fighter.name} regenera energía por {effect.name}")

            # 3. Crowd Control
            elif effect.type == "stun":
                if random.random() < effect.value:
                    skip_turn = True
                    print(f"[COMBAT] ¡{fighter.name} está {effect.name} y no puede actuar!")
            
            # Duration Tick
            effect.duration -= 1
            if effect.duration > 0:
                remaining_effects.append(effect)
            else:
                print(f"[COMBAT] El efecto {effect.name} de {fighter.name} ha terminado.")
        
        fighter.status_effects = remaining_effects
        return not skip_turn

    def apply_status_effect(self, target: FighterProfile, effect_template: StatusEffect):
        """Adds a new effect or stacks an existing one up to 5."""
        if not effect_template: return
        
        existing = next((e for e in target.status_effects if e.name == effect_template.name), None)
        if existing:
            if existing.stacks < 5:
                existing.stacks += 1
                existing.duration = max(existing.duration, effect_template.duration)
                print(f"[COMBAT] ¡{target.name} ahora tiene {existing.name} x{existing.stacks}!")
        else:
            # Create a copy so we don't modify the database move
            new_effect = effect_template.model_copy()
            target.status_effects.append(new_effect)
            print(f"[COMBAT] ¡{target.name} ha sido {new_effect.name}!")

    def calculate_damage(self, attacker: FighterProfile, defender: FighterProfile, move: Move) -> dict:
        """Calculates damage factoring in Blind, Shield, and specialization."""
        # 1. Hit Probability (Check for Blind)
        base_acc = 0.9
        blind_effect = next((e for e in attacker.status_effects if e.name == "Cegado"), None)
        if blind_effect:
            base_acc -= blind_effect.value
        
        is_hit = random.random() < base_acc
        if not is_hit:
            print(f"[COMBAT] ¡{attacker.name} FALLÓ el ataque!")
            return {"damage": 0, "is_hit": False, "is_crit": False}

        # 2. Base Damage
        stat_val = attacker.stats.fuerza if move.type == "Fisico" else attacker.stats.poder
        damage = (move.base_damage + stat_val) * move.multiplier
        
        # 3. Resistances & Shields
        shield_effect = next((e for e in defender.status_effects if e.type == "buff" and "Escudo" in e.name), None)
        if shield_effect:
            damage *= (1.0 - shield_effect.value)
            print(f"[COMBAT] El Escudo de {defender.name} absorbe parte del daño.")

        if move.type == "Magico" and move.element in defender.stats.resistencias_elementales:
            res = min(0.4, defender.stats.resistencias_elementales[move.element])
            damage *= (1.0 - res)
        elif move.type == "Fisico":
             damage -= defender.stats.resistencia_fisica
        
        damage = max(1, damage)
        
        # 4. Critical Logic
        is_crit = random.random() < (0.05 + attacker.hype * 0.5)
        if is_crit:
            damage *= 2.0
            print(f"[COMBAT] ¡CRÍTICO! {attacker.name} golpea con fuerza letal.")

        return {"damage": int(damage), "is_hit": True, "is_crit": is_crit}

    def process_defend(self, fighter: FighterProfile):
        """Standard defense action: grants shield and restores resources."""
        self.apply_status_effect(fighter, StatusEffect(
            name="Protegido", 
            type="buff", 
            value=0.5, 
            duration=1
        ))
        # Restore 15% of max resources
        fighter.estamina = min(fighter.stats.estamina_max, fighter.estamina + fighter.stats.estamina_max * 0.15)
        fighter.energia = min(fighter.stats.energia_max, fighter.energia + fighter.stats.energia_max * 0.15)
        print(f"[COMBAT] {fighter.name} se pone en guardia y recupera energías.")

    def process_move(self, attacker: FighterProfile, defender: FighterProfile, move: Move):
        """Executes a specialized move, applying status effects even if damage is 0."""
        # 1. Start of Turn Processing (Check for Stuns/DOTs)
        if not self.process_start_of_turn_effects(attacker):
            return {"damage": 0, "is_hit": False, "skip": True}

        # 2. Resource Check
        cost_resource = attacker.estamina if move.type == "Fisico" else attacker.energia
        damage_mult = 1.0
        if cost_resource < move.cost:
            print(f"[COMBAT] {attacker.name} agotado. Penalización de daño.")
            damage_mult = 0.2
        else:
            if move.type == "Fisico": attacker.estamina -= move.cost
            else: attacker.energia -= move.cost
        
        res = self.calculate_damage(attacker, defender, move)
        final_damage = int(res["damage"] * damage_mult)
        
        # 3. Apply Damage
        defender.hp -= final_damage
        if final_damage > 0:
            print(f"[COMBAT] {attacker.name} usa {move.name} y causa {final_damage} de daño.")
        elif res["is_hit"]:
            print(f"[COMBAT] {attacker.name} usa {move.name}.")

        # 4. Apply Effects (Always, even if 0 damage)
        if move.effect:
            target = attacker if move.effect.type in ["buff", "regen"] else defender
            self.apply_status_effect(target, move.effect)
        
        # 5. Specialized Interaction (Lifesteal / Thorns)
        lifesteal = next((e for e in attacker.status_effects if e.type == "lifesteal"), None)
        if lifesteal and final_damage > 0:
            heal = int(final_damage * lifesteal.value)
            attacker.hp = min(attacker.max_hp, attacker.hp + heal)
            print(f"[COMBAT] {attacker.name} drena {heal} de vida.")

        thorns = next((e for e in defender.status_effects if e.type == "thorns"), None)
        if thorns and move.type == "Fisico" and final_damage > 0:
            rebound = int(final_damage * thorns.value)
            attacker.hp -= rebound
            print(f"[COMBAT] ¡{attacker.name} se hiere con las espinas! (-{rebound})")

        return res

    def distribute_xp_to_fighters(self, stats_p1: dict):
        """
        Calculates and applies individual XP to every participating fighter.
        stats_p1: {"damage": total_dealt, "winner": True/False}
        """
        # Base XP: 20 per fight + participation bonus
        base_xp = 25 if stats_p1["winner"] else 10
        
        # Every fighter who was 'active' at some point gets XP
        for idx in self.participation_p1:
            if idx < len(self.team1):
                f = self.team1[idx]
                # Actually we need the DataManager to save the XP
                # But since the FighterProfile object is shared with the Account, 
                # we can just modify it and ensure it's saved.
                xp_gain = base_xp + (stats_p1["damage"] // 5) # Damage contribution
                f.xp += xp_gain
                print(f"[PROGRESSION] {f.name} ganó {xp_gain} XP.")
                # We don't handle level-up logic here (it's in DataManager), 
                # but we'll assume the BattleState or StateManager triggers it later.
