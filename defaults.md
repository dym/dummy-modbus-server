# Solis inverter register defaults (just for demonstration purposes)

Hand-made starter set (hybrid inverter, idle-ish daytime state). Replace it with the output of `dump_defaults.py` to mirror a real device. Value = raw 16-bit register value (decimal or 0x hex); Scale/Unit are informational only. Registers not listed read as 0 (or raise an error with `--strict`).

| Address | Kind | Name | Value | Writable | Scale | Unit |
|---|---|---|---|---|---|---|
| 33000 | input | Model No | 3333 | no |  |  |
| 33001 | input | DSP Version | 22 | no |  |  |
| 33002 | input | HMI Version | 11 | no |  |  |
| 33003 | input | Protocol Version | 1 | no |  |  |
| 33004 | input | Serial Number word 1 | 0xffff | no |  |  |
| 33005 | input | Serial Number word 2 | 0xeeee | no |  |  |
| 33006 | input | Serial Number word 3 | 0xdddd | no |  |  |
| 33007 | input | Serial Number word 4 | 0xcccc | no |  |  |
| 33008 | input | Serial Number word 5 | 0xbbbb | no |  |  |
| 33009 | input | Serial Number word 6 | 0xaaaa | no |  |  |
| 33010 | input | Serial Number word 7 | 0x9999 | no |  |  |
| 33011 | input | Serial Number word 8 | 0x8888 | no |  |  |
| 33012 | input | Serial Number word 9 | 0x7777 | no |  |  |
| 33013 | input | Serial Number word 10 | 0x6666 | no |  |  |
| 33014 | input | Serial Number word 11 | 0x5555 | no |  |  |
| 33015 | input | Serial Number word 12 | 0x4444 | no |  |  |
| 33016 | input | Serial Number word 13 | 0x3333 | no |  |  |
| 33017 | input | Serial Number word 14 | 0x2222 | no |  |  |
| 33018 | input | Serial Number word 15 | 0x1111 | no |  |  |
| 33019 | input | Serial Number word 16 | 0x0001 | no |  |  |
| 33022 | input | Clock Year | 26 | no |  |  |
| 33023 | input | Clock Month | 11 | no |  |  |
| 33024 | input | Clock Day | 24 | no |  |  |
| 33025 | input | Clock Hours | 12 | no |  |  |
| 33026 | input | Clock Minutes | 0 | no |  |  |
| 33027 | input | Clock Seconds | 0 | no |  |  |
| 33029 | input | PV Total Energy (high word) | 0 | no | 1 | kWh |
| 33030 | input | PV Total Energy (low word) | 8421 | no | 1 | kWh |
| 33035 | input | PV Today Energy | 123 | no | 0.1 | kWh |
| 33036 | input | PV Yesterday Energy | 98 | no | 0.1 | kWh |
| 33049 | input | PV Voltage 1 | 3850 | no | 0.1 | V |
| 33050 | input | PV Current 1 | 52 | no | 0.1 | A |
| 33051 | input | PV Voltage 2 | 3790 | no | 0.1 | V |
| 33052 | input | PV Current 2 | 48 | no | 0.1 | A |
| 33057 | input | Total PV Power (high word) | 0 | no | 1 | W |
| 33058 | input | Total PV Power (low word) | 3800 | no | 1 | W |
| 33073 | input | A Phase Voltage | 2300 | no | 0.1 | V |
| 33076 | input | A Phase Current | 120 | no | 0.1 | A |
| 33079 | input | Active Power (high word) | 0 | no | 1 | W |
| 33080 | input | Active Power (low word) | 2700 | no | 1 | W |
| 33093 | input | Temperature | 412 | no | 0.1 | C |
| 33094 | input | Grid Frequency | 5000 | no | 0.01 | Hz |
| 33095 | input | Status | 3 | no |  |  |
| 33121 | input | Operating Status Bits | 1 | no |  |  |
| 33122 | input | Operating Mode | 2 | no |  |  |
| 33132 | input | Storage Control Switching Value | 2 | no |  |  |
| 33133 | input | Battery Voltage | 520 | no | 0.1 | V |
| 33134 | input | Battery Current | 50 | no | 0.1 | A |
| 33135 | input | Battery Current Direction | 0 | no |  |  |
| 33139 | input | Battery SOC | 85 | no | 1 | % |
| 33140 | input | Battery SOH | 100 | no | 1 | % |
| 33147 | input | Household load power | 1200 | no | 1 | W |
| 33148 | input | Backup Load power | 0 | no | 1 | W |
| 33149 | input | Battery Power (high word) | 0 | no | 1 | W |
| 33150 | input | Battery Power (low word) | 260 | no | 1 | W |
| 33151 | input | AC Grid Port Power (high word) | 0 | no | 1 | W |
| 33152 | input | AC Grid Port Power (low word) | 1500 | no | 1 | W |
| 33161 | input | Total Battery Charge Energy (high word) | 0 | no | 1 | kWh |
| 33162 | input | Total Battery Charge Energy (low word) | 1520 | no | 1 | kWh |
| 33163 | input | Today Battery Charge Energy | 45 | no | 0.1 | kWh |
| 33165 | input | Total Battery Discharge Energy (high word) | 0 | no | 1 | kWh |
| 33166 | input | Total Battery Discharge Energy (low word) | 1410 | no | 1 | kWh |
| 33167 | input | Today Battery Discharge Energy | 20 | no | 0.1 | kWh |
| 33171 | input | Today Energy Imported From Grid | 31 | no | 0.1 | kWh |
| 33175 | input | Today Energy Fed Into Grid | 64 | no | 0.1 | kWh |
| 33179 | input | Today Energy Consumption | 87 | no | 0.1 | kWh |
| 33289 | input | TOU Function Version | 0xAA55 | no |  |  |
| 35000 | input | Inverter Type Definition | 0x0020 | no |  |  |
| 43007 | holding | Inverter Power State (On/Off) | 190 | yes |  |  |
| 43009 | holding | Battery Model | 2 | yes |  |  |
| 43010 | holding | Max Charge SOC | 100 | yes | 1 | % |
| 43011 | holding | Overdischarge SOC | 20 | yes | 1 | % |
| 43012 | holding | Max Charge Current | 500 | yes | 0.1 | A |
| 43013 | holding | Max Discharge Current | 500 | yes | 0.1 | A |
| 43018 | holding | Force Charge SOC | 10 | yes | 1 | % |
| 43019 | holding | Battery Rated Capacity | 100 | yes | 1 | Ah |
| 43024 | holding | Backup SOC | 20 | yes | 1 | % |
| 43070 | holding | Output Limit Gate | 1 | yes |  |  |
| 43073 | holding | Grid feed in Switch value | 0 | yes |  |  |
| 43074 | holding | Backflow Power | 0 | yes | 1 | W |
| 43081 | holding | Output Power Clamp | 5000 | yes | 1 | W |
| 43090 | holding | Grid overvoltage limit HV1 | 2530 | yes | 0.1 | V |
| 43092 | holding | Grid overvoltage limit HV2 | 2645 | yes | 0.1 | V |
| 43110 | holding | Storage control Switch value | 33 | yes |  |  |
| 43111 | holding | Backup Supply value | 0 | yes |  |  |
| 43117 | holding | Battery Max Charge Current | 500 | yes | 0.1 | A |
| 43118 | holding | Battery Max Discharge Current | 500 | yes | 0.1 | A |
| 43128 | holding | RC Inverter AC Grid Active Power | 0 | yes | 1 | W |
| 43132 | holding | RC Grid Adjustment | 0 | yes |  |  |
| 43135 | holding | RC Force Battery Charge/discharge | 0 | yes |  |  |
| 43137 | holding | Off-Grid Overdischarge SOC | 20 | yes | 1 | % |
| 43195 | holding | Export Calibration | 0 | yes | 1 | W |
| 43249 | holding | Special Settings (bit flags) | 0 | yes |  |  |
| 43282 | holding | RC Timeout | 5 | yes | 1 | min |
| 43291 | holding | Flexible Export Backflow Power | 0 | yes | 1 | W |
| 43292 | holding | Flexible Export Enabling Switch | 0 | yes |  |  |
| 43302 | holding | Hybrid auxiliary control flags | 0 | yes |  |  |
| 43452 | holding | Grid overvoltage limit HV3 | 2760 | yes | 0.1 | V |
| 43483 | holding | Hybrid Function Control | 0 | yes |  |  |
| 43707 | holding | Time of Use V2 Switch (bit flags) | 0 | yes |  |  |
| 43708 | holding | Grid Time of Use Charge cut off SOC (Slot 1) | 100 | yes | 1 | % |
| 43709 | holding | Grid Time of Use Charge battery current (Slot 1) | 500 | yes | 0.1 | A |
| 43710 | holding | Grid Time of Use Charge cut off voltage (Slot 1) | 0 | yes | 0.1 | V |
| 43711 | holding | Grid Time of Use Charge Start Hour (Slot 1) | 0 | yes |  |  |
| 43712 | holding | Grid Time of Use Charge Start Minute (Slot 1) | 0 | yes |  |  |
| 43713 | holding | Grid Time of Use Charge End Hour (Slot 1) | 6 | yes |  |  |
| 43714 | holding | Grid Time of Use Charge End Minute (Slot 1) | 0 | yes |  |  |
| 43750 | holding | Grid Time of Use Discharge cut off SOC (Slot 1) | 20 | yes | 1 | % |
| 43751 | holding | Grid Time of Use Discharge battery current (Slot 1) | 500 | yes | 0.1 | A |
| 43752 | holding | Grid Time of Use Discharge cut off voltage (Slot 1) | 0 | yes | 0.1 | V |
| 43753 | holding | Grid Time of Use Discharge Start Hour (Slot 1) | 18 | yes |  |  |
| 43754 | holding | Grid Time of Use Discharge Start Minute (Slot 1) | 0 | yes |  |  |
| 43755 | holding | Grid Time of Use Discharge End Hour (Slot 1) | 22 | yes |  |  |
| 43756 | holding | Grid Time of Use Discharge End Minute (Slot 1) | 0 | yes |  |  |
| 44100 | holding | Dispatch Active | 0 | yes |  |  |
| 44280 | holding | Remote Active Power Control Command | 0 | yes |  |  |
