from .base import *
from .base import _load_mock


class TestHttpDtsResolverNavigation(unittest.TestCase):
    def setUp(self):
        self.root_uri = "http://foobar.com/api/dts"
        self.resolver = HttpDtsResolver(self.root_uri)

    @requests_mock.mock()
    def test_navigation_simple(self, mock_set):
        """ Example 1 of Public Draft. Includes on top of it a citeType=poem"""
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example1.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1", type_="poem"),
                DtsReference("2", type_="poem"),
                DtsReference("3", type_="poem"),
                level=1,
                citation=DtsCitation("poem")
            ),
            reffs,
            "References are parsed with types and level"
        )

    @requests_mock.mock()
    def test_navigation_simple_level(self, mock_set):
        """ Test navigation second level """
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?level=2&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example2.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id, level=2)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1.1"),
                DtsReference("1.2"),
                DtsReference("2.1"),
                DtsReference("2.2"),
                DtsReference("3.1"),
                DtsReference("3.2"),
                level=2
            ),
            reffs,
            "Resolver forwards level=2 parameter"
        )

    @requests_mock.mock()
    def test_navigation_simple_ref_deeper_level(self, mock_set):
        """ Test navigation second level from single reff """
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?ref=1&level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example3.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id, subreference="1")

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1.1"),
                DtsReference("1.2"),
                level=2
            ),
            reffs,
            "Resolver forwards subreference parameter"
        )

    @requests_mock.mock()
    def test_navigation_simple_level_ref(self, mock_set):
        """ Test navigation 2 level deeper than requested reff"""
        _id = "urn:cts:latinLit:phi1294.phi001.perseus-lat2"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?ref=1&level=2&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example4.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id, subreference="1", level=2)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1.1.1"),
                DtsReference("1.1.2"),
                DtsReference("1.2.1"),
                DtsReference("1.2.2"),
                level=3
            ),
            reffs,
            "Resolver forwards level + subreference parameter correctly"
        )

    @requests_mock.mock()
    def test_navigation_ask_in_range(self, mock_set):
        """ Test that ranges are correctly requested"""
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?start=1&end=3&level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example5.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id, subreference=DtsReference(1, 3))

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1"),
                DtsReference("2"),
                DtsReference("3"),
                level=1
            ),
            reffs,
            "Resolver handles range reference as subreference parameter"
        )

    @requests_mock.mock()
    def test_navigation_ask_in_range_with_level(self, mock_set):
        """ Test that ranges are correctly requested"""
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?start=1&end=3&level=2&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example6.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id, subreference=DtsReference(1, 3), level=2)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1.1"),
                DtsReference("1.2"),
                DtsReference("2.1"),
                DtsReference("2.2"),
                DtsReference("3.1"),
                DtsReference("3.2"),
                level=2
            ),
            reffs,
            "Resolver forwards correctly range subreference and level"
        )

    @requests_mock.mock()
    def test_navigation_with_level_and_group(self, mock_set):
        """ Test that ranges are correctly parsed"""
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?ref=1&level=2&groupBy=2&id="+_id,
            text=_load_mock("navigation", "example7.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(
            _id, additional_parameters={"groupBy": 2},
            subreference=DtsReference(1), level=2
        )

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1.1.1", "1.1.2"),
                DtsReference("1.2.1", "1.2.2"),
                level=3
            ),
            reffs,
            "groupBy additional parameter is correctly forward + ranges are parsed"
        )

    @requests_mock.mock()
    def test_navigation_with_different_types(self, mock_set):
        """ Test a navigation where a root type of passage is defined but some are redefined """
        _id = "http://data.bnf.fr/ark:/12148/cb11936111v"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example8.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("Av", type_="preface"),
                DtsReference("Pr", type_="preface"),
                DtsReference("1", type_="letter"),
                DtsReference("2", type_="letter"),
                DtsReference("3", type_="letter"),
                level=1,
                citation=DtsCitation(name="letter")
            ),
            reffs,
            "Test that default Reference type is overridden when due"
        )

    @requests_mock.mock()
    def test_navigation_with_advanced_metadata(self, mock_set):
        """ Test references parsing with advanced metadata """
        _id = "http://data.bnf.fr/ark:/12148/cb11936111v"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "example9.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("Av"),
                DtsReference("Pr"),
                DtsReference("1"),
                DtsReference("2"),
                DtsReference("3"),
                level=1
            ),
            reffs,
            "Test that default Reference type is overridden when due"
        )

        ref_Av_metadata = Metadata()
        ref_Av_metadata.add(URIRef("http://purl.org/dc/terms/title"), "Avertissement de l'Éditeur")
        self.assertEqual(
            ref_Av_metadata.export(Mimetypes.JSON.Std),
            reffs[0].metadata.export(Mimetypes.JSON.Std),
            "References metadata should be parsed correctly"
        )

        ref_Pr_metadata = Metadata()
        ref_Pr_metadata.add(URIRef("http://purl.org/dc/terms/title"), "Préface")
        self.assertEqual(
            ref_Pr_metadata.export(Mimetypes.JSON.Std),
            reffs[1].metadata.export(Mimetypes.JSON.Std),
            "References metadata should be parsed correctly"
        )

        ref_1_metadata = Metadata()
        ref_1_metadata.add(URIRef("http://purl.org/dc/terms/title"), "Lettre 1")
        ref_1_metadata.add(URIRef("http://foo.bar/ontology#fictionalSender"), "Cécile Volanges")
        ref_1_metadata.add(URIRef("http://foo.bar/ontology#fictionalRecipient"), "Sophie Carnay")
        self.assertEqual(
            ref_1_metadata.export(Mimetypes.JSON.Std),
            reffs[2].metadata.export(Mimetypes.JSON.Std),
            "References metadata should be parsed correctly"
        )

        ref_2_metadata = Metadata()
        ref_2_metadata.add(URIRef("http://purl.org/dc/terms/title"), "Lettre 2")
        ref_2_metadata.add(URIRef("http://foo.bar/ontology#fictionalSender"), "La Marquise de Merteuil")
        ref_2_metadata.add(URIRef("http://foo.bar/ontology#fictionalRecipient"), "Vicomte de Valmont")
        self.assertEqual(
            ref_2_metadata.export(Mimetypes.JSON.Std),
            reffs[3].metadata.export(Mimetypes.JSON.Std),
            "References metadata should be parsed correctly"
        )

        ref_3_metadata = Metadata()
        ref_3_metadata.add(URIRef("http://purl.org/dc/terms/title"), "Lettre 3")
        ref_3_metadata.add(URIRef("http://foo.bar/ontology#fictionalSender"), "Cécile Volanges")
        ref_3_metadata.add(URIRef("http://foo.bar/ontology#fictionalRecipient"), "Sophie Carnay")
        self.assertEqual(
            ref_3_metadata.export(Mimetypes.JSON.Std),
            reffs[4].metadata.export(Mimetypes.JSON.Std),
            "References metadata should be parsed correctly"
        )

    @requests_mock.mock()
    def test_navigation_paginated(self, mock_set):
        """ Check that all pagination is browsed """
        _id = "urn:cts:greekLit:tlg0012.tlg001.opp-grc"
        mock_set.get(self.root_uri, text=_load_mock("root.json"))
        mock_set.get(
            self.root_uri+"/navigation?level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "paginated/page1.json"),
            complete_qs=True
        )
        mock_set.get(
            self.root_uri+"/navigation?page=2&level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "paginated/page2.json"),
            complete_qs=True
        )
        mock_set.get(
            self.root_uri+"/navigation?page=3&level=1&groupBy=1&id="+_id,
            text=_load_mock("navigation", "paginated/page3.json"),
            complete_qs=True
        )
        reffs = self.resolver.getReffs(_id)

        self.assertEqual(
            DtsReferenceSet(
                DtsReference("1", type_="poem"),
                DtsReference("2", type_="poem"),
                DtsReference("3", type_="poem"),
                DtsReference("4", type_="poem"),
                DtsReference("5", type_="poem"),
                DtsReference("6", type_="poem"),
                DtsReference("7", type_="poem"),
                DtsReference("8", type_="poem"),
                DtsReference("9", type_="poem"),
                level=1,
                citation=DtsCitation("poem")
            ),
            reffs,
            "Resolvers follows view property"
        )
