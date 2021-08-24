datadir = join_paths('share', 'icons')
icondir = join_paths('hicolor', 'scalable', 'apps')
if get_option('profile') == 'development'
install_data (
    join_paths(icondir, 'org.gnome.World.Secrets.Devel.svg'),
    install_dir: join_paths(datadir, icondir),
)
else
install_data (
    join_paths(icondir, 'org.gnome.World.Secrets.svg'),
    install_dir: join_paths(datadir, icondir)
)
endif

symbolicdir = join_paths('hicolor', 'symbolic', 'apps')
install_data (
    join_paths(symbolicdir, 'org.gnome.World.Secrets-symbolic.svg'),
    install_dir: join_paths(datadir, symbolicdir),
    rename: '@0@-symbolic.svg'.format(application_id),
)
