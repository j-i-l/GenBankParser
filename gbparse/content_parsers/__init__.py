from __future__ import absolute_import
from . import default_parsers as dp

default_parser = {
        'locus': {None: dp.locus},
        'definition': {None: dp.definition},
        'accession': {None: dp.accession},
        'version': {None: dp.version},
        'dblink': {None: dp.dblink},
        'keywords': {None: dp.simple_string},
        'source': {
            None: dp.source,
            'organism': dp.source_organism
            },
        'reference': {
            None: dp.reference,
            'authors': dp.reference_authors,
            'title': dp.reference_title,
            'journal': dp.reference_journal
            },
        'comment': {None: dp.simple_string},  # TODO
        'features': {
            None: dp.simple_string,
            'source': dp.features_source,
            'gene': dp.features_gene,
            'cds': dp.features_cds,
            'rrna': dp.features_rna,
            'trna': dp.features_rna,
            'ncrna': dp.features_rna,
            'tmrna': dp.features_rna,
            },
        'origin': {None: dp.origin},
        }
