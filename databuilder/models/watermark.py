from typing import Any, Dict, List, Union  # noqa: F401

from databuilder.models.neo4j_csv_serde import Neo4jCsvSerializable, NODE_KEY, \
    NODE_LABEL, RELATION_START_KEY, RELATION_START_LABEL, RELATION_END_KEY, \
    RELATION_END_LABEL, RELATION_TYPE, RELATION_REVERSE_TYPE


class Watermark(Neo4jCsvSerializable):
    # type: (...) -> None
    """
    Table watermark result model.
    Each instance represents one row of table watermark result.
    """
    LABEL = 'Watermark'
    KEY_FORMAT = '{database}://{cluster}.{schema}' \
                 '/{table}/{part_type}/'
    WATERMARK_TABLE_RELATION_TYPE = 'BELONG_TO_TABLE'
    TABLE_WATERMARK_RELATION_TYPE = 'WATERMARK'

    def __init__(self,
                 create_time,  # type: str
                 database,  # type: str
                 schema_name,  # type: str
                 table_name,  # type: str
                 part_name,  # type: str
                 part_type='high_watermark',  # type: str
                 cluster='gold',  # type: str
                 ):
        # type: (...) -> None
        self.create_time = create_time
        self.database = database.lower()
        self.schema = schema_name.lower()
        self.table = table_name.lower()
        self.parts = []  # type: list

        if '=' not in part_name:
            raise Exception('Only partition table has high watermark')

        # currently we don't consider nested partitions
        idx = part_name.find('=')
        name, value = part_name.lower()[:idx], part_name.lower()[idx + 1:]
        self.parts = [(name, value)]
        self.part_type = part_type.lower()
        self.cluster = cluster.lower()
        self._node_iter = iter(self.create_nodes())
        self._relation_iter = iter(self.create_relation())

    def create_next_node(self):
        # type: (...) -> Union[Dict[str, Any], None]
        # return the string representation of the data
        try:
            return next(self._node_iter)
        except StopIteration:
            return None

    def create_next_relation(self):
        # type: (...) -> Union[Dict[str, Any], None]
        try:
            return next(self._relation_iter)
        except StopIteration:
            return None

    def get_watermark_model_key(self):
        # type: (...) -> str
        return Watermark.KEY_FORMAT.format(database=self.database,
                                           cluster=self.cluster,
                                           schema=self.schema,
                                           table=self.table,
                                           part_type=self.part_type)

    def get_metadata_model_key(self):
        # type: (...) -> str
        return '{database}://{cluster}.{schema}/{table}'.format(database=self.database,
                                                                cluster=self.cluster,
                                                                schema=self.schema,
                                                                table=self.table)

    def create_nodes(self):
        # type: () -> List[Dict[str, Any]]
        """
        Create a list of Neo4j node records
        :return:
        """
        results = []
        for part in self.parts:
            results.append({
                NODE_KEY: self.get_watermark_model_key(),
                NODE_LABEL: Watermark.LABEL,
                'partition_key': part[0],
                'partition_value': part[1],
                'create_time': self.create_time
            })
        return results

    def create_relation(self):
        # type: () -> List[Dict[str, Any]]
        """
        Create a list of relation map between watermark record with original table
        :return:
        """
        results = [{
            RELATION_START_KEY: self.get_watermark_model_key(),
            RELATION_START_LABEL: Watermark.LABEL,
            RELATION_END_KEY: self.get_metadata_model_key(),
            RELATION_END_LABEL: 'Table',
            RELATION_TYPE: Watermark.WATERMARK_TABLE_RELATION_TYPE,
            RELATION_REVERSE_TYPE: Watermark.TABLE_WATERMARK_RELATION_TYPE
        }]
        return results
