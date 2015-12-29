import itertools
import random
import argparse
import json
import os
import csv

def main(args):
  #Path is relative to the directory which the script is run from
  words = dict()
  path = args.path
  jsonfn = 'wordderivatives.json'
  analysisfn = 'analysis.csv'
  pseudofn = 'pseudoinput.txt'
  if args.derive:
    filenames = getfilenames(path)
    getderivatives(words,filenames,path)
    writederivatives_to_json(words,jsonfn)
  if args.human:
    if words:
      writeanalysis(words,analysisfn)
    else:
      try:
        with open(jsonfn,'r') as f:
          words = json.load(f)
          writeanalysis(words,analysisfn)
      except FileNotFoundError:
        print('No .json file was found, please use --derive to create one')
  if args.create:
    inputfn = args.create
    if words:
      writeanalysis(words,analysisfn)
    else:
      try:
        with open(jsonfn,'r') as f:
          words = json.load(f)
          createpseudodatafile(words,pseudofn,inputfn)
      except FileNotFoundError:
        print('Either .json file was found then please use --derive to create one\
            or the input file was not found')

def createpseudodatafile(words,pseudofn,inputfn):
  """
    Description: Creates a pseudodatafile with 2 columns; 'incorrectword,correctword'
      where incorrect word is chosen from 
  """
  with open(pseudofn,'w') as pfhandle, open(inputfn,'r') as ihandle:
    ireader = csv.reader(ihandle,delimiter=',',quoting=csv.QUOTE_MINIMAL,quotechar='"')
    for row in ireader:
      word = row[1]
      #Get list of derivatives
      try:
        derivatives = list(words[word].keys())
        #Generate random integer that is within the index of derivatives
        i = random.randint(0,len(derivatives)-1)
        derivative = derivatives[i]
        pfhandle.write(derivative+','+word+'\n')
      except KeyError:
        #Word in input file was not seen when data was analyzed
        #  so we skip it from pseudodata
        continue

def writeanalysis(words,fn):
  with open(fn,'w') as f:
    for word,derivatives in words.items():
      f.write(word)
      for derivative,count in derivatives.items():
        f.write(','+derivative+','+str(count))
      f.write('\n')

def writederivatives_to_json(words,fn):
  """
    Description: Write derivative collection to json in directory of path.
  """
  with open(fn,'w') as f:
    json.dump(words,f)

def getderivatives(words,filenames,path):
  """
    Description: Iterate through all files in filenames and get derivatives for
      each occuring word. Derivatives of a word are incorrect spellings of that word.
  """
  for filename in filenames:
    getderivativesinfile(words,filename,path)

def getderivativesinfile(words,fn,path):
  """
    Description: Collect all words and derivatives seen in data along with count
  """
  #Boilerplate open call
  with open(path+'/'+fn,'r',newline='') as fhandle:
    reader = csv.reader(fhandle,delimiter=',',quoting=csv.QUOTE_MINIMAL,quotechar='"')
    #for row in itertools.islice(reader,0,5):
    for row in reader:
      word = row[1]
      derivative = row[0]
      if word not in words:
        #Word not seen before, add to dict
        words[word] = {derivative:1}
      elif derivative not in words[word]:
        #Word seen at least once before but derivative for word not seen before,
        #  add to subdict of word
        words[word][derivative] = 1
      else:
        # Word and derivative both seen at least once before, count the occurence
        derivativecount = words[word][derivative]
        words[word][derivative] = derivativecount + 1

def getfilenames(path='./'):
  """
    Description: Get the names of all files under path.
    Returns: list of filenames
  """
  (_,_,filenames) = next(os.walk(path),(None,None,[]))
  return filenames

# ---------------------------------------------------------
if __name__ == "__main__":
  #Set up command line argument handling
  parser = argparse.ArgumentParser(description='Analyse word derivatives of data.')
  #Path to data
  parser.add_argument('path',help='Relative path to data. IMPORTANT: Only data files\
      that are to be analysed for derivatives can be in directory at path. So it works\
      both when the data is fragmented in multiple data files and also concatenated into one large input.txt file\
      (but then make sure the input.txt file is the only file in the directory)')
  #Get derivatives from files in ./data and write to json
  parser.add_argument('--derive',action='store_true',help='Get derivatives and their frequencies for each word in datafiles in path')
  #Write analysis of the data in a human readable form
  parser.add_argument('--human',action='store_true',help='Write words, derivatives and frequencies in human readable form .csv file')
  #Create pseudodata from input file
  parser.add_argument('--create',metavar='INPUTFILE',help='Specify the two column input file from which to\
      generate pseudodata, where incorrect word gets replaced by word derivative chosen with equal probability')
  args = parser.parse_args()
  main(args)
