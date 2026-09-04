"""Smart Home Domain Graph — builds a scoped knowledge graph from Home Assistant data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from packages.schemas.entities import Entity, EntityType, Relation, RelationType

_kg_app = Path(__file__).resolve().parent
if str(_kg_app) not in sys.path:
    sys.path.insert(0, str(_kg_app))

from entity_store import EntityStore
from relation_store import RelationStore

DOMAIN = "smart_home"
TENANT_ID = "default"
USER_ID = "jeff"

ROOM_CODES: dict[str, str] = {
    "core": "Open Plan",
    "alpha": "Bedroom 1",
    "beta": "Bedroom 2",
    "chaos": "Laundry/Utility",
    "splash": "Rear Bathroom",
    "throne": "Ensuite Bathroom",
    "pass": "Hallway",
}

AREA_MAP: dict[str, dict[str, Any]] = {
    "bedroom": {
        "name": "Bedroom",
        "code": "alpha",
        "type": "bedroom",
        "aliases": ["Bedroom (Alpha)", "Bedroom 1", "Alpha"],
    },
    "alpha_bedroom": {
        "name": "Bedroom (Alpha)",
        "code": "alpha",
        "type": "bedroom",
        "aliases": ["Alpha Bedroom", "Bedroom 1"],
    },
    "beta_bedroom": {
        "name": "Beta Bedroom",
        "code": "beta",
        "type": "bedroom",
        "aliases": ["Spare Bedroom", "Bedroom 2", "Guest Bedroom", "Rear Bedroom"],
    },
    "beta_bedroom_2": {
        "name": "Beta Bedroom",
        "code": "beta",
        "type": "bedroom",
        "aliases": ["Spare Bedroom", "Bedroom 2"],
    },
    "core": {
        "name": "Openplan (Core)",
        "code": "core",
        "type": "open_plan",
        "aliases": ["Core", "Open Plan", "Living/Dining/Kitchen"],
    },
    "core_kitchen": {
        "name": "Core Kitchen",
        "code": "core",
        "type": "kitchen",
        "aliases": ["Kitchen"],
    },
    "living_room": {
        "name": "Living Room",
        "code": "core",
        "type": "living",
        "aliases": ["Lounge"],
    },
    "living_room_2": {
        "name": "Living Room (2)",
        "code": "core",
        "type": "living",
        "aliases": [],
    },
    "openplan": {
        "name": "Openplan",
        "code": "core",
        "type": "open_plan",
        "aliases": ["Core"],
    },
    "dining": {
        "name": "Dining",
        "code": "core",
        "type": "dining",
        "aliases": [],
    },
    "pass": {
        "name": "Hallway (Pass)",
        "code": "pass",
        "type": "hallway",
        "aliases": ["Hallway", "Pass"],
    },
    "throne_bathroom": {
        "name": "Ensuite (Throne) Bathroom",
        "code": "throne",
        "type": "bathroom_ensuite",
        "aliases": ["Throne", "Ensuite", "My Bathroom"],
    },
    "my_bathroom": {
        "name": "My Bathroom",
        "code": "throne",
        "type": "bathroom_ensuite",
        "aliases": ["Ensuite", "Throne"],
    },
    "secondary_bathroom": {
        "name": "Secondary Bathroom",
        "code": "splash",
        "type": "bathroom_rear",
        "aliases": ["Splash", "Rear Bathroom", "Guest Bathroom"],
    },
    "chaos": {
        "name": "Laundry/Utilities",
        "code": "chaos",
        "type": "utility",
        "aliases": ["Chaos", "Laundry"],
    },
    "laundry_room": {
        "name": "Laundry Room",
        "code": "chaos",
        "type": "utility",
        "aliases": ["Chaos"],
    },
    "attic": {
        "name": "Attic",
        "code": None,
        "type": "storage",
        "aliases": [],
    },
    "storage": {
        "name": "Storage",
        "code": None,
        "type": "storage",
        "aliases": [],
    },
    "parking": {
        "name": "Parking",
        "code": None,
        "type": "external",
        "aliases": [],
    },
    "default": {
        "name": "Default",
        "code": None,
        "type": "system",
        "aliases": [],
    },
}

ADJACENCY: list[tuple[str, str]] = [
    ("core", "pass"),
    ("alpha_bedroom", "pass"),
    ("alpha_bedroom", "throne_bathroom"),
    ("beta_bedroom", "pass"),
    ("secondary_bathroom", "pass"),
    ("chaos", "pass"),
    ("core", "core_kitchen"),
    ("core", "living_room"),
    ("core", "dining"),
]

ZONE_DEFS: dict[str, list[dict[str, str]]] = {
    "core": [
        {"id": "core_ne", "name": "Core NE", "description": "A1-B by balcony"},
        {"id": "core_nw", "name": "Core NW", "description": "A-A1 by kitchen"},
        {"id": "core_se", "name": "Core SE", "description": "Angled corner where south meets window stretch"},
        {"id": "core_sw", "name": "Core SW", "description": "South green wall + kitchen/radiator zone"},
    ],
    "alpha_bedroom": [
        {"id": "alpha_bed", "name": "Alpha Bed Zone", "description": "Bed area"},
        {"id": "alpha_flex", "name": "Alpha Flex Zone", "description": "Flexible/desk area"},
    ],
    "beta_bedroom": [
        {"id": "beta_bed", "name": "Beta Bed Zone", "description": "Bed area"},
        {"id": "beta_flex", "name": "Beta Flex Zone", "description": "Flexible area"},
    ],
    "pass": [
        {"id": "vault", "name": "Vault", "description": "Storage alcove"},
        {"id": "alpha_pass", "name": "Alpha Pass", "description": "Pass section near Alpha"},
        {"id": "beta_pass", "name": "Beta Pass", "description": "Pass section near Beta"},
        {"id": "splash_pass", "name": "Splash Pass", "description": "Pass section near Splash"},
        {"id": "chaos_pass", "name": "Chaos Pass", "description": "Pass section near Chaos"},
    ],
}

INTEGRATIONS: list[dict[str, Any]] = [
    {"id": "hue", "name": "Philips Hue", "domain": "hue", "type": "lighting"},
    {"id": "apple_tv", "name": "Apple TV", "domain": "apple_tv", "type": "media"},
    {"id": "matter", "name": "Matter", "domain": "matter", "type": "protocol"},
    {"id": "mqtt", "name": "MQTT", "domain": "mqtt", "type": "protocol"},
    {"id": "cast", "name": "Google Cast", "domain": "cast", "type": "media"},
    {"id": "vesync", "name": "VeSync", "domain": "vesync", "type": "appliance"},
    {"id": "withings", "name": "Withings", "domain": "withings", "type": "health"},
    {"id": "mobile_app", "name": "Mobile App", "domain": "mobile_app", "type": "companion"},
    {"id": "speedtestdotnet", "name": "SpeedTest", "domain": "speedtestdotnet", "type": "network"},
]

HUBS: list[dict[str, Any]] = [
    {"id": "hue_bridge", "name": "Hue Bridge Pro", "manufacturer": "Signify", "model": "Hue Bridge", "protocol": "zigbee", "area": "chaos"},
    {"id": "aqara_hub_m3", "name": "Aqara Hub M3", "manufacturer": "Aqara", "model": "Hub M3", "protocol": "zigbee/matter", "area": None},
]

DEVICES: list[dict[str, Any]] = [
    # Bedroom (Alpha)
    {"id": "alpha_ceiling_light_3", "name": "Alphabed Ceiling Light.3", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.alphabed_ceiling_light_3", "integration": "hue"},
    {"id": "alpha_ceiling_light_4", "name": "Alpha Ceiling Light.4", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.alpha_ceiling_light_4", "integration": "hue"},
    {"id": "alpha_ceiling_light_5", "name": "Alphabed Ceiling Light.5", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.alphabed_ceiling_light_5", "integration": "hue"},
    {"id": "alpha_ceiling_light_5_2", "name": "Alphabed Ceiling Light.5 (2)", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.alphabed_ceiling_light_5_2", "integration": "hue"},
    {"id": "alpha_ceiling_light_6", "name": "Alpha Ceiling Light.6", "type": EntityType.LIGHT, "area": "bedroom", "manufacturer": "Signify", "model": "Hue Essential spot", "entity_id": "light.alpha_ceiling_light_6", "integration": "hue"},
    {"id": "alphadoor_ceiling_light_6", "name": "Alphadoor Ceiling Light.6", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.alphadoor_ceiling_light_6", "integration": "hue"},
    {"id": "core_ceiling_3", "name": "Core Ceiling.3 (Alpha closet)", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.core_ceiling_3", "integration": "hue"},
    {"id": "nymane_3_spot_lamp", "name": "Nymane 3-spot Lamp - Low", "type": EntityType.LIGHT, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue Essential spot", "entity_id": "light.nymane_3_spot_lamp_low", "integration": "hue"},
    {"id": "alpha_gradient_tube", "name": "Alpha Gradient Light-tube.1", "type": EntityType.LIGHT, "area": "bedroom", "manufacturer": "Signify", "model": "Play gradient tube", "entity_id": "light.alpha_gradient_light_tube_1", "integration": "hue"},
    {"id": "right_bedside_lamp", "name": "Right Bedside Lamp", "type": EntityType.LIGHT, "area": "bedroom", "manufacturer": "Signify", "model": "Hue color candle", "entity_id": "light.right_bedside_lamp", "integration": "hue"},
    {"id": "ikea_skytrax", "name": "Ikea Skytrax Light", "type": EntityType.LIGHT, "area": "bedroom", "manufacturer": "IKEA", "model": "Dimmable light", "entity_id": "light.ikea_skytrax_light", "integration": "hue"},
    {"id": "alpha_dial_switch", "name": "Alpha Bedroom Dial Switch", "type": EntityType.SWITCH, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue tap dial switch", "entity_id": "event.alpha_bedroom_dial_switch_button_1", "integration": "hue"},
    {"id": "alpha_smart_button", "name": "Alpha Hue Smart Button", "type": EntityType.SWITCH, "area": "alpha_bedroom", "manufacturer": "Signify", "model": "Hue smart button", "entity_id": "event.alpha_hue_smart_button_button_1", "integration": "hue"},
    {"id": "withings_sleep", "name": "Withings Sleep Sensor", "type": EntityType.SENSOR, "area": "alpha_bedroom", "manufacturer": "Withings", "model": "Sleep Mat", "entity_id": "binary_sensor.withings_in_bed", "integration": "withings"},
    {"id": "core_300s", "name": "Core 300S Air Purifier", "type": EntityType.CLIMATE, "area": "bedroom", "manufacturer": "VeSync", "model": "Core300S", "entity_id": "fan.core_300s", "integration": "vesync"},
    {"id": "orange_homepod", "name": "Orange HomePod Mini", "type": EntityType.MEDIA_PLAYER, "area": "bedroom", "manufacturer": "Apple", "model": "HomePod Mini", "entity_id": "media_player.orange_homepod_mini", "integration": "apple_tv"},

    # Openplan (Core)
    {"id": "core_ceiling_1", "name": "Core Ceiling Light.1", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_1", "integration": "hue"},
    {"id": "core_ceiling_2", "name": "Core Ceiling Light.2", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_2", "integration": "hue"},
    {"id": "core_ceiling_4", "name": "Core Ceiling Light.4", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_4", "integration": "hue"},
    {"id": "core_ceiling_5", "name": "Core Ceiling Light.5", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_5", "integration": "hue"},
    {"id": "core_ceiling_5_2", "name": "Core Ceiling Light.5 (south)", "type": EntityType.LIGHT, "area": "living_room", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_5_2", "integration": "hue"},
    {"id": "core_ceiling_6", "name": "Core Ceiling Light.6", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_6", "integration": "hue"},
    {"id": "core_ceiling_7", "name": "Core Ceiling Light.7", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_7", "integration": "hue"},
    {"id": "core_ceiling_8", "name": "Core Ceiling Light.8", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color spot", "entity_id": "light.core_ceiling_light_8", "integration": "hue"},
    {"id": "core_ceiling_9", "name": "Core Ceiling Light.9 (kitchen fridge)", "type": EntityType.LIGHT, "area": "core_kitchen", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.core_ceiling_light_9", "integration": "hue"},
    {"id": "core_ceiling_10", "name": "Core Ceiling Light.10 (kitchen sink)", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.core_ceiling_light_10", "integration": "hue"},
    {"id": "monica_vibelucci", "name": "Monica Vibelucci Arc Floor Lamp", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue lightguide bulb", "entity_id": "light.core_statement_arc_floor_lamp_monica_vibelucci", "integration": "hue"},
    {"id": "signe_floor_1", "name": "Hue Signe Gradient Floor Lamp.1", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Signe gradient floor", "entity_id": "light.hue_signe_white_gradient_floor_lamp_1", "integration": "hue"},
    {"id": "signe_floor_2", "name": "Signe Gradient Floor 1", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Signe gradient floor", "entity_id": "light.signe_gradient_floor_1", "integration": "hue"},
    {"id": "klasnick_table_lamp", "name": "Klasnick Beige Table Lamp", "type": EntityType.LIGHT, "area": "core", "manufacturer": "Signify", "model": "Hue color candle", "entity_id": "light.klasnick_beige_table_lamp_with_e14_hue_colour", "integration": "hue"},
    {"id": "beige_ola_spotlight", "name": "Beige Ola Spotlight Lamp", "type": EntityType.LIGHT, "area": "living_room", "manufacturer": "Signify", "model": "Hue color lamp", "entity_id": "light.beige_ola_spotlight_lamp", "integration": "hue"},
    {"id": "core_tap_dial", "name": "Core Tap Dial Light Switch", "type": EntityType.SWITCH, "area": "core", "manufacturer": "Signify", "model": "Hue tap dial switch", "entity_id": "event.core_tap_dial_light_switch_button_1", "integration": "hue"},
    {"id": "core_lounge_homepod_1", "name": "Core Lounge HomePod", "type": EntityType.MEDIA_PLAYER, "area": "living_room", "manufacturer": "Apple", "model": "HomePod (gen 2)", "entity_id": "media_player.core_lounge_homepod", "integration": "apple_tv"},
    {"id": "core_lounge_homepod_2", "name": "Core Lounge HomePod (2)", "type": EntityType.MEDIA_PLAYER, "area": "living_room", "manufacturer": "Apple", "model": "HomePod (gen 2)", "entity_id": "media_player.core_lounge_homepod_2", "integration": "apple_tv"},
    {"id": "lounge_apple_tv", "name": "Lounge Apple TV (Wired)", "type": EntityType.MEDIA_PLAYER, "area": "living_room", "manufacturer": "Apple", "model": "Apple TV 4K (gen 3)", "entity_id": "media_player.lounge_apple_tv_wired", "integration": "apple_tv"},

    # Hallway (Pass)
    {"id": "pass_ceiling_1", "name": "Pass Ceiling Light.1", "type": EntityType.LIGHT, "area": "pass", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.pass_ceiling_light_1", "integration": "hue"},
    {"id": "pass_ceiling_1_2", "name": "Pass Ceiling Light.1 (2)", "type": EntityType.LIGHT, "area": "pass", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.pass_ceiling_light_1_2", "integration": "hue"},
    {"id": "pass_ceiling_2", "name": "Pass Ceiling Light.2", "type": EntityType.LIGHT, "area": "pass", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.pass_ceiling_light_2", "integration": "hue"},
    {"id": "pass_ceiling_4", "name": "Pass Ceiling Light.4", "type": EntityType.LIGHT, "area": "pass", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.pass_ceiling_light_4", "integration": "hue"},
    {"id": "pass_ceiling_5", "name": "Pass Ceiling Light.5", "type": EntityType.LIGHT, "area": "pass", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.pass_ceiling_light_5", "integration": "hue"},
    {"id": "hallway_dimmer", "name": "Hallway Dimmer Switch", "type": EntityType.SWITCH, "area": "pass", "manufacturer": "Signify", "model": "Hue dimmer switch", "entity_id": "event.hallway_dimmer_switch_button_1", "integration": "hue"},

    # Ensuite (Throne) Bathroom
    {"id": "throne_ceiling_2", "name": "Throne Ceiling above Shower Door", "type": EntityType.LIGHT, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.throne_ceiling_light_2", "integration": "hue"},
    {"id": "throne_ceiling_3", "name": "Throne Ceiling Light.3", "type": EntityType.LIGHT, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.throne_ceiling_light_3", "integration": "hue"},
    {"id": "throne_ceiling_3_2", "name": "Throne Ceiling above Sink", "type": EntityType.LIGHT, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.throne_ceiling_light_3_2", "integration": "hue"},
    {"id": "throne_ceiling_4", "name": "Throne Ceiling above Door", "type": EntityType.LIGHT, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.throne_ceiling_light_4", "integration": "hue"},
    {"id": "throne_dimmer", "name": "Bathroom Dimmer Switch", "type": EntityType.SWITCH, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue dimmer switch", "entity_id": "event.bathroom_dimmer_switch_button_1", "integration": "hue"},
    {"id": "throne_motion", "name": "Throne Motion Sensor", "type": EntityType.SENSOR, "area": "throne_bathroom", "manufacturer": "Signify", "model": "Hue motion sensor", "entity_id": "binary_sensor.hue_motion_sensor_motion_2", "integration": "hue"},

    # Secondary Bathroom (Splash)
    {"id": "splash_ceiling_1", "name": "Splash Ceiling Light.1", "type": EntityType.LIGHT, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.splash_ceiling_light_1", "integration": "hue"},
    {"id": "splash_ceiling_2", "name": "Splash Ceiling Light.2", "type": EntityType.LIGHT, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.splash_ceiling_light_2", "integration": "hue"},
    {"id": "splash_ceiling_3", "name": "Splash Ceiling Light.3", "type": EntityType.LIGHT, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.splash_ceiling_light_3", "integration": "hue"},
    {"id": "splash_ceiling_4", "name": "Splash Ceiling Light.4", "type": EntityType.LIGHT, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.splash_ceiling_light_4", "integration": "hue"},
    {"id": "splash_ceiling_5", "name": "Splash Ceiling Light.5", "type": EntityType.LIGHT, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.splash_ceiling_light_5", "integration": "hue"},
    {"id": "splash_dimmer", "name": "Splash Dimmer Switch", "type": EntityType.SWITCH, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue dimmer switch", "entity_id": "event.splash_dimmer_switch_button_1", "integration": "hue"},
    {"id": "splash_motion", "name": "Splash Motion Sensor", "type": EntityType.SENSOR, "area": "secondary_bathroom", "manufacturer": "Signify", "model": "Hue motion sensor", "entity_id": "binary_sensor.hue_motion_sensor_motion", "integration": "hue"},

    # Spare Bedroom (Beta)
    {"id": "beta_ceiling_3", "name": "Beta Ceiling Light.3", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.beta_ceiling_light_3", "integration": "hue"},
    {"id": "beta_ceiling_3_2", "name": "Beta Ceiling Light.3 (2)", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.beta_ceiling_light_3_2", "integration": "hue"},
    {"id": "beta_ceiling_4", "name": "Beta Ceiling Light.4", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.beta_ceiling_light_4", "integration": "hue"},
    {"id": "beta_ceiling_6", "name": "Beta Ceiling Light.6", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.beta_ceiling_light_6", "integration": "hue"},
    {"id": "betaflex_ceiling_1", "name": "Betaflex Ceiling Light.1", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.betaflex_ceiling_light_1", "integration": "hue"},
    {"id": "betaflex_ceiling_2", "name": "Betaflex Ceiling Light.2", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue ambiance spot", "entity_id": "light.betaflex_ceiling_light_2", "integration": "hue"},
    {"id": "beta_bed_lightstrip", "name": "Beta Bed Lightstrip", "type": EntityType.LIGHT, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue lightstrip plus", "entity_id": "light.beta_bed_lightstrip", "integration": "hue"},
    {"id": "beta_dial_switch", "name": "Hallway Tap Dial Switch (Beta)", "type": EntityType.SWITCH, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue tap dial switch", "entity_id": "event.hallway_tap_dial_switch_button_1", "integration": "hue"},
    {"id": "beta_motion", "name": "Beta Motion Sensor", "type": EntityType.SENSOR, "area": "beta_bedroom", "manufacturer": "Signify", "model": "Hue motion sensor", "entity_id": "binary_sensor.hue_motion_sensor_motion", "integration": "hue"},
    {"id": "bedroom_apple_tv", "name": "Bedroom Apple TV", "type": EntityType.MEDIA_PLAYER, "area": "beta_bedroom", "manufacturer": "Apple", "model": "Apple TV 4K (gen 3)", "entity_id": "media_player.bedroom_apple_tv", "integration": "apple_tv"},

    # Laundry/Utilities (Chaos)
    {"id": "chaos_ceiling", "name": "Laundry (Chaos) Ceiling Light", "type": EntityType.LIGHT, "area": "chaos", "manufacturer": "Signify", "model": "Hue white lamp", "entity_id": "light.laundry_chaos_ceiling_light", "integration": "hue"},
    {"id": "chaos_storage_bulb", "name": "White (E27) Hue Bulb", "type": EntityType.LIGHT, "area": "chaos", "manufacturer": "Signify", "model": "Hue white lamp", "entity_id": "light.white_e27_hue_bulb", "integration": "hue"},

    # Unassigned — Aqara presence zones (FP2 via Matter)
    {"id": "fp2_dining_zone", "name": "Absence 3min Dining Zone", "type": EntityType.SENSOR, "area": "dining", "manufacturer": "Aqara", "model": "FP2 zone", "entity_id": "binary_sensor.absence_for_3mins_dining_zone_occupancy", "integration": "matter"},
    {"id": "fp2_kitchen_zone", "name": "Absence 3min Kitchen Zone", "type": EntityType.SENSOR, "area": "core_kitchen", "manufacturer": "Aqara", "model": "FP2 zone", "entity_id": "binary_sensor.absence_for_3mins_kitchen_zone_occupancy", "integration": "matter"},
    {"id": "fp2_living_zone", "name": "Absence 3min Living Zone", "type": EntityType.SENSOR, "area": "living_room", "manufacturer": "Aqara", "model": "FP2 zone", "entity_id": "binary_sensor.absence_for_3mins_living_zone_occupancy", "integration": "matter"},
    {"id": "fp2_openplan_5min", "name": "Absence 5min Openplan", "type": EntityType.SENSOR, "area": "core", "manufacturer": "Aqara", "model": "FP2 zone", "entity_id": "binary_sensor.absence_for_5mins_openplan_occupancy", "integration": "matter"},
    {"id": "fp2_approaching", "name": "Approaching Openplan Room", "type": EntityType.SENSOR, "area": "core", "manufacturer": "Aqara", "model": "FP2 zone", "entity_id": "binary_sensor.approaching_openplan_room_occupancy", "integration": "matter"},

    # Curtain drivers
    {"id": "curtain_1", "name": "Aqara Curtain Driver E1", "type": EntityType.COVER, "area": None, "manufacturer": "Aqara", "model": "Curtain Driver E1", "entity_id": "cover.aqara_curtain_driver_e1", "integration": "matter"},
    {"id": "curtain_2", "name": "Aqara Curtain Driver E1 (2)", "type": EntityType.COVER, "area": None, "manufacturer": "Aqara", "model": "Curtain Driver E1", "entity_id": "cover.aqara_curtain_driver_e1_2", "integration": "matter"},

    # Door sensors
    {"id": "laundry_door", "name": "Laundry Door Sensor", "type": EntityType.SENSOR, "area": "chaos", "manufacturer": "Aqara", "model": "Door and Window Sensor", "entity_id": "binary_sensor.laundry_sns_door_door", "integration": "matter"},

    # Network
    {"id": "speedtest", "name": "SpeedTest", "type": EntityType.SENSOR, "area": "parking", "manufacturer": None, "model": None, "entity_id": "sensor.speedtest_download", "integration": "speedtestdotnet"},
]

LIGHT_GROUPS: list[dict[str, Any]] = [
    {"id": "bedroom_ceiling_group", "name": "Bedroom Ceiling", "area": "bedroom", "members": ["light.bedroom_ceiling"]},
    {"id": "bedroom_lamps_group", "name": "Bedroom Lamps", "area": "bedroom", "members": ["light.bedroom_lamps"]},
    {"id": "all_bedroom_bathroom_group", "name": "All Bedroom & Bathroom", "area": "bedroom", "members": ["light.all_bedroom_bathroom"]},
    {"id": "living_room_group", "name": "Living Room", "area": "living_room", "members": ["light.living_room"]},
    {"id": "living_room_ceiling_group", "name": "Living Room Ceiling", "area": "living_room", "members": ["light.living_room_ceiling"]},
    {"id": "living_room_lamps_group", "name": "Living Room Lamps", "area": "living_room", "members": ["light.living_room_lamps"]},
    {"id": "kitchen_group", "name": "Kitchen", "area": "core_kitchen", "members": ["light.kitchen"]},
    {"id": "kitchen_ceiling_group", "name": "Kitchen Ceiling", "area": "core_kitchen", "members": ["light.kitchen_ceiling"]},
    {"id": "hallway_group", "name": "Hallway", "area": "pass", "members": ["light.hallway"]},
    {"id": "spare_bedroom_group", "name": "Spare Bedroom", "area": "beta_bedroom", "members": ["light.spare_bedroom"]},
    {"id": "spare_bedroom_ceiling_group", "name": "Spare Bedroom Ceiling", "area": "beta_bedroom", "members": ["light.spare_bedroom_ceiling"]},
    {"id": "beta_bedroom_bath_group", "name": "Beta Bedroom & Bath", "area": "beta_bedroom", "members": ["light.beta_bedroom_bath"]},
    {"id": "secondary_bathroom_group", "name": "Secondary Bathroom", "area": "secondary_bathroom", "members": ["light.secondary_bathroom"]},
    {"id": "bathroom_group", "name": "Bathroom (Throne)", "area": "throne_bathroom", "members": ["light.bathroom"]},
    {"id": "laundry_room_group", "name": "Laundry Room", "area": "laundry_room", "members": ["light.laundry_room"]},
]

SCENES: list[dict[str, Any]] = [
    {"id": "bedroom_concentrate", "name": "Bedroom Concentrate", "area": "alpha_bedroom", "entity_id": "scene.bedroom_concentrate"},
    {"id": "bedroom_dimmed", "name": "Bedroom Dimmed", "area": "alpha_bedroom", "entity_id": "scene.bedroom_dimmed"},
    {"id": "bedroom_energise", "name": "Bedroom Energise", "area": "alpha_bedroom", "entity_id": "scene.bedroom_energise"},
    {"id": "bedroom_nightlight", "name": "Bedroom Nightlight", "area": "alpha_bedroom", "entity_id": "scene.bedroom_nightlight"},
    {"id": "bedroom_read", "name": "Bedroom Read", "area": "alpha_bedroom", "entity_id": "scene.bedroom_read"},
    {"id": "bedroom_relax", "name": "Bedroom Relax", "area": "alpha_bedroom", "entity_id": "scene.bedroom_relax"},
    {"id": "bedroom_sleepy", "name": "Bedroom Sleepy", "area": "alpha_bedroom", "entity_id": "scene.bedroom_sleepy"},
    {"id": "hallway_concentrate", "name": "Hallway Concentrate", "area": "pass", "entity_id": "scene.hallway_concentrate"},
    {"id": "hallway_energise", "name": "Hallway Energise", "area": "pass", "entity_id": "scene.hallway_energise"},
    {"id": "hallway_nightlight", "name": "Hallway Nightlight", "area": "pass", "entity_id": "scene.hallway_nightlight"},
    {"id": "hallway_read", "name": "Hallway Read", "area": "pass", "entity_id": "scene.hallway_read"},
    {"id": "hallway_relax", "name": "Hallway Relax", "area": "pass", "entity_id": "scene.hallway_relax"},
]

INPUT_HELPERS: list[dict[str, Any]] = [
    {"id": "core_lighting_auto", "name": "Core Lighting Auto", "type": "input_boolean", "entity_id": "input_boolean.core_lighting_auto"},
    {"id": "core_lighting_test", "name": "Core Lighting Test Enabled", "type": "input_boolean", "entity_id": "input_boolean.core_lighting_test_enabled"},
    {"id": "core_manual_override", "name": "Core Manual Override", "type": "input_boolean", "entity_id": "input_boolean.core_manual_override"},
    {"id": "core_ceiling_allowed", "name": "Core Ceiling Allowed", "type": "input_boolean", "entity_id": "input_boolean.core_ceiling_allowed"},
    {"id": "core_lighting_phase", "name": "Core Lighting Phase", "type": "input_select", "entity_id": "input_select.core_lighting_phase", "options": ["Morning", "Day", "Golden Hour", "Evening", "Night", "Late Night", "Away"]},
    {"id": "core_activity", "name": "Core Activity", "type": "input_select", "entity_id": "input_select.core_activity", "options": ["Idle", "Living", "Kitchen", "Dining", "Media", "Cleaning", "Manual"]},
    {"id": "core_ceiling_brightness", "name": "Core Ceiling Target Brightness", "type": "input_number", "entity_id": "input_number.core_ceiling_target_brightness"},
    {"id": "core_ambient_brightness", "name": "Core Ambient Target Brightness", "type": "input_number", "entity_id": "input_number.core_ambient_target_brightness"},
    {"id": "core_path_brightness", "name": "Core Path Target Brightness", "type": "input_number", "entity_id": "input_number.core_path_target_brightness"},
    {"id": "core_kitchen_brightness", "name": "Core Kitchen Target Brightness", "type": "input_number", "entity_id": "input_number.core_kitchen_target_brightness"},
    {"id": "core_target_kelvin", "name": "Core Target Kelvin", "type": "input_number", "entity_id": "input_number.core_target_kelvin"},
    {"id": "core_fade_seconds", "name": "Core Fade Seconds", "type": "input_number", "entity_id": "input_number.core_fade_seconds"},
]

BLUEPRINTS: list[dict[str, Any]] = [
    {
        "id": "ceiling_daily_rhythm_presence",
        "name": "Ceiling Daily Rhythm + Presence",
        "description": "Presence-based ceiling light automation following day phases (morning/day/evening/night) with sun elevation gating",
        "inputs": ["sensor_entity", "light_target", "sun_elevation_below", "morning_start", "morning_end", "evening_start", "night_start", "night_end"],
    },
    {
        "id": "bedroom_suite_bath_path",
        "name": "Bedroom Suite Bath Path",
        "description": "Coordinated bedroom-to-bathroom path lighting",
        "inputs": [],
    },
    {
        "id": "room_follow_me_atmosphere",
        "name": "Room Follow Me Atmosphere",
        "description": "Follow-me atmosphere lighting across rooms",
        "inputs": [],
    },
]

ROOM_MEMORY_FACTS: list[dict[str, Any]] = [
    {"area": "core", "fact": "Threshold is the invisible entry line between north wall A (start) and start of the kitchen run on west wall C", "confidence": 0.9},
    {"area": "core", "fact": "Quadrants: NE (A1-B by balcony), NW (A-A1 by kitchen), SW (south green wall + kitchen/radiator zone), SE (angled corner where south meets window stretch)", "confidence": 0.9},
    {"area": "core", "fact": "Radiators: 110 cm on north (A1-B) and 110 cm on south (west side). Approx 10 cm intrusion depth each", "confidence": 0.8},
    {"area": "core", "fact": "Compass anchors: 12 pm = South (green wall), 3 pm = West (kitchen run), 6 pm = North (A-B), 9 pm = East (balcony window wall)", "confidence": 0.9},
    {"area": "core", "fact": "Overheads: 6 Hue white + colour and 4 Hue white ambiance; 2 over A-B and 2 over C", "confidence": 0.8},
]

PROPERTY_FACTS: list[dict[str, Any]] = [
    {"id": "property_type", "fact": "2-bedroom flat, approximately 900 sqft", "category": "physical"},
    {"id": "property_constraint", "fact": "Rental property - no destructive installs", "category": "constraint"},
    {"id": "network_isp", "fact": "ISP: Hyperoptic 1 Gbps fibre, static IP", "category": "network"},
    {"id": "network_router", "fact": "Router: Unifi Cloud Gateway Ultra", "category": "network"},
    {"id": "network_wifi", "fact": "Wi-Fi AP: Unifi u7-pro/6+ AP", "category": "network"},
    {"id": "network_topology", "fact": "Flat LAN (no VLANs), all devices same network", "category": "network"},
    {"id": "compute_server", "fact": "Primary Server: GMKtec Mini PC N95 (Intel N95, 16GB RAM, 512GB SSD), Ubuntu 24.04 LTS", "category": "compute"},
    {"id": "compute_docker", "fact": "Docker running: homeassistant", "category": "compute"},
    {"id": "platform_primary", "fact": "Primary platform: Home Assistant", "category": "platform"},
    {"id": "platform_secondary", "fact": "Secondary platforms: Apple HomeKit, Google Home", "category": "platform"},
    {"id": "cloudflare_tunnel", "fact": "Cloudflare Tunnel active, serving: itsjeff.org, flat-affairs.org", "category": "network"},
]

CONTEXT_STATES: list[dict[str, Any]] = [
    {"id": "jeff_context", "name": "Jeff Context", "entity_id": "sensor.jeff_context", "states": ["asleep", "resting", "active_living", "active_bedroom", "home_idle", "away"]},
]


@dataclass
class SmartHomeGraph:
    """Assembled smart home domain graph."""
    entity_store: EntityStore = field(default_factory=EntityStore)
    relation_store: RelationStore = field(default_factory=RelationStore)
    domain: str = DOMAIN

    def build(self) -> "SmartHomeGraph":
        self._build_floor()
        self._build_areas()
        self._build_zones()
        self._build_adjacency()
        self._build_integrations()
        self._build_hubs()
        self._build_devices()
        self._build_light_groups()
        self._build_scenes()
        self._build_input_helpers()
        self._build_blueprints()
        self._build_facts()
        self._build_context_sensors()
        return self

    def _make_entity(self, id_suffix: str, entity_type: EntityType, name: str, **kwargs: Any) -> Entity:
        entity_id = f"{DOMAIN}:{id_suffix}"
        aliases = kwargs.pop("aliases", [])
        description = kwargs.pop("description", None)
        attributes = kwargs.pop("attributes", {})
        return self.entity_store.upsert(Entity(
            id=entity_id,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            entity_type=entity_type,
            name=name,
            aliases=aliases,
            description=description,
            attributes=attributes,
        ))

    def _make_relation(self, id_suffix: str, rel_type: RelationType, source_id: str, target_id: str, **kwargs: Any) -> Relation:
        rel_id = f"{DOMAIN}:rel:{id_suffix}"
        return self.relation_store.upsert(Relation(
            id=rel_id,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            relation_type=rel_type,
            source_entity_id=source_id,
            target_entity_id=target_id,
            confidence=kwargs.get("confidence", 1.0),
            provenance=kwargs.get("provenance", ["ha-inventory-2026-05-17"]),
        ))

    def _build_floor(self) -> None:
        self._make_entity("floor:main", EntityType.FLOOR, "Main Floor", description="Single floor flat")

    def _build_areas(self) -> None:
        for area_id, area_data in AREA_MAP.items():
            entity = self._make_entity(
                f"area:{area_id}",
                EntityType.AREA,
                area_data["name"],
                aliases=area_data.get("aliases", []),
                attributes={
                    "ha_area_id": area_id,
                    "room_code": area_data.get("code"),
                    "room_type": area_data.get("type"),
                },
            )
            self._make_relation(
                f"area_floor:{area_id}",
                RelationType.AREA_ON_FLOOR,
                entity.id,
                f"{DOMAIN}:floor:main",
            )

    def _build_zones(self) -> None:
        for area_id, zones in ZONE_DEFS.items():
            for zone in zones:
                entity = self._make_entity(
                    f"zone:{zone['id']}",
                    EntityType.ZONE,
                    zone["name"],
                    description=zone.get("description"),
                )
                self._make_relation(
                    f"zone_area:{zone['id']}",
                    RelationType.ZONE_WITHIN_AREA,
                    entity.id,
                    f"{DOMAIN}:area:{area_id}",
                )

    def _build_adjacency(self) -> None:
        for a, b in ADJACENCY:
            self._make_relation(
                f"adj:{a}_{b}",
                RelationType.AREA_ADJACENT_TO,
                f"{DOMAIN}:area:{a}",
                f"{DOMAIN}:area:{b}",
            )
            self._make_relation(
                f"adj:{b}_{a}",
                RelationType.AREA_ADJACENT_TO,
                f"{DOMAIN}:area:{b}",
                f"{DOMAIN}:area:{a}",
            )

    def _build_integrations(self) -> None:
        for integ in INTEGRATIONS:
            self._make_entity(
                f"integration:{integ['id']}",
                EntityType.INTEGRATION,
                integ["name"],
                attributes={"domain": integ["domain"], "type": integ["type"]},
            )

    def _build_hubs(self) -> None:
        for hub in HUBS:
            entity = self._make_entity(
                f"hub:{hub['id']}",
                EntityType.HUB,
                hub["name"],
                attributes={
                    "manufacturer": hub["manufacturer"],
                    "model": hub["model"],
                    "protocol": hub["protocol"],
                },
            )
            if hub.get("area"):
                self._make_relation(
                    f"hub_area:{hub['id']}",
                    RelationType.DEVICE_IN_AREA,
                    entity.id,
                    f"{DOMAIN}:area:{hub['area']}",
                )

    def _build_devices(self) -> None:
        for dev in DEVICES:
            entity = self._make_entity(
                f"device:{dev['id']}",
                dev["type"],
                dev["name"],
                attributes={
                    k: v for k, v in {
                        "manufacturer": dev.get("manufacturer"),
                        "model": dev.get("model"),
                        "ha_entity_id": dev.get("entity_id"),
                        "integration": dev.get("integration"),
                    }.items() if v is not None
                },
            )
            if dev.get("area"):
                self._make_relation(
                    f"dev_area:{dev['id']}",
                    RelationType.DEVICE_IN_AREA,
                    entity.id,
                    f"{DOMAIN}:area:{dev['area']}",
                )
            if dev.get("integration"):
                self._make_relation(
                    f"dev_integ:{dev['id']}",
                    RelationType.INTEGRATION_PROVIDES_DEVICE,
                    f"{DOMAIN}:integration:{dev['integration']}",
                    entity.id,
                )

    def _build_light_groups(self) -> None:
        for group in LIGHT_GROUPS:
            entity = self._make_entity(
                f"light_group:{group['id']}",
                EntityType.LIGHT_GROUP,
                group["name"],
                attributes={"ha_members": group["members"]},
            )
            if group.get("area"):
                self._make_relation(
                    f"lg_area:{group['id']}",
                    RelationType.DEVICE_IN_AREA,
                    entity.id,
                    f"{DOMAIN}:area:{group['area']}",
                )

    def _build_scenes(self) -> None:
        for scene in SCENES:
            entity = self._make_entity(
                f"scene:{scene['id']}",
                EntityType.SCENE,
                scene["name"],
                attributes={"ha_entity_id": scene["entity_id"]},
            )
            if scene.get("area"):
                self._make_relation(
                    f"scene_area:{scene['id']}",
                    RelationType.DEVICE_IN_AREA,
                    entity.id,
                    f"{DOMAIN}:area:{scene['area']}",
                )

    def _build_input_helpers(self) -> None:
        for helper in INPUT_HELPERS:
            self._make_entity(
                f"input:{helper['id']}",
                EntityType.INPUT_HELPER,
                helper["name"],
                attributes={
                    "ha_entity_id": helper["entity_id"],
                    "helper_type": helper["type"],
                    **({"options": helper["options"]} if "options" in helper else {}),
                },
            )

    def _build_blueprints(self) -> None:
        for bp in BLUEPRINTS:
            self._make_entity(
                f"blueprint:{bp['id']}",
                EntityType.BLUEPRINT,
                bp["name"],
                description=bp.get("description"),
                attributes={"inputs": bp.get("inputs", [])},
            )

    def _build_facts(self) -> None:
        for i, fact_data in enumerate(ROOM_MEMORY_FACTS):
            entity = self._make_entity(
                f"fact:room:{i}",
                EntityType.FACT,
                f"Room fact: {fact_data['fact'][:60]}",
                description=fact_data["fact"],
                attributes={"confidence": fact_data["confidence"]},
            )
            if fact_data.get("area"):
                self._make_relation(
                    f"fact_area:{i}",
                    RelationType.ENTITY_RELATED_TO,
                    entity.id,
                    f"{DOMAIN}:area:{fact_data['area']}",
                )

        for prop in PROPERTY_FACTS:
            self._make_entity(
                f"fact:property:{prop['id']}",
                EntityType.FACT,
                f"Property: {prop['fact'][:60]}",
                description=prop["fact"],
                attributes={"category": prop["category"]},
            )

    def _build_context_sensors(self) -> None:
        for ctx in CONTEXT_STATES:
            self._make_entity(
                f"context:{ctx['id']}",
                EntityType.SENSOR,
                ctx["name"],
                attributes={
                    "ha_entity_id": ctx["entity_id"],
                    "possible_states": ctx["states"],
                    "purpose": "user_context_detection",
                },
            )

    def summary(self) -> dict[str, Any]:
        all_entities = self.entity_store.all(TENANT_ID, USER_ID)
        type_counts: dict[str, int] = {}
        for e in all_entities:
            t = e.entity_type if isinstance(e.entity_type, str) else e.entity_type.value
            type_counts[t] = type_counts.get(t, 0) + 1

        return {
            "domain": self.domain,
            "total_entities": len(all_entities),
            "total_relations": len(self.relation_store._relations),
            "entity_types": type_counts,
            "areas": len([e for e in all_entities if e.entity_type == EntityType.AREA]),
            "zones": len([e for e in all_entities if e.entity_type == EntityType.ZONE]),
            "devices": len([e for e in all_entities if e.entity_type in (
                EntityType.LIGHT, EntityType.SENSOR, EntityType.SWITCH,
                EntityType.COVER, EntityType.MEDIA_PLAYER, EntityType.CLIMATE,
            )]),
            "light_groups": len([e for e in all_entities if e.entity_type == EntityType.LIGHT_GROUP]),
            "scenes": len([e for e in all_entities if e.entity_type == EntityType.SCENE]),
            "blueprints": len([e for e in all_entities if e.entity_type == EntityType.BLUEPRINT]),
            "facts": len([e for e in all_entities if e.entity_type == EntityType.FACT]),
        }

    def to_json(self) -> dict[str, Any]:
        all_entities = self.entity_store.all(TENANT_ID, USER_ID)
        all_relations = list(self.relation_store._relations.values())
        return {
            "domain": self.domain,
            "entities": [e.model_dump(mode="json") for e in all_entities],
            "relations": [r.model_dump(mode="json") for r in all_relations],
            "summary": self.summary(),
        }


def build_smart_home_graph() -> SmartHomeGraph:
    return SmartHomeGraph().build()


if __name__ == "__main__":
    graph = build_smart_home_graph()
    summary = graph.summary()
    print(f"Smart Home Domain Graph built:")
    print(f"  Entities: {summary['total_entities']}")
    print(f"  Relations: {summary['total_relations']}")
    print(f"  Areas: {summary['areas']}")
    print(f"  Zones: {summary['zones']}")
    print(f"  Devices: {summary['devices']}")
    print(f"  Light Groups: {summary['light_groups']}")
    print(f"  Scenes: {summary['scenes']}")
    print(f"  Blueprints: {summary['blueprints']}")
    print(f"  Facts: {summary['facts']}")
    print(f"\n  Entity type breakdown:")
    for t, count in sorted(summary["entity_types"].items()):
        print(f"    {t}: {count}")
