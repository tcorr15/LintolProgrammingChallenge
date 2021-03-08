"""
City Finder Processor
---------------------

This is an example of a Lintol processor. You can run it like so:

    python3 processor.py out-example-2021-02-01-hansard-plenary.txt

or, if you would like a nicely-formatted HTML page to look at:

    ltldoorstep -o html --output-file output.html process sample_transcripts/out-example-2021-02-01-hansard-plenary.txt processor.py -e dask.threaded

This will create output.html in the current directory and, in a browser (tested with Chrome), should look like output.png.
"""

import re
import sys
import logging
from dask.threaded import get

from ltldoorstep.processor import DoorstepProcessor
from ltldoorstep.aspect import AnnotatedTextAspect
from ltldoorstep.reports.report import combine_reports
from ltldoorstep.document_utils import load_text, split_into_paragraphs

# We name some cities - we will do all our comparisons in lowercase to match any casing
CITIES = ['armagh', 'belfast', 'derry', 'lisburn', 'newry', 'dublin', 'london', 'brussels']
TOWNS = ['comber', 'antrim', 'coleraine', 'enniskillen']
COUNTRIES = ['northen ireland', 'republic of ireland', 'england', 'scotland', 'wales']
SPEAKER = ['mr speaker']
MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'august', 'september',
          'october', 'november', 'december']
DAYS = [str(i) for i in range(0, 32)]
# COVID = ['lockdown', 'deaths', 'cases', 'r', 'reproduction']
# BREXIT_TERMS = ['backstop', 'border', 'union', 'protocol'],
# TRANSFER_TEST = []  # could be used at a later date
# ECONOMY = ['economy', 'restart']


def increment_array_and_count(tag_name, count, word):
    """
    Increment a count within a dictionary or add a new count if necessary
    """
    tag = tag_name
    try:
        count[word] += 1
    except:
        count[word] = 1
    return tag, count


def finder(text, rprt, array_of_keys, tag, warning_exceptions):
    """
    This will take the array of keys and search the unsorted data creates a report for any instances
    """
    paragraphs = split_into_paragraphs(text)
    counts = {item: 0 for item in array_of_keys}
    for para_n, (paragraph, line_number) in enumerate(paragraphs):
        paragraph_lower = paragraph.lower()
        for item in array_of_keys:
            occurrences = paragraph_lower.count(" " + item + " ")
            if occurrences > 0:
                counts[item] += occurrences
                content = AnnotatedTextAspect(paragraph)
                for match in re.finditer(item, paragraph_lower):
                    content.add(
                        note=f'Occurence of {item.title()}',
                        start_offset=match.start(),
                        end_offset=match.end(),
                        level=logging.INFO,
                        tags=[tag]
                    )
                if item in warning_exceptions:
                    urgency = logging.WARNING
                else:
                    urgency = logging.INFO
                rprt.add_issue(
                    urgency,
                    (tag+'-cropped-up'),
                    f'Found {item}',
                    line_number=line_number,
                    character_number=0,
                    content=content
                )
    for item, total in counts.items():
        if total > 0:
            rprt.add_issue(
                logging.INFO,
                (tag+'-totals'),
                f'Found {total} occurrences of {item.title()}'
            )
    return rprt


def country_finder(text, rprt):
    """
    Returns a count and log of instances where a range of key countries have been mentioned
    """
    return finder(text, rprt, COUNTRIES, 'country', ['northern ireland'])


def town_finder(text, rprt):
    """
    Returns a count and log of instances where a range of towns have been mentioned
    """
    return finder(text, rprt, TOWNS, 'town', [])


def city_finder(text, rprt):
    """
    Returns a count and log of instances where a range of key cities have been mentioned
    """
    return finder(text, rprt, CITIES, 'city', ['belfast'])


def mr_speaker_finder(text, rprt):
    """
    Returns a count and log of instances where the speaker has been mentioned
    """
    return finder(text, rprt, SPEAKER, 'speaker-mentioned', [])


