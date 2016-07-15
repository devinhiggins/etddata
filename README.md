ETD Datastream
=================
The code in this repository is designed to provide tools for creating new datastreams in Fedora Commons. 


Files
-----

*	new_datastream.py: Contains code to connect to Fedora repository, pulls out custom elements from all XML files and add them to a new datastream called "CUSTOM."
*	program_clean.py: Special function to clean up academic program name, based on known issues.
*	xmldata.py: Contains a range of functions for processing ETD metadata, most of which are not needed here. 
*	msu_programs.py: Organizes MSU colleges and departments into structured data based on HTML. Needs improvement.
