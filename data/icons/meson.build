datadir = join_paths('share', 'icons')
icondir = join_paths('hicolor', 'scalable', 'apps')
if get_option('profile') == 'development'
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe.Devel.svg'),
    install_dir: join_paths(datadir, icondir),
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
    rename: 'org.gnome.PasswordSafe.Devel-symbolic.svg'
)
else
install_data (
    join_paths(icondir, 'org.gnome.PasswordSafe-symbolic.svg'),
    install_dir: join_paths(datadir, icondir)
)
endif

