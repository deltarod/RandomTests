import requests
coverageFile = 'https://rcdata.nau.edu/genomic-ml/PeakSegFPOP/labels/H3K4me3_TDH_ENCODE/samples/aorta/ENCFF115HTK/coverage.bigWig'
penalty = 60000
chrom = 'chr1'
start = 30028082
end = 103863906


with requests.get(coverageFile) as cvg:
    if not cvg.status_code == 200:
        raise Exception


if not os.path.exists(coveragePath):
    return False

modelThreads = []

for penalty in penalties:
    modelData = job.copy()
    modelData['penalty'] = penalty

    modelArgs = (dataPath, modelData, trackUrl)

    modelThread = threading.Thread(target=generateModel, args=modelArgs)
    modelThreads.append(modelThread)
    modelThread.start()

for thread in modelThreads:
    thread.join()

finishQuery = {'command': 'update', 'args': {'id': job['id'], 'status': 'Done'}}

r = requests.post(cfg.jobUrl, json=finishQuery)

if not r.status_code == 200:
    print("Job Finish Request Error", r.status_code)
    return

os.remove(coveragePath)