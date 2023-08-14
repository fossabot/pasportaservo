# ![Pasporta Servo 3](https://cdn.rawgit.com/tejo-esperanto/pasportaservo/master/logos/pasportaservo_logo.svg)

[![TEJO](https://img.shields.io/badge/Projekto_de-TEJO-orange.svg)](http://tejo.org)
[![Esperanto](https://img.shields.io/badge/Esperanto-jes-green.svg)](https://eo.wikipedia.org/wiki/Esperanto)
[![Python 3.4](https://img.shields.io/badge/Python-3.5-blue.svg)](https://docs.python.org/3.5/)
[![Django 1.10](https://img.shields.io/badge/Django-1.11-0C4B33.svg)](https://docs.djangoproject.com/en/1.11/)
[![HTTP](https://img.shields.io/badge/HTTP-2-blue.svg)](https://http2.github.io/)
[![HTTPS](https://img.shields.io/badge/HTTPS-jes-green.svg)](https://www.ssllabs.com/ssltest/analyze.html?d=pasportaservo.org)
[![GNU AGPLv3](https://img.shields.io/badge/licenco-GNU_AGPLv3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0.html)
[![Kontaktu nin en Telegramo https://t.me/joinchat/Bg10skEz3jFXpBk-nZAuiw](https://img.shields.io/badge/babili%20en-Telegramo-179CDE.svg)](https://t.me/joinchat/Bg10skEz3jFXpBk-nZAuiw)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FinterDist%2Fpasportaservo.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FinterDist%2Fpasportaservo?ref=badge_shield)

[![Travis CI](https://img.shields.io/travis/tejoesperanto/pasportaservo.svg)](https://travis-ci.org/tejoesperanto/pasportaservo)
[![Codecov](https://img.shields.io/codecov/c/github/tejoesperanto/pasportaservo.svg)](https://codecov.io/gh/tejoesperanto/pasportaservo)


### [Pasporta Servo](https://eo.wikipedia.org/wiki/Pasporta_Servo) estas senpaga tutmonda gastiga servo.

#### La projekto komencis en 1974 kiel eta jarlibro, kaj ekde 2009 ankaŭ daŭras kiel retejo. En tiu ĉi deponejo kolektiĝas la kodo kiu ruligas la retejon [pasportaservo.org](https://pasportaservo.org).


- [Kontribui](#kontribui)
- [Instali](#instali)
- [Licenco](#licenco)

## Kontribui

Ĉu vi trovis cimon? Ĉu vi havas ideo kiel plibonigi la retejon? Nepre kreu [novan atentindaĵon](https://github.com/tejo-esperanto/pasportaservo/issues/new).



## Instali
# INSTALI

Ubuntu 16.10 / Debian Stretch:

    sudo apt install git python3-dev python3-pip python3-venv libjpeg-dev zlib1g-dev \
      postgresql-contrib postgresql-server-dev-all postgresql-9.6-postgis libgdal-dev

Fedora 27:

    sudo dnf install git python3-devel python3-crypto redhat-rpm-config zlib-devel libjpeg-devel libzip-devel \
      postgresql-server postgresql-contrib postgresql-devel


#### PostgreSQL

Se vi estas sub Fedora:

    sudo postgresql-setup --initdb --unit postgresql
    sudo systemctl enable postgresql
    sudo systemctl start postgresql

Por ĉiuj:

    sudo -u postgres createuser --interactive  # Enigu vian uzantnomon kaj poste 'y'
    createdb via-uzantnomo
    createdb pasportaservo


#### Fontkodo

Iru al la [Github projektpaĝo](https://github.com/tejo-esperanto/pasportaservo)
kaj forku ĝin. Poste, vi povas kloni ĝin:

    git clone https://github.com/via-uzantnomo/pasportaservo.git
    cd pasportaservo
    pip install wheel
    pip install -r requirements/dev.txt
    echo 'from .dev import *' > pasportaservo/settings/__init__.py
    ./manage.py migrate
    ./manage.py createsuperuser  # Nur la uzantnomo kaj pasvorto estas deviga
    ./manage.py runserver

Ĉu bone? Vidu http://localhost:8000

----


#### Retmesaĝoj

Dum disvolvigo, estas praktika uzi *MailDump* por provadi sendi retmesaĝoj.
Ekster la *env* virtuala medio, kun Pitono 2:

    pip install --user maildump
    maildump


### Problem-solvado

#### PostgreSQL: `unrecognized option --interactive`
Se la komando `sudo -u postgres createuser --interactive` malsukcesas (ekz., vi ricevas eraron "unrecognized option --interactive"), provu:

    $ sudo -u postgres psql
    psql (9.6.6)
    Type "help" for help.
    postgres=# CREATE ROLE {via-uzantonomo} WITH LOGIN CREATEDB CREATEROLE;
    postgres=# \q

#### PostgreSQL: Ĉu mi bone kreis la datumbazoj?

    $ sudo -u postgres psql
    psql (9.5.4)
    Type "help" for help.
    postgres=# \l
                                        List of databases
         Name      |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
    ---------------+----------+----------+-------------+-------------+-----------------------
     pasportaservo | {uzanto} | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
     template0     | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
                   |          |          |             |             | postgres=CTc/postgres
     template1     | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
                   |          |          |             |             | postgres=CTc/postgres

    postgres=# \q

Se vi vidas tabelon kiel ĉi-supre, ĉio glate paŝis.


### Komprenu la strukturon de la kodo

- **pasportaservo/**: ĝenerala dosierujo kun konfiguro, baz-nivelaj URL-oj…
- **hosting/**: la ĉefa programo por gastiganta servo

Kaj en la diversaj *aplikaĵon* (ekz. `hosting`, `book`, `links`…):

- models.py: strukturo de la datumoj
- urls.py: ligoj inter URL-oj kaj paĝo-vidoj
- views.py: difino de vidoj, paĝoj por prezentado
- templates/: pseŭdo-HTML dosieroj (ŝablonoj)


### Lerni Dĵangon

- https://tutorial.djangogirls.org/
- https://docs.djangoproject.com/en/stable/intro/tutorial01/
- https://docs.djangoproject.com/en/stable/


## Licenco

[GNU AGPLv3](LICENSE)


[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FinterDist%2Fpasportaservo.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FinterDist%2Fpasportaservo?ref=badge_large)