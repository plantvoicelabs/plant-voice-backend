import json
import os
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

PHASE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "current_phase.json")

# Sources:
# - Walkling, P. & Reints, V. (2025). Eggplant: How to Grow It. SDSU Extension
# - Manning, J., Brainard, D., & Heilig, G. (2016). How to Grow Eggplant. MSU Extension
# - Cornell Cooperative Extension. Eggplant – Growing Information. Cornell University
# - USDA-NRCS. Plant Guide: Eggplant (Solanum melongena)
# - Clemson Extension (2023). Growing Eggplant in Home Gardens

PHASE_DATA = {
    "germination": {
        "duration_days": {"min": 7, "max": 14},
        "temperature": {
            "unit": "°C",
            "critical_low": 15,
            "low": 20,
            "optimal_min": 25,
            "optimal_max": 30,
            "high": 35,
            "critical_high": 40
        },
        "humidity": {
            "unit": "%",
            "critical_low": 30,
            "low": 50,
            "optimal_min": 70,
            "optimal_max": 90,
            "high": 95,
            "critical_high": 100
        },
        "light": {
            "unit": "lux",
            "critical_low": 0,
            "low": 0,
            "optimal_min": 0,
            "optimal_max": 10000,
            "high": 50000,
            "critical_high": 100000,
            "photoperiod_hours": 0
        },
        "soil_moisture": {
            "unit": "%",
            "critical_low": 10,
            "low": 20,
            "optimal_min": 50,
            "optimal_max": 80,
            "high": 90,
            "critical_high": 100
        },
        "description": "Seeds begin to sprout. Radicle (root) and plumule (shoot) emerge from the seed. Low light or darkness is preferred during this phase.",
        "physiological_processes": "Imbibition (water absorption) activates metabolism. Root and shoot meristems start growing. Seed reserves fuel initial growth. No photosynthesis yet.",
        "visual_indicators": "Seed coat cracks. A white root tip and then a small green shoot (cotyledons) become visible at the soil surface.",
        "transition_signs": "Emergence of the seedling above soil (cotyledons unfurling) marks end of germination and start of seedling phase.",
        "common_problems": "Poor or delayed germination if soil is too cool, too dry, or waterlogged. Fungal issues (seed rot, damping-off) if medium is overly wet.",
        "tips": "Keep soil moist but not waterlogged. Warmth is essential for germination. Darkness or low light is acceptable."
    },
    "seedling": {
        "duration_days": {"min": 14, "max": 28},
        "temperature": {
            "unit": "°C",
            "critical_low": 10,
            "low": 15,
            "optimal_min": 18,
            "optimal_max": 30,
            "high": 35,
            "critical_high": 40
        },
        "humidity": {
            "unit": "%",
            "critical_low": 30,
            "low": 50,
            "optimal_min": 70,
            "optimal_max": 90,
            "high": 95,
            "critical_high": 100
        },
        "light": {
            "unit": "lux",
            "critical_low": 0,
            "low": 1000,
            "optimal_min": 10000,
            "optimal_max": 50000,
            "high": 80000,
            "critical_high": 100000,
            "photoperiod_hours": 6
        },
        "soil_moisture": {
            "unit": "%",
            "critical_low": 10,
            "low": 20,
            "optimal_min": 50,
            "optimal_max": 70,
            "high": 90,
            "critical_high": 100
        },
        "description": "Young seedling with cotyledons and first true leaves. Delicate stem and small root system developing.",
        "physiological_processes": "Establishment of photosynthesis as true leaves develop. Rapid root growth. Seed reserves deplete, plant becomes dependent on light and nutrients.",
        "visual_indicators": "Green cotyledons followed by emergence of 2-3 small true leaves. Seedling approximately 5-10 cm tall with soft stem.",
        "transition_signs": "Seedling is ready for vegetative phase when it has 2-3 sets of true leaves and is approximately 15 cm tall. Stem begins to thicken.",
        "common_problems": "Damping-off disease if overwatered. Leggy, weak growth if light is insufficient. Chilling injury if exposed to temperatures below 15°C.",
        "tips": "Gradually increase light exposure. Avoid overwatering. Protect from cold temperatures."
    },
    "vegetative": {
        "duration_days": {"min": 30, "max": 60},
        "temperature": {
            "unit": "°C",
            "critical_low": 10,
            "low": 15,
            "optimal_min": 22,
            "optimal_max": 30,
            "high": 35,
            "critical_high": 40
        },
        "humidity": {
            "unit": "%",
            "critical_low": 30,
            "low": 40,
            "optimal_min": 60,
            "optimal_max": 70,
            "high": 80,
            "critical_high": 90
        },
        "light": {
            "unit": "lux",
            "critical_low": 5000,
            "low": 10000,
            "optimal_min": 25000,
            "optimal_max": 80000,
            "high": 100000,
            "critical_high": 120000,
            "photoperiod_hours": 8
        },
        "soil_moisture": {
            "unit": "%",
            "critical_low": 10,
            "low": 30,
            "optimal_min": 50,
            "optimal_max": 80,
            "high": 90,
            "critical_high": 100
        },
        "description": "Period of rapid vegetative growth. Plant develops extensive foliage and roots but no flowers yet.",
        "physiological_processes": "Intense photosynthesis supports leaf, stem, and root growth. High nutrient uptake especially nitrogen to build biomass. Canopy expands to capture light.",
        "visual_indicators": "Many new leaves forming and darkening in color. Plant height increases to 30-60 cm. Stems thicken and start branching. No flower buds visible.",
        "transition_signs": "Initial flower buds becoming visible at shoot tips signal the shift from vegetative to flowering phase. Usually after 6-8 weeks of growth.",
        "common_problems": "Slow stunted growth if temperatures below 15°C or nutrients lacking. Excessive foliage with few flowers if nitrogen too high. Weak elongated stems in low light.",
        "tips": "Provide full sunlight and consistent watering. Consider fertilization. Monitor for pests like flea beetles."
    },
    "flowering": {
        "duration_days": {"min": 14, "max": 28},
        "temperature": {
            "unit": "°C",
            "critical_low": 15,
            "low": 18,
            "optimal_min": 22,
            "optimal_max": 32,
            "high": 35,
            "critical_high": 40
        },
        "humidity": {
            "unit": "%",
            "critical_low": 30,
            "low": 40,
            "optimal_min": 60,
            "optimal_max": 70,
            "high": 80,
            "critical_high": 90
        },
        "light": {
            "unit": "lux",
            "critical_low": 5000,
            "low": 10000,
            "optimal_min": 25000,
            "optimal_max": 80000,
            "high": 100000,
            "critical_high": 120000,
            "photoperiod_hours": 8
        },
        "soil_moisture": {
            "unit": "%",
            "critical_low": 10,
            "low": 30,
            "optimal_min": 50,
            "optimal_max": 80,
            "high": 90,
            "critical_high": 100
        },
        "description": "Plant develops flower buds and enters reproductive stage. Purple or white star-shaped flowers bloom, typically self-pollinating.",
        "physiological_processes": "Flower formation, pollination, and fertilization occur. Plant hormones direct energy from vegetative growth to reproductive organs. Adequate water and nutrients crucial.",
        "visual_indicators": "Clusters of violet-purple flowers visible on the plant, each with five lobes and yellow centers. Some blossoms may drop off naturally if not pollinated.",
        "transition_signs": "Successful pollination causes flowers to wither and tiny green fruits begin to form at the base of the blooms inside the calyx.",
        "common_problems": "Blossom drop if temperatures outside optimal range. High humidity above 80% makes pollen sticky and hinders pollination. Drought stress can abort flowers.",
        "tips": "Maintain stable temperature. Avoid overwatering. Reduce humidity slightly if possible. Avoid excessive nitrogen."
    },
    "fruiting": {
        "duration_days": {"min": 28, "max": 42},
        "temperature": {
            "unit": "°C",
            "critical_low": 15,
            "low": 18,
            "optimal_min": 22,
            "optimal_max": 32,
            "high": 35,
            "critical_high": 40
        },
        "humidity": {
            "unit": "%",
            "critical_low": 30,
            "low": 40,
            "optimal_min": 60,
            "optimal_max": 70,
            "high": 80,
            "critical_high": 90
        },
        "light": {
            "unit": "lux",
            "critical_low": 5000,
            "low": 10000,
            "optimal_min": 25000,
            "optimal_max": 80000,
            "high": 100000,
            "critical_high": 120000,
            "photoperiod_hours": 8
        },
        "soil_moisture": {
            "unit": "%",
            "critical_low": 10,
            "low": 30,
            "optimal_min": 50,
            "optimal_max": 80,
            "high": 90,
            "critical_high": 100
        },
        "description": "Fruits develop and grow to maturity. The plant may simultaneously have new flowers, developing fruits, and mature fruits.",
        "physiological_processes": "Rapid fruit enlargement with accumulation of water, sugars, and nutrients. High demand for potassium and consistent moisture to fill fruits.",
        "visual_indicators": "Small green eggplant fruits become visible and increase in size, turning characteristic deep purple as they ripen. Skin is glossy and firm when immature.",
        "transition_signs": "Indicators of fruit maturity include glossy skin that yields slightly to pressure and vibrant coloration. Overripe fruits develop dull matte color.",
        "common_problems": "Blossom-end rot if soil moisture fluctuates widely. Sunscald from intense sun and heat. Fruit rots in prolonged high humidity.",
        "tips": "Consistent watering prevents blossom end rot. Support heavy branches. Harvest fruits when glossy and firm."
    }
}


