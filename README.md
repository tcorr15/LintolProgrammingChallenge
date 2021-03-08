# Processor for NI Assembly Hansard Minutes

# About
This program is a Lintol processor that will process the following:
	- cities mentioned
	- local towns mentioned
	- any british isles mentioned
	- any time the speaker is spoken to
	- any article that has been mentioned
	- any date that is mentioned
	- any percetages that are mentioned and,
	- any other stats that are mentioned

# Pre-installation requirement

To install all the necessary libraries:
	pip3 install requirements.txt

# Instructions for running

To get an HTML file:

    ltldoorstep -o html --output-file output.html process sample_transcripts/out-example-2021-02-01-hansard-plenary.txt processor.py -e dask.threaded

To get a JSON file

    ltldoorstep -o json --output-file tests/test_report.json process sample_transcripts/out-example-2021-02-01-hansard-plenary.txt processor.py -e dask.threaded
