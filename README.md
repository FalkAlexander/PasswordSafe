# KeepassGtk
KeepassGtk is a password manager which makes use of the Keepass v.4 format.
There is the awesome pykeepass library from Philipp Schmitt used (https://github.com/pschmitt/pykeepass).

Planned Features:
* Creating a new Keepass v.4 database
* Password authentification + password changing of a database
* Creating and editing groups, entries
* Nice GUI

# Prerequisites
* Python 3.6.5 or newer
* pykeepass 2.8.1
* Gtk 3.22

# Known issues
* For creating databases is used a workaround because the library can't create new ones. There is used a clean pre-configured database which password (liufhre86ewoiwejmrcu8owe; AES-256; Argon2) is being changed.