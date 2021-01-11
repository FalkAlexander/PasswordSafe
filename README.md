# Password Safe
Password Safe is a password manager which integrates perfectly with the GNOME desktop and provides an easy and uncluttered interface for the management of password databases.

<img src="https://gitlab.gnome.org/World/PasswordSafe/-/raw/master/screenshots/browser.png" width="800px" />

## Features:
* ⭐ Create or import a KeePass v.4 safe
* 🔐 Password, keyfile and composite key authentication
* 📝 Create and edit groups and entries
* ✨ Assign a color and additional attributes to entries
* 🗑 Move and delete groups and entries
* 📎 Add files to your encrypted database
* 🔗 Link multiple properties together with references
* 🎲 Cryptographically strong password and passphrase generator
* 🛠 Database password and keyfile changing
* 🔎 Search tool with local, global and fulltext filter
* 🕐 Automatic database lock during inactivity and session lock
* 📲 Responsive UI for both desktop and mobile

# Installation
## Install via distribution package manager
In distribution package manager, you can find Password Safe under name `gnome-passwordsafe`.

[![Packaging status](https://repology.org/badge/vertical-allrepos/gnome-passwordsafe.svg)](https://repology.org/project/gnome-passwordsafe/versions)


## Install via Flathub

<a href="https://flathub.org/apps/details/org.gnome.PasswordSafe">
<img src="https://flathub.org/assets/badges/flathub-badge-i-en.png" width="190px" />
</a>

## Install Development Flatpak
Download the [latest artifact](https://gitlab.gnome.org/World/PasswordSafe/-/jobs/artifacts/master/download?job=flatpak) and extract it.  
To install, open the flatpak package with GNOME Software and install it.  
If you don't have GNOME Software then run
```
flatpak install org.gnome.PasswordSafeDevel.flatpak
```


## Building from source


#### Option 1: with GNOME Builder
Open GNOME Builder, click the "Clone..." button, paste the repository url.
Clone the project and hit the ![](https://terminal.run/stuff/run_button.png) button to start building Password Safe.

#### Option 2: with Flatpak Builder
```
# Clone Password Safe repository
git clone https://gitlab.gnome.org/World/PasswordSafe.git
cd PasswordSafe
# Add Flathub repository
flatpak remote-add flathub --if-not-exists https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-add gnome-nightly --if-not-exists https://sdk.gnome.org/gnome-nightly.flatpakrepo
# Install the required GNOME runtimes
flatpak install gnome-nightly org.gnome.Platform//master org.gnome.Sdk//master
# Start building
flatpak-builder --repo=repo org.gnome.PasswordSafeDevel flatpak/org.gnome.PasswordSafe.json --force-clean
# Create the Flatpak
flatpak build-export repo org.gnome.PasswordSafeDevel
flatpak build-bundle repo org.gnome.PasswordSafeDevel.flatpak org.gnome.PasswordSafeDevel
# Install the Flatpak
flatpak install org.gnome.PasswordSafeDevel.flatpak

```


#### Option 3: with Meson
##### Prerequisites:
* python >= 3.7.9
* [pykeepass](https://github.com/libkeepass/pykeepass) >= 3.2.1
* gtk >= 3.24.1
* libhandy >= 1.0.0
* libpwquality >= 1.4.0
* meson >= 0.51.0
* git

```
git clone https://gitlab.gnome.org/World/PasswordSafe.git
cd PasswordSafe
meson . _build --prefix=/usr
ninja -C _build
sudo ninja -C _build install
```

# Translations
Helping to translate Password Safe or add support to a new language is very welcome.  
You can find everything you need at: [l10n.gnome.org/module/PasswordSafe/](https://l10n.gnome.org/module/PasswordSafe/)

# Supported encryption algorithms
### Encryption algorithms:
* AES 256-bit
* Twofish 256-bit
* ChaCha20 256-bit

### Derivation algorithms:
* Argon2 KDBX4
* AES-KDF KDBX 3.1

# Data protection
Please be careful when using development versions. Create enough backups if you're using a production database with a Password Safe development version. It is possible that data loss will occur, though I give my best that this will never happen.  

Development versions create a backup of your database on unlocking by default. These can be found at ```~/.cache/passwordsafe/backup/``` where every backup is named by database name and date. If you don't want this behavior you can turn it off via dconf:  
```
gsettings set org.gnome.PasswordSafe development-backup-mode false
```

# Contact
You can contact through chat (Matrix protocol) on [#passwordsafe:gnome.org](https://matrix.to/#/#passwordsafe:gnome.org) channel.
