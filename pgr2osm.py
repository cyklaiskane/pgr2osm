import sys
import io
import asyncio
import asyncpg
import logging
import postgis
import lxml.etree as etree
import xml.etree.ElementTree as ET

from postgis.asyncpg import register


async def add_node(elem, id, point):
    node = etree.Element('node', {
        'id': str(id),
        'lat': str(point.y),
        'lon': str(point.x)
    })
    await elem.write(node)
    node = None

async def add_way(elem, record, line):
    way = etree.Element('way', {'id': str(record['id'])})
    etree.SubElement(way, 'nd', {'ref': str(record['source'])})
    nid = record['id'] * -1000
    for point in line[1:-1]:
        await add_node(elem, nid, point)
        etree.SubElement(way, 'nd', {'ref': str(nid)})
        nid -= 1
    etree.SubElement(way, 'nd', {'ref': str(record['target'])})
    exclude = ['id', 'geom', 'objectid', 'line_geom', 'source', 'target']
    tags = {k: v for k, v in record.items() if k not in exclude and v is not None}
    for k, v in tags.items():
        etree.SubElement(way, 'tag', {'k': k, 'v': str(v)})
    await elem.write(way)
    way = None



async def iterate_vertices(pool, elem):
    async with pool.acquire() as con, con.transaction():
        async for record in con.cursor('''
            SELECT id, ST_Transform(the_geom, 4326) as geom
            FROM nvdb_skane_network_vertices_pgr
        '''):
            await add_node(elem, record['id'], record['geom'])


async def iterate_edges(pool, elem):
    async with pool.acquire() as con, con.transaction():
        async for record in con.cursor('''
            SELECT
                *,
                objectid as id,
                ST_Transform(ST_LineMerge(geom), 4326) as line_geom
            FROM nvdb_skane_network
        '''):
            await add_way(elem, record, record['line_geom'])


async def run():
    pool = await asyncpg.create_pool(database='gis', loop=loop, init=register,
                                     min_size=5, max_size=10)

    async with etree.xmlfile(AsyncXmlOut()) as xf, xf.element('osm', {
        'version': '0.6', 'upload': 'false', 'generator': 'pgr2osm'
    }):
        await asyncio.gather(iterate_vertices(pool, xf),
                             iterate_edges(pool, xf), return_exceptions=True)

    await pool.close()


class AsyncXmlOut(object):
    async def write(self, data):
        print(data.decode('utf-8'))

    async def close(self):
        pass


logging.getLogger("asyncio").setLevel(logging.DEBUG)

loop = asyncio.get_event_loop()
loop.set_debug(True)
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
