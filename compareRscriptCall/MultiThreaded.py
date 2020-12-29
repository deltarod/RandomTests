import time
import subprocess
import threading
import pandas as pd
import matplotlib.pyplot as plt
import os


coverage = 'https://rcdata.nau.edu/genomic-ml/PeakSegFPOP/labels/H3K4me3_TDH_ENCODE/samples/aorta/ENCFF115HTK/coverage.bigWig'

subProcessPath = os.path.join('out', 'subprocess')
try:
    os.makedirs(subProcessPath)
except FileExistsError:
    pass


def doOs(coverageFile, penalty):
    scriptLocation = os.path.join('compareRscriptCall', 'GenerateModel.R')
    segmentsFile = coverageFile + '_penalty=%f_segments.bed' % penalty
    osCommand = 'Rscript %s %s %f' % (scriptLocation, coverageFile, penalty)
    os.system(osCommand)
    osDf = pd.read_csv(segmentsFile, header=None, sep='\t')


def doSubprocess(coverageFile, penalty):
    scriptLocation = os.path.join('compareRscriptCall', 'GenerateModel.R')
    segmentsFile = coverageFile + '_penalty=%f_segments.bed' % penalty
    subprocess.run(['Rscript', scriptLocation, coverageFile, '%f' % penalty])
    subprocessDf = pd.read_csv(segmentsFile, header=None, sep='\t')
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
    compareDir = os.path.join(subProcessPath, '%s%s%s' % (row['chrom'], row['start'], row['end']))
    try:
        os.makedirs(compareDir)
    except FileExistsError:
        pass
    coverageFile = os.path.join(compareDir, 'coverage.bedGraph')

    subprocess.run(['bin/bigWigToBedGraph',
                    coverage,
                    coverageFile,
                    '-chrom=%s' % row['chrom'],
                    '-start=%s' % row['start'],
                    '-end=%s' % row['end']])

    data = pd.read_csv(coverageFile, header=None, sep='\t')
    data.columns = ['chrom', 'start', 'end', 'height']

    fixDataDf(data).to_csv(coverageFile, sep='\t', header=False, index=False)

    osStart, osEnd = doTest(doOs, coverageFile)

    subprocessStart, subprocessEnd = doTest(doSubprocess, coverageFile)

    return pd.Series({'length': row['end'] - row['start'], 'osStart': osStart, 'osEnd': osEnd, 'osDiff': osEnd - osStart,
                      'subprocessStart': subprocessStart, 'subprocessEnd': subprocessEnd,
                      'subprocessDiff': subprocessEnd - subprocessStart})


def doTest(target, coverageFile):
    penalties = [100, 1000, 10000, 100000, 1000000]
    threads = []
    start = time.time()
    for penalty in penalties:
        args = (coverageFile, penalty)
        thread = threading.Thread(target=target, args=args)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    end = time.time()
    return start, end

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

plt.title('comparison of multi threaded speed for Rcall with os or subprocess')

plt.legend()

plt.savefig('compareRscriptCall/Screenshots/MultiResults.png')
