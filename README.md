# README

A set of helpful tools to scrap data from instagram
> [!NOTE]
> Some tool requires you to set ur account cookies
> Getting those cookies is up to you

## POSTS:

### extract:
```console
uv run posts.py '<username>'
```

### download:
```console
cat '<username>-posts.json' | jq '.posts' | uv run download_posts.py - '<username>'
```

## REELS:
> [!WARNING]
> This requires you to set ur accounts cookies in the `./.env` file (check `./.env.example`)

### extract:
```console
uv run reels.py '<username>'
```
### download:
> [!NOTE]
> Keep in mind that this will make requests for each reel (to get media url)
> So bigger accounts (with ton of reels) might get ur account flagged as bot (or scrapping)
> That's why its advices to not use your main account

```console
cat '<username>-reels.json' | jq '.reels' | uv run download_reels.py - '<username>'
```

## HIGHLIGHTS:
> [!WARNING]
> This requires you to set ur accounts cookies in the `./.env` file (check `./.env.example`)
> This requires the user to have posted atleast 1 post or you supply the `user_id` inplace of `username`

### extract:
```console
uv run highlights.py '<username>'
```

### download:
> [!NOTE]
> Keep in mind that this will make requests for each highlight group (that you see in someone profile) to get items url
> So bigger accounts (with ton of highlights groups) might get ur account flagged as bot (or scrapping)
> That's why its advices to not use your main account

```console
cat '<username>-highlights.json' | jq '.highlights' | uv run download_highlights.py - '<username>'
```
