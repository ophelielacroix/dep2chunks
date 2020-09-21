
import sys, os
import argparse
from ud_utils import *

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--uddir', type=str, default="ud-treebanks-v2.6")
    parser.add_argument('-o', '--outdir', type=str)
    parser.add_argument('-t', '--treebanks', nargs='*', type=str)
    parser.add_argument('-c', '--chunks', default="syn", choices=["syn", "core"])
    args = parser.parse_args()

    assert(os.path.isdir(args.uddir))
    assert(os.path.isdir(args.outdir))

    if not args.treebanks:
        print("Processing all UD treebanks \n")
        treebanks = [v for v in tbk_map.values()]
    else:
        treebanks = []
        for tbk in args.treebanks:
            if not tbk in tbk_map:
                print(tbk, "is not a valid treebank name -- SKIP")
            else:
                treebanks.append(tbk_map[tbk])

    out_tag = "BI-CHUNK-CORE" if args.chunks == "core" else "BI-CHUNK-SYN"

    for tbk_name in treebanks:
        print("Processing", tbk_name)
        tbk_name = "UD_"+tbk_name
        if not os.path.exists(os.path.join(args.outdir, tbk_name)):
            os.makedirs(os.path.join(args.outdir, tbk_name))
        for filename in [f for f in os.listdir(os.path.join(args.uddir, tbk_name)) if f.endswith(".conllu")]:
            print("\t", filename.replace(".conllu", "").split("-")[-1], end=" ")
            print()
            with open(os.path.join(args.uddir, tbk_name, filename)) as f:
                sentences = read_conllu(f)
                for sent in sentences:
                    tokens = sent["tokens"]
                    for tok in tokens:
                        head = [str(i) for i, t in enumerate(tokens) if t["ID"] == tok["HEAD"]]
                        tok["dep_head"] = head[0] if head != [] else "_"
                    tokens = deduce_chunks(tokens, level=args.chunks)
                    # for t in tokens:
                    #     print("\t".join([t["ID"], t["FORM"], t["UPOSTAG"], t["HEAD"], t["BI-CHUNK-SYN"]]))
                    # exit()
            print(len(sentences), "sentences")
            with open(os.path.join(args.outdir, tbk_name, filename), 'wt') as f:
                for sent in sentences:
                    for t in sent["tokens"]:
                        f.write("\t".join([t["ID"], t["FORM"], t["UPOSTAG"], t["HEAD"], t[out_tag]])+"\n")
                    f.write("\n")




