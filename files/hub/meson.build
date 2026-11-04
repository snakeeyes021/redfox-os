project('redfox-hub',
  version: '0.1.0',
  license: 'Apache-2.0',
  meson_version: '>= 1.0.0',
)

# RedFox Hub: a Python + libadwaita app, built into the RedFoxOS image
# (files/scripts/install-redfox-hub.sh installs it to /usr). See README.md.

app_id = 'tech.redfoxlabs.Hub'
pkgdatadir = get_option('prefix') / get_option('datadir') / 'redfox-hub'

subdir('src')
subdir('data')
