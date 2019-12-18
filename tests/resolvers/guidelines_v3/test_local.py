# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from MyCapytain.resolvers.capitains.local import XmlCapitainsLocalResolver
from MyCapytain.common.constants import XPATH_NAMESPACES, Mimetypes, RDF_NAMESPACES, get_graph
from MyCapytain.common.reference._capitains_cts import CtsReference, URN
from MyCapytain.errors import InvalidURN, UnknownObjectError, UndispatchedTextError
from MyCapytain.resources.prototypes.metadata import Collection
from MyCapytain.resources.collections.capitains import XmlCapitainsCollectionMetadata
from MyCapytain.resources.prototypes.capitains.collection import CapitainsCollectionMetadata, CapitainsReadableMetadata
from MyCapytain.resources.prototypes.cts.text import PrototypeCtsPassage
from MyCapytain.resolvers.utils import CollectionDispatcher
from unittest import TestCase
from rdflib.namespace import DC, DCTERMS
from rdflib import RDFS


class TestXMLFolderResolverBehindTheScene(TestCase):
    """ Test behind the scene functions of the Resolver """
    def test_resource_parser(self):
        """ Test that the initiation finds correctly the resources """
        Repository = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3"])
        collection = Repository.inventory["urn:cts:formulae:passau"]
        sub_collection = Repository.inventory["urn:cts:formulae:passau.heuwieser0073"]
        collected_collection = Repository.inventory["a:different.identifier"]
        self.assertEqual(
            collection.id, "urn:cts:formulae:passau",
            "Passau is found"
        )
        # Check backward compatibility
        self.assertEqual(
            collection.urn, collection.id,
            "urn and id should be equal"
        )
        self.assertEqual(
            len(collection.collections), 2,
            "Passau has two sub-collections."
        )
        self.assertEqual(
            len(collection.readableDescendants), 7,
            "Passau has seven readable descendants."
        )
        self.assertEqual(
            sub_collection.id, "urn:cts:formulae:passau.heuwieser0073",
            "Passau number 73 is found."
        )
        self.assertEqual(
            len(sub_collection.texts), 5,
            "Passau 73 has 5 readable versions."
        )
        self.assertEqual(
            collected_collection.id, "a:different.identifier",
            "The collected collection is found."
        )
        self.assertEqual(
            len(collected_collection.texts), 4,
            "The collected collection has 4 readable versions."
        )

    def test_text_resource(self):
        """ Test to get the text resource to perform other queries """
        Repository = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3"])
        text, metadata = Repository.__getText__("urn:cts:formulae:passau.heuwieser0073.lat001")
        self.assertEqual(
            len(text.citation), 1,
            "Passau 73, version 1 has a single citation unit."
        )
        self.assertIn(
            "Noticia qualiter isti iuraverunt pro illam marcam",
            text.getTextualNode(CtsReference("1")).export(output=Mimetypes.PLAINTEXT),
            "It should be possible to retrieve text"
        )

    def test_missing_text_resource(self):
        """ Test to make sure the correct warning is raised if a text is missing """
        with self.assertLogs(XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3_missing"]).logger) as cm:
            Repository = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3_missing"])
            text, metadata = Repository.__getText__("urn:cts:formulae:passau.heuwieser0073.lat005")
            self.assertIsNone(text)
        self.assertIn('WARNING:root:The file '
                      'tests/testing_data/guidelines_v3_missing/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml '
                      'is mentioned in the metadata but does not exist', cm.output)
        self.assertIn(
            'ERROR:root:tests/testing_data/guidelines_v3_missing/data/passau/heuwieser0073/passau.heuwieser0073.lat005.xml is not present',
            cm.output
        )

    def test_get_capabilities(self):
        """ Check Get Capabilities """
        Repository = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3"])
        self.assertEqual(
            len(Repository.__getTextMetadata__()[0]), 18,
            "General no filter works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(category="cts:edition")[0]), 16,
            "Type filter works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(category="cts:commentary")[0]), 1,
            "Type filter works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(lang="deu")[0]), 1,
            "Filtering on language works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(category="cts:edition", lang="ger")[0]), 0,
            "Type filter + lang works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(category="cts:translation", lang="deu")[0]), 1,
            "Type filter + lang works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(category="cts:commentary", lang="fre")[0]), 1,
            "Type filter + lang works"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(page=1, limit=2, pagination=True)[0]), 2,
            "Pagination works without other filters"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(page=2, limit=2, pagination=True)[0]), 2,
            "Pagination works without other filters at list end"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(urn="urn:cts:formulae:passau")[0]), 7,
            "URN Filtering works. 7 texts should be found in Passau."
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(urn="a:different.identifier")[0]), 4,
            "URN Filtering works. 4 texts should be found in a:different.identifier"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__(urn="urn:cts:formulae:passau.heuwieser0073.lat005")[0]), 1,
            "Complete URN filtering works"
        )

    def test_get_shared_textgroup_cross_repo(self):
        """ Check Get Capabilities """
        Repository = XmlCapitainsLocalResolver(
            ["./tests/testing_data/guidelines_v3_missing",
             "./tests/testing_data/guidelines_v3"]
        )
        self.assertIsNotNone(
            Repository.__getText__("urn:cts:formulae:passau.heuwieser0073.lat005"),
            "We should find Passau 73, version 5"
        )
        self.assertIsNotNone(
            Repository.__getText__("urn:cts:formulae:passau.heuwieser0073.lat001"),
            "We should find Passau 73, version 1"
        )
        self.assertEqual(
            len(Repository.__getTextMetadata__()[0]), 18,
            "Texts repeated in the two repos should not be repeated in the resolver."
        )

    def test_get_capabilities_nocites(self):
        """ Check Get Capabilities latinLit data"""
        Repository = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3_missing"])
        self.assertEqual(
            len(Repository.__getTextMetadata__(urn="urn:cts:formulae:passau.heuwieser0073.lat005")[0]), 0,
            "Texts without citations were ignored"
        )

    def test_pagination(self):
        self.assertEqual(
            XmlCapitainsLocalResolver.pagination(2, 30, 150), (30, 60, 2, 30),
            " Pagination should return Array limits "
        )
        self.assertEqual(
            XmlCapitainsLocalResolver.pagination(4, 40, 150), (120, 150, 4, 30),
            " Pagination should return Array limits "
        )
        self.assertEqual(
            XmlCapitainsLocalResolver.pagination(5, 40, 150), (120, 150, 4, 30),
            " Pagination should return Array limits "
        )
        self.assertEqual(
            XmlCapitainsLocalResolver.pagination(5, 100, 150), (100, 150, 2, 50),
            " Pagination should give corrected page and correct count"
        )
        self.assertEqual(
            XmlCapitainsLocalResolver.pagination(5, 110, 150), (40, 50, 5, 10),
            " Pagination should use default limit (10) when getting too much "
        )


