fname = '../ESBL_genbank_example.txt'
with open(fname, 'r') as fobj:
    genome = {}
    i = 10
    lines = []
    while i:
        i -= 1
        print i
        lines.append(fobj.readline())
