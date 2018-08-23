# Password Safe
Password Safe is a password manager which makes use of the Keepass v.4 format.
It integrates perfectly with the GNOME desktop and provides an easy and uncluttered interface for the management of password databases.

![Screenshot](https://terminal.run/stuff/overview.png)

## Features:
* ⭐ Create and import a Keepass v.4 safe
* 🔐 Password, keyfile and composite key authentification
* 📝 Create and edit groups, entries
* 🗑 Move and delete groups and entries
* 🎲 Password randomizer
* 🛠 Database password changing
* 🔎 Search tool with local, global and fulltext filter
* 🕐 Automatic database lock during inactivity

# Installation
## Development Flatpak
Download the [latest artifact](https://gitlab.gnome.org/World/PasswordSafe/-/jobs/artifacts/master/download?job=flatpak) and extract it.  
To install, open the flatpak package with GNOME Software and install it.  
If you don't have GNOME Software then run
```
flatpak install passwordsafe-git.flatpak
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
flatpak-builder --repo=repo passwordsafe-git flatpak/org.gnome.PasswordSafe.json --force-clean
# Create the Flatpak
flatpak build-export repo passwordsafe-git
flatpak build-bundle repo passwordsafe-git.flatpak org.gnome.PasswordSafe
# Install the Flatpak
flatpak install passwordsafe-git.flatpak

```


#### Option 3: with Meson
##### Prerequisites:
* Python 3.6.5 or newer
* pykeepass 2.8.2
* Gtk 3.22
* Meson
* Git

```
git clone https://gitlab.gnome.org/World/PasswordSafe.git
cd PasswordSafe
meson . _build --prefix=/usr
ninja -C _build
sudo ninja -C _build install
```

## Install via distribution package manager
* Arch Linux: [passwordsafe-git](https://aur.archlinux.org/packages/gnome-passwordsafe-git/)

# Translations
Helping to translate Password Safe or add support to a new language is very welcome.  
You can find everything you need at: https://l10n.gnome.org/module/PasswordSafe/

# Supported encryption algorithms
Fully supported are AES 256 encryption algorithm and AES-KDF (KDBX 3.1) derivation algorithm (KeepassXC defaults).
Other algorithms are not supported right now and can may or may not work and/or produce failures.

# Data protection
Please be careful when using development versions. Create enough backups if you're using a production database with Password Safe. It is possible that data loss will occur, though I give my best that this will never happen.  

Development versions create a backup of your database on unlocking by default. These can be found at ```~/.cache/passwordsafe/backup/``` where every backup is named by database name and date. If you don't want this behavior you can turn it off via dconf:  
```
gsettings set org.gnome.PasswordSafe development-backup-mode false
```

# Known issues
* For creating databases is used a workaround because the library can't create new ones (yet).

# Used libraries
There is the awesome pykeepass library from Philipp Schmitt used (https://github.com/pschmitt/pykeepass).

# Contact
You can contact the project through [Matrix](https://matrix.org). The room is
[#keepassgtk:disroot.org](https://matrix.to/#/#keepassgtk:disroot.org). You can
join through [any application on this list](https://matrix.org/docs/projects/try-matrix-now.html).
