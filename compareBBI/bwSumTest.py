import bbi
import time
import subprocess
import pandas as pd
import matplotlib.pyplot as plt

dirUrl = 'https://rcdata.nau.edu/genomic-ml/PeakSegFPOP/labels/H3K4me3_TDH_ENCODE/samples/aorta/ENCFF115HTK/'
fileUrl = '%scoverage.bigWig' % dirUrl


def runTest(fileUrl, chrom, start, end, bins):
    diff = end - start
    if diff <= bins:
        raise Exception
    bbiStartTime = time.time()
    with bbi.open(fileUrl) as file:
        bbiOut = file.fetch(chrom, start, end, bins)
    bbiEndTime = time.time()
    bbiLen = len(bbiOut)

    subprocessStartTime = time.time()

    subprocessOut = subprocess.run(['./bigWigSummary', fileUrl, chrom, str(start), str(end), str(bins)],
                           stdout=subprocess.PIPE).stdout.decode('utf-8')
    subprocessEndTime = time.time()
    subprocessLen = len(subprocessOut.split())

    return {'chrom': chrom, 'start': start, 'end': end, 'diff': diff, 'bins': bins,
            'bbiStartTime': bbiStartTime, 'bbiEndTime': bbiEndTime,
            'bbiTimeDiff': bbiEndTime - bbiStartTime, 'bbiLen': bbiLen,
            'subprocessStartTime': subprocessStartTime, 'subprocessEndTime': subprocessEndTime,
            'subprocessTimeDiff': subprocessEndTime - subprocessStartTime, 'subprocessLen': subprocessLen}


chrom = 'chr1'
problemStart = 30028082
problemEnd = 103863906

binsToTest = [10, 100, 500, 1000, 2000, 5000, 10000, 50000, 100000]

binDf = pd.DataFrame()
for bins in binsToTest:
    testOutput = runTest(fileUrl, chrom, problemStart, problemEnd, bins)
    binDf = binDf.append(pd.Series(testOutput), ignore_index=True)


xVals = binDf['bins'].values

plt.plot(xVals, binDf['bbiTimeDiff'].values, label='bbi time diff')
plt.plot(xVals, binDf['subprocessTimeDiff'].values, label='subprocess time diff')

plt.xlabel('num bins')
plt.ylabel('time taken')

plt.title('comparison of bin size between bbi.fetch and subprocess')

plt.legend()

plt.savefig('Screenshots/SumResults.png')