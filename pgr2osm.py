import asyncio
import asyncpg
import logging
import lxml.etree as etree

from postgis.asyncpg import register


async def add_node(xf, id, point):
    await xf.write(etree.Element('node', {
        'id': str(id),
        'lat': str(point.y),
        'lon': str(point.x)
    }))


async def add_way(xf, record, line):
    way = etree.Element('way', {'id': str(record['id'])})
    etree.SubElement(way, 'nd', {'ref': str(record['source'])})
    nid = record['id'] * -1000
    for point in line[1:-1]:
        await add_node(xf, nid, point)
        etree.SubElement(way, 'nd', {'ref': str(nid)})
        nid -= 1
    etree.SubElement(way, 'nd', {'ref': str(record['target'])})
    exclude = ['id', 'geom', 'objectid', 'line_geom', 'source', 'target']
    tags = {k: v for k, v in record.items() if k not in exclude and v is not None}
    for k, v in tags.items():
        etree.SubElement(way, 'tag', {'k': k, 'v': str(v)})
    await xf.write(way)
    way = None


async def iterate_vertices(pool, xf):
    async with pool.acquire() as con, con.transaction():
        async for record in con.cursor('''
            SELECT id, the_geom as geom
            FROM nvdb_skane_network_vertices_pgr
            LIMIT 5
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
                max_speed as maxspeed,
                surface_name as surface,
                geom,
                source, target
            FROM nvdb_skane_network
            LEFT JOIN (VALUES (1, 'paved'), (2, 'unpaved')) AS surfaces (surface, surface_name) USING (surface)
            LIMIT 10
        '''):
            log.debug(record)
            await add_way(xf, record, record['geom'])


async def run():
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
loop.set_debug(True)
logging.getLogger('asyncio').setLevel(logging.DEBUG)
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
