import itertools
import os.path
import pickle
import random
import re
import sys

from zipfile import ZipFile

import pyprind



# ==================== Input related code ====================

def read_movies_zip():
    """Yields all the lines from movies.zip one by one"""
    with ZipFile('movies.zip') as zipped:
        with zipped.open('movies.list') as file:
            for line in file:
                yield line.decode('ISO-8859-1')

# a regular expression which matches movie titles from the format in movies.list
# https://en.wikipedia.org/wiki/Regular_expression
titleregex = re.compile('(^.*)\s*?\([\d\?]{4}[/IVXL]*\)')


# regex matching any of the single characters we don't want in our input
badchars = re.compile('[\"\'\n\(\)]')

def cleanline(line: str):
    """Given a raw line, return a cleaned up title"""
    
    # first step: pull out the part of the line we want
    # if you haven't peeked at movies.list yet take a look, you'll understand 
    # why we want to clean up
    match = re.search(titleregex, line)
    if match is None:
        print('Could not parse line ', line)
        return match

    # pull out a specific part of the regex: match group 1
    # that's (^.*) in the regex above
    dirtyTitle = match.group(1)

    # remove any of the bad characters and drop all to lowercase
    return re.sub(badchars, '', dirtyTitle).lower()

def clean_input(names):
    """Given a collection of names, clean them up and remove duplicates"""
    # The expression with the parenthesis is called a generator expression, it's basically shorthand for
    # for name in names:
    #   yield cleanline(name)
    # https://wiki.python.org/moin/Generators
    namegen = (cleanline(name) for name in names)
    
    # finally, create a set
    # a set is an unordered collection which only allows unique members.
    # adding something to a set a second time doesn't do anything
    return set(namegen)

#==================== Markov related code ====================
# for an explaination of Markov chains in general see http://setosa.io/blog/2014/07/26/markov-chains/

def weighted_choice(choices):
    """Given a list of (choice, weight) tuples, return a weighted random selection"""
    total = sum(weight for choice, weight in choices)
    randval = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
      if upto + weight >= randval:
         return choice
      upto += weight
    assert False, "Shouldn't get here"



def markov_randwalk(mark, start):
    """Given a markov chain dict and a starting symbol, generates a string by walking the chain"""
    # set up previous to be our start symbol
    previous = mark[start]
    title = []
    
    # if we have an initial value, i.e. if start isnt '_start_' add it to title
    #  so it will be printed
    if not start == '_start_':
        title.append(start)

    while True:
        # dict.items() produces a list of (key, value) pairs. Coincidentally,
        # this is exactly the input that weighted choice wants!
        newword = weighted_choice(previous.items())

        if newword == '_end_':
            # if we get the end symbol, we're done.
            # don't bother adding it to the title
            break
        title.append(newword)
        previous = mark[newword]
        
    # https://docs.python.org/3/library/stdtypes.html#str.join
    return ' '.join(title)

def calculate_chain(titles):
    """Given a list of clean inputs, computes the markov chain for the data given"""

    # set up our markov chain to have one node: _start_
    # start isn't an actual input, but represents the start of a sentance
    # e.g. nodes which are referenced by start are nodes we've seen at the
    # beginning of a title
    mark = {}
    mark['_start_'] = {}

    for title in pyprind.prog_bar(titles, title = 'generating markov chain'):
        if title is None:
            break
        
        # break the title into words
        words = title.split(' ')

        # previous always refers to the probabilities from the previous symbol
        # because this is the first word our previous is _start_
        previous = mark['_start_']

        for word in words:
            if word is '':
                break
                
            # note down which word we saw
            
            if word not in previous:
                # if we've never seen this word after the previous one, write it down
                previous[word] = 1
                
                if word not in mark:
                    # if we've never seen this word before _period_, add it to the overall chain as well
                    mark[word] = {}
            else:
                # if we've seen it before just increase it's weight by 1
                previous[word] += 1

            previous = mark[word]
        
        # when we've consumed all the input, add the special _end_ symbol to the last word in the sentance
        if '_end_' not in previous:
            previous['_end_'] = 1
        else:
            previous['_end_'] += 1
    return mark

#==================== Main body of program ====================

def titles(mark, seed = '_start_'):
    """Generates unique titles forever"""
    uniq = set()
    while True:
        title = markov_randwalk(mark, seed)
        if title == seed or title in uniq:
            continue
        uniq.add(title)
        yield title

if __name__ == '__main__':
    if not os.path.exists('markov.pickle'):
        progGen = pyprind.prog_bar(read_movies_zip(), iterations = 4085479, title = 'processing input file')
        
        mark = calculate_chain(clean_input(progGen))

        print('saving markov chain to disk...')
        # pickle is python's module for saving an object to disk. Because it's
        # expensive to clean up the input and calculate the chain, I save it to
        # disk so that we only do it once
        pickle.dump(mark, open('markov.pickle', mode='wb'))
    else:
        print('loading markov chain...')
        mark = pickle.load(open('markov.pickle', mode='rb'))

    print('Generating names')
    
    # https://docs.python.org/3/library/sys.html?highlight=sys.argv#sys.argv
    if len(sys.argv) > 1:
        seed = sys.argv[-1]
    else:
        seed = '_start_'

    n = 20
    # print n titles
    for title in itertools.islice(titles(mark, seed), n):
        print(title)
