import json

SYSTEM_PROMPT = """You are an expert, empathetic astrologer working for astrogunluk.tr.
You are provided with a user's natal chart, today's planetary transits, and exact aspects between transits and natal planets in JSON format.
Analyze this data and write a highly personalized, insightful daily horoscope.
Your text should:
1. Be exactly one paragraph, kept under 150 words.
2. Focus on the most exact transit aspects (those with the smallest orb).
3. Use an encouraging, insightful, and professional tone in Turkish.
4. Do not include raw data or JSON, just write the horoscope directly.
"""

def get_daily_horoscope_prompt(user_name: str, natal_json: dict, transit_json: dict, aspects_json: list) -> str:
    """
    Constructs the user prompt containing formatted astrological data.
    """

    # We serialize the dicts to pretty JSON for the LLM context
    natal_str = json.dumps(natal_json, indent=2)
    transit_str = json.dumps(transit_json, indent=2)
    aspects_str = json.dumps(aspects_json, indent=2)

    prompt = f"""
Kullanıcı (User): {user_name}

Natal Harita Verisi (Natal Chart Data):
{natal_str}

Bugünkü Transit Gezegenler (Current Transits):
{transit_str}

Transitlerin Natal Haritaya Açıları (Active Transit Aspects to Natal):
{aspects_str}

Lütfen yukarıdaki astrolojik verileri kullanarak {user_name} için günlük, kişiselleştirilmiş burç yorumunu yazınız.
"""
    return prompt
