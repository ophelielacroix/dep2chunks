# UD dependencies to chunks

Convert UD dependencies to chunks (BIO format).

This code is a multi-lingual version of the algorithm proposed in the paper [Investigating NP-Chunking with Universal Dependencies for English](https://www.aclweb.org/anthology/W18-6010.pdf). 
It can be applied to any language of the [Universal Dependencies](https://universaldependencies.org/) treebanks.

Cite 
```
@inproceedings{lacroix2018investigating,
    title = "Investigating {NP}-Chunking with {U}niversal {D}ependencies for {E}nglish",
    author = "Lacroix, Oph{\'e}lie",
    booktitle = "Proceedings of the Second Workshop on Universal Dependencies ({UDW} 2018)",
    month = nov,
    year = "2018",
    address = "Brussels, Belgium",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/W18-6010",
    doi = "10.18653/v1/W18-6010",
    pages = "85--90",
    abstract = "Chunking is a pre-processing task generally dedicated to improving constituency parsing. In this paper, we want to show that universal dependency (UD) parsing can also leverage the information provided by the task of chunking even though annotated chunks are not provided with universal dependency trees. In particular, we introduce the possibility of deducing noun-phrase (NP) chunks from universal dependencies, focusing on English as a first example. We then demonstrate how the task of NP-chunking can benefit PoS-tagging in a multi-task learning setting {--} comparing two different strategies {--} and how it can be used as a feature for dependency parsing in order to learn enriched models.",
}
```

You can run it using:
 
```
python dep2chunks.py -u ud_directory -o output_directory -t treebank_name -c syn
```
where the option `-c` is for selecting between `syn` (i.e. syntactic --all types of chunks-- : VP, NP, PP...) and `core` (only NP chunks).

You can find the treebank names in the ud_utils.py file (e.g. `en_ewt` for the English Web Treebank).

