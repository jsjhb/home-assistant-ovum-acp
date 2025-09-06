Changelog for home-assistant-ovum-acp 0.3.1 (2025-09-06)
========================================================

Summary
-------

* rename MODBUS parameter slave to deviceid for pymodbus 3.10 compatibility


Changelog for home-assistant-ovum-acp 0.3.0 (2025-04-13)
========================================================

Summary
-------

* sorting and renaming of entities in a more logical way
* fix reading FWS pump power ratio and FWS draft temperature
* add verbose status descriptions
* disable HK2 entities by default


Details
-------

* correct reading of registers 0x203 and 0x204 regarding FWS
  draft temperature and pump power ratio 


Changelog for home-assistant-ovum-acp 0.2.1 (2025-02-17)
========================================================

Summary
-------

* rewrite to comply with newer version of pymodbus
* correct scaling and interpretation of values
* change icons for temperatures, define time entities as duration

Details
-------

* rewrite to get rid of BinaryPayloadDecoder
* adjust scaling of power values kW to W
* change icons for temperatures, define time entities as duration
* change scale of betriebsart warmwasser
* fix reading int32 value of firmware

