# Update python3-zxcvbn-rs-py-sources.json

Clone the project [zxcvbn-rs-py](https://github.com/fief-dev/zxcvbn-rs-py), checkout to the respective tag:

    git clone https://github.com/fief-dev/zxcvbn-rs-py
    git -C zxcvbn-rs-py checkout TAG
    flatpak-cargo-generator zxcvbn-rs-py/Cargo.lock \
    -o flatpak/python3-zxcvbn-rs-py-sources.json

# Update python3-validators.json

    flatpak-pip-generator validators -o flatpak/python3-validators

# Update python3-pyotp.json

    flatpak-pip-generator pyotp -o flatpak/python3-pyotp

# Update python3-pykeepass.json

    flatpak-pip-generator --build-isolation pykeepass -o flatpak/python3-pykeepass

Then add `"pykeepass-build-sources.json"` as a source and `--ignore-installed` to the `pip3` command.

# Update python3-pykcs11-sources.json

    flatpak-pip-generator pykcs11 -o flatpak/python3-pykcs11-sources
