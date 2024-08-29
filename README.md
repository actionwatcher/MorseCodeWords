Summary

MorseCodeX is somewhat similar to RufzXP that I wanted for myself on Mac. Though since it is Python it should work on Widnows and Linux as well. I extended the capabilities so it can be used to pactice contest environment for both calls and messages. The data source is selectable and can be SCP(supercheck partial), text (every message in separate line) or call history files. Format of the file determined automatically. In case of call history files the application extracts only message part it randomly select names for entries without names.
The application supports English and Cyrrillic characters data sources for V1.

Source Code Installation (prefered)

Python 3.9 + required (it can be used with lower version of Python but coloring of the result screens will be incorrect due to a bug in tkinter)
Following packages (channel::package) with all the dependencies need to be installed:
* conda-forge::python-sounddevice (numpy will be installed as dependency)
* only for macs: tkmacosx (that needs to be installed through pip3: pip3 install tkmacosx)

Binary Installation MacOS

* install portaudio. I use brew but any package manager will work: brew install portaudio
    if you don't have brew search internet for homebrew installation on mac. Currently supported on Catalina and higher
* download and unarchive MorseCode.zip

Training files are supercheck partials or call history files from N1MM+ logger website thus the training will be on callsignes or exchange messages. However the same way one can form any text file. For example the most common 100 words or anything one desires. Another example can be exchanges for specific contests, letters, numbers, mix and groups. 

Several message source files are povided for your convinuence.

SCPs: (mostly callsign practice)
* MASTER.SCP
* MASTERDX.SCP
* MASTERUSVE.SCP

Words: (general practice)
* letters.txt
* numbers.txt
* states_provinces.txt (US states and Canada provinces)

Call history: (for exchange practice)
* NAQPCW.txt

The QRN noise is lightdimmer.wav from ARRL website. Feel free record yourown and store it in qrn.wav file. Make sure that it is int16 wav and not float 32 @ 24000 samples per second at least

The QRM is slightly off frequency CQing from NU6N

Premessage checkbox controls if the app sends the pre exchange word: tu, r, qsl to simulate contest environment. There is no uniformity and requirements in the contests and I hear that operators send any of those with tu being the most frequent.

Latest Releases Candidate

v1.0_RC1
Windows  SHA256: 1E5A7C5B5CB8A9CADDAA5991B76BCEAA92751A87FA7019B3A9CC3BF71D802FE4
v1.0_RC2
Mac(x86) SHA256: f69e22bf3d6cbe8795d58eefd09c8a55e22b2bcfa033062a57d28ebedaf75735

Knowwn issues:
* slow launch for Mac version
* Mac version: application data files stored in Application directory

Latest Release

None