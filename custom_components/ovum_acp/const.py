from typing import Optional
from dataclasses import dataclass
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)

from typing import Dict, NamedTuple, Any


DOMAIN = "ovum_acp"
DEFAULT_NAME = "Ovum"
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_PORT = 502
DEFAULT_DEVICE_ID = 247
CONF_OVUM_HUB = "ovum_hub"
CONF_DEVICE_ID = DEFAULT_DEVICE_ID
ATTR_MANUFACTURER = "OVUM Wärmepumpen GmbH"


@dataclass
class SensorGroup:
    unit_of_measurement: Optional[str] = None
    icon: str = ""  # Optional
    device_class: Optional[str] = None  
    state_class: Optional[str] = None  
    force_update: bool = False  # Neues Attribut für die Gruppe
    
@dataclass
class OvumModbusSensorEntityDescription(SensorEntityDescription):
    """A class that describes Ovum ACP sensor entities."""


power_sensors_group = SensorGroup(
    unit_of_measurement=UnitOfPower.WATT,
    device_class=SensorDeviceClass.POWER,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:solar-power",
    force_update=True  # force_update für die gesamte Gruppe aktivieren

)

temperature_sensors_group = SensorGroup(
    unit_of_measurement=UnitOfTemperature.CELSIUS,
    device_class=SensorDeviceClass.TEMPERATURE,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:thermometer",  
)

information_sensors_group = SensorGroup(
    icon="mdi:information-outline"  
)

information_percentage_sensors_group = SensorGroup(
    unit_of_measurement="%",
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:percent"  
)

duration_minutes_sensors_group = SensorGroup(
    unit_of_measurement=UnitOfTime.MINUTES,
    device_class=SensorDeviceClass.DURATION,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:clock",
)

duration_hours_sensors_group = SensorGroup(
    unit_of_measurement=UnitOfTime.HOURS,
    device_class=SensorDeviceClass.DURATION,
    state_class=SensorStateClass.MEASUREMENT,
    icon="mdi:clock",
)

def create_sensor_descriptions(group: SensorGroup, sensors: list) -> dict:
    descriptions = {}
    for sensor in sensors:
        
        icon = sensor.get("icon", group.icon)
        if icon and not icon.startswith("mdi:"):
            icon = f"mdi:{icon}"
        
        
        enable = sensor.get("enable", True)
        
        descriptions[sensor["key"]] = OvumModbusSensorEntityDescription(
            name=sensor["name"],
            key=sensor["key"],
            native_unit_of_measurement=group.unit_of_measurement,
            icon=icon,
            device_class=group.device_class,
            state_class=group.state_class,
            entity_registry_enabled_default=enable,
            force_update=group.force_update  # force_update von der Gruppe übernehmen
        )
    return descriptions




power_sensors = [
    {"name": "AIR Leistung Wärme", "key": "waermeleistung", "icon": "heat-wave"},
    {"name": "PV Watch Messwert", "key": "pv_watch_messwert", "icon": "solar-power"},
    {"name": "AIR Leistung elektrisch", "key": "el_leistung_wp", "icon": "power-socket"},
    {"name": "sollwert_pvwatch_tcp", "key": "sollwert_pvwatch_tcp", "icon": "solar-power"},
    {"name": "sollwert_leistungsaufnahme_tcp", "key": "sollwert_leistungsaufnahme_tcp", "icon": "power-socket"},
]

