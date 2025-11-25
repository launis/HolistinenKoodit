import os

# Mallien konfiguraatio
# Mallien konfiguraatio
DEFAULT_MODEL = "gemini-2.5-flash"
FALLBACK_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-flash"]

# Vaiheet (Business Logic Definitions)
PHASES = [
    {
        "id": "phase_1",
        "name": "Vaihe 1",
        "phase_key": "VAIHE 1",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "properties": {
                        "keskusteluhistoria": {"type": "string", "example": "{{FILE: Keskusteluhistoria.pdf}}"},
                        "lopputuote": {"type": "string", "example": "{{FILE: Lopputuote.pdf}}"},
                        "reflektiodokumentti": {"type": "string", "example": "{{FILE: Reflektiodokumentti.pdf}}"}
                    }
                },
                "security_check": {
                    "type": "object",
                    "properties": {
                        "uhka_havaittu": {"type": "boolean", "example": False},
                        "adversariaalinen_simulaatio_tulos": {"type": "string", "example": "Ei havaittu uhkia."},
                        "riski_taso": {"type": "enum", "values": ["MATALA", "KESKITASO", "KORKEA"], "example": "MATALA"}
                    }
                }
            }
        }
    },
    {
        "id": "phase_2",
        "name": "Vaihe 2",
        "phase_key": "VAIHE 2",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "hypoteesit": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "example": "Väite-1"},
                            "vaite_teksti": {"type": "string", "example": "..."},
                            "loytyyko_todisteita": {"type": "boolean", "example": True}
                        }
                    }
                },
                "rag_todisteet": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "viittaa_hypoteesiin_id": {"type": "string", "example": "Väite-1"},
                            "perusteet": {"type": "string", "example": "..."},
                            "konteksti_segmentti": {"type": "string", "example": "..."},
                            "relevanssi_score": {"type": "number", "example": 9}
                        }
                    }
                }
            }
        }
    },
    {
        "id": "phase_3",
        "name": "Vaihe 3",
        "phase_key": "VAIHE 3",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "toulmin_analyysi": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "vaite_id": {"type": "string", "example": "Väite-1"},
                            "claim": {"type": "string", "example": "..."},
                            "data": {"type": "string", "example": "..."},
                            "warrant": {"type": "string", "example": "..."},
                            "backing": {"type": "string", "example": "..."}
                        }
                    }
                },
                "kognitiivinen_taso": {
                    "type": "object",
                    "properties": {
                        "bloom_taso": {"type": "string", "example": "Analyze"},
                        "strateginen_syvyys": {"type": "string", "example": "Syvällinen"}
                    }
                },
                "walton_skeema": {
                    "type": "object",
                    "properties": {
                        "tunnistettu_skeema": {"type": "string", "example": "Argument from Expert Opinion"},
                        "kriittiset_kysymykset": {"type": "array", "items": {"type": "string", "example": "Kysymys 1?"}}
                    }
                }
            }
        }
    },
    {
        "id": "phase_4",
        "name": "Vaihe 4",
        "phase_key": "VAIHE 4",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "walton_stressitesti_loydokset": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "kysymys": {"type": "string", "example": "Kysymys 1?"},
                            "kestiko_todistusaineisto": {"type": "boolean", "example": True},
                            "havainto": {"type": "string", "example": "..."}
                        }
                    }
                },
                "paattelyketjun_uskollisuus_auditointi": {
                    "type": "object",
                    "properties": {
                        "onko_post_hoc_rationalisointia": {"type": "boolean", "example": False},
                        "perustelu": {"type": "string", "example": "..."},
                        "uskollisuus_score": {"type": "string", "example": "KORKEA"}
                    }
                }
            }
        }
    },
    {
        "id": "phase_5",
        "name": "Vaihe 5",
        "phase_key": "VAIHE 5",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "kausaalinen_auditointi": {
                    "type": "object",
                    "properties": {
                        "aikajana_validi": {"type": "boolean", "example": True},
                        "havainnot": {"type": "string", "example": "..."}
                    }
                },
                "kontrafaktuaalinen_testi": {
                    "type": "object",
                    "properties": {
                        "skenaario_A_toteutunut": {"type": "string", "example": "..."},
                        "skenaario_B_simulaatio": {"type": "string", "example": "..."},
                        "uskottavuus_arvio": {"type": "string", "example": "..."}
                    }
                },
                "abduktiivinen_paatelma": {"type": "string", "example": "Aito Oivallus"}
            }
        }
    },
    {
        "id": "phase_6",
        "name": "Vaihe 6",
        "phase_key": "VAIHE 6",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "performatiivisuus_heuristiikat": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "heuristiikka": {"type": "string", "example": "Epäuskottava lineaarisuus"},
                            "lippu_nostettu": {"type": "boolean", "example": False},
                            "kuvaus": {"type": "string", "example": "..."}
                        }
                    }
                },
                "pre_mortem_analyysi": {
                    "type": "object",
                    "properties": {
                        "suoritettu": {"type": "boolean", "example": True},
                        "hiljaiset_signaalit": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "yleisarvio_aitoudesta": {"type": "string", "example": "Orgaaninen"}
            }
        }
    },
    {
        "id": "phase_7",
        "name": "Vaihe 7",
        "phase_key": "VAIHE 7",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "faktantarkistus_rfi": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "vaite": {"type": "string", "example": "..."},
                            "verifiointi_tulos": {"type": "string", "example": "Vahvistettu"},
                            "lahde_tai_paattely": {"type": "string", "example": "..."}
                        }
                    }
                },
                "eettiset_havainnot": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tyyppi": {"type": "string", "example": "Ei havaittu"},
                            "vakavuus": {"type": "string", "example": "N/A"},
                            "kuvaus": {"type": "string", "example": "..."}
                        }
                    }
                }
            }
        }
    },
    {
        "id": "phase_8",
        "name": "Vaihe 8",
        "phase_key": "VAIHE 8",
        "model": DEFAULT_MODEL,
        "schema": {
            "type": "object",
            "properties": {
                "konfliktin_ratkaisut": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "konflikti": {"type": "string", "example": "..."},
                            "ratkaisu_malli": {"type": "enum", "values": ["POPPER", "DREYFUS"], "example": "POPPER"},
                            "perustelu": {"type": "string", "example": "..."}
                        }
                    }
                },
                "mestaruus_poikkeama": {
                    "type": "object",
                    "properties": {
                        "tunnistettu": {"type": "boolean", "example": False},
                        "perustelu": {"type": "string", "example": ""}
                    }
                },
                "aitous_epaily": {
                    "type": "object",
                    "properties": {
                        "automaattinen_lippu": {"type": "boolean", "example": False},
                        "viesti_hitl:lle": {"type": "string", "example": ""}
                    }
                },
                "pisteet": {
                    "type": "object",
                    "properties": {
                        "analyysi_ja_prosessi": {
                            "type": "object",
                            "properties": {
                                "arvosana": {"type": "number", "example": 3},
                                "perustelu": {"type": "string", "example": "..."}
                            }
                        },
                        "arviointi_ja_argumentaatio": {
                            "type": "object",
                            "properties": {
                                "arvosana": {"type": "number", "example": 2},
                                "perustelu": {"type": "string", "example": "..."}
                            }
                        },
                        "synteesi_ja_luovuus": {
                            "type": "object",
                            "properties": {
                                "arvosana": {"type": "number", "example": 4},
                                "perustelu": {"type": "string", "example": "..."}
                            }
                        }
                    }
                },
                "kriittiset_havainnot_yhteenveto": {"type": "array", "items": {"type": "string", "example": "Havainto 1..."}}
            }
        }
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
