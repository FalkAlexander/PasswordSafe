# KeepassGtk
KeepassGtk is a password manager which makes use of the Keepass v.4 format.
There is the awesome pykeepass library from Philipp Schmitt used (https://github.com/pschmitt/pykeepass).

###### Screenshot
![Screenshot](https://terminal.run/stuff/keepassgtk_screenshot.png)

Features:
* Creating a new Keepass v.4 database
* Password, keyfile and composite key authentification
* Creating and editing groups, entries
* Moving and deleting groups and entries
* Password randomizer
* Password changing
* Automatic database locking

# Prerequisites
* Python 3.6.5 or newer
* pykeepass 2.8.2
* Gtk 3.22

### Building / Compiling
We are using Meson as our build system. There are some easy steps to follow in order to build KeepassGtk with Meson:

```
git clone https://github.com/TerminalDotRun/KeepassGtk.git
cd KeepassGtk
meson . _build --prefix=/usr
ninja -C _build
sudo ninja -C _build install
```

### Install
* Arch Linux AUR: [keepassgtk](https://aur.archlinux.org/packages/keepassgtk-git/)

# Known issues
* For creating databases is used a workaround because the library can't create new ones. There is used a clean pre-configured database which password (liufhre86ewoiwejmrcu8owe; AES-256; AES-KDF) is being changed.

# Contact
You can contact the project through [Matrix](https://matrix.org). The room is
[#keepassgtk:disroot.org](https://matrix.to/#/#keepassgtk:disroot.org). You can
join through [any application on this list](https://matrix.org/docs/projects/try-matrix-now.html).