import bbi
import time
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import os

fileUrl = 'https://rcdata.nau.edu/genomic-ml/PeakSegFPOP/labels/H3K4me3_TDH_ENCODE/samples/aorta/ENCFF115HTK/coverage.bigWig'


def compare(fileUrl, chrom, start, end):
    bbiStartTime = time.time()
    with bbi.open(fileUrl) as file:
        file.fetch(chrom, start, end)
    bbiEndTime = time.time()
    osStartTime = time.time()
    subprocess.run(['bin/bigWigToBedGraph',
                    fileUrl,
                    'out/out.bedGraph',
                    '-chrom=%s' % chrom,
                    '-start=%s' % start,
                    '-end=%s' % end],
                   stdout=subprocess.PIPE).stdout.decode('utf-8')
    osEndTime = time.time()
    return pd.Series({'chrom': chrom, 'start': start, 'end': end, 'length': end-start,
            'bbiStartTime': bbiStartTime, 'bbiEndTime': bbiEndTime,
            'bbiTimeDiff': bbiEndTime - bbiStartTime,
            'osStartTime': osStartTime, 'osEndTime': osEndTime,
            'osTimeDiff': osEndTime - osStartTime})


def applyTest(row):
    return compare(fileUrl, row['chrom'], row['start'], row['end'])


try:
    os.makedirs('out')
except FileExistsError:
    pass
probs = pd.read_csv('data/problems.bed', header=None, sep='\t')
probs.columns = ['chrom', 'start', 'end']
probs['length'] = probs['end'] - probs['start']
probs = probs.sort_values('length', ignore_index=True, ascending=False)
numTests = 10
biggest = probs.head(numTests)
output = biggest.apply(applyTest, axis=1)

xVals = output['length'].values
plt.plot(xVals, output['bbiTimeDiff'].values, label='bbi time diff')
plt.plot(xVals, output['osTimeDiff'].values, label='os time diff')

plt.xlabel('problem length')
plt.ylabel('time taken')

plt.title('comparison of length size between subprocess and bbi.fetch')

plt.legend()

plt.savefig('compareBBI/Screenshots/FullResults.png')