def get_current_phase():
    """Baca fase saat ini dari file JSON"""
    try:
        if os.path.exists(PHASE_FILE):
            with open(PHASE_FILE, "r") as f:
                data = json.load(f)
                phase_name = data.get("phase", "germination")
                
                if phase_name not in PHASE_DATA:
                    phase_name = "germination"
                
                phase_info = PHASE_DATA[phase_name]
                
                return {
                    "name": phase_name,
                    "updated_at": data.get("updated_at"),
                    "duration_days": phase_info["duration_days"],
                    "temperature": phase_info["temperature"],
                    "humidity": phase_info["humidity"],
                    "light": phase_info["light"],
                    "soil_moisture": phase_info["soil_moisture"],
                    "description": phase_info["description"],
                    "physiological_processes": phase_info["physiological_processes"],
                    "visual_indicators": phase_info["visual_indicators"],
                    "transition_signs": phase_info["transition_signs"],
                    "common_problems": phase_info["common_problems"],
                    "tips": phase_info["tips"]
                }
    except Exception as e:
        logger.error(f"Failed to read phase file: {e}")
    
    phase_info = PHASE_DATA["germination"]
    return {
        "name": "germination",
        "updated_at": None,
        "notes": "",
        "duration_days": phase_info["duration_days"],
        "temperature": phase_info["temperature"],
        "humidity": phase_info["humidity"],
        "light": phase_info["light"],
        "soil_moisture": phase_info["soil_moisture"],
        "description": phase_info["description"],
        "physiological_processes": phase_info["physiological_processes"],
        "visual_indicators": phase_info["visual_indicators"],
        "transition_signs": phase_info["transition_signs"],
        "common_problems": phase_info["common_problems"],
        "tips": phase_info["tips"]
    }


