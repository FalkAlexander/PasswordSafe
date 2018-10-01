datadir = join_paths('share', 'icons')
icondir = join_paths('hicolor', 'scalable', 'apps')
if get_option('profile') == 'development'
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe.svg'),
    install_dir: join_paths(datadir, icondir),
    rename: 'org.gnome.PasswordSafeDevel.svg'
)
else
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe.svg'),
    install_dir: join_paths(datadir, icondir)
)
endif

icondir = join_paths('hicolor', 'symbolic', 'apps')
if get_option('profile') == 'development'
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe-symbolic.svg'),
    install_dir: join_paths(datadir, icondir),
    rename: 'org.gnome.PasswordSafeDevel-symbolic.svg'
)
else
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe-symbolic.svg'),
    install_dir: join_paths(datadir, icondir)
)
endif

