import json
import os

def main():
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    topics_path = os.path.join(base, 'victron_mqtt.json')
    translations_dir = os.path.join(base, 'custom_components', 'victron_mqtt', 'translations')
    en_path = os.path.join(translations_dir, 'en.json')
    print(f"topics_path={topics_path}")
    print(f"en_path={en_path}")
    with open(topics_path, encoding='utf-8') as f:
        topics_data = json.load(f)

    with open(en_path, encoding='utf-8') as f:
        en = json.load(f)

    # Build enum lookup: enum_name -> {lowercase_id: human_readable_name}
    enum_lookup = {}
    for enum_def in topics_data.get('enums', []):
        enum_name = enum_def.get('name')
        enum_values = {}
        for ev in enum_def.get('EnumValues', []):
            # Use lowercase id as key, name as value
            enum_values[ev.get('id', '').lower()] = ev.get('name', '')
        enum_lookup[enum_name] = enum_values

    # MetricTypes that map to a SensorDeviceClass in entity.py.
    # These get native_unit_of_measurement set in code, so the translation
    # file must NOT carry unit_of_measurement for them.
    DEVICE_CLASS_METRIC_TYPES = {
        "MetricType.POWER",
        "MetricType.APPARENT_POWER",
        "MetricType.ENERGY",
        "MetricType.VOLTAGE",
        "MetricType.CURRENT",
        "MetricType.FREQUENCY",
        "MetricType.ELECTRIC_STORAGE_PERCENTAGE",
        "MetricType.TEMPERATURE",
        "MetricType.HUMIDITY",
        "MetricType.PRESSURE",
        "MetricType.DISTANCE",
        "MetricType.POWER_FACTOR",
        "MetricType.SPEED",
        "MetricType.LIQUID_VOLUME",
        "MetricType.DURATION",
        "MetricType.IRRADIANCE",
    }

    # Update topics: add or update entries in en.json under entity.sensor for each topic id
    entity = {}
    count = 0
    for topic in topics_data.get('topics', []):
        translation_key = topic.get('short_id').replace('{', '').replace('}', '') # same as in common.py
        topic_name = topic.get('generic_name')
        topic_unit = topic.get('unit_of_measurement')
        topic_metric_type = topic.get('metric_type')
        message_type = topic.get('message_type')
        is_adjustable_suffix = topic.get('is_adjustable_suffix')
        enum_name = topic.get('enum')
        is_main_topic = topic.get("main_topic", False)
        is_hidden = topic.get("hidden", False)

        if is_hidden:
            continue
        
        # Extract the part after the dot and make it lower case
        if '.' in message_type:
            entity_type = message_type.split('.', 1)[1].lower()
        else:
            # Fallback for old format
            entity_type = message_type.lower()

        if entity_type == "service":
            continue

        # Build entity entry with name and optional state for enums.
        # Only include unit_of_measurement in the translation when the metric
        # does NOT have a device_class (those get native_unit in code instead).
        entity_entry = {} if is_main_topic else {"name": topic_name}
        has_device_class = topic_metric_type in DEVICE_CLASS_METRIC_TYPES
        is_dynamic_unit = topic_unit is not None and "{" in topic_unit
        if topic_unit is not None and topic_unit != "%" and not has_device_class and not is_dynamic_unit:
            entity_entry["unit_of_measurement"] = topic_unit
        if entity_type != "button" and enum_name and enum_name in enum_lookup:
            entity_entry["state"] = enum_lookup[enum_name]

        # Add to original entity type
        if entity_type not in entity:
            entity[entity_type] = {}
        entity[entity_type][translation_key] = entity_entry
        count += 1
        
        # If is_adjustable_suffix is set, also add to sensor entity type
        if is_adjustable_suffix is not None and entity_type != 'sensor':
            if 'sensor' not in entity:
                entity['sensor'] = {}
            entity['sensor'][translation_key] = entity_entry
        # to support READ_ONLY we need everything in sensor and in binary_sensor
        if entity_type == 'switch':
            if 'binary_sensor' not in entity:
                entity['binary_sensor'] = {}
            entity['binary_sensor'][translation_key] = entity_entry
        if entity_type in ['number', 'select']:
            if 'sensor' not in entity:
                entity['sensor'] = {}
            entity['sensor'][translation_key] = entity_entry
    # Sort the entity dictionary and its nested dictionaries
    sorted_entity = {}
    for entity_type in sorted(entity.keys()):
        sorted_entity[entity_type] = {}
        for translation_key in sorted(entity[entity_type].keys()):
            entry = entity[entity_type][translation_key]
            sorted_entry = {}
            if "name" in entry:
                sorted_entry["name"] = entry["name"]
            if "unit_of_measurement" in entry:
                sorted_entry["unit_of_measurement"] = entry["unit_of_measurement"]
            if "state" in entry:
                # Sort the state dictionary alphabetically by key
                sorted_entry["state"] = dict(sorted(entry["state"].items()))
            sorted_entity[entity_type][translation_key] = sorted_entry
    
    en['entity'] = sorted_entity

    # Build lookup of units from generated English entity translations
    units_lookup = {}
    for entity_type, entries in sorted_entity.items():
        units_lookup[entity_type] = {}
        for translation_key, entry in entries.items():
            if 'unit_of_measurement' in entry:
                units_lookup[entity_type][translation_key] = entry['unit_of_measurement']

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"Updated {count} entities")

if __name__ == '__main__':
    main()
