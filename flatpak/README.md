# Update python3-zxcvbn-rs-py-sources.json

Clone the project [zxcvbn-rs-py](https://github.com/fief-dev/zxcvbn-rs-py), checkout to the respective tag:

    git clone https://github.com/fief-dev/zxcvbn-rs-py
    git -C zxcvbn-rs-py checkout TAG
    cargo -C zxcvbn-rs-py generate-lockfile
    flatpak-cargo-generator zxcvbn-rs-py/Cargo.lock \
    -o flatpak/python3-zxcvbn-rs-py-sources.json
