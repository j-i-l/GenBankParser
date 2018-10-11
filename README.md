# GenBankParser
__*Unofficial*__ parser for ncbi GenBank data in the _GenBank flatfile format_.

# Installation 

TODO: add pip install instructins and proper setup.py

# Package info

## Python compatibility
Works both with python2 and python3.

## Requirements
- [configparser](https://docs.python.org/2/library/configparser.html)

    >pip install configparser
    
- [requests](http://docs.python-requests.org/en/master/)

    >pip install requests
## Accepted content
This GenBankParser aims to parse uncompressed GenBank files in the _GenBank
flatfile format_. 

They are usually of a form similar to this:

```
LOCUS       XXXX             11111111 bp    DNA     circular BCT 01-JAN-2018
DEFINITION  Completely made up, complete genome.
ACCESSION   XXXX
VERSION     XXXX.1  GI:1111111111
DBLINK      BioProject: PRJNA111111
            BioSample: SAMN111111
KEYWORDS    .
SOURCE      Completely made up
  ORGANISM  Completely made up
            Bacteria; Proteobacteria; Gammaproteobacteria; Enterobacterales.
...

```

Accepted are either files with single genomes or genes like [this file](https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi?tool=portal&save=file&log$=seqview&db=nuccore&report=gbwithparts&id=22222&withparts=on) or a complete sequence of genomes available from the [NIH genetic sequence database](https://www.ncbi.nlm.nih.gov/genbank/).

If you want to process sequence of genomes downloaded from the [ncbi GenBank ftp server](ftp://ftp.ncbi.nih.gov/genbank/), please make sure to first decompress the files before using the GenBankParser.

In addition to GenBank files the GenBankParser also accepts GenBank UIDs. GenBankParser then tries to fetch the entries directly from the ncbi database. For an example see the [Use case]() below.

---
# Use cases

## Simple parsing

### Get a list of genomes

    from gbparse import Parser
    
    p = Parser()

    genome_file = '/path/to/genome_file.txt'

    with open(genome_file, 'r') as fobj:
        genomes = p.parse(fobj)

### Save genomes as json files to a directory


    from gbparse import Parser
    
    p = Parser()

    genome_file = '/path/to/genome_file.txt'
    genomes_save_path = '/path/to/genomes/'

    with open(genome_file, 'r') as fobj:
        genomes = p.parse(fobj, genomes_save_path)

## Processing

### retrieve set of all present genes in genomes
You might pass a callable to the parser method. The callable needs to accept 
a genome (a dictionary) as first argument but can de arbitrary otherwise.
Additional arguments can directly be passed to the parser method.

A simple use-case of a callable would be a method extracting certain 
information from each parsed genome, like the set of present genes:


    from gbparse import Parser

    # define a callable that retrieves all genes from a genomes
    def get_genes(genome, present_genomes):
        present_genomes.extend(
    	    list(set(
		    gene.get('gene', None)
		    for gene in genome['content'].get('genes', {})
	        ))
        )
        return None
    
    p = Parser()
    # define result variable
    list_of_present_genes = []

    genome_file = '/path/to/genome_file.txt'

    with open(genome_file, 'r') as fobj:
        p.parse(fobj, fct=get_genes, present_genomes=list_of_present_genes)

## Fetch from ncbi
Say we want the get the first 10 GenBank files that are returned when searching for 'hiv' on the Pubmed database.
Using the [ncbi entrez eutils](https://www.ncbi.nlm.nih.gov/books/NBK25500/) tool the query to retrieve UID's of these entries might look like this:

> https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=hiv&retstart=0&retmax=10&rettype=text&tool=biomed3&format=json

Here is how this can all be done in python:

    import requests
    from gbparse import Parser
    
    # first get the list of UID's
    resp = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=hiv&retstart=0&retmax=10&rettype=text&tool=biomed3&format=json')
    assert resp.status_code == 200
    as_json = resp.json()
    idlist = as_json['esearchresult']['idlist']
    
    # now get the data, parse it and cast the content into a list of genomes
    p = Parser()
    genomes = p.fetch(idlist)
