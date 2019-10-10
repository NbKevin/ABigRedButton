
# A Big Red Button: A Social Network Analyser for the Academia

## Introduction

This is a project intended to analyse the social network within researchers.
It works by iterating over their publications and analyse their relation to
each other following their mutual citation, shared keywords, co-authors, 
research direction and sibling institution, etc. The final result is a series
of graph representation (by edges) which can be visualised using whichever
tool of preference (e.g. Gephy).

The hope of this project is to unveil the hidden network between researchers,
and consequently their stories. This project also hopes to enable social
science and humanities researchers, as well as ones from other non-coding
fields to have access to filtered, processed and analysed data, and to make
their contribution and discoveries.

## Using

You need MongoDB `2.4+` and Python `3.7+`. First install the required packages
with `pip install -r requirements.txt` and then start the project with
`python_exec run.py NO_DEBUG`.

## Disclaimer

The data collected and gathered with this project is meant for the use
of academic research and for this purpose only. It henceforth qualifies
for the term of `Fair Use` and shall be exempted for any infringement complaint.
