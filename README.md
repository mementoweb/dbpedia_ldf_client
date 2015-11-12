# A DBPedia Proxy for Memento Compatible LDF Server

This proxy is a wrapper that converts the triples from [Memento LDF Server](https://github.com/mementoweb/Server.js/tree/memento) into a DBPedia like single page serialization. 

* Supports HTML, N3, N-Triples, XML, and Turtle serializations.
* Requires Python > 3.5.
* Requires the Python [RDFLib](https://github.com/RDFLib/rdflib) library version > 4.2, and uWSGI > 2.0.
