# Setup
In case you want to periodically run the scraper (for example every 15 minutes) you can add it to your `systemd` configuration.

If you want to run this on your local machine, I suggest you use the user-configuration of systemd, which gets activated on your first log-in after boot.

_This will not require root-privileges._

 1. Place `tum_video_scraper.service` and `tum_video_scraper.timer` in `~/.config/systemd/user`.
 2. Configure the `tum_video_scraper.service`: You need supply the path to your binary (or your python interpreter, to which you hand main.py) and all arguments you want to give the program in the `ExecStart` section.
 3. Perform a `systemctl --user daemon-reload`.
 4. Enable the timer service `systemctl --user enable --now tum_video_scraper.timer`. The service is now running and will be activated on login.
 5. If you want to perform a scrape right now, you can always force-start a run with `systemctl --user start tum_video_scraper.service`.