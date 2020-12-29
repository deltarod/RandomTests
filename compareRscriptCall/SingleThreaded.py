import time
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
import os

coverage = 'https://rcdata.nau.edu/genomic-ml/PeakSegFPOP/labels/H3K4me3_TDH_ENCODE/samples/aorta/ENCFF115HTK/coverage.bigWig'

subProcessPath = os.path.join('out', 'subprocess')
try:
    os.makedirs(subProcessPath)
except FileExistsError:
    pass


def compare(coverageUrl, chrom, start, end, penalty):
    compareDir = os.path.join(subProcessPath, '%s%s%s' % (chrom, start, end))
    try:
        os.makedirs(compareDir)
    except FileExistsError:
        pass
    coverageFile = os.path.join(compareDir, 'coverage.bedGraph')
    scriptLocation = os.path.join('compareRscriptCall', 'GenerateModel.R')
    subprocess.run(['bin/bigWigToBedGraph',
                     coverageUrl,
                     coverageFile,
                     '-chrom=%s' % chrom,
                     '-start=%s' % start,
                     '-end=%s' % end])

    data = pd.read_csv(coverageFile, header=None, sep='\t')
    data.columns = ['chrom', 'start', 'end', 'height']

    fixDataDf(data).to_csv(coverageFile, sep='\t', header=False, index=False)

    osCommand = 'Rscript %s %s %f' % (scriptLocation, coverageFile, penalty)
    segmentsFile = coverageFile + '_penalty=%f_segments.bed' % penalty

    osStart = time.time()
    os.system(osCommand)
    osDf = pd.read_csv(segmentsFile, header=None, sep='\t')
    osEnd = time.time()

    subprocessStart = time.time()
    subprocess.run(['Rscript', scriptLocation, coverageFile, '%f' % penalty])
    subprocessDf = pd.read_csv(segmentsFile, header=None, sep='\t')
    subprocessEnd = time.time()

    return {'length': end - start, 'osStart': osStart, 'osEnd': osEnd, 'osDiff': osEnd - osStart,
            'subprocessStart': subprocessStart, 'subprocessEnd': subprocessEnd,
            'subprocessDiff': subprocessEnd - subprocessStart}



def fixDataDf(data):
    chrom = data['chrom'].iloc[0]
    gapStarts = data['end'].tolist()
    gapStarts.insert(0, 0)
    gapEnds = data['start'].tolist()
    gapEnds.append(0)

    potentialGaps = pd.DataFrame({'start': gapStarts, 'end': gapEnds})

    gaps = potentialGaps[potentialGaps['start'] < potentialGaps['end']].copy()
    gaps['chrom'] = chrom
    gaps['height'] = 0

    output = pd.concat([data, gaps[gaps['start'] != 0]])
    return output.sort_values('start', ignore_index=True)


def runTest(row):
    return pd.Series(compare(coverage, row['chrom'], row['start'], row['end'], 60000))

probs = pd.read_csv('data/problems.bed', header=None, sep='\t')
probs.columns = ['chrom', 'start', 'end']
probs['length'] = probs['end'] - probs['start']
numTests = 10
tests = probs.head(numTests)

output = tests.apply(runTest, axis=1)

toGraph = output.sort_values('length', ignore_index=True)

xVals = toGraph['length'].values
plt.plot(xVals, toGraph['osDiff'].values, label='os time taken')
plt.plot(xVals, toGraph['subprocessDiff'].values, label='subprocess time taken')

plt.xlabel('problem length')
plt.ylabel('time taken')

plt.title('comparison of single threaded speed for Rcall with os or subprocess')

plt.legend()

plt.savefig('compareRscriptCall/Screenshots/SingleResults.png')



