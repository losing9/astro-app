import swisseph as swe
from datetime import datetime
import pytz
import math

class AstrologyEngine:
    def __init__(self):
        # We assume ephemeris files are in standard location or bundled with pyswisseph
        swe.set_ephe_path('')

    def _get_julian_day(self, dt: datetime) -> float:
        """Convert a UTC datetime to Julian Day."""
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
        return swe.julday(year, month, day, hour, swe.GREG_CAL)

    def _get_planet_positions(self, jd: float) -> dict:
        """Calculate positions of main planets."""
        planets = {
            'Sun': swe.SUN,
            'Moon': swe.MOON,
            'Mercury': swe.MERCURY,
            'Venus': swe.VENUS,
            'Mars': swe.MARS,
            'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN,
            'Uranus': swe.URANUS,
            'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO,
            'Node': swe.TRUE_NODE
        }

        positions = {}
        for name, pid in planets.items():
            # swe_calc_ut returns ((lon, lat, dist, speed_lon, speed_lat, speed_dist), ret_flag)
            res, _ = swe.calc_ut(jd, pid)
            lon = res[0]
            speed = res[3]

            sign_index = int(lon / 30)
            sign_names = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

            positions[name] = {
                'longitude': lon,
                'sign': sign_names[sign_index],
                'degree_in_sign': lon % 30,
                'speed': speed,
                'is_retrograde': speed < 0
            }

        return positions

    def _get_houses(self, jd: float, lat: float, lon: float) -> dict:
        """Calculate Placidus houses."""
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')

        houses = {}
        for i in range(1, 13):
            houses[f'House_{i}'] = cusps[i-1]

        return {
            'cusps': houses,
            'ascendant': ascmc[0],
            'mc': ascmc[1]
        }

    def calculate_natal_chart(self, utc_dt: datetime, lat: float, lon: float) -> dict:
        """Generate full natal chart data."""
        jd = self._get_julian_day(utc_dt)
        planets = self._get_planet_positions(jd)
        houses = self._get_houses(jd, lat, lon)

        return {
            'planets': planets,
            'houses': houses['cusps'],
            'ascendant': houses['ascendant'],
            'mc': houses['mc']
        }

    def calculate_transits(self, date_utc: datetime) -> dict:
        """Generate transit planet positions for a given day (00:00 UTC)."""
        # Ensure it's exactly 00:00 UTC
        dt_00 = datetime(date_utc.year, date_utc.month, date_utc.day, 0, 0, 0, tzinfo=pytz.UTC)
        jd = self._get_julian_day(dt_00)
        return self._get_planet_positions(jd)

    def calculate_aspects(self, natal_planets: dict, transit_planets: dict) -> list:
        """Calculate aspects between transiting planets and natal planets."""
        aspects_config = {
            'Conjunction': {'angle': 0, 'orb': 5},
            'Sextile': {'angle': 60, 'orb': 4},
            'Square': {'angle': 90, 'orb': 5},
            'Trine': {'angle': 120, 'orb': 5},
            'Opposition': {'angle': 180, 'orb': 5}
        }

        active_aspects = []

        for t_name, t_data in transit_planets.items():
            for n_name, n_data in natal_planets.items():

                # Distance calculation
                dist = abs(t_data['longitude'] - n_data['longitude'])
                if dist > 180:
                    dist = 360 - dist

                # Check for aspects
                for aspect_name, config in aspects_config.items():
                    target_angle = config['angle']
                    orb = config['orb']

                    diff = abs(dist - target_angle)
                    if diff <= orb:
                        active_aspects.append({
                            'transit_planet': t_name,
                            'natal_planet': n_name,
                            'aspect': aspect_name,
                            'orb': round(diff, 2)
                        })

        return active_aspects
