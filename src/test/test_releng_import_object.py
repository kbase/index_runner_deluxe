"""
Test importing objects into the RE directly, without going through the higher layers of code.
"""

from src.index_runner.releng.import_obj import import_object
from src.utils.service_utils import wait_for_dependencies
import unittest
from src.utils.re_client import save, get_doc, get_edge

# TODO TEST more tests. Just tests very basic happy path for now


class TestRelEngImportObject(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        wait_for_dependencies(elasticsearch=False)

    def test_genome(self):
        """
        Test importing a genome into the RE, including creating a object -> ncbi_taxon edge.
        """
        # stick a taxon node into the RE so seach works.
        # TODO remove when we switch to pulling the taxon ID directly.
        save('ncbi_taxon', [{
                "_key": "1423_2018-11-01",
                "id": "1423",
                "scientific_name": "Bacillus subtilis",
                "rank": "species",
                "aliases": [],  # dumped the aliases
                "ncbi_taxon_id": 1423,
                "gencode": 11,
                "first_version": "2018-11-01",
                "last_version": "2019-08-01",
                "created": 0,
                "expired": 9007199254740991,
                "release_created": 0,
                "release_expired": 9007199254740991
            }])

        # trigger the import
        import_object({
            "info": [
                7,
                "my_genome",
                "KBaseGenomes.Genome-15.1",
                "2016-10-05T17:11:32+0000",
                8,
                "someuser",
                6,
                "godilovebacillus",
                "31b40bb1004929f69cd4acfe247ea46d",
                351,
                {}
            ]
            })

        # check results
        obj_doc = get_re_doc('ws_object', '6:7')
        self.assertEqual(obj_doc['workspace_id'], 6)
        self.assertEqual(obj_doc['object_id'], 7)
        self.assertEqual(obj_doc['deleted'], False)
        hsh = "31b40bb1004929f69cd4acfe247ea46d"
        # Check for ws_object_hash
        hash_doc = get_re_doc('ws_object_hash', hsh)
        self.assertEqual(hash_doc['type'], 'MD5')
        # Check for ws_object_version
        ver_doc = get_re_doc('ws_object_version', '6:7:8')
        self.assertEqual(ver_doc['workspace_id'], 6)
        self.assertEqual(ver_doc['object_id'], 7)
        self.assertEqual(ver_doc['version'], 8)
        self.assertEqual(ver_doc['name'], "my_genome")
        self.assertEqual(ver_doc['hash'], "31b40bb1004929f69cd4acfe247ea46d")
        self.assertEqual(ver_doc['size'], 351)
        self.assertEqual(ver_doc['epoch'], 1475687492000)
        self.assertEqual(ver_doc['deleted'], False)
        # TODO Check for ws_copied_from
        # copy_edge = _wait_for_re_edge(
        #     'ws_copied_from',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_object_version/1:2:3'  # to
        # )
        # self.assertTrue(copy_edge)
        # Check for ws_version_of
        ver_edge = get_re_edge(
            'ws_version_of',  # collection
            'ws_object_version/6:7:8',  # from
            'ws_object/6:7'  # to
        )
        self.assertTrue(ver_edge)
        # Check for ws_workspace_contains_obj
        contains_edge = get_re_edge(
            'ws_workspace_contains_obj',  # collection
            'ws_workspace/6',  # from
            'ws_object/6:7'  # to
        )
        self.assertTrue(contains_edge)
        # TODO Check for ws_obj_created_with_method edge
        # created_with_edge = _wait_for_re_edge(
        #     'ws_obj_created_with_method',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_method_version/narrative:3.10.0:UNKNOWN'  # to
        # )
        # self.assertEqual(created_with_edge['method_params'], None)
        # TODO Check for ws_obj_created_with_module edge
        # module_edge = _wait_for_re_edge(
        #     'ws_obj_created_with_module',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_module_version/narrative:3.10.0'  # to
        # )
        # self.assertTrue(module_edge)
        # Check for ws_obj_instance_of_type
        type_edge = get_re_edge(
            'ws_obj_instance_of_type',  # collection
            'ws_object_version/6:7:8',  # from
            'ws_type_version/KBaseGenomes.Genome-15.1'  # to
        )
        self.assertTrue(type_edge)
        # Check for the ws_owner_of edge
        owner_edge = get_re_edge(
            'ws_owner_of',  # collection
            'ws_user/someuser',  # from
            'ws_object_version/6:7:8',  # to
        )
        self.assertTrue(owner_edge)
        # TODO Check for the ws_refers_to edges
        # referral_edge1 = get_edge(
        #     'ws_refers_to',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_object_version/1:1:1',  # to
        # )
        # self.assertTrue(referral_edge1)
        # referral_edge2 = _wait_for_re_edge(
        #     'ws_refers_to',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_object_version/2:2:2',  # to
        # )
        # self.assertTrue(referral_edge2)
        # TODO Check for the ws_prov_descendant_of edges
        # prov_edge1 = _wait_for_re_edge(
        #     'ws_prov_descendant_of',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_object_version/1:1:1',  # to
        # )
        # self.assertTrue(prov_edge1)
        # prov_edge2 = _wait_for_re_edge(
        #     'ws_prov_descendant_of',  # collection
        #     'ws_object_version/41347:5:1',  # from
        #     'ws_object_version/2:2:2',  # to
        # )
        # self.assertTrue(prov_edge2)

        taxon_edge = get_re_edge(
            'ws_obj_version_has_taxon',
            'ws_object_version/6:7:8',
            'ncbi_taxon/1423_2018-11-01')

        del taxon_edge['updated_at']
        self.assertEqual(taxon_edge, {
            '_from': 'ws_object_version/6:7:8',
            '_to': 'ncbi_taxon/1423_2018-11-01',
            'assigned_by': '_system'
        })


def get_re_doc(collection, key):
    d = get_doc(collection, key)
    if len(d['results']) > 0:
        return d['results'][0]
    return None


def get_re_edge(collection, from_, to, del_key=True):
    d = get_edge(collection, from_, to)
    if len(d['results']) > 0:
        r = d['results'][0]
        if del_key:
            del r['_key']
            del r['_id']
        del r['_rev']
        return r
    return None
