# THE WORLD TODAY — Monday, 23 November 2026

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/mutiafebrizki-ship-it/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/mutiafebrizki-ship-it/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Entry for the [make.fun bounty "Sum up 23 November's world news in one image"](https://make.fun/bounty/news-image-20261123) (`news-image-20261123`).

## What it is

A one-page newspaper front page — **THE WORLD TODAY** — that sums up the
world news of **Monday, 23 November 2026** in a single 1024×1024 image.
`main.py` draws the whole page itself (pure Python 3 standard library: its
own raster canvas, 5×7 bitmap font, pictograms and PNG encoder) and writes
it to `/output/entry.png`. No network, no clock, no randomness — two runs
produce byte-identical output.

## The day's stories

| Story | What happened |
|---|---|
| **COP31 collapses** (Antalya, Turkey) | The UN climate summit ended with no deal after the EU and about 130 countries rejected a draft text that left out fossil fuels. |
| **Strike kills 10 near Kyiv** (Dymer, Ukraine) | A Russian attack hit a block of flats; a boy of 7 was pulled alive from the rubble. |
| **AI sell-off shakes markets** (Tokyo & New York) | The Nikkei fell 5.06% and the S&P 500 dropped 3.7% on fears AI shares are overpriced; US futures rebounded on Monday. |
| **Iran hits US base in Bahrain** | Missiles and drones wounded two; Trump threatened to sink Iranian vessels as tankers were hit in the Strait of Hormuz. |
| **Russian frigate sunk off Libya** (Benghazi) | The frigate *Merkury* was hit by a suspected Ukrainian sea drone; ten crew were hurt. |
| **"El Chapo Isidro" captured** (Sinaloa, Mexico) | FBI most-wanted cartel boss Fausto Isidro Meza-Flores was seized and faces extradition to the US. |
| Also today | Drone strikes killed five children in Khartoum, Sudan; Marc Márquez won an eighth MotoGP title; Carlos Alcaraz won the ATP Finals. |

Sources: One Turn, FeedCast, RFE/RL, SimpleLife.news, WEBN, TALi News,
WARNPOINT (all reporting on 23 November 2026).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024 PNG, deterministic
```

## License

MIT — see [LICENSE](LICENSE).