temperature_sensors = [
    {"name": "AIR WP Austritt", "key": "waermepumpenaustritt", "icon": "thermometer"},
    {"name": "AIR WP Eintritt", "key": "waermepumpeneintritt", "icon": "thermometer"},
    {"name": "CUBE Temp WW oben", "key": "temperatur_wwspeicher_oben", "icon": "thermometer"},
    {"name": "CUBE Temp WW unten", "key": "temperatur_wwspeicher_unten", "icon": "thermometer"},
    {"name": "FWS Temp Zapf ist", "key": "temperatur_zapf_fws", "icon": "thermometer"},
    {"name": "CUBE Temp WW soll", "key": "temperatur_ww_soll", "icon": "thermometer"},
    {"name": "FWS Temp Zapf soll", "key": "temperatur_zapf_soll", "icon": "thermometer"},
    {"name": "HK1 Temp Vorlauf", "key": "vorlauftemperatur_hk1", "icon": "thermometer"},
    {"name": "HK1 Temp Rücklauf", "key": "ruecklauftemperatur_hk1", "icon": "thermometer"},
    {"name": "CUBE Temp Speicher", "key": "temperatur_speicher", "icon": "thermometer"},
    {"name": "AIR Temp aussen gemittelt", "key": "aussentemperatur_gemittelt", "icon": "thermometer"},
    {"name": "HK1 Temp Raum soll", "key": "raumsolltemperatur_hk1", "icon": "thermometer"},
    {"name": "HK2 Temp Vorlauf", "key": "vorlauftemperatur_hk2", "icon": "thermometer", "enable": False},
    {"name": "HK2 Temp Vorlauf soll", "key": "vorlaufsolltemperatur_hk2", "icon": "thermometer", "enable": False},
    {"name": "HK2 Temp Raum soll", "key": "raumsolltemperatur_hk2", "icon": "thermometer", "enable": False},
    {"name": "HK1 Temp Vorlauf soll", "key": "vorlaufsolltemperatur_hk1", "icon": "thermometer"},
    {"name": "CUBE Temp Speicher soll PV+", "key": "speichersolltemperatur_pvplus_betrieb", "icon": "thermometer"},
]

information_sensors = [
    {"name": "HK1 Pumpe num", "key": "pumpe_hk1_num", "icon": "information-outline", "enable": False},
    {"name": "HK1 Pumpe", "key": "pumpe_hk1", "icon": "information-outline"},
    {"name": "kombiausgang_pupu", "key": "kombiausgang_pupu", "icon": "information-outline"},
    {"name": "stufe2b", "key": "stufe2b", "icon": "information-outline"},
    {"name": "Kuehlventil", "key": "kuehlventil", "icon": "information-outline"},
    {"name": "stufe2a", "key": "stufe2a", "icon": "information-outline"},
    {"name": "WW Betriebsart num", "key": "betriebsart_warmwasser_num", "icon": "information-outline", "enable": False},
    {"name": "WW Betriebsart", "key": "betriebsart_warmwasser", "icon": "information-outline"},
    {"name": "status_kombiausgang_pupu_num", "key": "status_kombiausgang_pupu_num", "icon": "information-outline", "enable": False},
    {"name": "status_kombiausgang_pupu", "key": "status_kombiausgang_pupu", "icon": "information-outline"},
    {"name": "Anzahl aktive Alarme", "key": "anzahl_aktive_alarme", "icon": "counter"},
    {"name": "AIR max Neustarts erreicht", "key": "max_neustarts_erreicht", "icon": "information-outline"},
    {"name": "Autarkiegrad Überschussbetrieb", "key": "autarkiegrad_ueberschussbetrieb", "icon": "information-outline"},
    {"name": "Betriebsart Heizung num", "key": "betriebsart_heizung_num", "icon": "information-outline", "enable": False},
    {"name": "Betriebsart Heizung", "key": "betriebsart_heizung", "icon": "information-outline"},
    {"name": "kombiausgang_pupu_modi_num", "key": "kombiausgang_pupu_modi_num", "icon": "information-outline", "enable": False},
    {"name": "kombiausgang_pupu_modi", "key": "kombiausgang_pupu_modi", "icon": "information-outline"},
    {"name": "HK1 Betriebsart num", "key": "betriebsart_hk1_num", "icon": "information-outline", "enable": False},
    {"name": "HK1 Betriebsart", "key": "betriebsart_hk1", "icon": "information-outline"},
    {"name": "HK2 Betriebsart num", "key": "betriebsart_hk2_num", "icon": "information-outline", "enable": False},
    {"name": "HK2 Betriebsart", "key": "betriebsart_hk2", "icon": "information-outline", "enable": False},
    {"name": "PV+ WW Sollwertanhebung", "key": "sollwertanhebung_ww_pvplus", "icon": "information-outline"},
    {"name": "PV+ HZ Sollwertanhebung num", "key": "sollwertanhebung_heizung_pvplus_num", "icon": "information-outline", "enable": False},
    {"name": "PV+ HZ Sollwertanhebung", "key": "sollwertanhebung_heizung_pvplus", "icon": "information-outline"},
    {"name": "PV+ Regelungsart num", "key": "pvplus_regelungsart_num", "icon": "information-outline", "enable": False},
    {"name": "PV+ Regelungsart", "key": "pvplus_regelungsart", "icon": "information-outline"},
    {"name": "PV Anforderung aktiv", "key": "pv_anforderung_aktiv", "icon": "information-outline"},
    {"name": "Abtaustatus", "key": "abtaustatus", "icon": "information-outline"},
    {"name": "anforderungsart_kaeltekreis_num", "key": "anforderungsart_kaeltekreis_num", "icon": "information-outline", "enable": False},
    {"name": "anforderungsart_kaeltekreis", "key": "anforderungsart_kaeltekreis", "icon": "information-outline"},
    {"name": "SG Ready Modus num", "key": "sg_ready_modus_num", "icon": "information-outline", "enable": False},
    {"name": "SG Ready Modus", "key": "sg_ready_modus", "icon": "information-outline"},
    {"name": "SG Ready Kontakt1", "key": "sg_ready_kontakt1", "icon": "information-outline"},
    {"name": "SG Ready Kontakt2", "key": "sg_ready_kontakt2", "icon": "information-outline"},
    {"name": "WP Status num", "key": "wp_status_num", "icon": "information-outline", "enable": False},
    {"name": "WP Status", "key": "wp_status", "icon": "information-outline"},
]

