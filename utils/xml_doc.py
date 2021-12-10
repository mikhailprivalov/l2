import os
import xml.etree.ElementTree as ET
from laboratory.settings import BASE_DIR


def edit_xml_template(data):
    directories_file_path = os.path.join(BASE_DIR, "utils/xml_template/death_max.xml")
    tree = ET.parse(directories_file_path)
    root = tree.getroot()
    print(root)
    xml_str = ET.tostring(root, encoding='utf8').decode('utf8')
    for i in range(8):
        xml_str = xml_str.replace(f"/ns{i}:", "").replace(f"ns{i}:", "")

    print(type(xml_str))
    f = open(f'{BASE_DIR}/utils/xml_template/books-mod.xml', 'w')
    f.write(xml_str)
    f.close()

    return True
