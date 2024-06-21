#!/usr/bin/python2

import os.path
import sys
import itertools
import urllib
import gzip
import math
import array
import subprocess
import os
#from subprocess import call


#######################
# Auxiliary functions #
#######################

# Lexicographic order on first two elements of elements of lists
def lexorder(p1, p2):
  return (True if p1[0] < p2[0]
            else False if p1[0] > p2[0]
                   else p1[1]<p2[1])


#######################
# Top-level functions #
#######################

# generate(): Entry point of file - invoked at end of file
# generate reads a matrix name and a specification (given as a string)
#   from the command line.  It fetches the matrix
#   (from matrices/matrixname.mm), converts the spec to a list,
#   and then calls runspec.
def generate():
   if (len(sys.argv) != 2):
      #print "Usage: python specialize.py matrix-name"
      print ("Usage: " + sys.argv[0] + " matrix-name")
      print ("e.g.: "  + sys.argv[0] + " fidap005")
      print ("e.g.: "  + sys.argv[0] + " FL:FIDAP/ex5")
      return

   # Format of spec is described in doc.  This call turns it from
   # a string into a list, whose printed form matches the string.
   #spec = evalspec(sys.argv[2])

   # Read matrix.  Format is MM:name, FL:group:name, or just name
   matrixname = sys.argv[1]
   source = ''
   colon = matrixname.find(':')
   if colon != -1:
      source = matrixname[0:colon]
      matrixname = matrixname[colon+1:]
      if source == 'FL':
         colon = matrixname.find('/')
         if colon != -1:
            group = matrixname[0:colon]
            matrixname = matrixname[colon+1:]
         else:
            print "Error: FL name not in form 'FL:group:matrix'"
            exit()
   # This code assumes MM and FL matrices have different names - that is,
   # the MM and FL (and group name) suffixes are not retained in the filename.
   mm_matrixname = 'matrices/'+matrixname+'.mm'
   mtx_matrixname = 'matrices/'+matrixname+'.mtx'
   if not os.path.isfile(mm_matrixname):
      if not os.path.isfile(mtx_matrixname):
         inMM = False
         inFL = False
         # Get the matrix from website
         if source == 'MM' or source == '':
            inMM = fetch_from_MM(matrixname)
         else:  # source = 'FL'
            inFL = fetch_from_FL(group, matrixname)
         if not (inMM or inFL):
            print "Matrix not found locally or on web pages"
            exit()
      mtx_to_mm(matrixname)
   matrix = readmatrix(matrixname, mm_matrixname)

   # If matrix is really big, this will take some time, so
   # report progress
   global report_progress
   if matrix['nz'] >= 500000: report_progress = True

   return

#########################
# Matrix input routines #
#########################

# Matrices are read from the repositories in mtx format,
# converted to mm format and stored in matrices folder,
# then read from there into internal format.
# Internal format is a dictionary with fields that include
# at least 'name', 'n', 'nz', and 'data'.  The actual values
# are in the 'data' field, in the form of a list of (row,col,val)
# triples, in row major order; row and col are ints, but val is
# left as a string, since no calculations are ever done on the
# matrix values.

# readmatrix - given name and filename of matrix in mm format,
#   read it and create a "matrix" dictionary.
# (Filename is actually redundant; it's always matrices/<matrix>.mm.)
def readmatrix (name, file):
   mm = open(file, 'r')
   mm_mat = mm.readlines()
   contents = map(lambda x: x.split(), mm_mat)
   dims = contents.pop(0)
   n = int(dims[0])
   nz = int(dims[2])
   contents = map(lambda r: [int(r[0]), int(r[1]), r[2]], contents)
   return dict(name=name, n=n, nz=nz, data=contents)
      
# Get the given matrix from the matrix market.  It will be in
#   'mtx.gz' format.  Save it in matrices/matrixname.mtx.
# This is "web scraping," so is sensitive to the actual format
#   of web pages in the MatrixMarket.
def fetch_from_MM (matrixname):
   # First, need to find file's url.  Search MM matrix page
   mmpage = urllib.urlopen("http://math.nist.gov/MatrixMarket/matrices.html")
   lines = mmpage.readlines()
   theline = filter(lambda ln: ln.find(matrixname+'.') != -1, lines)
   if len(theline) > 1:
      print "Cannot uniquely identify " + matrixname + " in MatrixMarket."
      print "Download mtx file manually into matrices folder."
      return False
   if theline == []:
      return False
   # Found the line for this matrix.  Construct url for mtx.gz file.
   theline = theline[0]
   i = theline.find("/MatrixMarket")
   j = theline.find("html")
   maturl = "http://math.nist.gov" + theline[i:j] + "mtx.gz"
   print ("Matrix " + matrixname + " not in matrices;"
          + " retrieving from " + maturl)
   # urlretrieve gets a url and puts it in a file
   gzipfilename = "matrices/" + matrixname + ".mtx.gz"
   urllib.urlretrieve(maturl, gzipfilename)
   # gzip.open opens a gzipped file just like an ordinary file
   f = gzip.open(gzipfilename, 'rb')
   file_content = f.readlines()
   # save file in matrices folder.
   mtxfilename = "matrices/" + matrixname + ".mtx"
   mtxfile = open(mtxfilename, 'w')
   mtxfile.writelines(file_content)
   mtxfile.close()
   #call(["rm", gzipfilename])   
   os.system("rm " + gzipfilename)
   return True

