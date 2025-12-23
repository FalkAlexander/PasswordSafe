# Changelog

All notable changes to this project will be documented in this file.

## 12.2 - 2025-12-23
- Fix regression where OTPs codes were not loaded from 12.1

## 12.1 - 2025-12-13
- Load Entry properties lazily
- Load Entry widgets in an add_idle with low priority
- Updated translations

## 12.0 - 2025-09-13
Use newer widgets from libadwaita 1.8 and update to the GNOME 49 SDK.
- Various bug fixes
- Improve performance when sorting and filtering entries
- Add Audit feature
- Updated translations

## 11.1.1 - 2025-04-13
Fixup ci release job

## 11.1 - 2025-04-13
Declare on meson that we depend on pygobject 3.52.
- Updated translations

## 11.0 - 2025-04-05
Use newer widgets from libadwaita 1.7. and update to the GNOME 48 SDK.
- Show real database path
- Update to pykeepass 4.1.1.post1
- Add quick unlock setting
- Add fingerprint reader support
- Improve sidebar's width
- Various bug fixes
- Updated translations

## 10.4 - 2024-12-26
Minor release.
- Fix crash when closing a dialog when the db is locked
- Fix crash when using zxcvbn-rs 0.2
- Various bug fixes

## 10.3 - 2024-11-11
Minor release.
- Do not allow multiple preferences dialogs simultaneously
- Fix crash when deleting trash bin

## 10.2 - 2024-10-17
Minor release.
- Correctly select element after creating it
- Prevents data corruption when saving on certain virtual file systems
- Prevents a crash when deleting elements in trash

## 10.1 - 2024-09-21
Minor release.

- Fixes crash while searching

## 10.0 - 2024-09-20
Use newer widgets from libadwaita 1.6 and update to the GNOME 47 Sdk.
- Add tag support
- Migrate from zxcvbn to zxcvbn-rs
- Various bug fixes
- Updated translations
