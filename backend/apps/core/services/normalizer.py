def normalize_dashboard(weather, risk, alerts):
    return {
        "weather": weather or {},
        "risk": risk or {},
        "alerts": alerts or [],
    }
