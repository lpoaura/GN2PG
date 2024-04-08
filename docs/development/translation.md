# Translation

## Generate `po` files

```bash
pygettext3 -d base -o gn2pg/locale/gn2pg.pot gn2pg
msgmerge --update gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po gn2pg/locale/gn2pg.pot
```

## Generate `mo` files

```bash
msgfmt -o gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.mo gn2pg/locale/fr_FR/LC_MESSAGES/gn2pg.po
```
