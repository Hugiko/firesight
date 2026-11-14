# FireSight unified microgravity combustion tests: data dictionary

622 tests from NASA Physical Sciences Informatics (PSI) tables and NASA/TP-2015-216046 (FLEX).
Units are SI-consistent. Empty cells mean the value was not available in the source.

| Column | Meaning | Unit |
| --- | --- | --- |
| `test_id` | Unique test identifier (FireSight) |  |
| `investigation` | PSI investigation id (PSI-26 BASS, PSI-20 Saffire-I, PSI-100 Saffire-III, PSI-98 ACME BRE, PSI-159 ACME CFI-G, PSI-69 FLEX) |  |
| `date` | Test date when tabulated | ISO 8601 |
| `fuel` | Fuel or material as named in the source |  |
| `fuel_phase` | solid, liquid or gas |  |
| `material_class` | Material family |  |
| `geometry` | Sample or burner geometry |  |
| `size_mm` | Characteristic size (droplet initial diameter, sample width) | mm |
| `o2_pct` | Oxygen concentration | % by volume |
| `pressure_kpa` | Total pressure | kPa |
| `diluent` | Main inert gas |  |
| `co2_pct` | CO2 concentration (FLEX suppressant tests) | % by volume |
| `he_pct` | Helium concentration (FLEX diluent tests) | % by volume |
| `flow_cm_s` | Imposed flow velocity | cm/s |
| `flow_direction` | Flow configuration |  |
| `gravity` | micro (flight) or 1g (ground) |  |
| `ignited` | Whether ignition occurred | boolean |
| `outcome` | Outcome category as reported or mapped |  |
| `burn_time_s` | Burn duration | s |
| `extinction_diameter_mm` | Droplet diameter at extinction (FLEX) | mm |
| `burning_rate` | Droplet burning-rate constant (FLEX) | mm2/s |
| `adiabatic_temp_k` | Adiabatic flame temperature (ACME CFI-G table) | K |
| `notes` | Source notes and FireSight cleaning notes |  |
| `source` | Source table or report |  |
| `confidence` | measured (PSI table), extracted (NASA report) or estimated |  |

## Provenance

- PSI study tables: https://psi.nasa.gov (BASS, Saffire-I/III, ACME BRE, ACME CFI-G). Raw files require a free PSI login and are not redistributed.
- FLEX Table IX extracted from NASA/TP-2015-216046 (NTRS).
- Cleaning: FLEX pressures below 50 mmHg treated as typos and left empty; '~' and dashes parsed as approximate or missing.

## Use of SI

The extraction and cleaning code was written with an SI coding assistant; the values come from the NASA sources above.
