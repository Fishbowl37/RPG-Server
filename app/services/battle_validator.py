from datetime import datetime, timezone
from app.schemas.progression import BattleLog, MobConfig


class BattleValidator:
    """
    Validates battle logs submitted by clients.
    
    This is a critical anti-cheat component. We verify that the
    battle results are plausible given the stage configuration
    and player stats.
    """
    
    # Validation thresholds
    MIN_BATTLE_DURATION_MS = 5000   # Minimum 5 seconds
    MAX_BATTLE_DURATION_MS = 600000  # Maximum 10 minutes
    
    # Damage thresholds per player power
    MIN_DAMAGE_PER_POWER = 0.5  # At minimum, deal 0.5 damage per power
    MAX_DAMAGE_PER_POWER = 50   # At maximum, deal 50 damage per power (crits, etc.)
    
    @classmethod
    def validate_battle_log(
        cls,
        battle_log: BattleLog,
        expected_chapter: int,
        expected_stage: int,
        expected_mobs: list[MobConfig],
        session_created_at: datetime
    ) -> tuple[bool, str | None]:
        """
        Validate a battle log.
        
        Returns (is_valid, error_message).
        """
        # 1. Verify chapter/stage match
        if battle_log.chapter != expected_chapter or battle_log.stage != expected_stage:
            return False, "Chapter/stage mismatch"
        
        # 2. Verify battle duration is reasonable
        duration = battle_log.battle_end_time - battle_log.battle_start_time
        if duration < cls.MIN_BATTLE_DURATION_MS:
            return False, f"Battle too short ({duration}ms)"
        if duration > cls.MAX_BATTLE_DURATION_MS:
            return False, f"Battle too long ({duration}ms)"
        
        # 3. Verify battle started after session was created
        session_ts = int(session_created_at.timestamp() * 1000)
        if battle_log.battle_start_time < session_ts - 5000:  # 5s grace
            return False, "Battle started before session was created"
        
        # 4. Verify mob kill count matches expected
        expected_mob_count = len(expected_mobs)
        actual_kills = battle_log.stats.mobs_killed
        if actual_kills != expected_mob_count:
            return False, f"Kill count mismatch: expected {expected_mob_count}, got {actual_kills}"
        
        # 5. Verify damage is plausible for player power
        min_expected_damage = battle_log.player_power * cls.MIN_DAMAGE_PER_POWER
        max_expected_damage = battle_log.player_power * cls.MAX_DAMAGE_PER_POWER
        
        total_mob_health = sum(m.health for m in expected_mobs)
        
        # Player must have dealt enough damage to kill all mobs
        if battle_log.stats.total_damage_dealt < total_mob_health * 0.5:
            # Allow some grace for overkill, life steal, etc.
            return False, "Damage dealt too low for mob health"
        
        # Damage shouldn't be impossibly high
        if battle_log.stats.total_damage_dealt > max_expected_damage * 100:
            return False, "Damage dealt suspiciously high"
        
        # 6. Verify battle duration matches reported stats
        reported_duration = battle_log.stats.duration_ms
        if abs(reported_duration - duration) > 1000:  # 1s tolerance
            return False, "Duration mismatch in stats"
        
        # 7. Optional: Verify checksum if provided
        # In a full implementation, you'd verify a cryptographic checksum
        # of the battle events to detect tampering
        
        return True, None
    
    @classmethod
    def calculate_suspicion_score(
        cls,
        battle_log: BattleLog,
        expected_mobs: list[MobConfig]
    ) -> float:
        """
        Calculate a suspicion score for flagging potential cheaters.
        
        Returns a score from 0 (normal) to 1 (very suspicious).
        This can be used for logging and later review.
        """
        score = 0.0
        
        # Factor 1: Damage per second
        duration_s = battle_log.stats.duration_ms / 1000
        dps = battle_log.stats.total_damage_dealt / duration_s if duration_s > 0 else 0
        expected_dps = battle_log.player_power * 2  # Rough estimate
        
        if dps > expected_dps * 5:
            score += 0.3
        
        # Factor 2: Damage taken
        total_mob_damage = sum(m.damage for m in expected_mobs) * 10  # Rough estimate of potential damage
        if battle_log.stats.total_damage_received < total_mob_damage * 0.1:
            # Taking very little damage is suspicious
            score += 0.2
        
        # Factor 3: Battle speed
        min_reasonable_time = len(expected_mobs) * 3000  # 3s per mob minimum
        if battle_log.stats.duration_ms < min_reasonable_time:
            score += 0.3
        
        # Factor 4: Kill timestamps
        if battle_log.mob_kills:
            # Check if kills are evenly spaced (bot behavior)
            timestamps = [k.timestamp for k in battle_log.mob_kills]
            if len(timestamps) > 2:
                intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
                avg_interval = sum(intervals) / len(intervals)
                variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
                
                # Very low variance suggests automated play
                if variance < 100:  # Less than 100ms variance
                    score += 0.2
        
        return min(score, 1.0)

