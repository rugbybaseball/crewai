class SimulationEngine:
    def evaluate(self, final_plan: str, scenario: str) -> dict:
        plan_lower = str(final_plan).lower()

        
        # KPI logic
        rto_met = any(x in plan_lower for x in ["within 4 hours", "under 240 minutes", "rto met", "recovery time < 4h"])
        rpo_met = any(x in plan_lower for x in ["15 minutes", "rpo 15m", "recovery point 15"])
        services_restored = 95 if ("mobile banking" in plan_lower and "fraud detection" in plan_lower and "failover" in plan_lower) else 65
        comms_quality = 95 if ("customer notification" in plan_lower and "executive briefing" in plan_lower and "regulator" in plan_lower) else 55
        
        # Framework bonus (extra 10 points)
        framework_bonus = 10 if any(x in plan_lower for x in ["three ways", "calms", "guiding principle", "value stream", "feedback loop"]) else 0
        
        score = {
            "rto_met": rto_met,
            "rpo_met": rpo_met,
            "services_restored_pct": services_restored,
            "customer_impact_score": 100 - (100 - services_restored) * 0.6,
            "total_recovery_cost": 98000 if rto_met else 520000,
            "overall_kpi_score": round((services_restored + comms_quality) / 2 + framework_bonus, 1),
            "scenario": scenario
        }
        
        print("\n🔬 SIMULATION ENGINE EVALUATION (GOLD STANDARD):")
        for k, v in score.items():
            print(f"   {k}: {v}")
        return score