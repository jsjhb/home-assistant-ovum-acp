Changelog for home-assistant-ovum-acp 0.3.2 (2026-09-27)
========================================================

Summary
-------

* fix vorlaufsolltemperatur_hk1 off-by-one (fixes #3)
* add additional registers documented in later published documentation

Details
-------

Reading of register block 529-554 was errorneously shiftet in the wrong
direction. The documentation uses base-1 register numbering, whilst coding
uses base 0. The former implementation used "base 2", and just by chance
got the register for "VL SollDiff.". This fixed reading of
"kombiausgang_pupu_modi", and HK2-related values.

In a later surfaced version of the MODBUS register list for software
versions starting from "2401122-24/-23" (footer gives version 20250527),
additional 4 registers are published, intended for controlling the heat
pump via MODBUS writing. Writing is not implemented yet, values are read
for now.
In the newer publication there are still obvious errors, and
additional - perhaps misleading - statements for certain registers
regarding the fresh water system. Use with caution!

Acknoledgements
---------------

Thanks to user @weltmaister for identification, test and fixing of
issue #3!


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

