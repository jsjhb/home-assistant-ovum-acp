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
DEFAULT_SLAVE = 247
CONF_OVUM_HUB = "ovum_hub"
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
    {"name": "waermeleistung", "key": "waermeleistung", "icon": "heat-wave"},
    {"name": "pv_watch_messwert", "key": "pv_watch_messwert", "icon": "solar-power"},
    {"name": "el_leistung_wp", "key": "el_leistung_wp", "icon": "power-socket"},
    {"name": "sollwert_pvwatch_tcp", "key": "sollwert_pvwatch_tcp", "icon": "solar-power"},
    {"name": "sollwert_leistungsaufnahme_tcp", "key": "sollwert_leistungsaufnahme_tcp", "icon": "power-socket"},
]

temperature_sensors = [
    {"name": "waermepumpenaustritt", "key": "waermepumpenaustritt", "icon": "transmission-tower"},
    {"name": "waermepumpeneintritt", "key": "waermepumpeneintritt", "icon": "transmission-tower"},
    {"name": "temperatur_wwspeicher_oben", "key": "temperatur_wwspeicher_oben", "icon": "transmission-tower"},
    {"name": "temperatur_wwspeicher_unten", "key": "temperatur_wwspeicher_unten", "icon": "transmission-tower"},
    {"name": "temperatur_zapf_fws", "key": "temperatur_zapf_fws", "icon": "transmission-tower"},
    {"name": "temperatur_ww_soll", "key": "temperatur_ww_soll", "icon": "transmission-tower"},
    {"name": "temperatur_zapf_soll", "key": "temperatur_zapf_soll", "icon": "transmission-tower"},
    {"name": "vorlauftemperatur_hk1", "key": "vorlauftemperatur_hk1", "icon": "transmission-tower"},
    {"name": "ruecklauftemperatur_hk1", "key": "ruecklauftemperatur_hk1", "icon": "transmission-tower"},
    {"name": "temperatur_speicher", "key": "temperatur_speicher", "icon": "transmission-tower"},
    {"name": "aussentemperatur_gemittelt", "key": "aussentemperatur_gemittelt", "icon": "transmission-tower"},
    {"name": "raumsolltemperatur_hk1", "key": "raumsolltemperatur_hk1", "icon": "transmission-tower"},
    {"name": "vorlauftemperatur_hk2", "key": "vorlauftemperatur_hk2", "icon": "transmission-tower"},
    {"name": "vorlaufsolltemperatur_hk2", "key": "vorlaufsolltemperatur_hk2", "icon": "transmission-tower"},
    {"name": "raumsolltemperatur_hk2", "key": "raumsolltemperatur_hk2", "icon": "transmission-tower"},
    {"name": "vorlaufsolltemperatur_hk1", "key": "vorlaufsolltemperatur_hk1", "icon": "transmission-tower"},
    {"name": "speichersolltemperatur_pvplus_betrieb", "key": "speichersolltemperatur_pvplus_betrieb", "icon": "transmission-tower"},
]

information_sensors = [
    {"name": "pumpe_hk1", "key": "pumpe_hk1", "icon": "information-outline"},
    {"name": "kombiausgang_pupu", "key": "kombiausgang_pupu", "icon": "information-outline"},
    {"name": "stufe2b", "key": "stufe2b", "icon": "information-outline"},
    {"name": "kuehlventil", "key": "kuehlventil", "icon": "information-outline"},
    {"name": "stufe2a", "key": "stufe2a", "icon": "information-outline"},
    {"name": "betriebsstuden_kompressor", "key": "betriebsstuden_kompressor", "icon": "information-outline"},
    {"name": "laufzeit_seit_letztem_start", "key": "laufzeit_seit_letztem_start", "icon": "information-outline"},
    {"name": "betriebsart_warmwasser", "key": "betriebsart_warmwasser", "icon": "information-outline"},
    {"name": "status_kombiausgang_pupu", "key": "status_kombiausgang_pupu", "icon": "information-outline"},
    {"name": "anzahl_aktive_alarme", "key": "anzahl_aktive_alarme", "icon": "information-outline"},
    {"name": "max_neustarts_erreicht", "key": "max_neustarts_erreicht", "icon": "information-outline"},
    {"name": "autarkiegrad_ueberschussbetrieb", "key": "autarkiegrad_ueberschussbetrieb", "icon": "information-outline"},
    {"name": "betriebsart_heizung", "key": "betriebsart_heizung", "icon": "information-outline"},
    {"name": "kombiausgang_pupu_modi", "key": "kombiausgang_pupu_modi", "icon": "information-outline"},
    {"name": "betriebsart_hk1", "key": "betriebsart_hk1", "icon": "information-outline"},
    {"name": "betriebsart_hk1", "key": "betriebsart_hk1", "icon": "information-outline"},
    {"name": "sollwertanhebung_ww_pvplus", "key": "sollwertanhebung_ww_pvplus", "icon": "information-outline"},
    {"name": "sollwertanhebung_heizung_pvplus", "key": "sollwertanhebung_heizung_pvplus", "icon": "information-outline"},
    {"name": "pvplus_regelungsart", "key": "pvplus_regelungsart", "icon": "information-outline"},
    {"name": "pv_anforderung_aktiv", "key": "pv_anforderung_aktiv", "icon": "information-outline"},
    {"name": "abtaustatus", "key": "abtaustatus", "icon": "information-outline"},
    {"name": "anforderungsart_kaeltekreis", "key": "anforderungsart_kaeltekreis", "icon": "information-outline"},
    {"name": "sg_ready_modus", "key": "sg_ready_modus", "icon": "information-outline"},
    {"name": "sg_ready_kontakt1", "key": "sg_ready_kontakt1", "icon": "information-outline"},
    {"name": "sg_ready_kontakt2", "key": "sg_ready_kontakt2", "icon": "information-outline"},
    {"name": "wp_status", "key": "wp_status", "icon": "information-outline"},
]

SENSOR_TYPES = {
    **create_sensor_descriptions(power_sensors_group, power_sensors),
    **create_sensor_descriptions(temperature_sensors_group, temperature_sensors),
    **create_sensor_descriptions(information_sensors_group, information_sensors),
   
}


}