class TextXMLFolderResolver(TestCase):
    """ Ensure working state of resolver """
    def setUp(self):
        get_graph().remove((None, None, None))
        self.resolver = XmlCapitainsLocalResolver(["./tests/testing_data/guidelines_v3"])

    def test_getPassage_full(self):
        """ Test that we can get a full text """
        passage = self.resolver.getTextualNode("urn:cts:formulae:passau.heuwieser0073.lat005")
        self.assertIsInstance(
            passage, PrototypeCtsPassage,
            "GetPassage should always return passages objects"
        )

        children = passage.getReffs()

        # We check the passage is able to perform further requests and is well instantiated
        self.assertEqual(
            children[0], CtsReference('1'),
            "Resource should be string identifiers"
        )

        self.assertIn(
            "Ad Perinpah unam basilicam sine quisitione a sancto Stephano", passage.export(output=Mimetypes.PLAINTEXT),
            "Export CtsTextMetadata should work correctly"
        )

        self.assertCountEqual(
            passage.export(
                output=Mimetypes.PYTHON.ETREE
            ).xpath(
                ".//tei:div/tei:div[@n='1']//text()", namespaces=XPATH_NAMESPACES, magic_string=False
            )[:11],
            ["d", ") (", "C", ") ", "Ad", " ", "Perinpah", " ", "unam", " ", "basilicam"],
            "Export to Etree should give an Etree or Etree like object"
        )

    def test_getPassage_no_canonical(self):
        """ Test that we can get a subreference text passage where no canonical exists"""
        passage = self.resolver.getTextualNode("urn:cts:formulae:passau.heuwieser0073.lat001", "1")
        self.assertIn(
            "Noticia qualiter isti iuraverunt pro illam marcam", passage.export(Mimetypes.PLAINTEXT),
            "CapitainsCtsPassage should resolve if directly asked"
        )
        with self.assertRaises(UnknownObjectError):
            self.resolver.getTextualNode("urn:cts:formulae:passau.heuwieser0073", "2")
        with self.assertRaises(UnknownObjectError):
            self.resolver.getTextualNode("urn:cts:formulae:passau", "2")

    def test_getPassage_subreference(self):
        """ Test that we can get a subreference text passage"""
        passage = self.resolver.getTextualNode("urn:cts:formulae:salzburg.hauthaler-a0100.lat001", "1")

        # We check we made a reroute to GetPassage request
        self.assertIsInstance(
            passage, PrototypeCtsPassage,
            "GetPassage should always return passages objects"
        )

        children = list(passage.getReffs())

        self.assertEqual(
            str(children[0]), '1.1',
            "Resource should be string identifiers"
        )

        self.assertIn(
            "Et isti sunt testes exinde", passage.export(output=Mimetypes.PLAINTEXT),
            "Export CtsTextMetadata should work correctly"
        )
        with self.assertRaises(UnknownObjectError,
                               msg='Trying to retrieve text from an non-readable object should throw and error.'):
            self.resolver.getTextualNode("urn:cts:formulae:salzburg.hauthaler-a0100", "1")

        self.assertEqual(
            passage.export(output=Mimetypes.PYTHON.ETREE).xpath(".//tei:p[@n='2']//text()",
                                                                namespaces=XPATH_NAMESPACES,
                                                                magic_string=False)[:9],
            ["Et", " ", "isti", " ", "sunt", " ", "testes", " ", "exinde"],
            "Export to Etree should give an Etree or Etree like object"
        )

    def test_getPassage_full_metadata(self):
        """ Test that we can get a full text with its metadata"""
        text_id = "urn:cts:formulae:salzburg.hauthaler-a0100.lat001"
        passage = self.resolver.getTextualNode(text_id, metadata=True)
        self.assertEqual(passage.metadata.export(output=Mimetypes.JSON.LD),
                         self.resolver.getMetadata(objectId=text_id).metadata.export(output=Mimetypes.JSON.LD))

        self.assertIsInstance(
            passage, PrototypeCtsPassage,
            "GetPassage should always return passages objects"
        )
        self.assertEqual(
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term('title'), 'deu']),
            "Salzburger Urkundenbuch (Ed. Hauthaler); Codex A Nummer 100",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term('parent')][0]), "urn:cts:formulae:salzburg.hauthaler-a0100",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertIn(
            "a) Der Edle Vodalhard (Odalhard) übergibt dem Erzbischof 7 Huben am Ergoltsbach",
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term("description"), "deu"]),
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            passage.citation.name, "charta",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            len(passage.citation), 2,
            "Local Inventory Files should be parsed and aggregated correctly"
        )

        children = list(passage.getReffs(level=2))
        # We check the passage is able to perform further requests and is well instantiated
        self.assertEqual(
            children[0], CtsReference('1.1'),
            "Resource should be string identifiers"
        )

        self.assertIn(
            "Noverint igitur omnes Christi fideles", passage.export(output=Mimetypes.PLAINTEXT),
            "Export CtsTextMetadata should work correctly"
        )

        self.assertEqual(
            passage.export(
                output=Mimetypes.PYTHON.ETREE
            ).xpath(
                ".//tei:div[@n='1']/tei:p[@n='1']//text()", namespaces=XPATH_NAMESPACES, magic_string=False
            )[:11],
            ["a", ") ", "Noverint", " ", "igitur", " ", "omnes", " ", "Christi", " ", "fideles"],
            "Export to Etree should give an Etree or Etree like object"
        )

    def test_getPassage_prevnext(self):
        """ Test that we can get a full text with its metadata"""
        passage = self.resolver.getTextualNode("urn:cts:formulae:salzburg.hauthaler-a0100.lat001",
                                               subreference="1.2", metadata=True)

        self.assertIsInstance(
            passage, PrototypeCtsPassage,
            "GetPassage should always return passages objects"
        )
        self.assertEqual(
            passage.prevId, CtsReference("1.1"),
            "Previous CapitainsCtsPassage ID should be parsed"
        )
        self.assertEqual(
            passage.nextId, CtsReference("2.1"),
            "Next CapitainsCtsPassage ID should be parsed"
        )

        self.assertIn(
            "Et isti sunt testes exinde per aures attracti", passage.export(output=Mimetypes.PLAINTEXT),
            "Export CtsTextMetadata should work correctly"
        )

        self.assertEqual(
            passage.export(output=Mimetypes.PYTHON.ETREE).xpath(".//text()", namespaces=XPATH_NAMESPACES, magic_string=False)[:15],
            ["Et", " ", "isti", " ", "sunt", " ", "testes", " ", "exinde", " ", "per", " ", "aures", " ", "attracti"],
            "Export to Etree should give an Etree or Etree like object"
        )

    def test_getPassage_metadata_prevnext(self):
        """ Test that we can get a full text with its metadata"""
        text_id = "urn:cts:formulae:salzburg.hauthaler-a0100.lat001"
        passage = self.resolver.getTextualNode(
            text_id, subreference="1.2", metadata=True, prevnext=True
        )
        self.assertEqual(passage.metadata.export(output=Mimetypes.JSON.LD),
                         self.resolver.getMetadata(objectId=text_id).metadata.export(output=Mimetypes.JSON.LD))
        self.assertIsInstance(
            passage, PrototypeCtsPassage,
            "GetPassage should always return passages objects"
        )
        self.assertEqual(
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term('title'), 'deu']),
            "Salzburger Urkundenbuch (Ed. Hauthaler); Codex A Nummer 100",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term('parent')][0]), "urn:cts:formulae:salzburg.hauthaler-a0100",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertIn(
            "a) Der Edle Vodalhard (Odalhard) übergibt dem Erzbischof 7 Huben am Ergoltsbach",
            str(passage.metadata[RDF_NAMESPACES.CAPITAINS.term("description"), "deu"]),
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            passage.citation.name, "paragraph",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            passage.citation.root.name, "charta",
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            len(passage.citation.root), 2,
            "Local Inventory Files should be parsed and aggregated correctly"
        )
        self.assertEqual(
            passage.prevId, CtsReference("1.1"),
            "Previous CapitainsCtsPassage ID should be parsed"
        )
        self.assertEqual(
            passage.nextId, CtsReference("2.1"),
            "Next CapitainsCtsPassage ID should be parsed"
        )

        self.assertIn(
            "Et isti sunt testes exinde per aures attracti", passage.export(output=Mimetypes.PLAINTEXT),
            "Export CtsTextMetadata should work correctly"
        )

        self.assertEqual(
            passage.export(output=Mimetypes.PYTHON.ETREE).xpath(".//text()", namespaces=XPATH_NAMESPACES, magic_string=False)[:15],
            ["Et", " ", "isti", " ", "sunt", " ", "testes", " ", "exinde", " ", "per", " ", "aures", " ", "attracti"],
            "Export to Etree should give an Etree or Etree like object"
        )

    def test_getMetadata_full(self):
        """ Checks retrieval of Metadata information """
        metadata = self.resolver.getMetadata()
        self.assertIsInstance(
            metadata, Collection,
            "Resolver should return a collection object"
        )
        self.assertIsInstance(
            metadata.members[0], Collection,
            "Members of Inventory should be TextGroups"
        )
        self.assertEqual(
            len(metadata.members[0].members), 4,
            "There should be four grandchildren to top-level Collection."
        )
        self.assertEqual(
            len(metadata.descendants), 34,
            "There should be as many descendants as there is readables plus collections + 1 "
            "for default inventory"
        )
        self.assertEqual(
            len(metadata.readableDescendants), 18,
            "There should be as many readable descendants as there is readables"
        )
        self.assertEqual(
            len([x for x in metadata.readableDescendants if isinstance(x, CapitainsReadableMetadata)]), 18,
            "There should be 18 readable descendants"
        )
        self.assertEqual(
            len(metadata.export(output=Mimetypes.PYTHON.ETREE).xpath(
                "//cpt:readable[@urn='urn:cts:formulae:passau.heuwieser0073.lat002']",
                namespaces=XPATH_NAMESPACES)), 1,
            "There should be one node in exported format corresponding to Passau 73, version 2"
        )
        self.assertCountEqual(
            [x["@id"] for x in metadata.export(output=Mimetypes.JSON.DTS.Std)["member"]],
            ["default"],
            "There should only be one member in DTS JSON"
        )

    def test_getMetadata_subset(self):
        """ Checks retrieval of Metadata information """
        metadata = self.resolver.getMetadata(objectId="urn:cts:formulae:passau.heuwieser0073")
        self.assertIsInstance(
            metadata, Collection,
            "Resolver should return a collection object"
        )
        self.assertIsInstance(
            metadata.members[0], CapitainsReadableMetadata,
            "All members should be CapitainsReadableMetadata."
        )
        self.assertEqual(
            len(metadata.descendants), len(metadata.readableDescendants),
            "There should be as many descendants as there are readable descendants."
        )
        self.assertEqual(
            len(metadata.readableDescendants), 5,
            "There should be 5 readableDescendants"
        )
        self.assertEqual(
            len([x for x in metadata.readableDescendants if isinstance(x, CapitainsReadableMetadata)]), 5,
            "All readable descendants should be CapitainsReadableMetadata"
        )
        self.assertIsInstance(
            metadata.parent, CapitainsCollectionMetadata,
            "First parent should be CapitainsCollectionMetadata"
        )
        self.assertIsInstance(
            metadata.parents[0], CapitainsCollectionMetadata,
            "First parent should be CapitainsCollectionMetadata"
        )
        self.assertEqual(
            len(metadata.export(output=Mimetypes.PYTHON.ETREE).xpath(
                "//cpt:readable[@urn='urn:cts:formulae:passau.heuwieser0073.lat002']",
                namespaces={"cpt": "http://purl.org/capitains/ns/1.0#"})), 1,
            "There should be one node in exported format corresponding to Passau 73, version 2"
        )
        self.assertCountEqual(
            [x["@id"] for x in metadata.export(output=Mimetypes.JSON.DTS.Std)["member"]],
            ['urn:cts:formulae:passau.heuwieser0073.lat001', 'urn:cts:formulae:passau.heuwieser0073.lat002',
             'urn:cts:formulae:passau.heuwieser0073.lat003', 'urn:cts:formulae:passau.heuwieser0073.lat004',
             'urn:cts:formulae:passau.heuwieser0073.lat005'],
            "There should be five members in DTS JSON"
        )

        readable = self.resolver.getMetadata(objectId="urn:cts:formulae:passau.heuwieser0073.lat001")
        self.assertIsInstance(
            readable, CapitainsReadableMetadata, "Metadata should be commentary"
        )
        self.assertEqual(
            readable.lang, "lat", "Language is Latin"
        )
        self.assertIn(
            "ZEUGENAUSSAGEN (AUFZEICHNUNGEN) ÜBER DEN DER PASSAUER KIRCHE",
            readable.get_description("eng"),
            "Description should be the right one"
        )

    def test_getSiblings(self):
        """ Ensure getSiblings works well """
        previous, nextious = self.resolver.getSiblings(
            textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001", subreference="1.2"
        )
        self.assertEqual(
            previous, CtsReference("1.1"),
            "Previous reference should be well computed"
        )
        self.assertEqual(
            nextious, CtsReference("2.1"),
            "Next reference should be well computed"
        )

    def test_getSiblings_nextOnly(self):
        """ Ensure getSiblings works well when there is only the next passage"""
        previous, nextious = self.resolver.getSiblings(
            textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001", subreference="1.1"
        )
        self.assertEqual(
            previous, None,
            "Previous reference should not exist"
        )
        self.assertEqual(
            nextious, CtsReference("1.2"),
            "Next reference should be well computed"
        )

    def test_getSiblings_prevOnly(self):
        """ Ensure getSiblings works well when there is only the previous passage"""
        previous, nextious = self.resolver.getSiblings(
            textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001", subreference="2.2"
        )
        self.assertEqual(
            previous, CtsReference("2.1"),
            "Previous reference should be well computed"
        )
        self.assertEqual(
            nextious, None,
            "Next reference should not exist"
        )

    def test_getReffs_full(self):
        """ Ensure getReffs works well """
        reffs = self.resolver.getReffs(textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001", level=1)
        self.assertEqual(
            len(reffs), 2,
            "There should be 2 chartae"
        )
        self.assertEqual(
            reffs[0], CtsReference("1")
        )

        reffs = self.resolver.getReffs(textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001", level=2)
        self.assertEqual(
            len(reffs), 4,
            "There should be 4 paragraphs"
        )
        self.assertEqual(
            reffs[0], CtsReference("1.1")
        )

        reffs = self.resolver.getReffs(
            textId="urn:cts:formulae:salzburg.hauthaler-a0100.lat001",
            subreference="1",
            level=1
        )
        self.assertEqual(
            len(reffs), 2,
            "There should be 2 references"
        )
        self.assertEqual(
            reffs[0], CtsReference("1.1")
        )

    # Add test for parents here


class TextXMLFolderResolverDispatcher(TestCase):
    """ Ensure working state of resolver """
    def setUp(self):
        get_graph().remove((None, None, None))

    def test_dispatching_collections(self):
        tic = CapitainsCollectionMetadata()
        fulda = CapitainsCollectionMetadata("urn:cts:formulae:fulda_dronke", parent=tic)
        fulda.set_label("Codex diplomaticus Fuldensis", "lat")
        passau = CapitainsCollectionMetadata("urn:cts:formulae:passau", parent=tic)
        passau.set_label("Passauer Urkunden", "deu")
        collected = CapitainsCollectionMetadata("a:different.identifier", parent=tic)
        collected.set_label("A collected collection.", "eng")
        collected.set_label("Eine Sammelsammlung", "deu")
        collected = CapitainsCollectionMetadata("urn:cts:formulae:salzburg", parent=tic)
        collected.set_label("Salzburger Urkunden", "deu")

        dispatcher = CollectionDispatcher(tic)

        @dispatcher.inventory("urn:cts:formulae:fulda_dronke")
        def dispatchFulda(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:fulda_dronke"):
                return True
            return False

        @dispatcher.inventory("urn:cts:formulae:passau")
        def dispatchPassau(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:passau"):
                return True
            return False

        @dispatcher.inventory("a:different.identifier")
        def dispatchCollected(collection, path=None, **kwargs):
            if collected in collection.parents:
                return True
            return False

        @dispatcher.inventory("urn:cts:formulae:salzburg")
        def dispatchPassau(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:salzburg"):
                return True
            return False

        resolver = XmlCapitainsLocalResolver(
            ["./tests/testing_data/guidelines_v3"],
            dispatcher=dispatcher
        )
        fulda_stuff = resolver.getMetadata("urn:cts:formulae:fulda_dronke")
        collected_stuff = resolver.getMetadata("a:different.identifier")
        passau_stuff = resolver.getMetadata("urn:cts:formulae:passau")
        self.assertEqual(
            len(fulda_stuff.readableDescendants), 8,
            "There should be 8 readable descendants in Fulda"
        )
        self.assertIsInstance(
            fulda_stuff, CapitainsCollectionMetadata, "should be collection"
        )
        self.assertEqual(
            len(collected_stuff.readableDescendants), 4,
            "There should be 4 readable descendants in the collected collection"
        )
        self.assertEqual(
            len(passau_stuff.descendants), 9,
            "There should be 7 descendants in Passau"
        )
        self.assertEqual(
            str(collected_stuff.get_label(lang="deu")), "Eine Sammelsammlung",
            "Label should be correct"
        )

        with self.assertRaises(KeyError):
            _ = fulda_stuff["urn:cts:formulae:salzburg.hauthaler-a0100"]

    def test_dispatching_error(self):
        tic = CapitainsCollectionMetadata()
        fulda = CapitainsCollectionMetadata("urn:cts:formulae:fulda_dronke", parent=tic)
        fulda.set_label("Codex diplomaticus Fuldensis", "lat")
        dispatcher = CollectionDispatcher(tic)
        # We remove default dispatcher
        dispatcher.__methods__ = []

        @dispatcher.inventory("urn:cts:formulae:fulda_dronke")
        def dispatchFulda(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:fulda_dronke"):
                return True
            return False

        XmlCapitainsLocalResolver.RAISE_ON_UNDISPATCHED = True
        with self.assertRaises(UndispatchedTextError):
            resolver = XmlCapitainsLocalResolver(
                ["./tests/testing_data/guidelines_v3"],
                dispatcher=dispatcher
            )

        XmlCapitainsLocalResolver.RAISE_ON_UNDISPATCHED = False
        try:
            resolver = XmlCapitainsLocalResolver(
                ["./tests/testing_data/guidelines_v3"],
                dispatcher=dispatcher
            )
        except UndispatchedTextError as E:
            self.fail("UndispatchedTextError should not have been raised")

    # readableDescendants require that a text be sent through the resolver now.
    # So the next two tests will not work until we add the resolver as a property on the objects.
    def test_dispatching_output(self):
        tic = CapitainsCollectionMetadata()
        fulda = CapitainsCollectionMetadata("urn:cts:formulae:fulda_dronke", parent=tic)
        fulda.set_label("Codex diplomaticus Fuldensis", "lat")
        passau = CapitainsCollectionMetadata("urn:cts:formulae:passau", parent=tic)
        passau.set_label("Passauer Urkunden", "deu")
        collected = CapitainsCollectionMetadata("a:different.identifier", parent=tic)
        collected.set_label("A collected collection.", "eng")
        collected.set_label("Eine Sammelsammlung", "deu")
        collected = CapitainsCollectionMetadata("urn:cts:formulae:salzburg", parent=tic)
        collected.set_label("Salzburger Urkunden", "deu")

        dispatcher = CollectionDispatcher(tic)

        @dispatcher.inventory("urn:cts:formulae:fulda_dronke")
        def dispatchFulda(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:fulda_dronke"):
                return True
            return False

        @dispatcher.inventory("urn:cts:formulae:passau")
        def dispatchPassau(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:passau"):
                return True
            return False

        @dispatcher.inventory("a:different.identifier")
        def dispatchCollected(collection, path=None, **kwargs):
            if collected in collection.parents:
                return True
            return False

        @dispatcher.inventory("urn:cts:formulae:salzburg")
        def dispatchPassau(collection, path=None, **kwargs):
            if collection.id.startswith("urn:cts:formulae:salzburg"):
                return True
            return False

        resolver = XmlCapitainsLocalResolver(
            ["./tests/testing_data/guidelines_v3"],
            dispatcher=dispatcher
        )

        all = resolver.getMetadata().export(Mimetypes.XML.CTS)
        fulda_stuff = resolver.getMetadata("urn:cts:formulae:fulda_dronke").export(Mimetypes.XML.CTS)
        collected_stuff = resolver.getMetadata("a:different.identifier").export(Mimetypes.XML.CTS)
        passau_stuff = resolver.getMetadata("urn:cts:formulae:passau").export(Mimetypes.XML.CTS)
        get_graph().remove((None, None, None))
        fulda_stuff, collected_stuff, passau_stuff = XmlCapitainsCollectionMetadata.parse(fulda_stuff),\
                                                     XmlCapitainsCollectionMetadata.parse(collected_stuff), \
                                                     XmlCapitainsCollectionMetadata.parse(passau_stuff)
        self.assertEqual(
            len(fulda_stuff.readableDescendants), 0,
            "Readable descendants should only be available through the resolver"
        )
        self.assertIsInstance(
            fulda_stuff, XmlCapitainsCollectionMetadata, "should be collection"
        )
        self.assertEqual(
            len(collected_stuff.readableDescendants), 0,
            "Readable descendants should only be available through the resolver"
        )
        self.assertEqual(
            len(passau_stuff.descendants), 0,
            "Descendants should only be available through the resolver"
        )
        self.assertEqual(
            collected_stuff.get_label("fre"), None,  # CapitainsCtsText inventory have no label in CTS
            "Label should be correct"
        )
        get_graph().remove((None, None, None))
        all = XmlCapitainsCollectionMetadata.parse(all)
        self.assertEqual(
            len(all.readableDescendants), 0,
            "Readable descendants should only be available through the resolver"
        )