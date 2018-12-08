from gi.repository import Gio
from lxml import etree


class OATH_XML_Builder():
    filepath = NotImplemented
    tree = NotImplemented

    def __init__(self, filepath):
        self.filepath = filepath

    def create_xml(self, otp_count, look_ahead, secret):
        root_element = etree.Element("OneTimePasswordMeta")

        type_element = etree.SubElement(root_element, "Type")
        type_element.text = "OATH HOTP: RFC 4226"

        version_element = etree.SubElement(root_element, "Version")
        version_element.text = "1.0"

        generator_element = etree.SubElement(root_element, "Generator")
        generator_element.text = "PasswordSafe"

        secrets_element = etree.SubElement(root_element, "Secrets")
        encrypted_element = etree.SubElement(secrets_element, "Encrypted")

        synced_counter_element = etree.SubElement(root_element, "SyncedCounter")
        synced_counter_element.text = "0"

        otp_count_element = etree.SubElement(root_element, "OTPCount")
        otp_count_element.text = str(otp_count)

        look_ahead_count = etree.SubElement(root_element, "LookAheadCount")
        look_ahead_count.text = str(look_ahead)

        shared_secret_element = etree.SubElement(encrypted_element, "SharedSecret")
        shared_secret_element.text = str(secret)

        plain = etree.tostring(root_element, encoding="utf-8", xml_declaration=True, pretty_print=True)
        self.write_xml(plain)

    def parse_xml(self):
        self.tree = etree.ElementTree.parse(self.filepath)

    def set_secret_element(self, secret):
        root = self.tree.getroot()
        for elem in root.iter("SharedSecret"):
            elem.text = secret

    def get_secret_element(self):
        root = self.tree.getroot()
        for elem in root.iter("SharedSecret"):
            return elem.text

    def set_synced_counter(self, count):
        root = self.tree.getroot()
        for elem in root.iter("SyncedCounter"):
            return elem.text = count

    def increase_synced_counter(self):
        root = self.tree.getroot()
        steps = 0
        for elem in root.iter("OTPCount"):
            steps = elem.text

        for elem in root.iter("SyncedCounter"):
            elem.text = str(int(elem.text) + int(steps))

    def get_synced_counter(self):
        root = self.tree.getroot()
        for elem in root.iter("SyncedCounter"):
            return elem.text

    def get_otp_count(self):
        root = self.tree.getroot()
        for elem in root.iter("OTPCount"):
            return elem.text

    def build_xml_tree(self):
        plain = etree.tostring(self.root, encoding="utf-8", xml_declaration=True, pretty_print=True)
        return plain

    def write_xml(self, plain):
        xml_file = Gio.File.new_for_path(self.filepath)
        output_stream = xml_file.replace(None, False, Gio.FileCreateFlags.REPLACE_DESTINATION | Gio.FileCreateFlags.PRIVATE, None)
        output_stream.write_all(plain)
        output_stream.close()