def update_phase(phase_name: str):
    """Update fase ke file JSON"""
    if phase_name not in PHASE_DATA:
        raise ValueError(f"Invalid phase: {phase_name}. Valid phases: {list(PHASE_DATA.keys())}")
    
    data = {
        "phase": phase_name,
        "updated_at": datetime.now(pytz.timezone('Asia/Jakarta')).isoformat()
    }
    
    with open(PHASE_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Growth phase updated to: {phase_name}")
    return data


def analyze_sensor_for_phase(sensor_name: str, value: float):
    """
    Analisis sensor berdasarkan fase saat ini dengan klasifikasi:
    - critical_low: Plant damage may occur
    - low: Suboptimal, growth slowed
    - optimal: Within optimal range
    - high: Suboptimal, stress begins
    - critical_high: Plant damage may occur
    """
    phase = get_current_phase()
    
    # Map sensor name to phase data key
    sensor_key_map = {
        "temperature": "temperature",
        "humidity": "humidity",
        "light": "light",
        "soil_moisture": "soil_moisture"
    }
    
    sensor_key = sensor_key_map.get(sensor_name)
    if not sensor_key or sensor_key not in phase:
        return {"status": "unknown", "severity": "normal", "message": "Sensor not configured"}
    
    thresholds = phase[sensor_key]
    
    critical_low = thresholds.get("critical_low")
    low = thresholds.get("low")
    optimal_min = thresholds.get("optimal_min")
    optimal_max = thresholds.get("optimal_max")
    high = thresholds.get("high")
    critical_high = thresholds.get("critical_high")
    unit = thresholds.get("unit", "")
    
    sensor_display = sensor_name.replace("_", " ").title()
    phase_name = phase["name"]
    
    # Special handling for light during germination
    # Seeds prefer darkness, so low light (including 0) is actually optimal
    if sensor_name == "light" and phase_name == "germination":
        if value <= optimal_max:
            return {
                "status": "optimal",
                "severity": "normal",
                "message": f"Light is perfect for {phase_name} phase. Seeds prefer darkness."
            }
        elif value <= high:
            return {
                "status": "slightly_high",
                "severity": "warning",
                "message": f"Light is slightly above optimal for {phase_name} phase. Seeds prefer darkness."
            }
        else:
            return {
                "status": "high",
                "severity": "warning",
                "message": f"Light is too high for {phase_name} phase. Seeds need darkness to germinate."
            }
    
    # Determine status based on thresholds
    if value <= critical_low:
        return {
            "status": "critical_low",
            "severity": "critical",
            "message": f"{sensor_display} is critically low for {phase_name} phase. Plant damage may occur."
        }
    elif value <= low:
        return {
            "status": "low",
            "severity": "warning",
            "message": f"{sensor_display} is below optimal for {phase_name} phase. Growth may be slowed."
        }
    elif value >= critical_high:
        return {
            "status": "critical_high",
            "severity": "critical",
            "message": f"{sensor_display} is critically high for {phase_name} phase. Plant damage may occur."
        }
    elif value >= high:
        return {
            "status": "high",
            "severity": "warning",
            "message": f"{sensor_display} is above optimal for {phase_name} phase. Plant stress may begin."
        }
    elif optimal_min <= value <= optimal_max:
        return {
            "status": "optimal",
            "severity": "normal",
            "message": f"{sensor_display} is perfect for {phase_name} phase."
        }
    else:
        # Between low and optimal_min, or between optimal_max and high
        if value < optimal_min:
            return {
                "status": "slightly_low",
                "severity": "warning",
                "message": f"{sensor_display} is slightly below optimal for {phase_name} phase."
            }
        else:
            return {
                "status": "slightly_high",
                "severity": "warning",
                "message": f"{sensor_display} is slightly above optimal for {phase_name} phase."
            }


def get_all_phases():
    """Return semua fase yang tersedia"""
    return list(PHASE_DATA.keys())


def get_phase_info(phase_name: str):
    """Return informasi lengkap untuk fase tertentu"""
    if phase_name not in PHASE_DATA:
        return None
    return PHASE_DATA[phase_name]