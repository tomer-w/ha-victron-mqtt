import json
import os

def main():
    base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    topics_path = os.path.join(base, 'victron_mqtt.json')
    en_path = os.path.join(base, 'custom_components', 'victron_mqtt', 'translations', 'en.json')
    print(f"topics_path={topics_path}")
    print(f"en_path={en_path}")
    with open(topics_path, encoding='utf-8') as f:
        topics = json.load(f)

    with open(en_path, encoding='utf-8') as f:
        en = json.load(f)

    # Merge topics: add or update entries in en.json under entity.sensor for each topic id
    entity = en.get('entity', {})
    count = 0
    for topic in topics.get('topics', []):
        topic_id = topic.get('short_id').replace('{phase}', 'lx')
        topic_name = topic.get('name')
        message_type = topic.get('message_type', 'sensor')
        # Extract the part after the dot and make it lower case
        entity_type = message_type.split('.', 1)[1].lower()
        if entity_type not in entity:
            entity[entity_type] = {}
        entity[entity_type][topic_id] = {"name": topic_name}
        count+=1
    en['entity'] = entity

    with open(en_path, 'w', encoding='utf-8') as f:
        json.dump(en, f, ensure_ascii=False, indent=2)
    print(f"Updated {count} entities")

if __name__ == '__main__':
    main()