# Get the given matrix, in the given group, from the Florida
# collection.  Unlike fetch_from_MM, this does not scrape web
# pages, but is still dependent on the directory structure of
# the Florida collection.  The Florida collection also uses
# mtx format.
def fetch_from_FL (group, matrixname):
   # Example: http://www.cise.ufl.edu/research/sparse/MM/HB/bcsstm20.tar.gz
   flpage = ("http://www.cise.ufl.edu/research/sparse/MM/" + group + "/" + matrixname + ".tar.gz")
   #flpage = ("https://sparse.tamu.edu/MM/" + group + "/" + matrixname + ".tar.gz")

   print ("Matrix " + matrixname + " not in matrices;"
          + " retrieving from " + flpage)
   gzipfilename = "matrices/" + matrixname + ".tar.gz"
   urllib.urlretrieve(flpage, gzipfilename)
   #call(["tar", " xvf", gzipfilename]) 
   os.system("tar -xvf " + gzipfilename)
   #os.system("cd " + matrixname)
   os.system("mv " + matrixname + "/" + matrixname + ".mtx matrices/"+ matrixname + ".mtx")
   os.system("rm -rf " + matrixname)  
   os.system("rm " + gzipfilename)
   return True

# mtx_to_mm: matrix is in matrices folder in mtx format, but not
# in mm format (i.e. has just been downloaded from one of the
# collections for the first time).
# The main issues are: the mtx files sometimes contain zeros;
# indexing in mtx format is from one, but we want to index from zero;
# values are not in row-major order.  Furthermore, many
# matrices are "pattern" matrices - indices with no values; in
# that case, we fill in the values with consecutive integers.
def mtx_to_mm (matrixname):
   mtx = open('matrices/'+matrixname+'.mtx', 'r')
   mm = open('matrices/'+matrixname+'.mm', 'w')
   mtx_mat = mtx.readlines()
   # Some matrices have leading whitespaces; strip them
   mtx_mat = map(lambda ln: ln.strip(), mtx_mat)
   # Matrices begin with some meta-data, which we ignore
   while mtx_mat[0][0] not in '0123456789':
      mtx_mat.pop(0)
   # First numeric line gives n_r, n_c, nz; we assume n_r=n_c
   dims = mtx_mat.pop(0).split()
   dims = map(int, dims)
   global report_progress
   if dims[2] >= 500000:
      report_progress = True
      print "Converting to MM format..."
   contents = mtx_mat[:dims[2]]  # florida matrices exhibit some really
              # strange behavior, where len(contents) doesn't match
              # the actual length.  This solves this.  Keep in mind that
              # sometimes MM includes zeros, so dims[2] is not the
              # actual number of nonzeros.
   # Each line has form [row, col, val]
   contents = map(lambda x: x.split(), contents)
   # Handle pattern matrices: values are 1.0, 2.0, ...
   if len(contents[0]) == 2:
      contents = map(lambda p: [p[0][0], p[0][1], float(p[1])],
                     zip(contents, range(1, len(contents)+1)))
   # Convert indices to ints and sort
   contents = map(lambda elt: [int(elt[0]), int(elt[1]), elt[2]],
                  contents)
   contents = sorted(contents, lambda x, y: -1 if lexorder(x,y) else 1)
   # This test for zeros is kind of bogus, but seems to work:
   contents = filter(lambda x: float(x[2])!=0.0, contents)
   dims[2] = len(contents)  # Actual count of non-zeros
   # Convert to use zero-based indices, then convert to string and write
   to_zero_based = lambda r: [r[0]-1, r[1]-1, r[2]]
   to_string = lambda r: str(r[0]) + ' ' + str(r[1]) + ' ' + str(r[2])
   mm.write(to_string(dims) + '\n')
   for r in contents:
      mm.write(to_string(to_zero_based(r))+'\n')
   mtx.close()
   mm.close()
   return



#sys.setrecursionlimit(200000)
generate()

