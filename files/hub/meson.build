project('redfox-hub',
  version: '0.1.0',
  license: 'Apache-2.0',
  meson_version: '>= 1.0.0',
)

# RedFox Hub: a Python + libadwaita app. It installs to any prefix: /usr in
# the RedFoxOS image (files/scripts/install-redfox-hub.sh), or /app in a
# Flatpak. See README.md.

app_id = 'tech.redfoxlabs.Hub'
pkgdatadir = get_option('prefix') / get_option('datadir') / 'redfox-hub'

subdir('src')
subdir('data')
