set work_mem=16777216;
set max_parallel_workers_per_gather=1;


-- Vägtrafiknät
UPDATE nvdb_skane_network net
SET
  road_type = src.vagtr_474
FROM nvdb_skane_tne_ft_vagtrafiknat_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Tätort
UPDATE nvdb_skane_network net
SET
  residential = TRUE
FROM nvdb_skane_tne_ft_tattbebyggtomrade_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Väghållare
UPDATE nvdb_skane_network net
SET
  operator_type = src.vagha_6,
  operator_name = src.vagha_7
FROM nvdb_skane_tne_ft_vaghallare_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Vägbredd
UPDATE nvdb_skane_network net
SET
  width = src.bredd_156
FROM nvdb_skane_tne_ft_vagbredd_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Trafik
UPDATE nvdb_skane_network net
SET
  flow = src.adt_f_117,
  flow_id = src.avsni_119
FROM nvdb_skane_tne_ft_trafik_4 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Slitlager
UPDATE nvdb_skane_network net
SET
  surface = src.slitl_152
FROM nvdb_skane_tne_ft_slitlager_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Hastighetsgräns
UPDATE nvdb_skane_network net
SET
  max_speed = src.hogst_225
FROM nvdb_skane_tne_ft_hastighetsgrans_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- GCM typ
UPDATE nvdb_skane_network net
SET
  gcm_type = src.gcm_t_502
FROM nvdb_skane_tne_ft_gcm_vagtyp_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Gatunamn
UPDATE nvdb_skane_network net
SET
  road_name = src.namn_130
FROM nvdb_skane_tne_ft_gatunamn_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Trafik
UPDATE nvdb_skane_network net
SET
  road_class = src.klass_181
FROM nvdb_skane_tne_ft_funkvagklass_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;



-- Bro och tunnel
UPDATE nvdb_skane_network net
SET
  grade_type = src.konst_190
FROM nvdb_skane_tne_ft_bro_och_tunnel_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Driftsbidrag
UPDATE nvdb_skane_network net
SET
  subsidy = TRUE,
  subsidy_from_date = src.from_date,
  subsidy_to_date = src.to_date
FROM nvdb_skane_tne_ft_driftbidrag_statlig_116 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Förbjuden färdriktning
UPDATE nvdb_skane_network net
SET
  oneway = src.direction
FROM nvdb_skane_tne_ft_forbjudenfardriktning_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Förbud trafik
UPDATE nvdb_skane_network net
SET
  road_access = src.road_access
FROM (
  SELECT
    net.objectid,
    jsonb_agg(jsonb_build_object(
      'vehicle_deny', galle_447,
      'dest_allow', galle_453 = 10, -- 10: sant, 20: falskt
      'vehicle_allow', fordo_455_837,
      'activity_allow', verks_455_838,
      'direction', direction
    )) as road_access
  FROM nvdb_skane_tne_ft_forbudtrafik_1 src
  JOIN nvdb_skane_network net USING (route_id)
  WHERE net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001
  GROUP BY net.objectid
) src
WHERE
  net.objectid = src.objectid;


-- Motorväg
UPDATE nvdb_skane_network net
SET
  motorway = TRUE
FROM nvdb_skane_tne_ft_motorvag_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Motortrafikled
UPDATE nvdb_skane_network net
SET
  motorroad = TRUE
FROM nvdb_skane_tne_ft_motortrafikled_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;


-- Rekommenderad väg för cykel
UPDATE nvdb_skane_network net
SET
  cycleroad = TRUE
FROM nvdb_skane_tne_ft_c_rekbilvagcykeltrafi_1 src
WHERE
  net.route_id = src.route_id AND net.from_measure <= src.to_measure - 0.0000000001 AND net.to_measure >= src.from_measure + 0.0000000001;
