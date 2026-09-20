**English** | [Русский](README.ru.md)

# BLE-C600 for Home Assistant

C600 Bluetooth sensor integration based on [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), with fixes for BLE reads and retention of the last readings.

Supports pH, electrical conductivity, TDS, ORP, free chlorine, temperature, calculated salt content and battery level. Polling interval: 60 seconds.

## Installation

### Automatically

> [!TIP]
> Recommended installation method. HACS must be installed in Home Assistant.

[![Open the repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=OlegKocha&repository=BLE-C600&category=integration)

1. Click the button above and open the repository in HACS.
2. If the repository has not been added yet, open “Custom repositories” in HACS and add `https://github.com/OlegKocha/BLE-C600` with the “Integration” category.
3. Find `ble-c600` in HACS and download the integration.
4. Restart Home Assistant.

### Manually

In the Home Assistant terminal, clone the repository into a temporary directory and copy the integration to `/config/custom_components/`:

```bash
c600_tmp=$(mktemp -d)
git clone https://github.com/OlegKocha/BLE-C600.git "$c600_tmp/BLE-C600"
mkdir -p /config/custom_components
cp -R "$c600_tmp/BLE-C600/custom_components/ble_c600" /config/custom_components/
```

Restart Home Assistant. If your installation uses a configuration directory other than `/config`, replace the path in the commands.

### Configuration

1. Open “Settings → Devices & services → Add integration”.
2. Find `ble_c600` and follow the setup wizard.
3. Switch on C600 and wait for the first readings.

## Operation

Switch on C600 and wait for the first read. When the connection is lost, the last values are retained; the `data_stale` attribute indicates that they are stale, and `last_successful_read` shows the time of the last successful read. After restarting HA or reloading the integration, a new read is required: the cache is stored in memory.

## License

[MIT](LICENSE). Original project: [Dutch-Al/BLE-C600](https://github.com/Dutch-Al/BLE-C600), original code author: jdeath.

## Water dashboard example

An example table and a panel with eight sensors. Standard Home Assistant cards are used. To copy them to your own HA, use the code in the collapsible section.

### Parameter table

| Parameter | Color zones |
| :--- | :--- |
| **Water acidity or alkalinity (pH)** | 🔴 Strongly acidic environment (<5.0)<br>🟠 Moderately or slightly acidic water (5.0–6.5)<br>🟢 Neutral environment (suitable for drinking) (6.5–8.5)<br>🟣 Alkaline environment (above 8.5)<br> |
| **Mineralization (TDS)** - total dissolved solids | 🔵 Ultra-fresh water (<100 ppm)<br>🟢 Fresh water (100–1000 ppm)<br>🟠 Brackish water (1000–10000 ppm)<br>🔴 Saline water (≥10000 ppm) |
| **Electrical conductivity (EC)** - the ability of water to conduct electric current; depends on dissolved ions and temperature | 🔵 Ultrapure laboratory water (0.055–0.5 µS/cm)<br>🟣 Distilled water (0.5–10 µS/cm)<br>🟡 Reverse osmosis water, rainwater and meltwater (10–200 µS/cm)<br>🟢 Drinking tap water (200–800 µS/cm)<br>🟠 Seawater (>800 µS/cm)<br> |
| **Free chlorine** - the free chlorine content reading. The **0.2–1 ppm** range is typical of disinfected water and is not required for an unchlorinated well. | 🔵 Chlorine-free water (<0.2 ppm)<br>🟢 Ordinary tap water (0.2–1 ppm)<br>🟠 Heavily chlorinated water (1–5 ppm)<br>🔴 Heavily contaminated water (>5 ppm) |
| **Oxidation-reduction potential (ORP)** | 🟣 “Powerful reducing agent. Strong antioxidant properties.” Examples: water from household ionizers (catholyte) (below −200 mV), hydrogen water.<br><br>🔵 Weak reducing agent (antioxidant). Living water, easily absorbed by the body's cells without energy loss. Examples: fresh juices, human intracellular fluid, water from rare healing springs (−200 to −50 mV)<br><br>⚪ Transition range around zero (−50–0 mV)<br><br>🟢 Neutral zone. Close to the ORP of the body's internal environments. Examples: pure spring water, meltwater (0–150 mV)<br><br>🟡 Moderate oxidizer. Standard bottled drinking water. Requires the body to expend energy for absorption. Examples: most groundwater wells (in sand aquifers), dug wells, store-bought bottled water (150–400 mV)<br><br>🟠 High oxidation potential. The water is microbiologically safe, but is not suitable for continuous drinking in its raw state without harm to the microflora. Examples: ordinary tap water, some deep wells (400 to 650 mV)<br><br>🔴 Highest oxidizing capacity. Instant disinfection, killing any bacteria and viruses within seconds. Examples: properly chlorinated pool water, ozonated water, medical antiseptics (≥650 mV)<br><br> |
| **Salt** - calculated salt content. Calculated as **EC × 0.55** in this integration. This is not a separate analysis of sodium, chlorides or table salt. | 🔵 Ultrapure water (<50 ppm)<br>🟣 Ideal level (50–150 ppm)<br>🟢 Excellent, pleasant-tasting water (150–300 ppm)<br>🟡 Acceptable level, but the salt limit is exceeded and the water may be hard (300–600 ppm)<br>🟠 High salt content (600–1000 ppm)<br>🔴 Very high salt content (≥1000 ppm)<br><br> |
| **Water temperature** | 🔵 Below 15 °C;<br>🟣 15–<25 °C;<br>🟠 From 25 °C |
| **C600 battery** | 🔴 Below 20%;<br>🟠 20–<50%;<br>🟢 From 50% |

C600 is not a laboratory sensor and cannot guarantee an accurate assessment of water safety. Laboratory testing is required to obtain accurate measurements.

### Reading freshness

When C600 is switched off, the last saved values may still be displayed.

- **data_stale: true** — the last read did not provide a new value for this sensor.
- **data_stale: false** — the value was successfully received during the last processed poll.
- **last_successful_read** — the time of the last successful read, in UTC.

<details>
<summary>Copy the table to Home Assistant — instructions and YAML</summary>

1. Open the desired HA dashboard and enter edit mode.
2. Click “Add card” → “Manual”, or create a Markdown card and open the code editor.
3. Replace all of the card's code with the YAML below, including `type: markdown` and `content: |`.
4. Save the card and place it below the sensors. This is dashboard card code; it should not be added to `configuration.yaml`.

```yaml
type: markdown
content: |
  | Parameter | Color zones |
  | :--- | :--- |
  | **Water acidity or alkalinity (pH)** | 🔴 Strongly acidic environment (<5.0)<br>🟠 Moderately or slightly acidic water (5.0–6.5)<br>🟢 Neutral environment (suitable for drinking) (6.5–8.5)<br>🟣 Alkaline environment (above 8.5)<br> |
  | **Mineralization (TDS)** - total dissolved solids | 🔵 Ultra-fresh water (<100 ppm)<br>🟢 Fresh water (100–1000 ppm)<br>🟠 Brackish water (1000–10000 ppm)<br>🔴 Saline water (≥10000 ppm) |
  | **Electrical conductivity (EC)** - the ability of water to conduct electric current; depends on dissolved ions and temperature | 🔵 Ultrapure laboratory water (0.055–0.5 µS/cm)<br>🟣 Distilled water (0.5–10 µS/cm)<br>🟡 Reverse osmosis water, rainwater and meltwater (10–200 µS/cm)<br>🟢 Drinking tap water (200–800 µS/cm)<br>🟠 Seawater (>800 µS/cm)<br> |
  | **Free chlorine** - the free chlorine content reading. The **0.2–1 ppm** range is typical of disinfected water and is not required for an unchlorinated well. | 🔵 Chlorine-free water (<0.2 ppm)<br>🟢 Ordinary tap water (0.2–1 ppm)<br>🟠 Heavily chlorinated water (1–5 ppm)<br>🔴 Heavily contaminated water (>5 ppm) |
  | **Oxidation-reduction potential (ORP)** | 🟣 “Powerful reducing agent. Strong antioxidant properties.” Examples: water from household ionizers (catholyte) (below −200 mV), hydrogen water.<br><br>🔵 Weak reducing agent (antioxidant). Living water, easily absorbed by the body's cells without energy loss. Examples: fresh juices, human intracellular fluid, water from rare healing springs (−200 to −50 mV)<br><br>⚪ Transition range around zero (−50–0 mV)<br><br>🟢 Neutral zone. Close to the ORP of the body's internal environments. Examples: pure spring water, meltwater (0–150 mV)<br><br>🟡 Moderate oxidizer. Standard bottled drinking water. Requires the body to expend energy for absorption. Examples: most groundwater wells (in sand aquifers), dug wells, store-bought bottled water (150–400 mV)<br><br>🟠 High oxidation potential. The water is microbiologically safe, but is not suitable for continuous drinking in its raw state without harm to the microflora. Examples: ordinary tap water, some deep wells (400 to 650 mV)<br><br>🔴 Highest oxidizing capacity. Instant disinfection, killing any bacteria and viruses within seconds. Examples: properly chlorinated pool water, ozonated water, medical antiseptics (≥650 mV)<br><br> |
  | **Salt** - calculated salt content. Calculated as **EC × 0.55** in this integration. This is not a separate analysis of sodium, chlorides or table salt. | 🔵 Ultrapure water (<50 ppm)<br>🟣 Ideal level (50–150 ppm)<br>🟢 Excellent, pleasant-tasting water (150–300 ppm)<br>🟡 Acceptable level, but the salt limit is exceeded and the water may be hard (300–600 ppm)<br>🟠 High salt content (600–1000 ppm)<br>🔴 Very high salt content (≥1000 ppm)<br><br> |
  | **Water temperature** | 🔵 Below 15 °C;<br>🟣 15–<25 °C;<br>🟠 From 25 °C |
  | **C600 battery** | 🔴 Below 20%;<br>🟠 20–<50%;<br>🟢 From 50% |

  C600 is not a laboratory sensor and cannot guarantee an accurate assessment of water safety. Laboratory testing is required to obtain accurate measurements.

  ### Reading freshness

  When C600 is switched off, the last saved values may still be displayed.

  - **data_stale: true** — the last read did not provide a new value for this sensor.
  - **data_stale: false** — the value was successfully received during the last processed poll.
  - **last_successful_read** — the time of the last successful read, in UTC.
```

</details>

### Dashboard sensors

![Example C600 dashboard in Home Assistant: water composition, additional parameters, temperature and power](docs/images/water-dashboard.png)

<details>
<summary>Copy the sensors to Home Assistant — instructions and YAML</summary>

1. First, add the C600 integration and wait for readings.
2. Find your eight sensors in “Developer tools → States”. In the example below, `sensor.51_d5_ef_19_f3_86_…` are the author's device entity IDs. Replace each `entity:` with your sensor's actual entity ID. If only the prefix differs, you can replace `51_d5_ef_19_f3_86` throughout the block. Then check all eight entity IDs.
3. For ORP, check the unit in “States”: the example uses **mV**. The integration uses V as its native unit; select mV in the ORP entity settings and check the result. The `unit: mV` field in the card changes the label, not the numeric value. If you keep the state in V, use `unit: V`, `min: -1`, `max: 1`, and change the ORP thresholds to `-1`, `-0.2`, `-0.05`, `0`, `0.15`, `0.4`, `0.65`.
4. On the dashboard: “Edit” → “Add card” → “Manual”. Paste the entire block starting with `type: vertical-stack`, replacing the old card code.
5. Check the preview and save. If “Entity not found” appears, check the corresponding `entity:`.

**Color boundaries:** each `from` value is included in the next segment. For example, TDS 1000 is orange, Salt 150 is green, and ORP −200 is blue. pH 8.50 remains green, while 8.51 is purple; chlorine 1.0 remains green, while 1.1 is yellow-orange. In the author's YAML, EC starts with purple at 0, and the blue laboratory zone in the table is not shown separately. The settings are preserved as in the screenshot. The gauge maximum is the display limit, not the instrument's measurement limit.

```yaml
type: vertical-stack
cards:
- type: grid
  title: Water composition
  columns: 3
  square: false
  cards:
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_ph
    name: Acidity
    needle: true
    min: 0
    max: 14
    segments:
    - from: 0
      color: '#C63D32'
    - from: 5
      color: '#EF8C32'
    - from: 6.5
      color: '#5F9E4B'
    - from: 8.51
      color: '#8E6CBB'
    unit: pH
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_total_dissolved_solids
    name: Mineralization
    needle: true
    min: 0
    max: 15000
    segments:
    - from: 0
      color: '#4299D6'
    - from: 100
      color: '#5F9E4B'
    - from: 1000
      color: '#EF8C32'
    - from: 10000
      color: '#C63D32'
    unit: ppm
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_electrical_conductivity
    name: Conductivity
    needle: true
    min: 0
    max: 2000
    segments:
    - from: 0
      color: '#8E6CBB'
    - from: 10
      color: '#F0C34D'
    - from: 200
      color: '#5F9E4B'
    - from: 801
      color: '#EF8C32'
    unit: µS/cm
- type: grid
  title: Additional parameters
  columns: 3
  square: false
  cards:
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_free_chlorine
    name: Free chlorine
    needle: true
    min: 0
    max: 6
    segments:
    - from: 0
      color: '#4299D6'
    - from: 0.2
      color: '#388E3C'
    - from: 1.1
      color: '#F0AD3D'
    - from: 5.1
      color: '#C63D32'
    unit: ppm
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_oxidation_reduction_potential
    name: ORP
    needle: true
    min: -1000
    max: 1000
    segments:
    - from: -1000
      color: '#8E6CBB'
    - from: -200
      color: '#4299D6'
    - from: -50
      color: '#9E9E9E'
    - from: 0
      color: '#5F9E4B'
    - from: 150
      color: '#F0C34D'
    - from: 400
      color: '#EF8C32'
    - from: 650
      color: '#C63D32'
    unit: mV
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_salt
    name: Salt
    needle: true
    min: 0
    max: 1500
    segments:
    - from: 0
      color: '#4299D6'
    - from: 50
      color: '#8E6CBB'
    - from: 150
      color: '#5F9E4B'
    - from: 300
      color: '#F0C34D'
    - from: 600
      color: '#EF8C32'
    - from: 1000
      color: '#C63D32'
- type: grid
  title: Temperature and power
  columns: 2
  square: false
  cards:
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_temperature
    name: Water temperature
    needle: true
    min: 0
    max: 40
    segments:
    - from: 0
      color: '#4299D6'
    - from: 15
      color: '#8E6CBB'
    - from: 25
      color: '#F0AD3D'
  - type: gauge
    entity: sensor.51_d5_ef_19_f3_86_battery
    name: C600 battery
    needle: true
    min: 0
    max: 100
    segments:
    - from: 0
      color: '#C63D32'
    - from: 20
      color: '#F0AD3D'
    - from: 50
      color: '#5F9E4B'
```

</details>
