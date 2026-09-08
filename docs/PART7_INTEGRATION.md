# Part 7 – Weather to Risk Integration

This change adds the application seam required to consume normalized WeatherService data from Risk.

## Flow

Weather providers -> WeatherService -> WeatherRiskAdapter -> shared Risk feature builder -> existing Risk assessment engine.

The adapter does not call external providers directly. API credentials remain environment configuration.

## Model artifact boundary

`backend/ml/` provides a provider-independent loader, validator, and predictor interface for an offline-trained JSON artifact. The exact training-demo artifact schema is intentionally not guessed here; when the trained artifact is available, configure its path and validate it against the declared contract.

## Runtime behavior

When Weather credentials are absent, Risk keeps its existing database-derived feature sources and deterministic baseline engine. This permits setup and local development without secrets.
