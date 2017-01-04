# movies_markov.py
A markov chain generator program I wrote which spits out fake movie titles based on the imdb title corpus.
It was originally a project to help my brother learn python, so it's pretty well documented, and the code
isn't _too_ ugly.

Dependencies: python3 and [pyprind](https://github.com/rasbt/pyprind)

Run with python markov.py [optional seed word].

The first time it's run it will parse the input file (movies.zip) and generate a markov chain (takes about 30s on my machine).
After that it should load pretty fast.

Be warned: it looks like imdb also indexes porn films, so the titles can sometimes be a little risque!
