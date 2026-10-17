# POLARIS BASED SCRAPPING

This module (or collection of `.py` files) consists of logic that is needed to scrap data from instagram using `POLARIS`.  
The data here, is embedded into the `GET`'s response of the corresponding page and the `.py` files just extract those data out.  

# USAGE
To download a specific media from a instagram media link:
```console
uv run python -m polaris media <MEDIA_LINK>
```

where `<MEDIA_LINK>` could be:
- `https://www.instagram.com/<user>/p/<shortcode>`
- `https://www.instagram.com/<user>/reel/<shortcode>`
- `https://www.instagram.com/reel/<shortcode>`
- `https://www.instagram.com/p/<shortcode>`

> [!NOTE]
> It is capable of downloading (as of 2026-10-17):
> - SideCar (multiple video/images)
> - Image
> - Video

> [!NOTE]
> - It stores the `page` that it `GET` in `./tmp/<MEDIA_LINK>.page` and extracted json data in `./tmp/<MEDIA_LINK>.json`
> - It downloads the `<MEDIA_LINK>` media in `./out/<user>/<shortcode-pk_of_shortcode>/`
> - It stores the `init-data` of `<MEDIA_LINK>` in `./out/<user>/<shortcode-pk_of_shortcode>/init-data.json`
> - For videos it also downloads the corresponding thumbnail with file of extension `.thumb.jpg`

To list media (reels, posts) of a specific instagram profile link:
```console
uv run python -m polaris user <PAGE_LINK>
```

where `<PAGE_LINK>` could be:
- `https://www.instagram.com/<user>`
- `https://www.instagram.com/<user>/reels`

> [!NOTE]
> - It stores the `page` that it `GET` in `./tmp/<MEDIA_LINK>.page` and extracted json data in `./tmp/<MEDIA_LINK>.json`
> - It downloads the `<MEDIA_LINK>` media in `./out/<user>/<shortcode-pk_of_shortcode>/`
> - It stores the `init-data` of `<MEDIA_LINK>` in `./out/<user>/<shortcode-pk_of_shortcode>/init-data.json`
> - For videos it also downloads the corresponding thumbnail with file of extension `.thumb.jpg`

> [!NOTE]
> you can explore more options using `-h` or `--help`
