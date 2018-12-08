from passwordsafe.oath_xml_builder import OATH_XML_Builder
import pyotp


class HOTP_Helper():
    shared_secret = NotImplemented
    oath_xml_builder = NotImplemented

    def __init__(self, shared_secret):
        self.shared_secret = shared_secret

    def get_future_hotp_token(self):
        hotp = pyotp.HOTP(self.shared_secret)
        synced_counter = int(self.oath_xml_builder.get_synced_counter())
        otp_count = int(self.oath_xml_builder.get_otp_count())
        token = ""
        for i in range(synced_counter, synced_counter + otp_count):
            token += hotp.at(i)
        
