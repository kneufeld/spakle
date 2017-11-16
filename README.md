# Spakle

Basically, [spakle](https://github.com/kneufeld/spakle) is a webhook
relay from [GitLab](https://about.gitlab.com/) to
[Slack](https://slack.com).

I needed a name and _spackle_ is something you smear on problems to hide
them. But you're not allowed to spell things properly in the open source
world so _spakle_ it is.

Anyhow, _spakle_ solves the problem that _slack_ only allows one hook
per channel in the freebie edition, as opposed to one hook for all
channels and then you specify the channel name.

## installation

`spakle` doesn't have any dependecies so that's cool. It's written in
python 3 so supposedly that's cool. Actually this is one of my first
python 3 projects so that actually is cool.

Damn you `print` vs `print()`! Rant over.

Anyhow, the following should do it.

```
git clone https://github.com/kneufeld/spakle.git /opt/spakle
```

I installed _spakle_ on my self hosted gitlab machine.

### spakle

I've included a `spakle.service` file for `systemd`.

```bash
# edit spakle.service for paths and ports as appropriate
cp spakle.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable spakle.service
systemctl start spakle.service
```

If you want to run it in `tmux` like the sysadmin of champions then...

```
/opt/spakle/spakle.py 0.0.0.0 8081
```

### configure slack

Create webhooks for your slack channels. Maybe some for commits, CI,
merge requests, etc. Match them to the GitLab triggers as you feel
appropriate.

As an example we'll use channel `#commits` with webhook url
`https://hooks.slack.com/services/ABC123/123ABC123`

### configure gitlab

* goto https://gitlab.example.com/your_group/your_project/services/slack/edit 
* in trigger `push` put `webhook` + `#` + `channel name`
* eg. `https://hooks.slack.com/services/ABC123/123ABC123#commits`
* repeat for each activated trigger
* `webhook` is url of `spakle` (don't forget the port)
* eg. `http://192.168.100.101:8081/`
* click the `test and save` button
* your `#commits` channel in slack should have a new entry

Note, `#channel_name` is optional in the trigger url but it's a nice note
to yourself as your copying and pasting various webhooks among the triggers.
Also, it's theorically forwards compatible if you upgrade to a paid slack
version.
