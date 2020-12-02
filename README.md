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
mkdir Code
cd Code
git clone https://github.com/cyklaiskane/pgr2osm.git
cd pgr2osm
pip install -r requirements.txt
PGHOST=localhost PGPORT=5432 PGUSER=postgres PGPASSWORD=foobar python pgr2osm.py > skane.osm
```

Detta skapar en katalog _Code_ i C: där källkoden för pgr2osm sparas. Därefter installeras de mjukvarubibliotek som krävs för körning. Till sist körs pgr2osm och resultatet skickas till filen _skane.osm_. Värdena för `PGHOST=`, `PGPORT=` etc beror på var PostGIS servern körs och med vilka inställningar samt värden den startats med.


## Använda den exporterade datan i OTP

### Förbereda och starta OTP

Innan en OTP instans kan startas behöver ruttningsdatabasen förberedas. Börja med att skapa följande kataloghierarki: _data/graphs/nvdb_ (ex: `mkdir C:\Code\data\graphs\nvdb`). Kopiera in `.osm` filen från föregående steg samt eventuell GTFS `.zip` fil i den nyss skapade `nvdb` katalogen. Kör därefter följande kommando i samlingskatalogen för att bygga en ruttgraf (OBS att kommandot är radbrutet för bättre läsbarhet, skriv allt på en rad för att köra):

```shell
docker run
  --rm
  -e JAVA_MX=4G
  -v "C:\Code\data":/data:rw
  trivectortraffic/opentripplanner:rsrvu
    --basePath /data
    --build /data/graphs/nvdb
```

Ovanstående kommand startar en temporär *docker container* med *imagen* `trivectortraffic/opentripplanner` som kör OTP i grafbyggarläge (`--build`). I detta läge analyserar OTP vilka datafiler som finns i den angivna katalogen (`/data/graphs/nvdb`). Grafobjektet som skapas innheåller både ett optimerat vägnätverk samt GTFS-data från zip-filen. Grafobjektet används sedan för ruttuppslagningar när OTP startas i server-läge. Grafgenerering behöver enbart utföras när antingen vägnätverket eller GTFS-datan ändras. Det går även att ha flera grafobjekt som innehåller olika data genom att skapa en ny katalog med data. Vilket grafobjekt eller `router` som ska användas kan väljas vid varje anrop och en standardrouter kan väljas vid uppstart av OTP serverinstansen.

När ruttgrafen har skapats kan en OTP instans startas med följande kommando:

```shell
docker run
  --rm
  -e JAVA_MX=4G
  -v "C:\Code\data":/data:rw
  -p 8080:8080
  trivectortraffic/opentripplanner:rsrvu
    --basePath /data
    --graphs /data/graphs
    --router nvdb
    --server
```

Kommandot startar en temporär OTP serverinstans (`--server`) som lyssnar på port 8080 lokalt. Denna instans läser in grafobjektet som skapades i föregående steg. Standard, eller `default`, routern sätts till `nvdb`.
