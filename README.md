# Grammatical-Error-Correction
![flow chart](https://github.com/jimmy133719/Grammatical-Error-Correction/blob/master/flow%20chart.png "Figure 1. Flow chart")

Figure 1. depicts the procedure of our method. Since our problem-word GEC model can only deal with at most five-word length string, I split the long sentence into five-word length by the following code, where `n` and `s` are the length we expected to split into and original sentence respectively.

```
def splitter(n, s):
    pieces = s.split()
    return (" ".join(pieces[i:i+n]) for i in range(0, len(pieces), n))
```

After ensuring that the length of string is allowable, we can feed the input string into model to generate candidates of correct string. The model can be viewed as a dictionary containing the common errors of specific word. There are three cases in model, replacement, deletion, and insertion. For example, if the model sees the word “university” in the input string, it will list all common errors and their corresponding correction as below.

*"university": [["R", "go", "going"], ["R", "grade", "year"],
["R", "student", "students"], ["R", "on", "at"], ["R", "of",
"from"], ["R", "in", "at"], ["I", "from", -2], ["I", "student", 1],
["R", "an", "a"], ["R", "of", "at"], ["R", "in", “from"]]*

The first element in each list represents which case it is. For replacement, the second element is the wrong word existing in the string, and the last element is the correct word to replace the wrong word. For deletion, the second and third element are the wrong word and it relative position to “university” respectively. For insertion, the third element has same meaning as that of deletion, while the second element is the correct word that needs to be inserted. The following code is to implement the correction stored in the model.

```
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
```
The function input `ngram` is the string we are going to correct. To apply model to the string, I convert the data type of `ngram` into list and loop over it to find the word that is in the model. In the case of replacement, there are no location identifiers, so we can easily replace the wrong word appeared with the correct one. In the case of deletion, we need to ensure that the wrong word is in the specific location, otherwise we can’t delete it. In the case of insertion, since we add a new word with respect to it relative location, whether the index of the word is in the range of string length needs to be taken into consideration.
After all the possible correction, the function will return a set of candidates. To avoid missing possible correction, I feed all candidates in the this function to generate more possible answers. I also view original string as a candidate to prevent the corrector from changing the correct sentence.  
Once we have enough candidates, we can query Linggle to get the count of each candidate. Since the sentences with less words usually have more counts, we need to add the string length term into the formula that computes the probability. Last, the candidate with highest probability will be the correction of the string.
