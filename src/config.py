import os

# Mallien konfiguraatio
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

# Vaiheet (Business Logic Definitions)
PHASES = [
    {
        "id": "phase_1",
        "name": "Vaihe 1",
        "phase_key": "VAIHE 1",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_2",
        "name": "Vaihe 2",
        "phase_key": "VAIHE 2",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_3",
        "name": "Vaihe 3",
        "phase_key": "VAIHE 3",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_4",
        "name": "Vaihe 4",
        "phase_key": "VAIHE 4",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_5",
        "name": "Vaihe 5",
        "phase_key": "VAIHE 5",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_6",
        "name": "Vaihe 6",
        "phase_key": "VAIHE 6",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_7",
        "name": "Vaihe 7",
        "phase_key": "VAIHE 7",
        "model": DEFAULT_MODEL
    },
    {
import os

# Mallien konfiguraatio
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

# Vaiheet (Business Logic Definitions)
PHASES = [
    {
        "id": "phase_1",
        "name": "Vaihe 1",
        "phase_key": "VAIHE 1",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_2",
        "name": "Vaihe 2",
        "phase_key": "VAIHE 2",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_3",
        "name": "Vaihe 3",
        "phase_key": "VAIHE 3",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_4",
        "name": "Vaihe 4",
        "phase_key": "VAIHE 4",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_5",
        "name": "Vaihe 5",
        "phase_key": "VAIHE 5",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_6",
        "name": "Vaihe 6",
        "phase_key": "VAIHE 6",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_7",
        "name": "Vaihe 7",
        "phase_key": "VAIHE 7",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_8",
        "name": "Vaihe 8",
        "phase_key": "VAIHE 8",
        "model": DEFAULT_MODEL
    },
    {
        "id": "phase_9",
        "name": "VAIHE 9: XAI-Raportoija",
        "phase_key": "VAIHE 9",
        "model": DEFAULT_MODEL
    }
]

# Suoritusmoodit
EXECUTION_MODES = {
    "MOODI_A": ["phase_1", "phase_2", "phase_3"],
    "MOODI_B": ["phase_4", "phase_5", "phase_6", "phase_7"],
    "MOODI_C": ["phase_8", "phase_9"]
}
