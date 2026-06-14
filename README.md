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

### extract:
> [!NOTE]
> This might requires you to set ur account cookies

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

### extract:
```console
uv run highlights.py '<username>'
```

### download:
> [!NOTE]
> This might requires you to set ur account cookies

```console
cat '<username>-highlights.json' | jq '.highlights' | uv run download_highlights.py - '<username>'
```
