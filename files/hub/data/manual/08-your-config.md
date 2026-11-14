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

## Your profile picture

Your config can also carry your account picture, as `profile_picture:` followed by the image in base64 (a PNG or JPEG of up to 1 MB; 256 pixels square is plenty). To get the base64 text of a picture, run:

```
base64 -w0 picture.jpg
```

Setup makes it your picture on the login screen and in Settings.

## Your Mailspring accounts

Your config can also bring your Mailspring accounts to a new install, already signed in. On the computer where Mailspring is set up, run:

```
redfox-config mailspring-export
```

It prints a `mailspring:` section with your accounts, their saved logins and the key they're encrypted with. Add it to your config, and keep the config encrypted (see above).

On the new install, run setup before you first open Mailspring. If Mailspring is open, setup asks you to quit it and run setup again; if Mailspring already has accounts, setup leaves them alone.
