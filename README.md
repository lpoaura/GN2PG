# GN2PG Client

![https://www.python.org/](https://img.shields.io/badge/python-3.10+-yellowgreen)
![https://www.postgresql.org/](https://img.shields.io/badge/PostgreSQL-10+-blue)
![https://python-poetry.org/](https://img.shields.io/badge/packaging%20tool-poetry-important)
![https://github.com/psf/black](https://img.shields.io/badge/code%20style-black-black)
![https://opensource.org/licenses/AGPL-3.0](https://img.shields.io/badge/licence-AGPL--3.0-blue)

This project provides an import data from [GeoNature] instances to a PostgreSQL database (client side).
Widely inspired from [ClientApiVN](https://framagit.org/lpo/Client_API_VN/)

> [!WARNING]
> The minimum version of the source GeoNature instance required for the incremental update must be a version 2.12.0

![Project logo](./docs/_static/src_gn2pg.png)

## Project Setup

GN2PG Client can be installed by running `pip`. It requires Python 3.10 or above to run.

```bash
pip install gn2pg-client
```

## Issues

Please report any bugs or requests that you have using the [GitHub issue tracker](https://github.com/lpoaura/gn2pg_client/issues)!

## [HowTo](https://lpoaura.github.io/GN2PG/usage/howto.html)

## [Contributing](https://lpoaura.github.io/GN2PG/development/contribute.html)

## Licence

[GNU AGPLv3](https://www.gnu.org/licenses/gpl.html)

## Team

<a href="">
<img height="100px" src="https://auvergne-rhone-alpes.lpo.fr/wp-content/uploads/LPO_AuRA.svg" title="DREAL AuRA">
</a>

[@lpofredc](https://github.com/lpofredc/) ([LPO Auvergne-Rhône-Alpes](https://github.com/lpoaura/)), lead developer

---

<a href="https://github.com/lpoaura/GN2PG/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=lpoaura/GN2PG" />
</a>

---

With the financial support of the [DREAL Auvergne-Rhône-Alpes](http://www.auvergne-rhone-alpes.developpement-durable.gouv.fr/) and the [Office français de la biodiversité](https://www.ofb.gouv.fr/).


<img height="100px" src="https://data.lpo-aura.org/web/images/blocmarque_pref_region_auvergne_rhone_alpes_rvb_web.png" title="DREAL AuRA"> <img height="100px" src="https://www.ofb.gouv.fr/sites/default/files/logo-ofb.png" title="OFB" style="padding-left:10px;">

[geonature]: https://geonature.fr
