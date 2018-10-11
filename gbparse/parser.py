from __future__ import unicode_literals, absolute_import, print_function
import os
import io
import json
import configparser
import requests
from .content_parsers import default_parser as content_parser


class Parser(object):
    def __init__(self):
        self._section = None
        self._subsection = None
        self._section_content = None
        self._section_content_lines = []
        self._genome_content = {}
        config = configparser.ConfigParser()
        config.read(
                os.path.join(
                    os.path.abspath(
                        os.path.dirname(__file__)
                        ),
                    'config.cfg'
                    )
                )
        self._val_indent_long = config.getint(
                'Default',
                'val_indent_long'
                )
        self._val_indent_short = config.getint(
                'Default',
                'val_indent_short'
                )
        self._val_sep_short = config.getint('Default', 'val_sep_short')
        self._val_sep_long = config.getint('Default', 'val_sep_long')
        self._genome_end = config.get('Default', 'val_genome_end')
        self.ncbi_nuccore_url = config.get(
                'GenBank',
                'ncbi_nuccore_url',
                fallback=None
                )
        self._section_sep = {"FEATURE".lower(): self._val_sep_long}
        self._known_sections = []
        self._known_subsections = {}
        # This attribute holds all conversion functions in form of a dict
        self.content_parser = content_parser
        return None

    class MissingSectionExeption(Exception):
        pass

    class SectionContentParsingException(Exception):
        pass

    @property
    def _val_sep(self,):
        # TODO: this info should be loaded from a json config file
        if self._section == 'FEATURES'.lower():
            return self._val_sep_long
        elif self._section == 'ORIGIN'.lower():
            return 0
        else:
            return self._val_sep_short

    @property
    def _subsection_possible(self,):
        # TODO: this info should be loaded from a json config file
        if self._section == 'ORIGIN'.lower():
            return False
        else:
            return True

    @property
    def _val_indent_subs(self,):
        # TODO: this info should be loaded from a json config file
        if self._section == 'FEATURES'.lower():
            return self._val_indent_long
        else:
            return self._val_indent_short

    def parse(self, fileobject, save_to=None, fct=None, *args, **kwargs):
        """
        This is the 'main' method of a Parser object.
        It takes a fileobject, runs through the lines in the fileobject while
        trying to associate each line to the corresponding section and/or sub-
        section.

        Parameter:
        ----------
        :param fileobject: Opened file that contains the output of
            <some request>.
        :param save_to: string or None determining what to do with the parsed
        genome(s).
            - save_to=None: a list of genomes is generated and returned
                once the parser ran through the file. This mode is not
                recommended if you parse a large list of genomes, as all
                genomes are then loaded into memory.
            - save_to='some/path/to/existing/folder': each genome is saved to
                as a separate json-file in the specified folder. The files are
                named after the LOCUS entry
        :param fct: callable taking a genome as a mandatory first argument.
            This attribute can be used to directly perform a task with each
            genome that is read from the fileobject.
        :param args: Unnamed attributes that will be passed to the callable
            provided in fct.
        :param kwargs: Named attributes that will be passed to the callable
            provided in fct.

        :return: list of parsed genomes
        """
        self._genome_content = {}
        if save_to is None:
            parsed_genomes = []
        for line in fileobject:
            if line.startswith(' '):  # we are in a subsection or content
                if self._subsection_possible and \
                        line[self._val_indent_subs].isalnum():  # new subsect
                    assert(self.parse_section())
                    self._section_content_lines = []
                    assert (self._section is not None)  # subsection must be in
                    # a section
                    # get subsection
                    self._subsection = line[:self._val_sep].strip().lower()
                    self._section_content = []
                else:  # in content block
                    # make sure we know where to put content
                    assert (self._section is not None)
                    assert (self._section_content_lines)
            else:  # we are in a new section or at the end
                if line.startswith(self._genome_end):  # genome ended
                    assert (self.parse_section())  # make sure previous section
                    # is correctly parsed
                    genome = self.parse_genome()
                    if fct is not None:
                        fct(genome, *args, **kwargs)
                    if save_to is None:
                        parsed_genomes.append(genome)
                    else:
                        with open(
                                os.path.join(
                                    save_to,
                                    '{0}.json'.format(genome['locus'][None])
                                ),
                                'w'
                                ) as f_out:
                            json.dump(genome, f_out)
                else:  # new section
                    assert (self.parse_section())  # make sure previous section
                    # is correctly parsed
                    self._subsection = None
                    self._section_content = None
                    self._section_content_lines = []
                    self._section = line[
                            :line.find(' ')
                            ].lower()  # get section
            # # just checking that section (and subsection) are correct
            # assert (self._section in self._known_sections) \
            #         'The current section is not known.'
            # assert (
            #           self._subsection in self._known_subsections[
            #               self._section
            #               ] \
            #         if self._subsection is not None \
            #         else True) \
            #         'The current subsection is not a known subsection for ' \
            #         'the current section'
            # reading out the content
            self._section_content_lines.append(
                    line[self._val_sep:].strip()
                    )
        if save_to is None:
            return parsed_genomes
        else:
            return None

    def _fallback_parser(self, *args):
        missing_parser = False
        if self._section is not None and \
                self._section not in self.content_parser.keys():
            if self._section.isalnum():
                missing_parser = True
        elif self._subsection is not None and \
                self._subsection not in self.content_parser[
                        self._section].keys():
            missing_parser = True
        if missing_parser:
            print(
                    'There is no parser defined for the following '
                    'section/subsection:\nSection:\t{0}\nSubsection:'
                    '\t{1}'.format(self._section, self._subsection)
                    )
        return None

    def parse_section(self,):
        """
        Called at the start of each new section or subsection.
        This method calls the appropriate converter function for the content of
        the previous section (or subsection) if it exists.

        If there is an error during the conversion, this method raises a custom
        Exception.
        """
        # print(self._section, self._subsection, self._section_content_lines)
        if self._section_content_lines:
            # call the appropriate conversion function
            _section_content = self.content_parser.get(
                    self._section,
                    {}
                    ).get(
                            self._subsection,
                            # if self._section is not present, i.e. this boils
                            # down to {}.get(self._subsection)
                            self._fallback_parser
                            )(
                                self._section_content_lines,
                                self._genome_content
                                )
            if _section_content is not None:  # if the content parser did not
                # modify an existing object.
                self._section_content = _section_content
                if self._subsection is not None:  # make sure a section with
                    # subsections is a dictionary.
                    if not isinstance(
                            self._genome_content[self._section],
                            dict
                            ):
                        # need to make this section a dict
                        self._genome_content[self._section] = {
                                None: self._genome_content[self._section]
                                }
                    # add the subsection to the dict of the section
                    self._genome_content[
                            self._section
                            ][
                                    self._subsection
                                    ] = self._section_content
                else:  # dealing with a section
                    self._genome_content[self._section] = {
                        None: self._section_content
                        }
            self._section_content = None  # reset the section content
            self._section_content_lines = []  # reset the content lines
            return True
        elif self._section is None:  # the beginning of the file
            return True
        else:
            raise self.__class__.SectionContentParsingException(
                    'Parsing the content of section {0}{1} failed'.format(
                        self._section,
                        self._subsection if self._subsection else ''
                    )
                )

    def parse_genome(self,):
        genome = dict(self._genome_content)
        self._section = None
        self._subsection = None
        self._sction_content = None
        self._genome_content = {}
        return genome

    def fetch(self, genome_id, *args, **kwargs):
        """
        Method to directly fetch a genome from ncbi GenBank.

        This method tries to fetch a genome and passes the returned content
        as a file object directly to the _self.parser_ method. A part from
        genomd_id instead of fileobject this method takes the same arguments as
        self.parser.

        Parameter:
        ----------
        :param genome_id: Id of the genome(s) to fetch. This can either be an
            int, a string or a list of integers or strings. Possible forms are:
            genome_id = 12345
            genome_id = '12345'
            genome_id = '12345,23456'
            genome_id = [12345, 23456]
            genome_id = ['CP12345', '23456', 34567]
        :type genome_id: int, list

        For additional parameters refer to the self.parser method.
        """

        assert isinstance(genome_id, (int, str, unicode, list)), \
            'genome_id must either be an integer, string or list.'
        if isinstance(genome_id, int):
            genome_id = [genome_id]
        elif isinstance(genome_id, (str, unicode)):
            genome_id = genome_id.replace(' ', '').split(',')
            assert all(
                    [
                        gen_id.isdigit() or gen_id[2:].isdigit()
                        for gen_id in genome_id]
                    ), 'Not all provided genome_ids are numbers.'
        else:
            assert all(
                    [
                        (gen_id.isdigit() or gen_id[2:].isdigit())
                        if isinstance(gen_id, (str, unicode))
                        else isinstance(gen_id, int)
                        for gen_id in genome_id
                        ]
                    ), 'All elements in the genome_id list must either be '\
                        'a string or an integer'
        response = requests.get(
                self.ncbi_nuccore_url.format(','.join(map(str, genome_id)))
                )
        assert response.status_code == 200, 'The provided genome id(s) '\
            'is/are not valid. No content could be fetched from ncbi.'
        response_obj = io.TextIOWrapper(
                io.BytesIO(response.content),
                encoding=response.encoding
                )
        return self.parse(response_obj, *args, **kwargs)