def get_frequently_used_stat(text, rprt):
    """
    Gathers the counts of each stat, article and date that is used and as a warning reports the most frequent of each
    """
    paragraphs = split_into_paragraphs(text)
    stat_counts = {}
    article_counts = {}
    percent_counts = {}
    date_counts = {}
    for para_n, (paragraph, line_number) in enumerate(paragraphs):
        paragraph_lower = paragraph.lower()
        word_Array = paragraph_lower.split(' ')
        for count, word in enumerate(word_Array):
            try:
                word_as_int = int(word)  # Check if the word is an int
                deliminator = " "
                if word_Array[count-1] == 'article':  # checks to see if the stat is referring to an article
                    tag, article_counts = increment_array_and_count('article', article_counts, word)
                elif word_Array[count+1] == 'percent' or word_Array[count+1] == "%":  # checks if the stat is referring to a %
                    tag, percent_counts = increment_array_and_count('percent', percent_counts, word)
                elif word_Array[count-1] in MONTHS and word_Array[count-2] in DAYS:  # checks if it is a dd/mm/yyyy
                    word = deliminator.join(word_Array[(count - 2):(count + 1)])
                    tag, date_counts = increment_array_and_count('date', date_counts, word)
                elif word_Array[count-1] in MONTHS and word_Array[count-2] not in DAYS:  # checks to see if it is a mm/yyyy
                    word = deliminator.join(word_Array[count - 1:count + 1])
                    tag, date_counts = increment_array_and_count('date', date_counts, word)
                elif (word_Array[count-1] not in MONTHS and word_Array[count-2] not in DAYS) or (word_Array[count+1] not in MONTHS):
                    tag, stat_counts = increment_array_and_count('stat', stat_counts, word)
                content = AnnotatedTextAspect(paragraph)
                for match in re.finditer(word, paragraph_lower):
                    content.add(
                        note=f'Occurence of {word.title()}',
                        start_offset=match.start(),
                        end_offset=match.end(),
                        level=logging.INFO,
                        tags=[tag]
                    )
                if word in []:
                    urgency = logging.WARNING
                else:
                    urgency = logging.INFO
                rprt.add_issue(
                    urgency,
                    (tag + '-cropped-up'),
                    f'Found {word}',
                    line_number=line_number,
                    character_number=0,
                    content=content
                )
            except:
                pass
    if len(article_counts.keys()) > 0:
        for item, total in article_counts.items():
            if total > 0:
                rprt.add_issue(
                    logging.INFO,
                    'article-totals',
                    f'Found {total} occurrences of {item.title()}'
                )
        maxCount = 0
        maxItem = ""
        for item, total in article_counts.items():
            if total > maxCount:
                maxItem = item
                maxCount = total
        rprt.add_issue(
            logging.WARNING,
            'article-most-mentioned',
            f'Found {maxCount} occurrences of Article {maxItem}'
        )
    if len(stat_counts.keys()) > 0:
        for item, total in stat_counts.items():
            if total > 0:
                rprt.add_issue(
                    logging.INFO,
                    'stat-totals',
                    f'Found {total} occurrences of {item.title()}'
                )
        maxCount = 0
        maxItem = ""
        for item, total in stat_counts.items():
            if total > maxCount:
                maxItem = item
                maxCount = total
        rprt.add_issue(
            logging.WARNING,
            'stat-most-mentioned',
            f'Found {maxCount} occurrences of {maxItem}'
        )
    if len(percent_counts.keys()) > 0:
        for item, total in percent_counts.items():
            if total > 0:
                rprt.add_issue(
                    logging.INFO,
                    'percent-totals',
                    f'Found {total} occurrences of {item.title()}'
                )
        maxCount = 0
        maxItem = ""
        for item, total in percent_counts.items():
            if total > maxCount:
                maxItem = item
                maxCount = total
        rprt.add_issue(
            logging.WARNING,
            'percent-most-mentioned',
            f'Found {maxCount} occurrences of {maxItem}%'
        )
    if len(date_counts.keys()) > 0:
        for item, total in date_counts.items():
            if total > 0:
                rprt.add_issue(
                    logging.INFO,
                    'date-totals',
                    f'Found {total} occurrences of {item.title()}'
                )
        maxCount = 0
        maxItem = ""
        for item, total in date_counts.items():
            if total > maxCount:
                maxItem = item
                maxCount = total
        rprt.add_issue(
            logging.WARNING,
            'date-most-mentioned',
            f'Found {maxCount} occurrences of {maxItem}'
        )
    return rprt


class CityFinderProcessor(DoorstepProcessor):
    """
    This class wraps some of the Lintol magic under the hood, that lets us plug
    our city finder into the online version, and create reports mixing and matching
    from various processors.
    """

    # This is the type of report we create - it could be tabular (e.g. CSV), geospatial
    # (e.g. GeoJSON) or document, as in this case.
    preset = 'document'

    # This is a unique code and version to identity the processor. The code should be
    # hyphenated, lowercase, and start with lintol-code-challenge
    code = 'lintol-code-challenge-finder'

    # This is a short phrase or description explaining the processor.
    description = "City, Town and Country Finder for Lintol Coding Challenge"

    # Some of our processors get very complex, so this lets us build up execution graphs
    # However, for the coding challenge, you probably only want one or more steps.
    # To add two more, create functions like city_finder called town_finder and country_finder,
    # then uncomment the code in this function (and remove the extra parenthesis in the 'output' line)
    def get_workflow(self, filename, metadata={}):
        workflow = {
            'load-text': (load_text, filename),
            'get-report': (self.make_report, ),
            'step-A': (city_finder, 'load-text', 'get-report'),
            'step-B': (town_finder, 'load-text', 'get-report'),
            'step-C': (country_finder, 'load-text', 'get-report'),
            'step-D': (mr_speaker_finder, 'load-text', 'get-report'),
            'step-E': (get_frequently_used_stat, 'load-text', 'get-report'),
            'output': (workflow_condense, 'step-A'),  # 'step-B', 'step-C')  # , 'Step-D')
        }
        return workflow


# If there are several steps, this final function pulls them into one big report.
def workflow_condense(base, *args):
    return combine_reports(*args, base=base)


# This is the actual variable Lintol looks for to set up the processor - you
# shouldn't need to touch it (except to change the class name, if neeeded)
processor = CityFinderProcessor.make
# Lintol will normally execute this processor in its own magical way, but you
# can also run it via the command line without using ltldoorstep at all (just the
# libraries already imported). The code below lets this happen, and prints out a
# JSON version of the report.
if __name__ == "__main__":
    argv = sys.argv
    processor = CityFinderProcessor()
    processor.initialize()
    workflow = processor.build_workflow(argv[1])
    print(get(workflow, 'output'))
