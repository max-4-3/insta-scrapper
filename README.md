## POSTS:

### extract:
```console
uv run posts.py '<username>'
```
### download:
```console
cat '<username>.json' | jq '.total_posts' | uv run download_posts.py - '<username>'
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
cat '<username>-reels.json' | jq '.total_reels' | uv run download_reels.py - '<username>'
```

## HIGHLIGHTS:
> [!WARNING]
> This requires you to set ur accounts cookies in the `./.env` file (check `./.env.example`)

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
cat '<username>-highlights.json' | jq '.total_highlights' | uv run download_highlights.py - '<username>'
```
