# Your config file

Your own settings and secrets live in one file, and RedFox sets your computers up from it.

## What it holds

`~/.config/redfox/config.yaml` holds the settings that belong to you rather than to the system, such as your NordVPN token and the names of your computers, along with any secrets they need.

When a setup step needs it and it isn't there yet, a terminal asks for it. You can paste it, enter a file path or an `https://` link, or type `F` to choose a file. To give it a new one at any time, run:

```
redfox-config setup
```

## Keeping a large config

A small config fits in a note in your password manager, ready to paste. Once it grows, for example with a profile picture or several mail accounts, keep it as an encrypted file instead:

1. Encrypt it: `age -p -o config.yaml.age config.yaml`. age asks for a passphrase. Use a long one, such as one your password manager generates.
2. Keep `config.yaml.age` wherever suits you: cloud storage, a NAS, a USB stick.
3. Save the passphrase in your password manager.
4. Delete the unencrypted copy you encrypted it from.

On a new computer, give setup the encrypted file (a path, an `https://` link, or `F` to choose it), then type the passphrase. If it's wrong you can try again, and nothing is saved until the file decrypts.

When you change your config, encrypt `~/.config/redfox/config.yaml` again the same way and replace the old copy.
