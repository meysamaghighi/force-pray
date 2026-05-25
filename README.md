# force-pray

A macOS background daemon that hijacks your screen at prayer time so you actually stop working. Times are for **Stockholm**, using the Shia Ithna-Ashari (Jafari) method — the same method Imam Ali Islamic Center uses.

## Why not parse the PDF directly?

The PDF at `imamalicenter.se/Bonetider-pdf/Stockholm.pdf` renders prayer times as **vector graphics**, not selectable text — extracting them reliably would need OCR with model-specific tuning every month. The Aladhan API with `method=0` (Shia Jafari) for Stockholm produces times within ~1 minute of the PDF. If you want to align exactly, edit `OFFSETS_MIN` in `prayer_times.py` after comparing.

## What it does

At each of Fajr, Dhuhr, Asr, Maghrib, Isha:
1. Plays the macOS *Glass* chime + says *"It's time for {prayer}, go pray"* aloud
2. Opens a fullscreen, always-on-top, undecorated window with `حَيَّ عَلَى الصَّلَاة`
3. Will not close for 7 minutes

## How to dismiss (hard but possible)

- **Wait it out** — auto-closes after 7 minutes (the default countdown).
- **Hold to dismiss** — press and hold the green button for 10 seconds.
- **Emergency phrase** — type, with the window focused:
  ```
  ya allah forgive me i need to work
  ```

## Install (auto-start on login)

```sh
./install.sh
```

Installs a launchd user agent (`~/Library/LaunchAgents/com.meysam.forcepray.plist`) with `KeepAlive=true`, so even if the daemon crashes it gets restarted.

## Uninstall

```sh
./uninstall.sh
```

## Manual run / debug

```sh
.venv/bin/python prayer_times.py            # show today's times
.venv/bin/python blocker.py --prayer Dhuhr  # preview the blocker
.venv/bin/python daemon.py                  # run the watcher in foreground
```

Logs at `~/.force-pray/daemon.log`.

## Tweaking

- **Which prayers fire**: edit `ACTIVE_PRAYERS` in `daemon.py`. To follow the Shia practice of combining Dhuhr+Asr and Maghrib+Isha, set it to `["Fajr", "Dhuhr", "Maghrib"]`.
- **Block duration**: `DEFAULT_COUNTDOWN_SEC` in `blocker.py`.
- **Hold-to-dismiss seconds**: `HOLD_SECONDS` in `blocker.py`.
- **Emergency phrase**: `EMERGENCY_PHRASE` in `blocker.py`.
- **Time offsets vs the PDF**: `OFFSETS_MIN` in `prayer_times.py`.

## Files

- `prayer_times.py` — fetch + cache daily times
- `blocker.py`      — the fullscreen "go pray" window
- `daemon.py`       — long-running scheduler
- `com.meysam.forcepray.plist` — launchd config
- `install.sh` / `uninstall.sh` — register with launchd
