conf = configuration_data()
conf.set('PKGDATADIR', pkgdatadir)
conf.set('VERSION', meson.project_version())

configure_file(
  input: 'redfox-hub.in',
  output: 'redfox-hub',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x',
)

configure_file(
  input: 'build_config.py.in',
  output: 'build_config.py',
  configuration: conf,
  install: true,
  install_dir: pkgdatadir / 'redfox_hub',
)

install_subdir('redfox_hub',
  install_dir: pkgdatadir,
  exclude_directories: ['__pycache__'],
)
