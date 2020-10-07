import asyncio
import uvloop
import asyncpg
import logging
import json
import lxml.etree as etree

from postgis.asyncpg import register

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logging.basicConfig(level=logging.DEBUG)

VEHICLES = {
    1: 'emergency',  # ambulans
    2: 'vehicle',  # anläggningens fordon
    3: 'vehicle',  # arbetsfordon
    5: 'vehicle',  # beskickningsfordon
    6: 'share_taxi',  # beställd taxi
    7: 'vehicle',  # besökare
    10: 'motorcar',  # bil
    13: 'motorcar',  # bilägare med arrendekontrakt
    15: 'coach',  # bokbuss
    20: 'bus',  # buss
    30: 'bicycle',  # cykel
    35: 'trailer',  # efterfordon
    40: 'vehicle',  # fordon
    44: 'hgv_articulated',  # fordon eller fordonståg vars längd, lasten inräknad, överstiger 10 meter
    45: 'vehicle',  # fordon enligt beskrivning
    50: 'bus',  # fordon i linjetrafik
    51: 'bus',  # fordon i linjetrafik vid på‐och avstigning
    65: 'vehicle',  # fordon med särskilt tillstånd
    70: 'disabled',  # fordon som används av rörelsehindrade med särskilt tillstånd
    71: 'goods',  # fordon som används för distribution av post
    73: 'atv',  # fyrhjulig moped
    75: 'disabled',  # färdtjänstfordon
    77: 'goods',  # godstransporter
    80: 'horse',  # hästfordon
    85: 'vehicle',  # kommunens servicefordon
    90: 'hgv',  # lastbil
    91: 'hgv',  # lastbil vid på‐och avlastning
    95: 'hgv',  # 2‐axlig lastbil
    100: 'goods',  # lätt lastbil
    105: 'motorcycle',  # lätt motorcykel
    110: 'atv',  # lätt terrängvagn
    120: 'moped',  # moped
    130: 'mofa',  # moped klass I
    140: 'moped',  # moped klass II
    150: 'motorcycle',  # motorcykel
    170: 'motor_vehicle',  # motordrivna fordon
    175: 'motor_vehicle',  # motorfordon
    180: 'agricultural',  # motorredskap
    190: 'agricultural',  # motorredskap klass I
    200: 'agricultural',  # motorredskap klass II
    210: 'motorcar',  # personbil
    500: 'goods',  # på‐eller avlastning av gods
    510: 'psv',  # på‐eller avstigning
    520: 'trailer',  # påhängsvagn
    215: 'hgv',  # renhållningsbil
    530: 'psv',  # skolskjuts
    540: 'trailer',  # släpkärra
    550: 'trailer',  # släpvagn
    220: 'taxi',  # taxi
    230: 'atv',  # terrängmotorfordon
    240: 'atv',  # terrängmotorfordon och terrängsläp
    250: 'snowmobile',  # terrängskoter
    255: 'atv',  # terrängsläp
    260: 'atv',  # terrängvagn
    265: 'vehicle',  # trafik
    270: 'agricultural',  # traktor
    272: 'goods',  # transporter
    274: 'moped',  # trehjulig moped
    276: 'agricultural',  # truck
    280: 'hgv',  # tung lastbil
    285: 'motorcycle',  # tung motorcykel
    290: 'agricultural',  # tung terrängvagn
    300: 'emergency',  # utryckningsfordon
    9999: 'vehicle',  # okänt
}

ACTIVITY = {
    10: 'permissive',  # anläggningsarbeten
    20: 'private',  # boende inom området
    50: 'destination',  # färdtjänst
    70: 'delivery',  # på-eller avlastning av gods
    80: 'destination',  # på-eller avstigning
    120: 'destination',  # transport
    160: 'permissive',  # underhållsarbeten
    170: 'delivery',  # varuleveranser
    180: 'permissive',  # verksamhet enligt beskrivning
}


async def add_node(xf, id, point):
    await xf.write(etree.Element('node', {
        'id': str(id),
        'lat': str(point.y),
        'lon': str(point.x)
    }))


def get_access(items):
    directions = ['', ':forward', ':backward', '']
    tags = {}
    for item in items:
        key = VEHICLES.get(item['vehicle_deny'], 'vehicle')
        key += directions[item['direction']]
        value = 'destination' if item['dest_allow'] else 'no'
        value = ACTIVITY.get(item['activity_allow'], value)
        tags[key] = value
        if item['vehicle_allow']:
            key = VEHICLES.get(item['vehicle_allow'], 'vehicle')
            key += directions[item['direction']]
            tags[key] = 'yes'
    return tags


