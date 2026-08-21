1. Clone repository
2. Create .env in same dir as `docker-compose.yml` with
    ```
    DISCORD_BOT_TOKEN=
    DJANGO_SECRET_KEY=
    ```
    django secret key can be generated with 
    ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
3. Download latest version of lilypond and install to `/usr/local/bin/lilypond`
   (on linux 64 bit)
   ```bash
   curl -LO https://gitlab.com/lilypond/lilypond/-/releases/v2.26.0/downloads/lilypond-2.26.0-linux-x86_64.tar.gz
   tar xzf lilypond-2.26.0-linux-x86_64.tar.gz
   sudo mv lilypond-2.26.0 /usr/local/lilypond-2.26.0
   sudo ln -s /usr/local/lilypond-2.26.0/bin/lilypond /usr/local/bin/lilypond
    ```
   (on arm (raspberry pi)) -> build from source
4. Generate ssh key and add to github
   `ssh-keygen -t ed25519 -f ~/.ssh/lilypond_render_deploy -N "" -C "lilypond_render deploy key"` `chmod 600 ~/.ssh/lilypond_render_deploy`