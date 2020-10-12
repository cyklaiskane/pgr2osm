# pgr2osm

Exporterar data från en databas förberedd med _nvdb-tools_ till en fil i OSM-format.


## Windows

### Krav

Kräver Python 3.7 eller högre samt Git. I Windows kan Python installeras via _Microsoft Store_. Sök på Python i butiken och installera en lämplig version. Git kan hämtas från https://git-scm.com/downloads

När både Python och Git är installerade kan man verifiera att de fungerar genom att öppna ett PowerShell-fönster och skriva.

```shell
python --version
git --version
```

Vilket borde visa något i stil med `git version N.NN.N.windows` och `Python 3.N.N`.


### Installera och köra

Öppna ett PowerShell och kör följande kommandon

```shell
cd \
mkdir temp
cd temp
git clone https://github.com/cyklaiskane/pgr2osm.git
cd pgr2osm
pip install -r requirements.txt
PGHOST=localhost PGPORT=5432 PGUSER=postgres PGPASSWORD=foobar python pgr2osm.py > skane.osm
```

Detta skapar en katalog _temp_ i C: där källkoden för pgr2osm sparas. Därefter installeras de mjukvarubibliotek som krävs för körning. Till sist körs pgr2osm och resultatet skickas till filen _skane.osm_. Värdena för `PGHOST=`, `PGPORT=` etc beror på var PostGIS servern körs och med vilka inställningar samt värden den startats med.
