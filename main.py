# coding=utf-8
"""Grammar Checker in Python 3; see http://norvig.com/spell-correct.html

Copyright (c) 2019-2019 Jason S. Chang
MIT license: www.opensource.org/licenses/mit-license.php
"""

import re, json, operator, sys, urllib, requests, string
import numpy as np
from collections import Counter
from math import log10, log


# model path
problem_word_path = 'model.txt'

# linggle api url
NGRAM_API_URI = "https://{0}.linggle.com/query/"
EXP_API_URI = "https://{0}.linggle.com/example/"

# set length upperbound
max_len = 5

punc = [i for i in string.punctuation]

###################
# Linggle api 
###################
class Linggle:
	def __init__(self, ver='www'):
		self.ver = ver
	def __getitem__(self, query):
		return self.search(query)
	def search(self, query):
		query = query.replace('/', '@')
		query = urllib.parse.quote(query, safe='')
		req = requests.get(NGRAM_API_URI.format(self.ver) + query)
		results = req.json()
		return results.get("ngrams", [])
	def get_example(self, ngram_str):
		res = requests.post(EXP_API_URI.format(self.ver), json={'ngram': ngram_str})
		if res.status_code == 200:
			result = res.json()
			return result.get("examples", [])
		return []


# open linggle api
ling = Linggle()



#####################
# Ngram probability #
#####################
def P(ngram, logN=12., MINCOUNT=40.): 
	"Probability of ngram based Web 1T using Linggle API"
#	ngram, leng = ' '.join(ngram), float(len(ngram))
	leng = float(len(ngram.split(' ')))
    # query number
	linggle_ngram = ling.search(ngram)
	linggle_ngram = linggle_ngram[0][1] if len(linggle_ngram)>0 else 0
	return (log(linggle_ngram,10)-12)/pow(leng,1./2.5) if linggle_ngram>0 else (log10(MINCOUNT)-12) # original: pow(leng, 1./2.5)



##############################################
# Result after first edition
##############################################
def edits1(ngram, model):
    "TODO: handle possible Insert, Delete, Replace edits using data from model"
    splits = ngram.split(' ') # convert input string into the list of words in string
    replaces = []
    deletes = []
    inserts = []
    for i in range(len(splits)): # loop the word in string
        problem_word = channel_model(splits[i],model)
        if problem_word is not []: # check if the word is in model
            for j in range(len(problem_word)): # loop the correction for this word
                # replace
                if problem_word[j][0] == 'R': 
                    replaces.append(ngram.replace(problem_word[j][1], problem_word[j][2]))
                # delete
                elif problem_word[j][0] == 'D': 
                    if i+problem_word[j][2] < len(splits) and i+problem_word[j][2]>-1 and splits[i+problem_word[j][2]] == problem_word[j][1]:                        
                        deletes.append(ngram.replace(splits[i+problem_word[j][2]]+' ', ''))
                # insert
                elif problem_word[j][0] == 'I':
                    temp = [item for item in splits]
                    # ways to deal with the correction before and after the word are different
                    if problem_word[j][2] < 0:
                        temp.insert(max(0,i+problem_word[j][2]+1),problem_word[j][1])
                    else:
                        temp.insert(i+problem_word[j][2],problem_word[j][1])
                    inserts.append(' '.join(temp))
             
    return set(deletes + replaces + inserts)

##########################
# Result after second edition
##########################
def edits2(ngram, model): 
	"All changes that are two edits away from ngram"
	return set(e2 for e1 in edits1(ngram, model) for e2 in edits1(e1, model))



#############################
# candidates
#############################
def candidates(ngram, model): 
	"TODO: Generate possible correction"
	return (edits1(ngram, model) or edits2(ngram, model) or [ngram]) 


###############################
# select best correction from candidates
###############################
def correction(ngram, model): 
    "TODO: Return most probable grammatical error correction for ngram."
#    print(candidates(ngram, model))
    return max(candidates(ngram, model), key=P)
	



################################
# check if problem word is in model
################################
def channel_model(problem_word, model):
	return model[problem_word] if(problem_word in model) else []



##############################
# load model json
##############################
def read_problem_word(path):
	with open(path, 'r') as f:
		model = json.load(f)
	return model

###########################################
# split string into five-word length    
###########################################
def splitter(n, s):
    pieces = s.split()
    return (" ".join(pieces[i:i+n]) for i in range(0, len(pieces), n))


#################
# MAIN
#################
if __name__ == '__main__':
    # read problem_word
    model = read_problem_word(problem_word_path)
	
    "TODO: Read testing data, write correction to output file"
    f1 = open('input.txt','r')
    contents = f1.read()
    f1.close()
    sentences = contents.split('\n')
    sentences = list(filter(None, sentences))
    
    # if the string contains more than five words, split it into the strings with at most five words
    correct_sentences = []
    for sentence in sentences:
        if len(sentence.split(' '))>5:
            correct_sentence = ''
            cnt = 0
            for piece in splitter(5, sentence):
                if cnt == 0:
                    correct_sentence += correction(piece, model)
                else:
                    correct_sentence += (' '+correction(piece, model))
                cnt += 1
        else:        
            correct_sentence = correction(sentence, model)
        print('before correction: {}\nafter correction: {}\n'.format(sentence, correct_sentence))
        correct_sentences.append(correct_sentence)
            
    # read ground truth to evaluate    
    f = open('output.txt','r')
    gt_contents = f.read()
    f.close()
    gt_sentences = gt_contents.split('\n')
    gt_sentences = list(filter(None, gt_sentences))

    
    accuracy = len([gt_sentences[i] for i in range(0, len(gt_sentences)) if gt_sentences[i] == correct_sentences[i]]) / len(gt_sentences)
    print('accuracy: {}'.format(accuracy))