information_percentage_sensors = [
    {"name": "FWS Pumpe Leistung", "key": "pumpe_fws_ausgang", "icon": "information-outline"},
]

duration_minutes_sensors = [
    {"name": "AIR Laufzeit seit letztem Start", "key": "laufzeit_seit_letztem_start"},
]

duration_hours_sensors = [
    {"name": "AIR Betriebsstuden Kompressor", "key": "betriebsstuden_kompressor"},
]

SENSOR_TYPES = {
    **create_sensor_descriptions(power_sensors_group, power_sensors),
    **create_sensor_descriptions(temperature_sensors_group, temperature_sensors),
    **create_sensor_descriptions(information_sensors_group, information_sensors),
    **create_sensor_descriptions(information_percentage_sensors_group, information_percentage_sensors),
    **create_sensor_descriptions(duration_minutes_sensors_group, duration_minutes_sensors),
    **create_sensor_descriptions(duration_hours_sensors_group, duration_hours_sensors),
   
}

BETRIEBSART_MODI = {
    0: "Aus",
    1: "Ein",
    2: "Zeitprogramm",
    3: "Urlaub",
    4: "Party",
}

BETRIEBSART_HK = {
    0: "Inaktiv",
    1: "Heizen",
    2: "Kühlen",
    3: "Heizen&Kühlen",
}

KAELTEKREIS_MODI = {
    0: "Keine",
    1: "Warmwasser",
    2: "Heizung",
    3: "externe",
    4: "Kühlung",
    6: "Manuell",
}

PUPU_MODI = {
    0: "PuPu",
    1: "Warmwasser",
    2: "Sekundärpumpe",
    3: "Ladekreis aktiv",
    4: "Ladekreis kühlen",
    5: "Ladekreis heizen",
    6: "Ladekreis Warmwasser",
}

PV_UEBERSCHUSSREGELUNG = {
    0: "Ovum PV-Watch",
    1: "PV-Watch TCP",
    2: "Sollwert TCP",
}

SGREADY_MODUS = {
    0: "Schaltkontakte",
    1: "TCP",
}

SOLLWERTANHEBUNG_PVPLUS = {
    0: "Aus",
    1: "Heizkreis",
    2: "Speicher",
    3: "Heizkreis und Speicher",
}

WP_STATUS = {
    0: "Modbus TCP offline",
    1: "Bereit",
    2: "Hauptschalter aus",
    3: "EVU Sperre",
    4: "maximale Neustarts erreicht",
    5: "Sperrzeit",
    6: "Kompressorheizung",
    7: "Warmwasserbetrieb",
    8: "Heizbetrieb",
    9: "externe Anforderung",
    10: "Kühlung",
    11: "Abtauung",
}

