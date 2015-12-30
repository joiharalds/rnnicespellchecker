import itertools
import random
import argparse
import json
import os
import csv

def main(args):
  fn_to_deriv = dict()
  jsonfn = 'wordderivatives.json'
  analysisfn = 'analysis.csv'
  pseudofn = 'pseudoinput.txt'
  if args.derive:
    #Path is relative to the directory which the script is run from
    path = args.derive
    filenames = getfilenames(path)
    getderivatives(fn_to_deriv,filenames,path)
    writederivatives_to_json(fn_to_deriv,jsonfn)
  if args.human:
    if fn_to_deriv:
      writeanalysis(fn_to_deriv,analysisfn)
    else:
      try:
        with open(jsonfn,'r') as f:
          fn_to_deriv = json.load(f)
          writeanalysis(fn_to_deriv,analysisfn)
      except FileNotFoundError:
        print('No .json file was found, please use --derive to create one')
  if args.create:
    path = args.create
    filenames = getfilenames(path)
    if fn_to_deriv:
      createpseudodatafiles(fn_to_deriv,filenames,path)
    else:
      try:
        with open(jsonfn,'r') as f:
          fn_to_deriv = json.load(f)
          createpseudodatafiles(fn_to_deriv,filenames,path)
      except FileNotFoundError:
        print('Either .json file was found then please use --derive to create one\
            or the input file was not found')

def createpseudodatafiles(fn_to_deriv,filenames,path):
  """
    Description: Iterate through all files in filenames and create a pseudodatafile
      based on each of the files with the corresponding derivatives from fn_to_deriv.
      The pseudodatafile for file1 will have the filename file1.pseudo
  """
  for filename in filenames:
    createpseudodatafile(fn_to_deriv,filename,path)

def createpseudodatafile(fn_to_deriv,inputfn,path):
  """
    Description: Creates a pseudodatafile with 2 columns; 'incorrectword,correctword'
      where incorrect word is chosen from 
    Args:
      inputfn: file to create pseudodata from
      path: relative path from the scripts rundir to inputfn
  """
  pseudodir = './pseudodata'
  if not os.path.exists(pseudodir):
    os.makedirs(pseudodir)
  #Base name on the name of the input data file
  pseudofn = 'pseudo_'+inputfn
  with open(pseudodir+'/'+pseudofn,'w') as pfhandle,\
      open(path+'/'+inputfn,'r',newline='') as ihandle:
    ireader = csv.reader(ihandle,delimiter=',',quoting=csv.QUOTE_MINIMAL,quotechar='"')
    for row in ireader:
      try:
        word = row[1]
        #Get list of derivatives for word specific to the given file
        derivatives = list(fn_to_deriv[inputfn][word].keys())
        # **** Probability ****
        #There is 4/7 probability that we choose from the list of possible derivatives
        # for the given word. The correct word is included in this list.
        l = [1,2,3,4,5,6,7]
        if random.choice(l) > 3:
          derivative = random.choice(derivatives)
        else:
          derivative = word
        pfhandle.write(derivative+','+word+'\n')
      except (KeyError,IndexError):
        #Word in input file was not seen when data was analyzed so we skip it
        #  from pseudodata. Skip over empty lines in input.txt
        continue

def writeanalysis(fn_to_deriv,fn):
  with open(fn,'w') as f:
    for fn,words in fn_to_deriv.items():
      for word,derivatives in words.items():
        f.write(word)
        for derivative,count in derivatives.items():
          f.write(','+derivative+','+str(count))
        f.write('\n')

def writederivatives_to_json(fn_to_deriv,fn):
  """
    Description: Write derivative collection to json in directory of path.
  """
  with open(fn,'w') as f:
    json.dump(fn_to_deriv,f)

def getderivatives(fn_to_deriv,filenames,path):
  """
    Description: Iterate through all files in filenames and get derivatives for
      each occuring word. Derivatives of a word are incorrect spellings of that word.
  """
  for filename in filenames:
    getderivativesinfile(fn_to_deriv,filename,path)

def getderivativesinfile(fn_to_deriv,fn,path):
  """
    Description: Collect all fn_to_deriv and derivatives seen in data along with count
      Each file has its own set of derivatives to reduce noise when creating
      pseudodata.
  """
  with open(path+'/'+fn,'r',newline='') as fhandle:
    reader = csv.reader(fhandle,delimiter=',',quoting=csv.QUOTE_MINIMAL,quotechar='"')
    #for row in itertools.islice(reader,0,5):
    for row in reader:
      try:
        word = row[1]
        derivative = row[0]
        #Remove ' from the set of possible derivatives since it causes problems
        #  in Lua code
        if derivative == "'":
          continue
        if fn not in fn_to_deriv:
          fn_to_deriv[fn] = {word:{derivative:1}}
        if word not in fn_to_deriv[fn]:
          #Word not seen before, add to dict
          fn_to_deriv[fn][word] = {derivative:1}
        elif derivative not in fn_to_deriv[fn][word]:
          #Word seen at least once before but derivative for word not seen before,
          #  add to subdict of word
          fn_to_deriv[fn][word][derivative] = 1
        else:
          # Word and derivative both seen at least once before, count the occurence
          derivativecount = fn_to_deriv[fn][word][derivative]
          fn_to_deriv[fn][word][derivative] = derivativecount + 1
      except IndexError:
        #IndexError probably created because some rows are empty so it is correct to
        #  ignore them
        continue

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
  #Get derivatives from files in ./data and write to json
  parser.add_argument('--derive',metavar='DATAPATH',help='Get derivatives and their frequencies for each word in datafiles in path.\
      Relative path to data. IMPORTANT: Only data files that are to be analysed for\
      derivatives can be in directory at path. So it works both when the data is\
      fragmented in multiple data files and also concatenated into one large input.txt file\
      (but then make sure the input.txt file is the only file in the directory)')
  #Write analysis of the data in a human readable form
  parser.add_argument('--human',action='store_true',help='Write fn_to_deriv, derivatives and frequencies in human readable form .csv file')
  #Create pseudodata from input file
  parser.add_argument('--create',metavar='DATAPATH',help='Specify the two column input file from which to\
      generate pseudodata, where incorrect word gets replaced by word derivative chosen with equal probability')
  args = parser.parse_args()
  main(args)