async def add_way(xf, record, line):
    way = etree.Element('way', {'id': str(record['id'])})
    etree.SubElement(way, 'nd', {'ref': str(record['source'])})
    nid = record['id'] * -1000
    for point in line[1:-1]:
        await add_node(xf, nid, point)
        etree.SubElement(way, 'nd', {'ref': str(nid)})
        nid -= 1
    etree.SubElement(way, 'nd', {'ref': str(record['target'])})
    exclude = ['id', 'geom', 'source', 'target', 'access_json']
    tags = {}
    if record['access_json'] is not None:
        items = json.loads(record['access_json'])
        tags.update(get_access(items))
    tags.update({k: v for k, v in record.items() if k not in exclude and v is not None})
    for k, v in tags.items():
        etree.SubElement(way, 'tag', {'k': k, 'v': str(v)})
    await xf.write(way)
    way = None


async def iterate_vertices(pool, xf):
    async with pool.acquire() as con, con.transaction():
        async for record in con.cursor('''
            SELECT id, st_transform(the_geom, 4326) as geom
            FROM nvdb_skane_network_vertices_pgr
            --WHERE st_intersects(the_geom, st_buffer(st_setsrid(st_makepoint(13.357, 55.657), 4326),0.015))
            --LIMIT 10
        '''):
            await add_node(xf, record['id'], record['geom'])


async def iterate_edges(pool, xf):
    async with pool.acquire() as con, con.transaction():
        async for record in con.cursor('''
            SELECT
                objectid as id,
                road_name as name,
                CASE
                    WHEN road_type = 2 THEN 'cycleway'
                    WHEN motorway THEN 'motorway'
                    WHEN motorroad THEN 'trunk'
                    WHEN road_class = 1 THEN 'trunk'
                    WHEN road_class = 2 THEN 'primary'
                    WHEN road_class < 5 THEN 'secondary'
                    WHEN road_class < 6 THEN 'tertiary'
                    WHEN road_class < 8 AND residential THEN 'residential'
                    WHEN road_class < 8 THEN 'unclassified'
                    WHEN road_class = 9 AND surface = 2 THEN 'track'
                    ELSE 'service'
                END as highway,
                width,
                CASE oneway
                    WHEN 1 THEN '-1'
                    WHEN 2 THEN 'yes'
                    ELSE NULL
                END as oneway,
                road_access as access_json,
                CASE WHEN bicycleroad THEN 'designated' ELSE NULL END as bicycle,
                max_speed as maxspeed,
                surface_name as surface,
                st_transform(geom, 4326) geom,
                from_vertex source,
                to_vertex target
            FROM nvdb_skane_network
            LEFT JOIN (VALUES (1, 'paved'), (2, 'unpaved')) AS surfaces (surface, surface_name) USING (surface)
            --WHERE st_intersects(geom, st_buffer(st_setsrid(st_makepoint(13.357, 55.657), 4326),0.01))
            --WHERE oneway IS NOT NULL OR road_access IS NOT NULL LIMIT 50
        '''):
            await add_way(xf, record, record['geom'])


async def run():
    log.debug('Hej')
    pool = await asyncpg.create_pool(database='gis', loop=loop, init=register,
                                     min_size=5, max_size=10)

    async with etree.xmlfile(AsyncXmlOut(), encoding='UTF-8') as xf:
        await xf.write_declaration()
        async with xf.element('osm', {
            'version': '0.6', 'upload': 'false', 'generator': 'pgr2osm'
        }):
            await asyncio.gather(iterate_vertices(pool, xf),
                                 iterate_edges(pool, xf),
                                 return_exceptions=True)

    await pool.close()


class AsyncXmlOut(object):
    async def write(self, data):
        print(data.decode('utf-8'))

    async def close(self):
        pass


log = logging.getLogger('pgr2osm')
log.setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
#loop.set_debug(True)
loop.run_until_complete(run())

"""
<?xml version='1.0' encoding='UTF-8'?>
<osm version='0.6' upload='true' generator='JOSM'>
  <node id='-12' action='modify' visible='true' lat='1.0' lon='0.25' />
  <node id='-10' action='modify' visible='true' lat='0.5' lon='0.5' />
  <node id='-100' action='modify' visible='true' lat='0.5' lon='0.5' />
  <node id='-8' action='modify' visible='true' lat='1.0' lon='0.0' />
  <node id='-6' action='modify' visible='true' lat='0.0' lon='0.0' />
  <node id='-4' action='modify' visible='true' lat='1.0' lon='1.0' />
  <way id='-16' action='modify' visible='true'>
    <nd ref='-12' />
    <nd ref='-10' />
    <nd ref='-100' />
    <nd ref='-8' />
    <nd ref='-12' />
    <tag k='area' v='yes' />
    <tag k='park_ride' v='bus' />
  </way>
  <way id='-14' action='modify' visible='true'>
    <nd ref='-6' />
    <nd ref='-4' />
    <tag k='highway' v='residential' />
  </way>
</osm>
"""