def deduce_chunks(words, level="syn", debug=False):
    """
    deduce chunks
    - syntactic chunks (high-level NP, VP, PP...)   ---> "BI-CHUNK-SYN"
    - core chunks (only NP) ---> "BI-CHUNK-CORE"
    """


    def get_neighbors(i, words):
        nghbs = []
        for j in range(i+1, len(words)):
            nghbs.append(words[j]["CHUNKS"])
            if words[j]["DEPREL"] not in ["fixed", "goeswith"]:
                break
        for j in range(i-1, -1, -1):
            nghbs.append(words[j]["CHUNKS"])
            if words[j]["DEPREL"] not in ["fixed", "goeswith"]:
                break
        return nghbs

    # first loop:
    # tagging the head of chunks (root of the subtrees)
    nb_chunks = 0
    for i, tok in enumerate(words):
        ### NP: nouns, proper nouns and pronouns
        if tok["UPOSTAG"] in ["PROPN", "PRON", "NUM"]:
            nb_chunks += 1
            tok["CHUNKS"] = "NP-"+str(nb_chunks)
        elif tok["UPOSTAG"] in ["NOUN"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                nb_chunks += 1
                tok["CHUNKS"] = "NP-"+str(nb_chunks)
        elif tok["UPOSTAG"] in ["SYM"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            elif tok["FORM"].lower() in numerical_symbol or "$" in tok["FORM"]:
                nb_chunks += 1
                tok["CHUNKS"] = "NP-"+str(nb_chunks)
            else: # punct reparandum discourse
                tok["CHUNKS"] = None
        elif tok["UPOSTAG"] in ["X"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                tok["CHUNKS"] = None
        ### VP : auxiliaries and verbs
        elif tok["UPOSTAG"] in ["AUX", "VERB"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                nb_chunks += 1
                tok["CHUNKS"] = "VP-"+str(nb_chunks)
        ### PP : prepositions
        elif tok["UPOSTAG"] in ["ADP"]:
            if any(dep in tok["DEPREL"] for dep in ["case", "mark", "compound:prt"]):
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                tok["CHUNKS"] = None
        elif tok["UPOSTAG"] in ["PART"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                tok["CHUNKS"] = None
        ### ADV : adverbs
        elif tok["UPOSTAG"] in ["ADV"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                nb_chunks += 1
                tok["CHUNKS"] = "ADVP-"+str(nb_chunks)
        elif tok["UPOSTAG"] in ["DET"]:
            if "advmod" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "ADVP-"+str(nb_chunks)
            else:
                nb_chunks += 1
                tok["CHUNKS"] = None
        ### ADJ : adjectives
        elif tok["UPOSTAG"] in ["ADJ"]:
            if "case" in tok["DEPREL"]:
                nb_chunks += 1
                tok["CHUNKS"] = "PP-"+str(nb_chunks)
            else:
                nb_chunks += 1
                tok["CHUNKS"] = "ADJP-"+str(nb_chunks)
        ### CONJ : conjunctions
        elif tok["UPOSTAG"] in ["SCONJ", "CCONJ"]:
            nb_chunks += 1
            tok["CHUNKS"] = "CONJ-"+str(nb_chunks)
        else:
            tok["CHUNKS"] = None

    attach = True
    while attach:
        attach = False
        for i, tok in enumerate(words):
            head = tok["dep_head"]
            if head == '_':
                continue
            head = int(head)

            ### attaching core chunks
            if words[head]["CHUNKS"] is not None \
               and tok["CHUNKS"] != words[head]["CHUNKS"]:

                head_chunk = words[head]["CHUNKS"].split("-")[0]

                ### the incoming dependency of the token is labelled with one of the primary dependency of its head
                if tok["DEPREL"] in chunk_deps[head_chunk]["primary"]:
                    deprel = tok["DEPREL"]

                    ### no PoS tag constraints or the token's PoS is allowed
                    if len(chunk_deps[head_chunk]["primary"][deprel]) == 0 or \
                        tok["UPOSTAG"] in chunk_deps[head_chunk]["primary"][deprel]:
                        attach = True
                        tok["CHUNKS"] = words[head]["CHUNKS"]
                        # attaching all tokens in between
                        for j in range(i, head):
                            words[j]["CHUNKS"]= words[head]["CHUNKS"]
                        for j in range(head,i):
                            words[j]["CHUNKS"]= words[head]["CHUNKS"]
                        continue

                neighbors = get_neighbors(i, words)

                ### the token is a neighbor of its head and its incoming dependency is in the secondary list
                if tok["DEPREL"] in chunk_deps[head_chunk]["secondary"] and \
                   words[head]["CHUNKS"] in neighbors:

                    if tok["DEPREL"] == "punct" and tok["FORM"] not in  ["-", "/", "'", '"', "(", ")"]:
                       continue

                    deprel = tok["DEPREL"]
                    if len(chunk_deps[head_chunk]["secondary"][deprel]) != 0 and \
                       tok["UPOSTAG"] not in chunk_deps[head_chunk]["secondary"][deprel]:
                       continue

                    attach = True
                    tok["CHUNKS"] = words[head]["CHUNKS"]

            ### re-attach alone punctuations, conjunctions and parts in between a chunk
            if (tok["DEPREL"] in ["punct", "cc"] or (tok["DEPREL"] =="case" and tok["UPOSTAG"] == "PART")) and i != 0 and i != len(words)-1:
               if words[i-1]["CHUNKS"] == words[i+1]["CHUNKS"] and tok["CHUNKS"] != words[i-1]["CHUNKS"] and words[i-1]["CHUNKS"] != None:
                   attach = True
                   tok["CHUNKS"] = words[i-1]["CHUNKS"]

    ### fill the gaps (if there are some splitted chunks, we group them)
    fill_gaps = False
    if fill_gaps:
        chunks = {}
        last = None
        for i, tok in enumerate(words):
            if tok["CHUNKS"] != None:
                if tok["CHUNKS"] in chunks:
                    if last != tok["CHUNKS"]:
                        for j in range(chunks[tok["CHUNKS"]], i):
                            words[j]["CHUNKS"] = tok["CHUNKS"]
                else:
                    chunks[tok["CHUNKS"]] = i
            last = tok["CHUNKS"]

    #### turn indexed chunks into BIO encoding
    cur_s_chunk = None
    s_chunks = []
    is_s_splitted = False
    if level == "core": # core chunks (NPs)
        for tok in words:
            if tok["CHUNKS"] is None or not tok["CHUNKS"].startswith("NP-"):
                cur_s_chunk = None
                tok["BI-CHUNK-CORE"] = 'O'
            elif tok["CHUNKS"] != cur_s_chunk:
                if tok["CHUNKS"] in s_chunks:
                    is_s_splitted = True
                s_chunks.append(tok["CHUNKS"])
                tok["BI-CHUNK-CORE"] = 'B'
                cur_s_chunk = tok["CHUNKS"]
            else:
                tok["BI-CHUNK-CORE"] = 'I'
    else: # syntactic chunks
        for tok in words:
            if tok["CHUNKS"] is None:
                cur_s_chunk = None
                tok["BI-CHUNK-SYN"] = 'O'
            elif tok["CHUNKS"] != cur_s_chunk:
                if tok["CHUNKS"] in s_chunks:
                    is_s_splitted = True
                s_chunks.append(tok["CHUNKS"])
                tok["BI-CHUNK-SYN"] = 'B-'+tok["CHUNKS"].split('-')[0]
                cur_s_chunk = tok["CHUNKS"]
            else:
                tok["BI-CHUNK-SYN"] = 'I-'+tok["CHUNKS"].split('-')[0]

    return words



def read_conllu(stream, clean=False):

    conllu_headers = ["ID", "FORM", "LEMMA", "UPOSTAG", "XPOSTAG", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC"]

    sent_id = 1
    sentences = [{"sent_id": "", "text":"", "tokens":[], "dot":0, "dash":0}]

    for line in stream:
        if line[0] == "#":
            if line.split(' = ', maxsplit=1)[0] == "# sent_id":
                sentences[-1]["sent_id"] = line.strip().split(' = ', maxsplit=1)[1]
                sent_id += 1
            elif line.split(' = ', maxsplit=1)[0] == "# text":
                sentences[-1]["text"] = line.strip().split(' = ', maxsplit=1)[1]
        elif len(line.strip().split("\t")) <= 1:
            sentences.append({"sent_id": "", "text":"", "tokens":[], "dot":0, "dash":0})
        elif "." in line.strip().split("\t")[0]:
            sentences[-1]["dot"] += 1
        elif "-" in line.strip().split("\t")[0]:
            sentences[-1]["dash"] += 1
        else:
            line = line.strip().split('\t')
            sentences[-1]["tokens"].append({h:e for h,e in zip(conllu_headers, line)})


    if len(sentences[-1]["tokens"]) == 0:
        del sentences[-1]

    return sentences



if __name__ == '__main__':

    main()