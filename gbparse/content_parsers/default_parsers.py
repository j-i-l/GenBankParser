from __future__ import unicode_literals, print_function, absolute_import
# we might need to pass en existing dict/list then return None
# if return is None then do not further process content.


def simple_string(content_lines, genome_content):
    _content = ' '.join(content_lines)
    return _content


def locus(content_lines, genome_content):
    _content = ''.join(content_lines).split()
    locus_dict = {'locus': {
            None: _content[0],
            'size [{0}]'.format(_content[2]): _content[1],
            _content[3]: _content[4],
            _content[5]: _content[6]
            }
            }
    genome_content.update(locus_dict)
    return None


def definition(content_lines, genome_content):
    genome_content.update(
            {'definition': simple_string(content_lines, None)}
            )
    return None


def accession(content_lines, genome_content):
    genome_content.update(
            {'accession': simple_string(content_lines, None)}
            )
    return None


def version(content_lines, genome_content):
    _content = ''.join(content_lines).split()
    version_dict = {'version': {
            None: _content[0],
            }
            }
    if len(_content) > 1:
        for _c in _content[1:]:
            _c_k, _c_v = _c.split(':')
            version_dict['version'][_c_k] = _c_v
    genome_content.update(version_dict)
    return None


def dblink(content_lines, genome_content):
    dblink_dict = {'dblink': {}}
    for c_line in content_lines:
        _c_k, _c_v = c_line.strip().replace(' ', '').split(':')
        dblink_dict['dblink'][_c_k] = _c_v
    genome_content.update(dblink_dict)
    return None


def keywords(content_lines, genome_content):
    # TODO: not sure how exactly a keyword string looks like.
    _content = ''.join(content_lines).split()
    genome_content.update({'keywords': _content})
    return None


def _assert_key(gc, _key='content', _value_type=dict):
    if _key not in gc:
        gc[_key] = _value_type()


def source(content_lines, genome_content):
    _content = ' '.join(content_lines)
    _assert_key(genome_content)
    source_dict = {'source': _content.lower()}
    genome_content['content'].update(source_dict)
    return None


def source_organism(content_lines, genome_content):
    _content = '{0}; {1}'.format(
            content_lines[0],
            ''.join(content_lines[1:]).lower()
            )
    _assert_key(genome_content)
    organism_dict = {'organism': [
            x.strip() for x in _content.split(';')
            ]
            }
    genome_content['content'].update(organism_dict)
    return None


def reference(content_lines, genome_content):
    if 'reference' not in genome_content:
        genome_content['reference'] = [
                    {'info': simple_string(content_lines, None)}
                ]
        return None
    else:
        genome_content['reference'].append(
                {'info': simple_string(content_lines, None)}
                )
        return None


def reference_authors(content_lines, genome_content):
    _content = ''.join(content_lines)
    if '. and ' in _content:
        rest, last = _content.split(' and ')
    elif '.and ' in _content:
        rest, last = _content.split('and ')
    else:
        rest, last = _content, ''
    _content = rest.split(', ')
    _content += [last] if last else []
    authors_dict = {
            'authors': ['{0} {1}'.format(
                _auth[:_auth.index(',')],
                _auth[_auth.index(',') + 1:]
                ) for _auth in _content
                ]
            }
    genome_content['reference'][-1].update(authors_dict)
    return None


def reference_title(content_lines, genome_content):
    genome_content['reference'][-1].update(
            {'title': simple_string(content_lines, None)}
            )
    return None


def reference_journal(content_lines, genome_content):
    genome_content['reference'][-1].update(
            {'journal': simple_string(content_lines, None)}
            )
    return None


def _features_source_digest(_k, _v):
    """
    This function properly converts all entries in the FEATURE-source section
    TODO: The proper conversions for each key, value pair need to be made
    """
    if _k == 'collection_date':
        return _v.replace('"', '').lower()  # TODO
    else:
        return _v.replace('"', '').lower()  # TODO


def _features_gene_or_cds_digest(_k, _v):
    """
    This function properly converts all entries in the FEATURE-gene and
    FEATURE-cds sections
    TODO: The proper conversions for each key, value pair need to be made
    """
    if _k == '':
        return _v.replace('"', '').lower()  # TODO
    else:
        return _v.replace('"', '').lower()  # TODO


def _get_gene(_content):
    """
    Create a dictionary from the content of either the FEATURES-gene or the
    FEATURES-cds sections using _features_gene_or_cds_digest to convert each
    value contained in the content.

    Parameter:
    ----------
    :param _content: List of strings each of the form 'some_key="some_value"'
    :return: conversion of the _content to a dictionary.
    """
    _gene = {}
    for _line in _content:
        if '=' in _line:
            _key, _val = _line.split('=')
            _gene[_key.lower()] = _features_gene_or_cds_digest(
                    _key, _val
                    )
        else:
            _gene['bp_range'] = _line
    return _gene


def features_source(content_lines, genome_content):
    _assert_key(genome_content)
    _content = ''.join(content_lines).split('/')
    source_dict = {}
    for _line in _content:
        if '=' in _line:
            _key, _val = _line.split('=')
            source_dict[_key.lower()] = _features_source_digest(
                    _key, _val
                    )
        else:
            source_dict['bp_range'] = _line
    genome_content['content'].update(source_dict)
    return None


def features_gene(content_lines, genome_content):
    _assert_key(genome_content)
    _assert_key(genome_content['content'], 'genes', _value_type=list)
    _content = ''.join(content_lines).split('/')
    _gene = _get_gene(_content)
    _gene['_done'] = False
    _gene['cds_included'] = False
    _gene['rna_included'] = False
    if len(genome_content['content']['genes']):
        genome_content['content']['genes'][-1]['_done'] = True
    genome_content['content']['genes'].append(
                _gene
            )
    return None


def features_cds(content_lines, genome_content):
    _assert_key(genome_content)
    _assert_key(genome_content['content'], 'genes', _value_type=list)
    _content = ''.join(content_lines).split('/')
    _gene = _get_gene(_content)
    _gene['cds_included'] = True  # will overwrite on update
    _gene['_done'] = True
    if not len(genome_content['content']['genes']) or \
            genome_content['content']['genes'][-1]['_done']:
        print(
                'There is a cds without preceding gene part.\nA new gene '
                'will thus be added'
                )
        _gene['rna_included'] = False
        genome_content['content']['genes'].append(
                _gene
                )
    else:
        genome_content['content']['genes'][-1].update(
                    _gene
                )


def features_rna(content_lines, genome_content):
    _assert_key(genome_content)
    _assert_key(genome_content['content'], 'genes', _value_type=list)
    _content = ''.join(content_lines).split('/')
    _gene = _get_gene(_content)
    _gene['rna_included'] = True  # will overwrite on update
    _gene['_done'] = True
    if not len(genome_content['content']['genes']) or \
            genome_content['content']['genes'][-1]['_done']:
        print(
                'There is a <x>RNA without preceding gene part.\nA new gene '
                'will thus be added'
                )
        _gene['cds_included'] = False
        genome_content['content']['genes'].append(
                _gene
            )
    else:
        genome_content['content']['genes'][-1].update(
                    _gene
                )


def origin(content_lines, genome_content):
    _assert_key(genome_content)
    _content = ''.join(
                    ' '.join(
                        [' '.join(x.split(' ')[1:]) for x in content_lines]
                    ).split(' ')
                )
    origin_dict = {'sequence': _content}
    genome_content['content'].update(origin_dict)
    return None
