#!/usr/bin/python
import sys
import pylab
from  scipy.io.mmio import mmread, mminfo
from scipy.sparse import coo_matrix


def main():
    if (len(sys.argv) != 2):
        print "Usage: " + sys.argv[0] + " matrix-name"
        sys.exit(0)
    # end if 
    
    matrixName=sys.argv[1]+ ".mtx"
    mm = open(sys.argv[1]+'.mm', 'w')
    outputName=sys.argv[1]+ ".png"
    #outputName=sys.argv[1]+ ".pdf"

    (n,n,nz,void,fld,symm) = mminfo(matrixName)


    A = mmread(matrixName).tocsr().tocoo()
    
    # creating a file in coo format    
    #print n, n, A.size
    mm.write( str(n) + ' ' + str(n) + ' ' + str(A.size) + '\n')
    for i in range(A.size):
        mm.write(  str(A.row[i])+ ' ' + str(A.col[i])+ ' ' + str(A.data[i])+  '\n')
        #print A.row[i]+1, A.col[i]+1 , A.data[i]
    # end for    
    #print repr(A)
    #print A.col
    #print A.size
    # end of creating a file in coo format    
    
    
    #pylab.title("Matrix :" + matrixName, fontsize=22)
    pylab.title("Matrix: " + sys.argv[1] + ", n:" + str(n) + ", nz:" + str(A.size) + '\n',fontsize=10 )
    pylab.spy(A,marker='.',markersize=1)
    pylab.savefig(outputName,format=None)
    #pylab.show()
    
# end of main()    

if __name__ == '__main__':
    main()
# end if            

