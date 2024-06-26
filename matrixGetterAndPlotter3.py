#!/usr/bin/python3

import sys
import urllib.request, urllib.parse, urllib.error
import os
import gzip
import functools

#import os.path
#import itertools
#import math
#import array
#import subprocess


import pylab
from  scipy.io import mmread, mminfo
#from  scipy.io.mmio import mmread, mminfo
from scipy.sparse import coo_matrix

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

# main(): Entry point of file - invoked at end of file
# generate reads a matrix name and a specification (given as a string)
#   from the command line.  It fetches the matrix
#   (from matrices/matrixname.mm), converts the spec to a list,
#   and then calls runspec.
def main():
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
            print ("Error: FL name not in form 'FL:group:matrix'")
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
         # end if
         if not (inMM or inFL):
            print ("Matrix not found locally or on web pages")
            exit()
         # end if   
      #mtx_to_mm(matrixname)
   # end if    
   #matrix = readmatrix(matrixname, mm_matrixname)

   # If matrix is really big, this will take some time, so
   # report progress
   #global report_progress
   #if matrix['nz'] >= 500000: report_progress = True
   generate_mm_and_plot(matrixname) 
   return
# end of main()


def generate_mm_and_plot(sysArgv1):

    matrixName='matrices/'+sysArgv1+ ".mtx"
    mm = open('matrices/' +sysArgv1 +'.mm', 'w')
    outputName='matrices/'+sysArgv1 + ".png"
    #outputName=sys.argv[1]+ ".pdf"

    (n,n,nz,void,fld,symm) = mminfo(matrixName)
    
    A = mmread(matrixName).tocsr().tocoo()
    # creating a file in coo format    
    mm.write( str(n) + ' ' + str(n) + ' ' + str(A.size) + '\n')
    for i in range(A.size):
        mm.write(  str(A.row[i])+ ' ' + str(A.col[i])+ ' ' + str(A.data[i])+  '\n')
        #print A.row[i]+1, A.col[i]+1 , A.data[i]
    # end for    
    #print repr(A)
    #print A.col
    #print A.size
    # end of creating a file in coo format    
    #pylab.title("Matrix :" + matrixname, fontsize=22)
    pylab.title("Matrix: " + sysArgv1 + ", n:" + str(n) + ", nz:" + str(A.size) ,fontsize=14 )
    pylab.spy(A,marker='.',markersize=1)
    frame = pylab.gca()
    frame.axes.get_xaxis().set_ticks([])
    pylab.savefig(outputName,format=None)
    #pylab.show()
# end of generate_mm_and_plot()    



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
   contents = [x.split() for x in mm_mat]
   dims = contents.pop(0)
   n = int(dims[0])
   nz = int(dims[2])
   contents = [[int(r[0]), int(r[1]), r[2]] for r in contents]
   return dict(name=name, n=n, nz=nz, data=contents)

      
# Get the given matrix from the matrix market.  It will be in
#   'mtx.gz' format.  Save it in matrices/matrixname.mtx.
# This is "web scraping," so is sensitive to the actual format
#   of web pages in the MatrixMarket.
def fetch_from_MM (matrixname):
   # First, need to find file's url.  Search MM matrix page
   mmpage = urllib.request.urlopen("http://math.nist.gov/MatrixMarket/matrices.html")
   mislineas = mmpage.readlines()
   lines = []
   for ln in mislineas:
       lines.append(ln.decode("utf-8"))
   # end for     
   
   theline = [ln for ln in lines if ln.find(matrixname+'.') != -1]
   if len(theline) > 1:
      print("Cannot uniquely identify " + matrixname + " in MatrixMarket.")
      print("Download mtx file manually into matrices folder.")
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
   urllib.request.urlretrieve(maturl, gzipfilename)
   # gzip.open opens a gzipped file just like an ordinary file
   f = gzip.open(gzipfilename, 'rt')
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
   urllib.request.urlretrieve(flpage, gzipfilename)
   #call(["tar", " xvf", gzipfilename]) 
   os.system("tar -xvf " + gzipfilename)
   #os.system("cd " + matrixname)
   os.system("mv " + matrixname + "/" + matrixname + ".mtx matrices/"+ matrixname + ".mtx")
   os.system("rm -rf " + matrixname)  
   os.system("rm " + gzipfilename)
   return True


if __name__ == '__main__':
    main()
# end if            

