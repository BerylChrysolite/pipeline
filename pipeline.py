#!/usr/bin/python
#pipeline.py

'''
The MIT License (MIT)

Copyright (c) 2013 Charles Lin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
'''

#module of functions/code/structures from the myc project that has now been
#addapted for general use


import sys
from utils import *

import time
import re
#the master data table
#everything starts with this
#format is as follows

#FILE_PATH UNIQUE_ID NAME BACKGROUND ENRICHED_REGION ENRICHED_MACS COLOR

#FILE_PATH = FOLDER WHERE THE BAM FILE LIVES
#UNIQUE_ID = TONY UNIQUE ID
#GENOME = GENOME USED. MM9, HG18 ARE SUPPORTED
#NAME = IDENTIFIER OF THE DATASET NEEDS TO BE UNIQUE
#BACKGROUND = NAME OF THE BACKGROUND DATASET
#ENRICHED_REGION = NAME OF THE ERROR MODEL ENRICHED REGION OUTPUT
#ENRICHED_MACS = NAME OF THE MACS PEAKS BED FILE
#COLOR = COMMA SEPARATED RGB CODE


#==========================================================================
#===================FORMATTING FOLDERS=====================================
#==========================================================================

def formatFolder(folderName,create=False):

    '''
    makes sure a folder exists and if not makes it
    returns a bool for folder
    '''
    
    if folderName[-1] != '/':
        folderName +='/'

    try: 
        foo = os.listdir(folderName)
        return folderName
    except OSError:
        print('folder %s does not exist' % (folderName))
        if create:
            os.system('mkdir %s' % (folderName))
            return folderName
        else:
                    
            return False 


#==========================================================================
#===================FORMATTING THE MASTER DATA TABLE=======================
#==========================================================================

def formatDataTable(dataFile):
    '''
    formats the dataFile and rewrites.
    first 3 columns are required for every line.
    if they aren't there the line is deleted
    '''
    print('reformatting data table')


    dataTable = parseTable(dataFile,'\t')

    newDataTable = [['FILE_PATH','UNIQUE_ID','GENOME','NAME','BACKGROUND','ENRICHED_REGION','ENRICHED_MACS','COLOR']]
    #first check to make sure the table is formatted correctly
    
    for line in dataTable[1:]:
        if len(line) < 3:
            continue
        #check if it at least has the first 3 columns filled in
        if len(line[0]) == 0 or len(line[1]) == 0 or len(line[2]) == 0:
            print('ERROR required fields missing in line')
            print(line)
        #if the first three are filled in, check to make sure there are 8 columns
        else:
            if len(line) > 3 and len(line) < 8:
                newLine = line + (8-len(line))*['']
                newDataTable.append(newLine)
            elif len(line) >= 8:
                newLine = line[0:8]
                newDataTable.append(newLine)
    
    #lower case all of the genomes
    #make the color 0,0,0 for blank lines and strip out any " marks
    for i in range(1,len(newDataTable)):
        newDataTable[i][2] = lower(newDataTable[i][2])
        color = newDataTable[i][7]
        if len(color) == 0:
            newDataTable[i][7] = '0,0,0'
    unParseTable(newDataTable,dataFile,'\t')
    return newDataTable

                




#==========================================================================
#===================LOADING THE MASTER DATA TABLE==========================
#==========================================================================

def loadDataTable(dataFile):

    if type(dataFile) == str:
        dataTable = parseTable(dataFile,'\t')
    else:
        dataTable = list(dataFile)
    #first check to make sure the table is formatted correctly
    for line in dataTable:
        #print(line)
        if len(line) != 8:
            print('this line did not pass')
            print(line)
            dataTable = formatDataTable(dataFile)
            break
        
    dataDict = {}

    
    
    for line in dataTable[1:]:
        
        dataDict[line[3]] = {}

        dataDict[line[3]]['folder'] = line[0]
        dataDict[line[3]]['uniqueID'] = line[1]
        dataDict[line[3]]['genome']=upper(line[2])
        genome = line[2]
        dataDict[line[3]]['bam'] = line[0]+line[1]+'.'+genome+'.bwt.sorted.bam'
        dataDict[line[3]]['sam'] = line[0]+line[1]+'.'+genome+'.bwt.sam'
        dataDict[line[3]]['ylf'] = line[0]+line[1]+'.'+genome+'.bwt.ylf'
        dataDict[line[3]]['enriched'] = line[5]
        dataDict[line[3]]['background'] = line[4]
        dataDict[line[3]]['enrichedMacs'] = line[6]
        dataDict[line[3]]['color'] = line[7]
            

    return dataDict

#==========================================================================
#===================LOADING THE MASTER DATA TABLE==========================
#==========================================================================

def summary(dataFile,outputFile=''):

    '''
    gives a summary of the data and its completeness
    '''

    dataDict = loadDataTable(dataFile)

    dataList = dataDict.keys()
    dataList.sort()
    output= []
    for name in dataList:
        uniqueID = dataDict[name]['uniqueID']
        cmd = 'perl /nfs/young_ata/scripts/getTONY_info.pl -i %s -f 2' % (uniqueID)
        tonyQuery = os.popen(cmd)

        tonyName = tonyQuery.read().rstrip()
        
        print('dataset name\t%s\tcorresponds to tony name\t%s' % (name,tonyName))
        output.append('dataset name\t%s\tcorresponds to tony name\t%s' % (name,tonyName))

    #for each dataset
    for name in dataList:
        #check for the bam
        try:
            bam = open(dataDict[name]['bam'],'r')
            hasBam = True
        except IOError:
            hasBam = False

        #check for ylf
        try:
            ylf = open(dataDict[name]['ylf'],'r')
            hasYlf = True
        except IOError:
            hasYlf = False

        if hasBam == False:
            print('No .bam file for %s' % (name))
            output.append('No .bam file for %s' % (name))
        if hasYlf == False:
            print('No .ylf file for %s' % (name))
            output.append('No .ylf file for %s' % (name))

    if outputFile:
        unParseTable(output,outputFile,'')
        


#mapping the data


#==========================================================================
#===================CALLING BOWTIE TO MAP DATA=============================
#==========================================================================


def callBowtie(dataFile,dataList = [],overwrite = False):

    '''
    calls bowtie for the dataset names specified. if blank, calls everything
    '''
    
    dataDict = loadDataTable(dataFile)

    if len(dataList) == 0:
        dataList = dataDict.keys()
    
    for name in dataList:
        
        #make sure the output folder exists
        try:
            foo = os.listdir(dataDict[name]['folder'])
        except OSError:
            print('no output folder %s for dataset %s. Creating directory %s now.' % (dataDict[name]['folder'],name,dataDict[name]['folder']))
            os.system('mkdir %s' % (dataDict[name]['folder']))

            
        if upper(dataDict[name]['genome']) == 'HG18' or upper(dataDict[name]['genome']) == 'MM8':
            cmd = 'perl /nfs/young_ata/scripts/generateSAM_file.pl -R -G -c 4 -B -i %s -o %s' % (dataDict[name]['uniqueID'],dataDict[name]['folder'])
        elif upper(dataDict[name]['genome']) == 'RN5':
            cmd = 'perl /nfs/young_ata/CYL_code/generateSam_rat.pl -R -c 4 -B -i %s -o %s' % (dataDict[name]['uniqueID'],dataDict[name]['folder'])
        else:
            cmd = 'perl /nfs/young_ata/scripts/generateSAM_file.pl -R -c 4 -B -i %s -o %s' % (dataDict[name]['uniqueID'],dataDict[name]['folder'])
        
        #first check if the bam exists
        if overwrite:
            print(cmd)
            os.system(cmd)
        else:
            try:
                foo = open(dataDict[name]['bam'],'r')
                print('BAM file already exists for %s. OVERWRITE = FALSE' % (name))
            except IOError:
                print('no bam file found for %s, mapping now' % (name))
                print(cmd)
                os.system(cmd)



#==========================================================================
#===================GETTING MAPPING STATS==================================
#==========================================================================

def bowtieStats(dataFile,namesList=[]):

    '''
    gets stats from the bowtie out file for each bam
    does not assume bowtie output format is always the same
    '''
    dataDict = loadDataTable(dataFile)
    print('DATASET\t\tSEED LENGTH\tTOTAL READS (MILLIONS)\tALIGNED\tFAILED\tMULTI')
    if len(namesList) == 0:
        namesList= dataDict.keys()
    for name in namesList:

        readLength,readCount,alignedReads,failedReads,multiReads = False,False,False,False,False
        bowtieOutFile = dataDict[name]['folder'] + dataDict[name]['uniqueID']+ '.bowtie.output'
        try:
            bowtieOut = open(bowtieOutFile,'r')
        except IOError:
            print('NO BOWTIE OUTPUT FOR %s' % (name))
            continue
        for line in bowtieOut:
            #get the read length
            if line[0] == '':
                continue
            if line[0:4] == 'File':
                readLength = line.split('=')[1][1:-1]

            if line[0] == '#' and line.count('reads') == 1:
                
                if line.count('processed') == 1:

                    readCount = line.split(':')[1][1:-1]
                    readCount = round(float(readCount)/1000000,2)
                if line.count('reported alignment') == 1:
                    alignedReads = line[-9:-1]

                if line.count('failed') == 1:
                    failedReads = line[-9:-1]
                if line.count('suppressed') == 1:
                    multiReads = line[-9:-1]

        if readLength and readCount and alignedReads and failedReads and multiReads:
            print('%s\t\t%s\t%s\t%s\t%s\t%s' % (name,readLength,readCount,alignedReads,failedReads,multiReads))
        else:
            print('%s\tNO DATA AVAILABLE' % (name))


        
        

#==========================================================================
#===================MERGE BAMS=============================================
#==========================================================================

def mergeBams(dataFile,mergedName,namesList,color='',background =''):

    '''
    merges a set of bams and adds an entry to the dataFile
    '''
    dataDict = loadDataTable(dataFile)

    #make an .sh file to call the merging
    
    bamFolder = dataDict[namesList[0]]['folder']
    genome = lower(dataDict[namesList[0]]['genome'])
    if color == '':
        color = dataDict[namesList[0]]['color']

    if background == '':
        background = dataDict[namesList[0]]['background']

        
    
    if bamFolder[-1] != '/':
        bamFolder+='/'
    mergedFullPath = bamFolder+mergedName +'.'+genome+'.bwt.sorted.bam'

    mergeShFile = open(mergedFullPath+'.sh','w')

    mergeShFile.write('cd %s\n' % (bamFolder))

    cmd1 = 'samtools merge %s ' % mergedFullPath

    for name in namesList:

        cmd1+= ' %s' % (dataDict[name]['bam'])

    mergeShFile.write(cmd1+'\n')

    cmd2 = 'samtools sort %s %s' % (mergedFullPath,bamFolder+mergedName+'.'+genome+'.bwt.sorted')
    mergeShFile.write(cmd2+'\n')

    cmd3 = 'samtools index %s' % (mergedFullPath)
    mergeShFile.write(cmd3+'\n')

    mergeShFile.close()

    runCmd = "bsub -o /dev/null 'bash %s'" % (mergedFullPath+'.sh')
    os.system(runCmd)

    dataTable = parseTable(dataFile,'\t')

    dataTable.append([bamFolder,mergedName,genome,mergedName,background,'','',color])
    unParseTable(dataTable,dataFile,'\t')
    formatDataTable(dataFile)


#==========================================================================
#===================CALLING MACS ==========================================
#==========================================================================

def callMacs(dataFile,macsFolder,namesList = [],overwrite=False,pvalue='1e-9'):

    '''
    calls the macs error model
    '''
    dataDict = loadDataTable(dataFile)

    if macsFolder[-1] != '/':
        macsFolder+='/'
    formatFolder(macsFolder,True)

    #if no names are given, process all the data
    if len(namesList) == 0:

        namesList = dataDict.keys()


    for name in namesList:
        
        #skip if a background set
        if upper(dataDict[name]['background']) == 'NONE':
            continue

        #check for the bam
        try:
            bam = open(dataDict[name]['bam'],'r')
            hasBam = True
        except IOError:
            hasBam = False

        #check for background
        try:
            backgroundName = dataDict[name]['background']
            backbroundBam = open(dataDict[backgroundName]['bam'],'r')
            hasBackground = True
        except IOError:
            hasBackground = False

        if not hasBam:
            print('no bam found for %s. macs not called' % (name))
            continue

        if not hasBackground:
            print('no background bam %s found for dataset %s. macs not called' % (backgroundName,name))
            continue
        #make a new folder for every dataset
        outdir = macsFolder+name
        #print(outdir)
        try:
            foo = os.listdir(outdir)
            if not overwrite:
                print('MACS output already exists for %s. OVERWRITE = FALSE' % (name))
                continue
            
        except OSError:
            os.system('mkdir %s' % (outdir))
            
        os.chdir(outdir)
        genome = dataDict[name]['genome']
        #print('USING %s FOR THE GENOME' % genome)
        
        bamFile = dataDict[name]['bam']
        backgroundName =  dataDict[name]['background']
        backgroundBamFile = dataDict[backgroundName]['bam']
        if upper(genome[0:2]) == 'HG':
            cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'macs14 -t %s -c %s -f BAM -g hs -n %s -p %s -w -S --space=50'" % (bamFile,backgroundBamFile,name,pvalue)
        elif upper(genome[0:2]) == 'MM':
            cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'macs14 -t %s -c %s -f BAM -g mm -n %s -p %s -w -S --space=50'" % (bamFile,backgroundBamFile,name,pvalue)
        elif upper(genome[0:2]) == 'RN':
            cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'macs14 -t %s -c %s -f BAM -g 2000000000 -n %s -p %s -w -S --space=50'" % (bamFile,backgroundBamFile,name,pvalue)
        print(cmd)
        os.system(cmd)

#==========================================================================
#===================FORMAT MACS OUTPUT=====================================
#==========================================================================

def formatMacsOutput(dataFile,macsFolder,macsEnrichedFolder,wiggleFolder,wigLink=True):

    dataDict = loadDataTable(dataFile)

    if macsFolder[-1] != '/':
        macsFolder+='/'

    if macsEnrichedFolder[-1] != '/':
        macsEnrichedFolder+='/'

    #make an output directory for the macsEnriched
    formatFolder(macsEnrichedFolder,True)
    #make an output directory for the wiggles
    formatFolder(wiggleFolder,True)


        
    
    namesList = dataDict.keys()
    namesList.sort()
    dataTable = parseTable(dataFile,'\t')

    if wigLink:
        genome = lower(dataDict[namesList[0]]['genome'])
        cellType = lower(namesList[0].split('_')[0])
        wigLinkFolder = '/lab/solexa_young/bam/wiggles/%s/%s' % (genome,cellType)
        formatFolder(wigLinkFolder,True)


    newDataTable = [dataTable[0]]

    dataTableRows = [line[3] for line in dataTable]
    for name in namesList:
        outwiggleFileName = '%s%s_treat_afterfiting_all.wig.gz' % (wiggleFolder,name)
        #find the row in the old dataTable
        print('looking for macs output for %s' % (name))
        i = dataTableRows.index(name)
        #skip if a background set
        if upper(dataDict[name]['background']) == 'NONE':
            newLine = list(dataTable[i])
            newLine[6] = 'NONE'
            newDataTable.append(newLine)
            continue
        #check to see if the wiggle exists in the correct folder
        try:
            outwiggle = open('%s%s_treat_afterfiting_all.wig.gz' % (wiggleFolder,name),'r')
            outwiggle.close()
        except IOError:
            #move the wiggle and add the itemrgb line
            if dataDict[name]['color'] == '0,0,0':
                print('moving wiggle for %s over without changing color' % (name))
                cmd = 'mv %s%s/%s_MACS_wiggle/treat/%s_treat_afterfiting_all.wig.gz %s' % (macsFolder,name,name,name,outwiggleFileName)
                os.system(cmd)
            else:
                try:
                    #print(name)
                    print('for dataset %s going from %s%s/%s_MACS_wiggle/treat/%s_treat_afterfiting_all.wig.gz' % (name,macsFolder,name,name,name))
                    wiggle = open('%s%s/%s_MACS_wiggle/treat/%s_treat_afterfiting_all.wig.gz' % (macsFolder,name,name,name),'r')
                    #print(name)
                    print('and writing to %s%s_treat_afterfiting_all.wig.gz' % (wiggleFolder,name))
                
                    outwiggle = open(outwiggleFileName,'w')

                    print('writing new wiggle with color line for %s' % (name))
                    header = wiggle.readline().rstrip()
                    color = dataDict[name]['color']
                    header = header + ' itemRgb="On" color="%s"' % (color) + '\n'
                    outwiggle.write(header)
                    for line in wiggle:
                        outwiggle.write(line)
                    outwiggle.close()
                    wiggle.close()

                
                except IOError:
                    print('WARNING: NO MACS WIGGLE FOR %s' %(name)) 

        
        if wigLink:
            #time.sleep(10)
            print('Creating symlink for dataset %s in %s' % (name,wigLinkFolder))
            os.system('cd %s' % (wigLinkFolder))
            os.chdir(wigLinkFolder)
            print('cd %s' % (wigLinkFolder))
            wigLinkFileName = '%s_treat_afterfitting_all.wig.gz' % (name)
            print('ln -s %s %s' % (outwiggleFileName,wigLinkFileName))
            os.system('ln -s %s %s' % (outwiggleFileName,wigLinkFileName))


        #first check if the thing exists
        try:
            foo = open('%s%s_peaks.bed' % (macsEnrichedFolder,name),'r')
            newLine = list(dataTable[i])
            newLine[6] = name+'_peaks.bed'
            newDataTable.append(newLine)
        except IOError:
            #move the bedFile of the peaks
        
            try:
                foo = open('%s%s/%s_peaks.bed' % (macsFolder,name,name),'r')
                cmd = 'mv %s%s/%s_peaks.bed %s' % (macsFolder,name,name,macsEnrichedFolder)
                newLine = list(dataTable[i])
                newLine[6] = name+'_peaks.bed'
                newDataTable.append(newLine)
                print(cmd)
                os.system(cmd)
            except IOError:
                print('WARNING: NO MACS OUTPUT FOR %s' %(name)) 
                newLine = list(dataTable[i])
                newLine[6] = 'NONE'
                newDataTable.append(newLine)


        

    unParseTable(newDataTable,dataFile,'\t')

#==========================================================================
#===================MAKING GFFS OF TSS REGIONS=============================
#==========================================================================
        
def makeGeneGFFs(annotFile,gffFolder,species='HG18'):

    '''
    makes a tss gff with the given window size for all genes in the annotation
    tss +/-5kb
    tss +/-300
    body +300/+3000
    can work on any genome build given the right annot file
    '''


    if gffFolder[-1] != '/':
        gffFolder+='/'

    try:
        foo = os.listdir(gffFolder)
        print('Directory %s already exists. Using %s to store gff' % (gffFolder,gffFolder))
    except OSError:
        cmd = 'mkdir %s' % (gffFolder)
        print('making directory %s to store gffs' % (gffFolder))
        os.system(cmd)


    startDict = makeStartDict(annotFile)

    geneList = startDict.keys()
    
    tssLoci = []
    for gene in geneList:
        tssLocus = Locus(startDict[gene]['chr'],startDict[gene]['start'][0]-5000,startDict[gene]['start'][0]+5000,startDict[gene]['sense'],gene)
        tssLoci.append(tssLocus)
    tssCollection = LocusCollection(tssLoci,500)
    tssGFF_5kb = locusCollectionToGFF(tssCollection)


    for gene in geneList:
        tssLocus = Locus(startDict[gene]['chr'],startDict[gene]['start'][0]-1000,startDict[gene]['start'][0]+1000,startDict[gene]['sense'],gene)
        tssLoci.append(tssLocus)
    tssCollection = LocusCollection(tssLoci,500)
    tssGFF_1kb = locusCollectionToGFF(tssCollection)
    
    tssGFF_300 = []
    txnGFF = []

    for line in tssGFF_5kb:
        gene = line[1]
        chrom = startDict[gene]['chr']
        start = startDict[gene]['start'][0]
        end = startDict[gene]['end'][0]
        sense = startDict[gene]['sense']
        name = startDict[gene]['name']
        tssLine = [chrom,gene,'',start-300,start+300,'',sense,'',gene]
        if sense == '+':
            txnLine = [chrom,gene,'',start+300,end+3000,'',sense,'',gene]
        else:
            txnLine = [chrom,gene,'',end-3000,start-300,'',sense,'',gene]

        tssGFF_300.append(tssLine)
        txnGFF.append(txnLine)

     
    unParseTable(tssGFF_5kb,gffFolder + '%s_TSS_ALL_-5000_+5000.gff' % (species),'\t')
    unParseTable(tssGFF_5kb,gffFolder + '%s_TSS_ALL_-1000_+1000.gff' % (species),'\t')
    unParseTable(tssGFF_300,gffFolder + '%s_TSS_ALL_-300_+300.gff' % (species),'\t')
    unParseTable(txnGFF,gffFolder + '%s_BODY_ALL_+300_+3000.gff' % (species),'\t')

#==========================================================================
#===================MAKING GFFS OF CHROMS==================================
#==========================================================================
        
def makeChromGFFs(chromLengthFile,gffFolder,chromList = [],genome='HG18',binSize = 100000,singleGFF = True):

    '''
    makes GFFs of chromosomes, each chrom gets its own gff
    '''
    formatFolder(gffFolder,True)
    chromLengthDict = {}
    chromLengthTable = parseTable(chromLengthFile,'\t')


    genomesList = uniquify([line[2] for line in chromLengthTable])

    for x in genomesList:
        chromLengthDict[upper(x)] = {}

    for line in chromLengthTable:
        chromLengthDict[upper(line[2])][line[0]] = int(line[4])
    if len(chromList) ==0:
        chromList = chromLengthDict[upper(genome)].keys()
        chromList.sort()
    masterGFF = []
    for chrom in chromList:
        if chromLengthDict[upper(genome)].has_key(chrom):
            chromGFF = []
            ticker = 1
            for i in range(1,chromLengthDict[genome][chrom],int(binSize)):
                chromGFF.append([chrom,'bin_%s' % (str(ticker)),'',i,i+binSize,'','.','',''])
                ticker+=1
            if not singleGFF:
                unParseTable(chromGFF,gffFolder+'%s_%s_BIN_%s.gff' % (upper(genome),upper(chrom),str(binSize)),'\t')
            if singleGFF:
                masterGFF+=chromGFF

    if singleGFF:
        unParseTable(masterGFF,gffFolder+'%s_BIN_%s.gff' % (upper(genome),str(binSize)),'\t')




    




#==========================================================================
#===================MAKING GFFS OF ENHANCER REGIONS========================
#==========================================================================


def makeEnhancerGFFs(dataFile,gffName,namesList,annotFile,gffFolder,enrichedFolder,window=2000,macs=True):
    '''
    find all possible enhancers.
    enhancers defined as h3k27ac binding sites +/-5kb outside of promoters
    we define center of enhancer as the center of the bound region
    '''

    dataDict = loadDataTable(dataFile)


    if enrichedFolder[-1] != '/':
        enrichedFolder+='/'

    if gffFolder[-1] != '/':
        gffFolder+='/'

    #nameList = ['H128_H3K27AC','H2171_H3K27AC','MM1S_H3K27AC_DMSO','MM1S_H3K27AC_JQ1','U87_H3K27AC','P493-6_T0_H3K27AC','P493-6_T1_H3K27AC','P493-6_T24_H3K27AC']

    #first make the tss collection
    tssGFF = makeTSSGFF(annotFile,5000,5000)
    tssCollection = gffToLocusCollection(tssGFF)

    #make a blank collection to load enhancers into
    enhancerCollection = LocusCollection([],500)

    #don't allow overlapping enhancers
    species = upper(dataDict[namesList[0]]['genome'])


    for name in namesList:


        print('finding enhancers in %s' % (name))
        if macs:
            boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enrichedMacs'],name)
        else:
            boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enriched'],name)
        for locus in boundCollection.getLoci():
            #make sure an overlapping enhancer doesn't already exist
            if len(tssCollection.getOverlap(locus,'both')) == 0 and len(enhancerCollection.getOverlap(locus,'both')) == 0:
                center = (locus.start()+locus.end())/2
                gffLocus = Locus(locus.chr(),center-window,center+window,'.',locus.ID())
                enhancerCollection.append(gffLocus)


    enhancerGFF = locusCollectionToGFF(enhancerCollection)
    print('Found %s enhancers in %s' % (len(enhancerGFF),gffName))
    unParseTable(enhancerGFF,gffFolder+'%s_ENHANCERS_%s_-%s_+%s.gff' % (species,gffName,window,window),'\t')


#==========================================================================
#===================MAKING GFFS OF ENRICHED REGIONS========================
#==========================================================================


def makeEnrichedGFFs(dataFile,namesList,gffFolder,enrichedFolder,macs=True,window=0):
    '''
    make gffs from enriched regions +/- a window
    '''

    dataDict = loadDataTable(dataFile)
    

    if enrichedFolder[-1] != '/':
        enrichedFolder+='/'

    if gffFolder[-1] != '/':
        gffFolder+='/'


    if len(namesList) == 0:
        namesList = dataDict.keys()
    species = upper(dataDict[namesList[0]]['genome'])
    for name in namesList:

        
        print('making enriched region gff in %s' % (name))
        if macs:
            if len(dataDict[name]['enrichedMacs']) ==0 or dataDict[name]['enrichedMacs'] =='NONE':
                continue
            boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enrichedMacs'],name)
        else:
            if len(dataDict[name]['enriched']) ==0 or dataDict[name]['enriched'] =='NONE':
                continue
            boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enriched'],name)
        
        boundLoci = boundCollection.getLoci()

        enrichedCollection = LocusCollection([],500)
        for locus in boundLoci:
            searchLocus = makeSearchLocus(locus,int(window),int(window))
            enrichedCollection.append(searchLocus)
            
        enrichedGFF = locusCollectionToGFF(enrichedCollection)
        print('Found %s enriched regions in %s' % (len(enrichedGFF),name))
        unParseTable(enrichedGFF,gffFolder+'%s_ENRICHED_%s_-%s_+%s.gff' % (species,name,window,window),'\t')


#==========================================================================
#===================MAKING GFFS OF ENRICHED REGIONS========================
#==========================================================================

def makePromoterGFF(dataFile,annotFile,promoterFactor,enrichedFolder,gffFolder,window=0,transcribedGeneFile=''):

    '''
    uses a promoter associated factor to define promoter regsion.  Can include a window to extend promoter regions as well as a transcribed gene list to restrict set of genes
    '''
    window = int(window)
    #loading the dataTable
    dataDict = loadDataTable(dataFile)

    #finding the promoter factor in the enriched folder
    formatFolder(enrichedFolder,True)
    formatFolder(gffFolder,True)

    #establishing the output filename
    genome = dataDict[promoterFactor]['genome']
    
    output = '%s%s_PROMOTER_%s_-%s_+%s.gff' % (gffFolder,upper(genome),promoterFactor,window,window)

    #getting the promoter factor
    enrichedCollection = importBoundRegion(enrichedFolder + dataDict[promoterFactor]['enrichedMacs'],promoterFactor)

    #making the start dict
    startDict = makeStartDict(annotFile)

    #getting list of transcribed genes
    if len(transcribedGeneFile) > 0:
        transcribedTable = parseTable(transcribedGeneFile,'\t')

        geneList = [line[1] for line in transcribedTable]

    else:
        geneList = startDict.keys()

        
    #now make collection of all transcribed gene TSSs

    tssLoci = []

    for geneID in geneList:
        tssLocus = Locus(startDict[geneID]['chr'],startDict[geneID]['start'][0],startDict[geneID]['start'][0]+1,'.',geneID)
        tssLoci.append(tssLocus)

    tssCollection = LocusCollection(tssLoci,50)

    #a promoter is a single promoter associated enriched region 
    #site that overlaps at most 2 unique genes

    promoterGFF = []
    promoterLoci = enrichedCollection.getLoci()

    for locus in promoterLoci:

        overlappingTSSLoci = tssCollection.getOverlap(locus,'both')
        if len(overlappingTSSLoci) == 0:
            continue
        else:


            geneNames = [startDict[x.ID()]['name'] for x in overlappingTSSLoci]
            geneNames = uniquify(geneNames)

            if len(geneNames) <= 2:
                refseqString = join([x.ID() for x in overlappingTSSLoci],',')
                chrom = locus.chr()
                start = locus.start()-window
                end = locus.end()+window
                strand = locus.sense()
                promoterGFF.append([chrom,locus.ID(),'',start,end,'',strand,'',refseqString])

    unParseTable(promoterGFF,output,'\t')
#==========================================================================
#===================MAP ENRICHED REGIONS TO GFF============================
#==========================================================================

def mapEnrichedToGFF(dataFile,setName,gffList,cellTypeList,enrichedFolder,mappedFolder,macs=True,namesList=[]):

    '''
    maps enriched regions from a set of cell types to a set of gffs
    tries to make a new folder for each gff
    '''

    dataDict = loadDataTable(dataFile)

    formatFolder(enrichedFolder,True)
    formatFolder(mappedFolder,True)


    for gffFile in gffList:

        gffName = gffFile.split('/')[-1].split('.')[0]
        print('making enriched regions to %s' % (gffName))
        #make the gff into a collection


        try:
            foo = os.listdir(mappedFolder)
        except OSError:
            print('making directory %s to hold mapped enriched files' % (mappedFolder))
            os.system('mkdir %s' % (mappedFolder))


        
        outdir = mappedFolder+gffName+'/'

        try:
            foo = os.listdir(mappedFolder+gffName)
        except OSError:
            os.system('mkdir %s' % (outdir))
        
        #first filter the name list
        cellTypeNameList =[] 
        if len(namesList) == 0:
            namesList = dataDict.keys()
        for name in namesList:

            #check to make sure in the right celltype
            #also make sure to not process WCEs
            if dataDict[name]['background'] == 'NONE':
                continue
            cellName = name.split('_')[0]
            if macs == True:
                if cellTypeList.count(cellName) == 1 and dataDict[name]['enrichedMacs'] != 'NONE':
                    cellTypeNameList.append(name)

            else:
                if cellTypeList.count(cellName) == 1 and dataDict[name]['enriched'] != 'NONE':
                    cellTypeNameList.append(name)

        cellTypeNameList.sort()

        mappedGFF = [['GFF_LINE','ID'] + cellTypeNameList]
        #now we go through the gff and fill in stuff
        gffTable = parseTable(gffFile,'\t')

        gffLoci = []
        #making the header line
        for line in gffTable:
            gffLocus = Locus(line[0],line[3],line[4],line[6],line[8])
            gffLine = gffLocus.__str__()
            gffID = line[1]
            
            gffLoci.append(gffLocus)
            mappedGFF.append([gffLine,gffID])
            
        for name in cellTypeNameList:
            print('dataset %s' % (name))
            if macs:
                enrichedCollection = importBoundRegion(enrichedFolder + dataDict[name]['enrichedMacs'],name)
            else:
                enrichedCollection = importBoundRegion(enrichedFolder + dataDict[name]['enriched'],name)
            for i in range(len(gffLoci)):
                if len(enrichedCollection.getOverlap(gffLoci[i],'both')) > 0:
                    mappedGFF[i+1].append(1)
                else:
                    mappedGFF[i+1].append(0)


        unParseTable(mappedGFF,outdir+gffName+'_'+setName+'.txt','\t')





#==========================================================================
#===================MAPPING BAMS TO GFFS===================================
#==========================================================================

def mapBams(dataFile,cellTypeList,gffList,mappedFolder,nBin = 200,overWrite =False,nameList = []):
    
    '''
    for each gff maps all of the data and writes to a specific folder named after the gff
    can map either by cell type or by a specific name list
    '''

    dataDict = loadDataTable(dataFile)
    if mappedFolder[-1] != '/':
        mappedFolder+='/'

    for gffFile in gffList:
        
        #check to make sure gff exists
        try:
            foo = open(gffFile,'r')
        except IOError:
            print('ERROR: GFF FILE %s DOES NOT EXIST' % (gffFile))

        gffName = gffFile.split('/')[-1].split('.')[0]

        #see if the parent directory exists, if not make it
        try:
            foo = os.listdir(mappedFolder)
        except OSError:
            print('%s directory not found for mapped bams. making it' % (mappedFolder))
            os.system('mkdir %s' % (mappedFolder))


        
        #make this directory specifically for the gff
        try:
            foo = os.listdir(mappedFolder+gffName)
        except OSError:
            print('%s directory not found for this gff: %s. making it' % (mappedFolder+gffName,gffName))
            os.system('mkdir %s%s' % (mappedFolder,gffName))

        outdir = mappedFolder+gffName+'/'

        if len(nameList) == 0:
            nameList = dataDict.keys()
        

        for name in nameList:
            
            #filter based on celltype
            cellName = name.split('_')[0]
            if cellTypeList.count(cellName) != 1:
                continue
            fullBamFile = dataDict[name]['bam']
            outFile = outdir+gffName+'_'+name+'.gff'

            if overWrite:
                cmd1 = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/scripts/bamToGFF.py -d -f 1 -e 200 -r -m %s -b %s -i %s -o %s'" % (nBin,fullBamFile,gffFile,outFile)
                print(cmd1)
                os.system(cmd1)
            else:
                try:
                    Foo = open(outFile,'r')
                    print('File %s Already Exists, not mapping' % (outFile))
                except IOError:

                    cmd1 = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/scripts/bamToGFF.py -d -f 1 -e 200 -r -m %s -b %s -i %s -o %s'" % (nBin,fullBamFile,gffFile,outFile)
                    print(cmd1)
                    os.system(cmd1)


#==========================================================================
#===================MAKING GFF LISTS=======================================
#==========================================================================

def makeGFFListFile(mappedEnrichedFile,setList,output):

    '''
    #setList defines the dataset names to be used
    AND operators within lists, OR operators outside of lists
    [[A,B],[C,D]] = (A AND B) OR (C AND D) for this row
    [[A],[B],[C],[D]] = A OR B OR C OR D for this row

    '''
    geneListFile = []
    boundGFFTable = parseTable(mappedEnrichedFile,'\t')
    header = boundGFFTable[0]

    outputFolder = join(output.split('/')[0:-1],'/')+'/'
    formatFolder(outputFolder,True)
    
    #convert the setList into column numbers
    columnSet = []
    for bindingSet in setList:
        try:
            columnSet.append([header.index(x) for x in bindingSet])
        except ValueError:
            print('ERROR: not all datasets in binding table')
            exit()

    for i in range(1,len(boundGFFTable),1):
        
        line = boundGFFTable[i]
        refID = line[1]

        #print(columnSet)
        #print(i)
        #if any of these end up being true, the line gets added
        for andColumns in columnSet:
            
            bindingVector = [int(line[x]) for x in andColumns]
            if refID == "NM_133941":
                print bindingVector
            #print(bindingVector)
            if bindingVector.count(1) == len(bindingVector):
                
                geneListFile.append([i,boundGFFTable[i][1]])
                break
    print(len(geneListFile))
    unParseTable(geneListFile,output,'\t')


#==========================================================================
#===================MAKE HYPER TABLE=======================================
#==========================================================================

def hyperOccupancyEnrichment(dataFile,annotFile,namesList,tssGFFFile,transcribedGenesList,enrichedFolder,outputFolder,window=100000,macs=True):

    dataDict = loadDataTable(dataFile)
        
    startDict = makeStartDict(annotFile)
    #making sure output folder exists
    formatFolder(outputFolder,True)

    #making a transcribed tss collection
    tssGFF = parseTable(tssGFFFile,'\t')
    
    #transcribedGenes
    print('Loading transcribed genes')
    transcribedGenesTable = parseTable(transcribedGenesList,'\t')
    
    transcribedGenes = [int(line[0])-1 for line in transcribedGenesTable]

    tssLoci = []
    for i in transcribedGenes:
        line = tssGFF[i]
        tssLocus = Locus(line[0],line[3],line[4],line[6],line[1])
        tssLoci.append(tssLocus)
    print('making transcribed TSS collection')
    tssCollection = LocusCollection(tssLoci,500)

    for name in namesList:
        print('Finding hyperoccupancy for %s' %(name))
        hyperTable = []

        if name.count('MM1S') == 1:
            #mycTransLocusSense = Locus('chr14',105130609,105404388,'+','NM_002467')
            #tssCollection.append(mycTransLocusSense)
            mycTransLocusAnti = Locus('chr14',105404388-5000,105404388+5000,'-','NM_002467')
            mycTransLocusSense = Locus('chr14',105130609-5000,105130609+5000,'+','NM_002467')

            tssCollection.append(mycTransLocusAnti)
            tssCollection.append(mycTransLocusSense)

    
        peakTable = parseTable(enrichedFolder+dataDict[name]['enrichedMacs'],'\t')
        ticker = 0
        for peakLine in peakTable:
            if ticker%1000 == 0:
                print(ticker)
            ticker+=1
            peakLocus = Locus(peakLine[0],peakLine[1],peakLine[2],'.',peakLine[3])
            #check tss status
            signal = float(peakLine[4])
            proxGenes = []
            overlappingTSSLoci = tssCollection.getOverlap(peakLocus,'both')
            if len(overlappingTSSLoci) > 0:
                #this is a tss peak
                tss_peak = 1
                proxGenes+= [locus.ID() for locus in overlappingTSSLoci]
            else:
                #this is an enhancer or outside peak
                tss_peak = 0

                peakCenter = (int(peakLine[1]) + int(peakLine[2]))/2
                searchLocus = Locus(peakLine[0],peakCenter-window,peakCenter+window,'.',peakLine[3])
                overlappingProxLoci = tssCollection.getOverlap(searchLocus,'both')
                proxGenes += [locus.ID() for locus in overlappingProxLoci]
                if peakLine[3] == 'MACS_peak_10552':
                    print(overlappingProxLoci)
                    print([locus.start() for locus in overlappingProxLoci])
                    print([locus.ID() for locus in overlappingProxLoci])
            if len(proxGenes) > 0:
                proxGenes = uniquify(proxGenes)

                proxString = join(proxGenes,',')
                proxNames = uniquify([startDict[geneID]['name'] for geneID in proxGenes])
                proxNamesString = join(proxNames,',')
                newLine = [peakLine[0],peakLine[1],peakLine[2],peakLine[3],signal,tss_peak,proxString,proxNamesString]
                hyperTable.append(newLine)

        #now sort the hyper table
        sortedHyperTable = [['CHROM','START','STOP','NAME','SIGNAL','TSS_PEAK','PROXIMAL_GENE_IDS','PROXIMAL_GENE_NAMES']]

        peakOrder = order([float(line[4]) for line in hyperTable],decreasing=True)

        for i in peakOrder:
            sortedHyperTable.append(hyperTable[i])

        #now do the gene assignment way

        geneDict = {'totalSignal':defaultdict(float),'proximalEvents':defaultdict(int)}
        for line in sortedHyperTable[1:]:
            proximalGenes = line[6].split(',')
            if len(proximalGenes) == 0:
                continue
            else:
                signal = float(line[4])

                for geneID in proximalGenes:
                    geneDict['proximalEvents'][geneID]+=1
                    geneDict['totalSignal'][geneID]+=signal

        geneCentricTable = [] 
        geneList = geneDict['totalSignal'].keys()
        print(len(geneDict['totalSignal'].keys()))
        print(len(geneDict['proximalEvents'].keys()))
        peakOrder = order([geneDict['totalSignal'][geneID] for geneID in geneList],decreasing=True)
        
        for i in peakOrder:
            geneID = geneList[i]
            geneName = startDict[geneID]['name']
            geneCentricTable.append([geneID,geneName,geneDict['proximalEvents'][geneID],geneDict['totalSignal'][geneID]])
        
        collapsedGeneCentricTable = [['GENE_ID','GENE_NAME','PROXIMAL_EVENTS','SIGNAL']] 
        
        usedNames = []
        for line in geneCentricTable:
            geneName = line[1]
            if usedNames.count(geneName) == 0:
                collapsedGeneCentricTable.append(line)
                usedNames.append(geneName)
        
        unParseTable(sortedHyperTable,'%s%s_hyperPeaks.txt' % (outputFolder,name),'\t')
        unParseTable(collapsedGeneCentricTable,'%s%s_hyperGenes.txt' % (outputFolder,name),'\t')


#==========================================================================
#===================MAKE HYPER DENISTY=====================================
#==========================================================================
                
def hyperOccupancyDensity(annotFile,hyperPeakFile,namesList,gffName,mappedFolder,outFolder,referenceName=''):

    '''
    finds the gene assignment of peaks
    then maps to genes for each datasets in namesList
    '''

    startDict = makeStartDict(annotFile)
    assignDict = {'promoter':defaultdict(list),'enhancer':defaultdict(list)}

    hyperPeaks = parseTable(hyperPeakFile,'\t')
    for line in hyperPeaks[1:]:
        peakID = int(line[3].split('_')[-1])-1
        geneList = line[6].split(',')
        if int(line[5]) == 1:
            assignDict['promoter'][peakID] += geneList
        else:
            assignDict['enhancer'][peakID] += geneList

    if len(referenceName) == 0:
        referenceName = namesList[0]

    for name in namesList:
        print('working on %s' % (name))
        newTable = [['REFSEQ_ID','NAME','PROMOTER_REGIONS','PROMOTER_SIGNAL','DISTAL_REGIONS','DISTAL_SIGNAL']]
        mappedGFF = parseTable('%s%s/%s_%s.gff' % (mappedFolder,gffName,gffName,name),'\t')
        geneDict = {'promoter':defaultdict(list),'enhancer':defaultdict(list)}
        for line in mappedGFF[1:]:
            peakID = int(line[0].split('_')[-1])
            regionSize = int(line[1].split(':')[-1].split('-')[1])-int(line[1].split(':')[-1].split('-')[0])
            if assignDict['promoter'].has_key(peakID):
                for geneID in assignDict['promoter'][peakID]:
                    geneDict['promoter'][geneID].append(float(line[2])*regionSize)
            elif assignDict['enhancer'].has_key(peakID):
                for geneID in assignDict['enhancer'][peakID]:
                    geneDict['enhancer'][geneID].append(float(line[2])*regionSize)
            else:
                continue

        
        if name == referenceName:
            keeperIDs = []
            allGenes = uniquify(geneDict['promoter'].keys()+geneDict['enhancer'].keys())
            peakOrder = order([(sum(geneDict['enhancer'][x])+ sum(geneDict['promoter'][x])) for x in allGenes],decreasing=True)

            peakOrderedGenes = [allGenes[x] for x in peakOrder]
            
            usedNames =[]
            for geneID in peakOrderedGenes:
                geneName = startDict[geneID]['name']
                if usedNames.count(geneName) == 1:
                    continue
                usedNames.append(geneName)
                keeperIDs.append(geneID)

        
        #now write the table!
        for geneID in keeperIDs:
            geneName = startDict[geneID]['name']
            promoterRegions = len(geneDict['promoter'][geneID])
            promoterSignal = sum(geneDict['promoter'][geneID])
            enhancerRegions = len(geneDict['enhancer'][geneID])
            enhancerSignal = sum(geneDict['enhancer'][geneID])


            newLine = [geneID,geneName,promoterRegions,promoterSignal,enhancerRegions,enhancerSignal]
            newTable.append(newLine)
        print('writing table for %s' % (name))
        unParseTable(newTable,'%s%s_%s_REF_geneMapped.txt' % (outFolder,name,referenceName),'\t')
                

#==========================================================================
#===================PLOTTING INDIVIDUAL GENES=============================
#==========================================================================



def callGenePlot(dataFile,geneID,plotName,annotFile,namesList,outputFolder,region='TXN',yScale = 'UNIFORM'):

    '''
    calls bamPlot to plot a gene for a given set of bams
    currently works for mm9 and hg18

    '''
    formatFolder(outputFolder,True)

    dataDict = loadDataTable(dataFile)

    startDict= makeStartDict(annotFile)

    if len(geneID) != 0 and startDict.has_key(geneID) == True:
        start = startDict[geneID]['start'][0]
        end = startDict[geneID]['end'][0]
        chrom = startDict[geneID]['chr']
        sense = startDict[geneID]['sense']
        geneLength = abs(end-start)

    if ['TSS','TXN'].count(region) == 1 and len(geneID) == 0:
        print('ERROR: If no gene specified under refseqID, you must enter coordinates in the region field. e.g. chrN:+:1-1000')

    if region == 'TSS':
        
        locusString = '%s:%s:%s-%s' % (chrom,sense,start-5000,start+5000)

    elif region == 'TXN':
        offset =  int(round(.5*geneLength,-3))
        if sense == '+':
            locusString = '%s:%s:%s-%s' % (chrom,sense,start-offset,end+offset)
        else:
            locusString = '%s:%s:%s-%s' % (chrom,sense,end-offset,start+offset)            
    else:
        locusString = region

    nameString = join(namesList,',')
    if startDict.has_key(geneID):
        titleString = startDict[geneID]['name'] +'_' + plotName + '.pdf'
    else:
        titleString = geneID+'_'+plotName+'.pdf'
    colorString = join([dataDict[name]['color'] for name in namesList],':')
    bamList = [dataDict[name]['bam'] for name in namesList]
    bamString = join(bamList,',')
    genome = lower(dataDict[namesList[0]]['genome'])
    cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/scripts/bamPlot.py -n %s -t %s -c %s -g %s -p multiple -y %s -b %s -i %s -o %s'" % (nameString,titleString,colorString,genome,yScale,bamString,locusString,outputFolder)

    #cmd = "python /nfs/young_ata/scripts/bamPlot.py -n %s -t %s -c %s -g hg18 -p multiple -y uniform -b %s -i %s -o %s" % (nameString,titleString,colorString,bamString,locusString,outputFolder)
    print(cmd)
    os.system(cmd)

#==========================================================================
#=======================PLOTTING GROUPS OF GENES===========================
#==========================================================================

def plotGeneList(dataFile,annotFile,geneList,namesList,outputFolder,upsearch,downsearch,yScale = 'UNIFORM',byName = True):

    '''
    plots the txn region for a bunch of genes in a given window. uses either name or ID
    '''
    
    startDict = makeStartDict(annotFile)
    if byName:
        geneList = [upper(x) for x in geneList]
        nameDict = defaultdict(list)
        
        for key in startDict.keys():
            nameDict[startDict[key]['name']].append(key)
            
        refIDList = []

        for geneName in geneList:
            mouseName = lower(geneName)
            mouseName = upper(mouseName[0]) + mouseName[1:]
            #tries both the human and mouse nomenclature
            refIDs = nameDict[upper(geneName)] + nameDict[mouseName]
            if len(refIDs) ==0:
                print('Gene name %s not in annotation file %s' % (geneName,annotFile))
                continue
            refNumbers = [x.split('_')[-1] for x in refIDs]
            #take the lowest refseq number for the gene name as this is usually the best annotation
            refIndex = refNumbers.index(min(refNumbers))
            refIDList.append(refIDs[refIndex])
            print('Gene %s corresponds to ID %s' % (geneName,refIDs[refIndex]))

    else:
        refIDList = geneList

    for refID in refIDList:

        chrom = startDict[refID]['chr']
        sense = startDict[refID]['sense']
        if sense == '+':
            start = startDict[refID]['start'][0] - upsearch
            stop = startDict[refID]['end'][0] + downsearch
        else:
            start = startDict[refID]['start'][0] + upsearch
            stop = startDict[refID]['end'][0] - downsearch

        geneName = startDict[refID]['name']
        plotName = '_-%s_+%s' % (upsearch,downsearch)
        regionString = '%s:%s:%s-%s' % (chrom,sense,start,stop)
        print('plotting %s with window %s in region %s to outputfolder %s' % (geneName,plotName,regionString,outputFolder))
        callGenePlot(dataFile,refID,plotName,annotFile,namesList,outputFolder,regionString,yScale)



#==========================================================================
#===================MAKING META GFFS OF TXN REGIONS========================
#==========================================================================
        
def makeMetaGFFs(annotFile,gffFolder,genome,geneListFile =''):
    '''
    makes gffs of txn regions for meta genes
    '''
    formatFolder(gffFolder,True)

    genome = upper(genome)

        
    startDict = makeStartDict(annotFile)
    
    tssGFF = []
    txnGFF = []
    ttrGFF = []
    
    if len(geneListFile) == 0:
        geneList = startDict.keys()
        geneListName = 'ALL'
    else:
        geneListTable = parseTable(geneListFile,'\t')
        geneList = [line[1] for line in geneListTable]
        geneListName = geneListFile.split('/')[-1].split('.')[0]
    for gene in geneList:

        chrom = startDict[gene]['chr']
        sense = startDict[gene]['sense']
        start = startDict[gene]['start'][0]
        end = startDict[gene]['end'][0]

        if sense == '+':
            tssGFF.append([chrom,gene,'',start-3000,start,'',sense,'',gene])
            txnGFF.append([chrom,gene,'',start,end,'',sense,'',gene])
            ttrGFF.append([chrom,gene,'',end,end+3000,'',sense,'',gene])
        else:
            tssGFF.append([chrom,gene,'',start,start+3000,'',sense,'',gene])
            txnGFF.append([chrom,gene,'',end,start,'',sense,'',gene])
            ttrGFF.append([chrom,gene,'',end-3000,end,'',sense,'',gene])


    unParseTable(tssGFF,'%s%s_TSS_%s_-3000_+0.gff' % (gffFolder,genome,geneListName),'\t')
    unParseTable(txnGFF,'%s%s_TXN_%s_-0_+0.gff' % (gffFolder,genome,geneListName),'\t')
    unParseTable(ttrGFF,'%s%s_TTR_%s_-0_+3000.gff' % (gffFolder,genome,geneListName),'\t')




#==========================================================================
#===================MAPPING BAMS TO METAS==================================
#==========================================================================

def mapMetaBams(dataFile,metaName,gffList,cellTypeList,metaFolder,nameList= [],overwrite=False):

    '''
    calls bam mapping for all pol2 and respective wce samples
    '''

    formatFolder(metaFolder,True)

    dataDict = loadDataTable(dataFile)
    if len(nameList) == 0:
        nameList = dataDict.keys()
    outdir = metaFolder + metaName + '/'
    print('out directory is %s' % outdir)

    try:
        foo = os.listdir(outdir)
    except OSError:
        os.system('mkdir %s' % (outdir))
    
    gffString = join(gffList,',')

    for cellType in cellTypeList:
        

        cellTypeNames =[]
        
        #find all of the pol2 stuff
        for name in nameList:
            if name.count(cellType) == 1:
                cellTypeNames+=[name]
        print(cellTypeNames)
        for name in cellTypeNames:


                    
            bamFile = dataDict[name]['bam']

            cmd = 'python /nfs/young_ata/CYL_code/temp/reef/makeBamMeta.py -c -n %s -g %s -b %s -o %s' % (name,gffString,bamFile,outdir)
            if overwrite == False:
                try:
                    foo = open('%s%s_metaSettings.txt' % (outdir,name),'r')
                    print('meta for %s already exists, skipping.' % (name))
                    continue
                except IOError:
                    print(cmd)
                    os.system(cmd)
            else:

                print(cmd)
                os.system(cmd)

#==========================================================================
#===================MANUALLY FINISH METAS==================================
#==========================================================================

def finishMetas(metaFolder,settingsFileList=[]):

    '''
    manually finishes off meta code in case bad things happened

    '''

    if metaFolder[-1] != '/':
        metaFolder+='/'

    metaFiles = os.listdir(metaFolder)
    if len(settingsFileList) == 0:
        settingsFileList = filter(lambda x:x.count('metaSettings') == 1,metaFiles)

    for settingsFile in settingsFileList:
        settingsName = settingsFile[0:-17]
        cmd = 'bsub -o /dev/null python /nfs/young_ata/CYL_code/temp/reef/makeBamMeta.py -c -f -n %s -o %s' % (settingsName,metaFolder)
        
        print(cmd)
        os.system(cmd)
    

#==========================================================================
#===================MAKING ORDERED HEATMAPS================================
#==========================================================================

    
def callHeatPlotOrdered(dataFile,gffFile,namesList,orderByName,geneListFile,outputFolder,mappedFolder,relative=False):

    '''
    calls a heatmap ordered by a single dataset
    will spit out a series of heatmaps all ordered by the same reference dataset
    bound table is the binding table for enriched regions in this gff
    boundList is the OR set of requirements necessary to qualify a 
    '''

    dataDict = loadDataTable(dataFile)


    if mappedFolder[-1] != '/':
        mappedFolder+='/'

    if outputFolder[-1] != '/':
        outputFolder+='/'


    gffName = gffFile.split('/')[-1].split('.')[0]
    #get all of the mappedGFFs

    referenceMappedGFF = mappedFolder + gffName + '/' + gffName + '_'+orderByName + '.gff'
    
    for name in namesList:

        mappedGFF = mappedFolder + gffName + '/' + gffName + '_'+name + '.gff'
        
        color = dataDict[name]['color']
        output = outputFolder + '%s_%s_%s_order.png' % (gffName,name,orderByName)
        if relative:
            cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'R --no-save %s %s %s %s %s %s < /nfs/young_ata/scripts/heatMapOrdered.R'" % (referenceMappedGFF,mappedGFF,color,output,geneListFile,1)
            #cmd = "bsub -R 'rusage[mem=2200]' 'R --no-save %s %s %s %s %s %s < /nfs/young_ata/scripts/heatMapOrdered.R'" % (referenceMappedGFF,mappedGFF,color,output,geneListFile,1)
            
        else:
            cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'R --no-save %s %s %s %s %s %s < /nfs/young_ata/scripts/heatMapOrdered.R'" % (referenceMappedGFF,mappedGFF,color,output,geneListFile,0)
            #cmd = "bsub -R 'rusage[mem=2200]' 'R --no-save %s %s %s %s %s %s < /nfs/young_ata/scripts/heatMapOrdered.R'" % (referenceMappedGFF,mappedGFF,color,output,geneListFile,0)
            
        #cmd = 'R --no-save %s %s %s %s %s < /nfs/young_ata/scripts/heatMapOrdered.R' % (referenceMappedGFF,mappedGFF,color,output,geneListFile)
        print(cmd)
        os.system(cmd)








#=========================================================================================================
#EVERYTHING BELOW HAS NOT BEEN INTEGRATED INTO PIPELINE YET


# #making all of the ylfs

# #==========================================================================
# #===================CONVERTING SAMS TO YLFS================================
# #==========================================================================


# def makeYLFs(dataList=[],overwrite = False):
#     '''
#     makes sams for the dataset names specified. if blank, calls everything
#     '''

#     dataDict = loadDataTable()

#     if len(dataList) == 0:
#         dataList = dataDict.keys()
    
#     for name in dataList:
        
#         try:
#             sam = open(dataDict[name]['sam'],'r')
#         except IOError:
#             print('WARNING: No .sam file for %s' % (name))
#             continue
#         cmd = 'bsub -o /dev/null python /nfs/young_ata/CYL_code/samToYLF.py %s %s BWT1,BWT2' % (dataDict[name]['sam'],dataDict[name]['ylf'])
#         if overwrite:
#             print('making a .ylf for %s' % (name))
#             os.system(cmd)
#         else:
#             try:
#                 ylf = open(dataDict[name]['ylf'],'r')
#             except IOError:
#                 print('Making a .ylf for %s' % (name))
#                 os.system(cmd)



# #==========================================================================
# #===================CALLING THE ERROR MODEL================================
# #==========================================================================

        
# def callErrorModel(errorFolder,dataList = [],overwrite = False):

#     '''
#     for each dataset, calls the error model
#     '''

#     dataDict = loadDataTable()

#     if len(dataList) == 0:
#         dataList = dataDict.keys()

#     paramTemplate = [
#         ['TARGET READS FILE',''],
#         ['BACKGROUND READS FILE',''],
#         ['EXPERIMENT NAME', ''],
#         ['GENOME BUILD^(SPECIES AMD GENOME BUILD)', 'HG18'],
#         ['READ CATEGORIE(S) USED^(SEPARATE WITH COMMA)', 'BWT1,BWT2'],
#         ['MAXIMUM READ REPEATS', '2'],
#         ['GENOMIC BIN WIDTH^(BP)', '25'],
#         ['READ EXTENSION MODEL^(1=0to+200BP,2=-400BPto+600BP)', '1'],
#         ['P-VALUE THRESHOLD(S)^(SEPARATE WITH COMMA)', '1E-7,1E-8,1E-9'],
#         ['FRACTION OF GENOME AVAILABLE^(.5=50%)', '0.50'],
#         ['BIN TO REGION COMPRESS DISTANCE^(BP)', '200'],
#         ['COMPARISON FLANK DISTANCE^(BP)', '100'],
#         ['MINIMUM BIN ENRICHMENT OVER BACKGROUND^(NORMALIZED FOLD ENRICHMENT)', '2'],
#         ['MINIMUM REGION ENRICHMENT OVER BACKGROUND^(NORMALIZED FOLD ENRICHMENT)','5'],
#         ['MINIMUM REGION PEAK HEIGHT', '2'],
#         ['MINIMUM REGION LENGTH', '2'],
#         ['MODEL FOR CALLING GENES^(1=START SITES,2=FULL GENE)', '2'],
#         ['DISTANCE TO CALL GENES^(BP)', '2000'],
#         ['GENE LIST FILE(S)^(FILE LOCATION)','/nfs/young_ata/gene_tables/HG18_REFSEQ'],
#         ['WRITE BROWSER TRACK^(0=NO,1=YES,2=WRITE BACKGROUND TRACK ALSO)', '2'],
#         ['BROWSER TRACK FLOOR^(COUNTS)', '2'],
#         ['NORMALIZE TO READS PER MILLION^(1=YES,0=NO)', '0'],
#         ['DENSITY PLOT REGION(S)^(NAME,CHR,START,END)', '0'],
#         ['METAGENE PARAMETERS^(UPSTREAM_BP,DOWNSTREAM_BP,GENOMIC_BINS_PER_CLUSTERGRAM_BIN,NUMBER_OF_INGENE_BINS)','2000,2500,2,50'],
#         ['WRITE BIN COUNT HISTOGRAM^(1=YES,0=NO)', '1'],
#         ['WRITE DENSITY FILE^(1=YES,0=NO)', '0'],
#         ['WRITE GENOME SEQUENCE AT ENRICHMENT PEAKS^(+/- BP WINDOW)', '0'],
#         ['OUTPUT FOLDER LOCATION^(0=CURRENT DIRECTORY)', '0'],
#         ['END']
#         ]
    
#     for name in dataList:
        
#         #don't run error model on background datasets
#         if dataDict[name]['background'] == 'NONE':
#             continue
        
#         paramFile = list(paramTemplate)
#         paramFile[0][1] = dataDict[name]['ylf']
#         backgroundName =  dataDict[name]['background']
#         paramFile[1][1] = dataDict[backgroundName]['ylf']
#         paramFile[2][1] = name
        
#         #if overwrite is false, check for an enriched region file and skip if it exists
#         if overwrite == False:

#             if dataDict[name]['enriched'] != 'NONE':
#                 continue

#         #write the parameter file
#         paramFileName = name + '_ChIPseq_totalcounts_enrichedregions.txt'
#         print(paramFileName)
#         unParseTable(paramFile,errorFolder+paramFileName,'\t')

#         #now call the error model for this file
        
#         print('changing directory to %s' % (errorFolder))
#         os.chdir(errorFolder)
#         cmd = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/GMF_code/Solexa/ENRICHED_REGIONS_CODE_NEW/SOLEXA_ENRICHED_REGIONS.py %s'" % (paramFileName)
#         print(cmd)
#         os.system(cmd)


# #==========================================================================
# #===================FORMATTING ERROR MODEL=================================
# #==========================================================================

# def formatErrorModelOutput(dataTableFile,errorOutput,wiggleFolder,enrichedRegionsFolder):

#     '''
#     takes a folder of error model output and moves the enriched regions and wiggles to the right folder
#     updates the dataTable with the names of the enrichedRegions
#     '''

#     dataTable = parseTable(dataTableFile,'\t')
        
#     nameList = [line[3] for line in dataTable[1:]]

#     if errorOutput[-1] != '/':
#         errorOutput+='/'

#     if wiggleFolder[-1] != '/':
#         wiggleFolder+='/'

#     if enrichedRegionsFolder[-1] != '/':
#         enrichedRegionsFolder+='/'

#     outputFolders = os.listdir(errorOutput)

#     #filter for folders

#     outputFolders = filter(lambda x: x.split('.')[-1] != 'txt',outputFolders)

#     #get rid of any hidden files

#     outputFolders = filter(lambda x: x[0] != '.',outputFolders)

#     for output in outputFolders:

#         #get the name of the dataset
#         name = join(output.split('_')[:-2],'_')

#         #first move the wiggle
#         cmd = 'mv %s%s/*.WIG.gz %s &' % (errorOutput,output,wiggleFolder)
#         print(cmd)
#         os.system(cmd)
        
#         #next move the enriched region
#         cmd = 'mv %s%s/1e-09/ENRICHED_REGIONS_%s %s &' % (errorOutput,output,output,enrichedRegionsFolder)
#         print(cmd)
#         os.system(cmd)

#         #next update the dataTable
#         i = nameList.index(name)
#         dataTable[i+1][5] = 'ENRICHED_REGIONS_'+output
#         print(dataTable[i+1])

#     unParseTable(dataTable,dataTableFile,'\t')



# #==========================================================================
# #===================MAKING GFFS OF TSS REGIONS=============================
# #==========================================================================
        
# def makeTSSGFFs(dataTable,annotFile,upstream,downstream,gffFolder,species='HG18'):

#     '''
#     we're making several kinds of gffs for this study
#     all regions will be 10kb in size,
#     all binding sites will be within 2kb of one another or reference points
#     '''
#     dataDict = loadDataTable(dataTable)

#     if gffFolder[-1] != '/':
#         gffFolder+='/'



#     #TSS
#     #tss gff for all genes
#     tssGFF = makeTSSGFF(annotFile,upstream,downstream)
    
#     unParseTable(tssGFF,gffFolder + '%s_TSS_ALL_-%s_+%s.gff' % (species,upstream,downstream),'\t')

# #==========================================================================
# #===================MAKING GFFS OF GENE BODY REGIONS=======================
# #==========================================================================
        
# def makeBodyGFFs(annotFile,gffFolder):

#     '''
#     we're making several kinds of gffs for this study
#     all regions will be 10kb in size,
#     all binding sites will be within 2kb of one another or reference points
#     '''
#     dataDict = loadDataTable()

#     if gffFolder[-1] != '/':
#         gffFolder+='/'

#     startDict = makeStartDict(annotFile)

#     #TSS
#     #tss gff for all genes

#     bodyGFF = []

#     for gene in startDict.keys():

#         chrom = startDict[gene]['chr']
#         sense = startDict[gene]['sense']
#         start = startDict[gene]['start'][0]
#         end = startDict[gene]['end'][0]

#         if sense == '+':

#             bodyGFF.append([chrom,gene,'',start+300,end+3000,'',sense,'',gene])

#         else:

#             bodyGFF.append([chrom,gene,'',end-3000,start-300,'',sense,'',gene])
    
#     unParseTable(bodyGFF,gffFolder + 'HG18_BODY_ALL_+300_+3000.gff','\t')



# #==========================================================================
# #===================MAKING GFFS OF ENHANCER REGIONS========================
# #==========================================================================


# def makeEnhancerGFFs(dataTable,gffName,nameList,annotFile,gffFolder,enrichedFolder,macs=True):
#     '''
#     find all possible enhancers.
#     enhancers defined as h3k27ac binding sites +/-5kb outside of promoters
#     we define center of enhancer as the center of the bound region
#     '''

#     dataDict = loadDataTable(dataTable)


#     if enrichedFolder[-1] != '/':
#         enrichedFolder+='/'

#     if gffFolder[-1] != '/':
#         gffFolder+='/'

#     #nameList = ['H128_H3K27AC','H2171_H3K27AC','MM1S_H3K27AC_DMSO','MM1S_H3K27AC_JQ1','U87_H3K27AC','P493-6_T0_H3K27AC','P493-6_T1_H3K27AC','P493-6_T24_H3K27AC']

#     #first make the tss collection
#     tssGFF = makeTSSGFF(annotFile,5000,5000)
#     tssCollection = gffToLocusCollection(tssGFF)

#     #make a blank collection to load enhancers into
#     enhancerCollection = LocusCollection([],500)

#     #don't allow overlapping enhancers
#     for name in nameList:


#         print('finding enhancers in %s' % (name))
#         if macs:
#             boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enrichedMacs'],name)
#         else:
#             boundCollection = importBoundRegion(enrichedFolder + dataDict[name]['enriched'],name)
#         for locus in boundCollection.getLoci():
#             #make sure an overlapping enhancer doesn't already exist
#             if len(tssCollection.getOverlap(locus,'both')) == 0 and len(enhancerCollection.getOverlap(locus,'both')) == 0:
#                 center = (locus.start()+locus.end())/2
#                 gffLocus = Locus(locus.chr(),center-5000,center+5000,'.',locus.ID())
#                 enhancerCollection.append(gffLocus)


#     enhancerGFF = locusCollectionToGFF(enhancerCollection)
#     print('Found %s enhancers in %s' % (len(enhancerGFF),gffName))
#     unParseTable(enhancerGFF,gffFolder+'HG18_ENHANCERS_%s_-5000_+5000.gff' % (gffName),'\t')


# #==========================================================================
# #===================MAKE ELEMENTS GFF======================================
# #==========================================================================

# def makeElementsGFF(tssGFFFile,transcribedListFile,enhancerGFFFile,enhancerListFile,rnaTableFile,gffFolder,elementsName):


#     '''
#     makes a gff of elements active promoters, silent promoters, active enhancers, rRNA genes, tRNA genes
#     '''


#     elementGFF = []

#     #start with the promoters

#     transcribedList= parseTable(transcribedListFile,'\t')

#     #all lists are 1 indexed
#     transcribedList = [int(line[0])-1 for line in transcribedList]

#     tssGFF = parseTable(tssGFFFile,'\t')

#     for i in range(len(tssGFF)):

#         newLine = list(tssGFF[i])

#         if transcribedList.count(i) == 1:
#             newLine[1] = 'ACTIVE'
#             transcribedList.remove(i)
#         else:
#             newLine[1] = 'SILENT'
        
#         newLine[3] = int(newLine[3]) +4000
#         newLine[4] = int(newLine[4]) -4000

#         elementGFF.append(newLine)

#     #now lets get enhancers

#     enhancerList = parseTable(enhancerListFile,'\t')
    
    
#     enhancerList = [int(line[0])-1 for line in enhancerList]


#     enhancerGFF = parseTable(enhancerGFFFile,'\t')

#     for i in enhancerList:

#         newLine = list(enhancerGFF[i])
#         newLine[1] = 'ENHANCER'
#         newLine[3] = int(newLine[3]) +4000
#         newLine[4] = int(newLine[4]) -4000

#         elementGFF.append(newLine)


#     #now lets do RNA genes

#     rnaTable = parseTable(rnaTableFile,'\t')

#     for line in rnaTable[1:]:
        
#         #check if it's a tRNA
#         if line[6] == 'Eddy-tRNAscanSE' and float(line[8]) >20:
#             #now we know we have a potential tRNA
#             #check the score to make sure it's legit
#             #use the 20 cutoff

#             if line[5] == '+':

#                 newLine = [line[0],'tRNA','',int(line[1]) - 1000,int(line[1]) + 1000,float(line[8]),'+','',line[3]]
#             else:
#                 newLine = [line[0],'tRNA','',int(line[2]) - 1000,int(line[2]) + 1000,float(line[8]),'+','',line[3]]                    
#             elementGFF.append(newLine)
#         #now lets get rRNA genes
#         if line[6] == 'Eddy-BLAST-otherrnalib' and line[7] == 'rRNA':
#             if line[5] == '+':

#                 newLine = [line[0],'rRNA','',int(line[1]) - 1000,int(line[1]) + 1000,float(line[8]),'+','',line[3]]
#             else:
#                 newLine = [line[0],'rRNA','',int(line[2]) - 1000,int(line[2]) + 1000,float(line[8]),'+','',line[3]]
#             elementGFF.append(newLine)
#     unParseTable(elementGFF,gffFolder+elementsName,'\t')

# #==========================================================================
# #===================MAKING GFF FROM MACS PEAKS=============================
# #==========================================================================


# def makePeakGFF(namesList,macsFolder,window,gffFolder):

#     '''
#     takes a macs summit file and makes a gff of all summits +/- window and spits it out in the gff folder
#     '''

#     dataDict = loadDataTable()
#     if macsFolder[-1] != '/':
#         macsFolder+='/'

#     if gffFolder[-1] !='/':
#         gffFolder+='/'

#     for name in namesList:

#         summitBed = parseTable(macsFolder+name+'/' +name+'_summits.bed','\t')

#         summitGFF = []

#         for line in summitBed:

#             chrom = line[0]
#             start = int(line[1]) - window
#             end = int(line[1]) + window
#             name = line[3]
#             score = line[4]

#             newLine = [chrom,name,'',start,end,score,'.','',name]

#             summitGFF.append(newLine)

#         unParseTable(summitGFF,'%sHG18_%s_summits_-%s_+%s.gff' % (gffFolder,name,window,window),'\t')



# #==========================================================================
# #===================RANKING E-BOXESFROM MACS PEAKS=========================
# #==========================================================================


# def rankEboxes(name,genomeDirectory,window,macsFolder,motifFolder,asDict=False):

#     '''
#     takes a summit bed and ranks eboxes by height from a sequence in a window around the bed

#     '''
    
#     #hardcoded ebox motif

#     motifRegex = 'CA..TG'
#     if macsFolder[-1] != '/':
#         macsFolder+='/'

#     if motifFolder[-1] != '/':
#         motifFolder+='/'

#     dataDict = loadDataTable()
#     window = int(window)

#     summitBed = parseTable(macsFolder+name+'/' +name+'_summits.bed','\t')
#     eboxDict = defaultdict(list)
#     ticker= 0
#     for line in summitBed:
#         if ticker % 1000 == 0:
#             print(ticker)
#         ticker+=1

#         chrom = line[0]
#         peakName = line[3]
#         sense = '.'


#         start = int(line[1])-window
#         end = int(line[1])+window
#         height = float(line[4])

#         sequenceLine = fetchSeq(genomeDirectory,chrom,start,end,True)
        
#         motifVector = []
#         matches = re.finditer(motifRegex,upper(sequenceLine))
#         if matches:
#             for match in matches:
#                 motifVector.append(match.group())
        
#         #count only 1 of each motif type per line
#         motifVector = uniquify(motifVector)
#         for motif in motifVector:

#             eboxDict[motif].append(height)


#     eboxTable =[]
#     eboxTableOrdered =[['EBOX','OCCURENCES','AVG_HEIGHT']]
#     for ebox in eboxDict.keys():
#         newLine = [ebox,len(eboxDict[ebox]),mean(eboxDict[ebox])]
#         eboxTable.append(newLine)


#     occurenceOrder = order([line[2] for line in eboxTable],decreasing=True)
    
#     for x in occurenceOrder:
#         eboxTableOrdered.append(eboxTable[x])
#     print(eboxTableOrdered)
#     unParseTable(eboxTableOrdered,motifFolder+name+'_eboxes_unique.txt','\t')


# #==========================================================================
# #===================MAKE A FASTA FROM A PEAK FILE==========================
# #==========================================================================
    

        
# def makePeakFastas(name,genomeDirectory,window,tssGFFFile,enhancerGFFFile,macsFolder,outFolder,top=''):

#     '''
#     makes a ranked fasta based on peak height. best = True takes only the best peak from each region
#     '''

#     if macsFolder[-1] != '/':
#         macsFolder+='/'

#     if outFolder[-1] != '/':
#         outFolder+='/'

#     dataDict = loadDataTable()
#     window = int(window)

        
#     #load in the tss GFF and enhancerGFF
#     tssGFF = parseTable(tssGFFFile,'\t')
#     tssCollection = gffToLocusCollection(tssGFF)

#     enhancerGFF = parseTable(enhancerGFFFile,'\t')
#     enhancerCollection = gffToLocusCollection(enhancerGFF)

#     peakTable = parseTable(macsFolder+name+'/' +name+'_summits.bed','\t')

#     tssFastaList = []
#     enhancerFastaList = []
#     ticker =0
#     outsideBoth = 0

#     for line in peakTable:
#         if ticker % 1000 == 0:
#             print(ticker)
#         ticker+=1

#         chrom = line[0]
#         peakName = line[3]
#         sense = '.'


#         start = int(line[1])-window
#         end = int(line[1])+window
#         height = float(line[4])

#         peakLocus = Locus(chrom,start,end,sense,peakName)
#         #check to see if the peak is near a promoter or enhancer
#         if len(tssCollection.getOverlap(peakLocus,'both')) > 0 and len(enhancerCollection.getOverlap(peakLocus,'both')) == 0:
        
#             fastaHeader = '>%s:%s:%s-%s|%s|%s' % (chrom,sense,start,end,peakName,height)
#             fastaLine = fetchSeq(genomeDirectory,chrom,start,end,True)
#             tssFastaList.append([fastaHeader,fastaLine])
#         if len(tssCollection.getOverlap(peakLocus,'both')) == 0 and len(enhancerCollection.getOverlap(peakLocus,'both')) >0:

        
#             fastaHeader = '>%s:%s:%s-%s|%s|%s' % (chrom,sense,start,end,peakName,height)
#             fastaLine = fetchSeq(genomeDirectory,chrom,start,end,True)
#             enhancerFastaList.append([fastaHeader,fastaLine])

#         if len(tssCollection.getOverlap(peakLocus,'both')) == 0 and len(enhancerCollection.getOverlap(peakLocus,'both')) == 0:
#             outsideBoth+=1


#     #this returns a fastaList
#     print('found %s tss bound regions' % len(tssFastaList))
#     print('found %s enhancer bound regions' % len(enhancerFastaList))
#     print('found %s bound regions outside both' % outsideBoth)
    
    
#     #write the tss fasta
#     peakOrder = order([float(fasta[0].split('|')[-1]) for fasta in tssFastaList],decreasing=True)

#     outFasta = open('%s%s_TSS_-%s_+%s_top%s.fasta' % (outFolder,name,window,window,top),'w')
#     if not top:
#         top = len(tssFastaList)
#     else:
#         top = int(top)

#     for i in range(top):

#         peakIndex = peakOrder[i]

#         outFasta.write(tssFastaList[peakIndex][0]+'\n')
#         outFasta.write(tssFastaList[peakIndex][1]+'\n')


#     outFasta.close()

#     #write the enhancer fasta

#     if not top:
#         top = len(enhancerFastaList)
#     else:
#         top = int(top)

#     peakOrder = order([float(fasta[0].split('|')[-1]) for fasta in enhancerFastaList],decreasing=True)

#     outFasta = open('%s%s_ENHANCER_-%s_+%s_top%s.fasta' % (outFolder,name,window,window,top),'w')

#     for i in range(top):

#         peakIndex = peakOrder[i]

#         outFasta.write(enhancerFastaList[peakIndex][0]+'\n')
#         outFasta.write(enhancerFastaList[peakIndex][1]+'\n')


#     outFasta.close()            

# #==========================================================================
# #===================RANKING E-BOXES FROM FASTA=============================
# #==========================================================================

# def rankEboxFasta(fastaFile,eboxTableFile,motifFolder):

#     '''
#     finds all of the eboxes in a fasta and writes a table of how often they occur and the avg. score
#     for that particular sequence
#     '''

#     motifRegex = 'CA..TG'
#     if motifFolder[-1] != '/':
#         motifFolder+='/'

#     fastaName = fastaFile.split('/')[-1].split('.')[0]

#     fasta = parseTable(fastaFile,'\t')


#     eboxDict = defaultdict(float)

#     eboxTable = parseTable(eboxTableFile,'\t')


#     for line in eboxTable[1:]:
#         eboxDict[line[0]] = float(line[2])
#     print(eboxDict)

#     occurenceDict = defaultdict(int)

#     for line in fasta:
#         line = line[0]
#         if line[0] == '>':
#             continue


#         matches = re.finditer(motifRegex,upper(line))
#         if matches:
#             for match in matches:
#                 occurenceDict[match.group()]+=1


#     strengthOrder = order([line[2] for line in eboxTable[1:]],decreasing=True)
#     print(strengthOrder)
#     eboxList = [eboxTable[x+1][0] for x in strengthOrder]

#     print(occurenceDict)
#     occurenceTable = [['EBOX','OCCURENCES']]

#     for ebox in eboxList:

#         occurenceTable.append([ebox,occurenceDict[ebox]])


#     unParseTable(occurenceTable,motifFolder+fastaName+'_eboxes.txt','\t')


    





                                                                                                            
# #==========================================================================
# #===================CALL MEME==============================================
# #==========================================================================

# def callMEME(fastaFolder,overwrite = False):

#     '''
#     calls MEME on a folder full of fastas. has option to overwrite
#     '''
#     if fastaFolder[-1]!='/':
#         fastaFolder+='/'
#     fastaFolderList = os.listdir(fastaFolder)

#     fastaFileList = filter(lambda x: x.split('.')[-1] == 'fasta',fastaFolderList)

#     for fastaFile in fastaFileList:

#         fastaName = fastaFile.split('.')[0]
#         #the don't overwrite condition
#         if overwrite == False and fastaFolderList.count(fastaName) == 1:
            
#             print('yay')
#             continue
#         print('calling MEME on %s' % fastaName)
#         output = fastaFolder+fastaName+'/'

#         cmd = "bsub -R 'rusage[mem=2200]' 'meme -dna -evt 1 -mod zoops -nmotifs 10 -minw 4 -maxw 10 -revcomp -o %s -maxsize 1000000 %s'" % (output,fastaFolder+fastaFile)
#         print(cmd)
#         os.system(cmd)

    
    
# #==========================================================================
# #===================MAPPING BAMS TO GFFS===================================
# #==========================================================================

# def mapMycBams(cellTypeList,gffList,mappedFolder,dataFile = '',nBin = 200,overWrite =False,nameList = []):
    
#     '''
#     for each gff maps all of the data and writes to a specific folder named after the gff
#     '''
#     dataDict = loadDataTable(dataFile)
#     if mappedFolder[-1] != '/':
#         mappedFolder+='/'

#     for gffFile in gffList:
        
#         #check to make sure gff exists
#         try:
#             foo = open(gffFile,'r')
#         except IOError:
#             print('ERROR: GFF FILE %s DOES NOT EXIST' % (gffFile))

#         gffName = gffFile.split('/')[-1].split('.')[0]
        
#         #make this directory
#         try:
#             foo = os.listdir(mappedFolder+gffName)
#         except OSError:
#             os.system('mkdir %s%s' % (mappedFolder,gffName))

#         outdir = mappedFolder+gffName+'/'

#         if len(nameList) == 0:
#             nameList = dataDict.keys()
        

#         for name in nameList:
            
#             #filter based on celltype
#             cellName = name.split('_')[0]
#             if cellTypeList.count(cellName) != 1:
#                 continue
#             fullBamFile = dataDict[name]['bam']
#             outFile = outdir+gffName+'_'+name+'.gff'

#             if overWrite:
#                 cmd1 = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/scripts/bamToGFF.py -u -d -f 1 -e 200 -r -m %s -b %s -i %s -o %s'" % (nBin,fullBamFile,gffFile,outFile)
#                 print(cmd1)
#                 os.system(cmd1)
#             else:
#                 try:
#                     Foo = open(outFile,'r')
#                     print('File %s Already Exists, not mapping' % (outFile))
#                 except IOError:

#                     cmd1 = "bsub -o /dev/null -R 'rusage[mem=2200]' 'python /nfs/young_ata/scripts/bamToGFF.py -u -d -f 1 -e 200 -r -m %s -b %s -i %s -o %s'" % (nBin,fullBamFile,gffFile,outFile)
#                     print(cmd1)
#                     os.system(cmd1)

# #==========================================================================
# #===================PULLING MOTIFS FROM FASTAS=============================
# #==========================================================================


# def rankedFastaMotifs(fastaFile,outFolder):

    
#     '''
#     takes a ranked fasta and spits out a bunch of files that are nifty
#     '''

#     if outFolder[-1] != '/':
#         outFolder+='/'
#     fastaName = fastaFile.split('/')[-1].split('.')[0]
#     try:
#         os.listdir('%s%s_rankedMotifs/' % (outFolder,fastaName))
#     except  OSError:
#         os.system('mkdir %s%s_rankedMotifs/' % (outFolder,fastaName))
#     fasta = parseTable(fastaFile,'\t')
#     #hard coded for E-boxes
#     motif = '[ACTG]CA[ACTG]{2}TG[ATCG]'
#     motifLen = 8
#     nBins = 10
    
#     binSize = len(fasta)/nBins

#     heightTable = [['BIN','HEIGHT','NSITES','A','C','G','T']]
    

#     for i in range(nBins):
#         compDict = defaultdict(int)
#         start = i*binSize
#         end = (i+1) * binSize
#         heightVector = []
#         motifVector = []
#         for j in range(start,end,2):
#             headerLine = fasta[j][0]
#             sequenceLine = fasta[j+1][0]
#             heightVector.append(float(headerLine.split('|')[-1]))
#             matches = re.finditer(motif,upper(sequenceLine))
#             if matches:
#                 for match in matches:
#                     motifVector.append(match.group())
#             lineComp = composition(sequenceLine,['A','T','C','G'])
#             for x in lineComp.keys():
#                 compDict[x] += lineComp[x]
#         totalSequence = sum([compDict[x] for x in compDict.keys()])
        
#         compLine = [float(compDict[x])/totalSequence for x in ['A','C','G','T']]

#         heightTable.append([i+1,mean(heightVector),len(motifVector)]+compLine)
#         motifMatrix = [['A','C','G','T']]
#         for position in range(motifLen):
#             positionVector = [x[position] for x in motifVector]
#             positionCounts = [positionVector.count('A'),positionVector.count('C'),positionVector.count('G'),positionVector.count('T')]
#             positionCounts = [round(100*float(x)/len(positionVector),0) for x in positionCounts]
#             motifMatrix.append(positionCounts)
#         unParseTable(motifMatrix,'%s%s_rankedMotifs/motif_nBin_%s.txt' % (outFolder,fastaName,i),'\t')
#         motifFasta = [[x] for x in motifVector]
#         unParseTable(motifFasta,'%s%s_rankedMotifs/motif_nBin_%s.fasta' % (outFolder,fastaName,i),'\t')



#     unParseTable(heightTable,'%s%s_rankedMotifs/motif_heights.txt' % (outFolder,fastaName),'\t')

# #==========================================================================
# #===================GFF MOTIF TO BED ======================================
# #==========================================================================

# def gffMotifToBed(name,motif,genomeDirectory,gffFile,bedFolder):

#     '''
#     writes a bed track showing where motifs are within gff regions
#     '''

#     gffName = gffFile.split('/')[-1].split('.')[0]
#     trackLine = 'track name="%s" description="%s" visibility=3' % (name,gffName)

#     bed = open('%s%s_%s.bed' % (bedFolder,gffName,name),'w')
#     bed.write(trackLine+'\n')
#     gff = parseTable(gffFile,'\t')
#     ticker =0
#     for line in gff:
#         if ticker%1000 == 0:
#             print ticker
#         ticker+=1
#         chrom = line[0]
#         start = int(line[3])
#         end = int(line[4])
#         try:
#             sequence = fetchSeq(genomeDirectory,chrom,start,end,True)
#         except IOError:
#             continue
#         motifs = re.finditer(motif,upper(sequence))
#         for match in motifs:
    
#             newLine = join([chrom,str(start+match.start()),str(start+match.end())],'\t')
#             bed.write(newLine+'\n')


#     bed.close()

    
# #check for mapped bams
# #==========================================================================
# #===================CHECK MAPPED BAMS======================================
# #==========================================================================

# def checkMappedBams(gffList,mappedFolder):

#     '''
#     goes through the mapped folder to make sure each bam was mapped to each gff correctly
#     prints an error message if things messed up
#     '''
#     dataDict = loadDataTable()
#     if mappedFolder[-1] != '/':
#         mappedFolder+='/'

#     for gffFile in gffList:

#         gffName = gffFile.split('/')[-1].split('.')[0]
        
#         outdir = mappedFolder+gffName+'/'

#         nameList = dataDict.keys()
        
#         for name in nameList:

#             outFile = outdir+gffName+'_'+name+'.gff'
#             try:
#                 foo = open(outFile,'\r')
#             except IOError:
#                 print('NO MAPPED BAM FOR %s FOUND FOR DATASET %s' % (gffName,name))



        

# #==========================================================================
# #===================FINDING TARGET GENES===================================
# #==========================================================================



   
# def mergeTargetLists(startDict,namesList,enrichedFolder):
#     dataDict = loadDataTable()
#     targetGeneList = []


#     for name in namesList:

#         enrichedFile = enrichedFolder + dataDict[name]['enriched']
#         targetGeneList +=  targetGenes(startDict,enrichedFile,-1000,1000)

#     targetGeneList = uniquify(targetGeneList)
#     return targetGeneList


# #==========================================================================
# #===================MAP ENRICHED REGIONS TO GFF============================
# #==========================================================================

# def mapEnrichedToGFF(dataFile,setName,gffList,cellTypeList,enrichedFolder,mappedFolder,macs=True):

#     '''
#     maps enriched regions from a set of cell types to a set of gffs
#     tries to make a new folder for each gff
#     '''

#     dataDict = loadDataTable(dataFile)
#     if enrichedFolder[-1] != '/':
#         enrichedFolder+='/'

#     if mappedFolder[-1] != '/':
#         mappedFolder+='/'

#     for gffFile in gffList:

#         gffName = gffFile.split('/')[-1].split('.')[0]
#         print('making enriched regions to %s' % (gffName))
#         #make the gff into a collection


        
#         outdir = mappedFolder+gffName+'/'

#         try:
#             foo = os.listdir(mappedFolder+gffName)
#         except OSError:
#             os.system('mkdir %s' % (outdir))
        
#         #first filter the name list
#         cellTypeNameList =[] 

#         for name in dataDict.keys():

#             #check to make sure in the right celltype
#             #also make sure to not process WCEs
#             if dataDict[name]['background'] == 'NONE':
#                 continue
#             cellName = name.split('_')[0]
#             if macs == True:
#                 if cellTypeList.count(cellName) == 1 and dataDict[name]['enrichedMacs'] != 'NONE':
#                     cellTypeNameList.append(name)

#             else:
#                 if cellTypeList.count(cellName) == 1 and dataDict[name]['enriched'] != 'NONE':
#                     cellTypeNameList.append(name)

#         cellTypeNameList.sort()

#         mappedGFF = [['GFF_LINE','ID'] + cellTypeNameList]
#         #now we go through the gff and fill in stuff
#         gffTable = parseTable(gffFile,'\t')

#         gffLoci = []
#         for line in gffTable:
#             gffLocus = Locus(line[0],line[3],line[4],line[6],line[8])
#             gffLine = gffLocus.__str__()
#             gffID = line[1]
            
#             gffLoci.append(gffLocus)
#             mappedGFF.append([gffLine,gffID])
            
#         for name in cellTypeNameList:
#             print('dataset %s' % (name))
#             if macs:
#                 enrichedCollection = importBoundRegion(enrichedFolder + dataDict[name]['enrichedMacs'],name)
#             else:
#                 enrichedCollection = importBoundRegion(enrichedFolder + dataDict[name]['enriched'],name)
#             for i in range(len(gffLoci)):
#                 if len(enrichedCollection.getOverlap(gffLoci[i],'both')) > 0:
#                     mappedGFF[i+1].append(1)
#                 else:
#                     mappedGFF[i+1].append(0)


#         unParseTable(mappedGFF,outdir+gffName+'_'+setName+'.txt','\t')


# #==========================================================================
# #===================FORMATTING NANOSTRING DATA=============================
# #==========================================================================

# def formatNanoString(nanoStringFolder,sampleNames,tssGFFFile,geneListFile,output):

#     '''
#     takes a folder of nanostring data numbered in our current schema
#     and formats it into a pickle and a table
#     '''

#     #first get the tss gff file loaded

#     tssGFF = parseTable(tssGFFFile,'\t')

#     geneListTable = parseTable(geneListFile,'\t')
    
#     geneList = [int(line[0]) -1 for line in geneListTable]

#     activeList = [tssGFF[i][1] for i in geneList]



#     nanoStringFileList = os.listdir(nanoStringFolder)

#     nanoDict = {'0hr':defaultdict(list),
#                 '1hr':defaultdict(list),
#                 '24hr':defaultdict(list),
#                 'notet':defaultdict(list),
#                 'H128':defaultdict(list),
#                 'H2171':defaultdict(list),
#                 }

#     sampleDict = {'01':'0hr',
#                   '02':'0hr',
#                   '03':'1hr',
#                   '04':'1hr',
#                   '05':'24hr',
#                   '06':'24hr',
#                   '07':'notet',
#                   '08':'notet',
#                   '09':'H2171',
#                   '10':'H2171',
#                   '11':'H128',
#                   '12':'H128',
#                   }

#     nameDict = defaultdict(str)
#     activityDict = defaultdict(str)
#     for nanoFile in nanoStringFileList:
#         if nanoFile.split('.')[-1] != 'RCC':
#             continue
#         sampleID = nanoFile.split('.')[0].split('_')[-1]
#         sampleName = sampleDict[sampleID]

#         dataTable = parseTable(nanoStringFolder+nanoFile,'\r')

#         for line in dataTable:

#             if line[0].count('NM') == 1:
#                 geneName = line[0].split(',')[1]
#                 refseqID = line[0].split(',')[2].split('.')[0]
#                 nameDict[refseqID] = geneName
#                 if activeList.count(refseqID) == 1:
#                     activityDict[refseqID] ='ACTIVE'
#                 else:
#                     activityDict[refseqID] = 'SILENT'
#                 geneCounts = int(line[0].split(',')[-1])
#                 nanoDict[sampleName][refseqID].append(geneCounts)


#     nanoTable = [['REFSEQ_ID','GENE','ACTIVITY'] +sampleNames]
#     nanoGeneList = nanoDict['0hr'].keys()


#     for refseqID in nanoGeneList:

#         newLine = [refseqID,nameDict[refseqID],activityDict[refseqID]]+[sum(nanoDict[x][refseqID][0:2]) for x in sampleNames]
#         nanoTable.append(newLine)



#     unParseTable(nanoTable,output,'\t') 

   




# #==========================================================================
# #===================PLOTTING INDIVIDUAL GENES=============================
# #==========================================================================

# def makeGeneListFile(gffBindingFile,setList,output):

#     '''

#     AND operators within lists, OR operators outside of lists
#     [[A,B],[C,D]] = (A AND B) OR (C AND D) for this row
#     [[A],[B],[C],[D]] = A OR B OR C OR D for this row

#     '''
#     geneListFile = []
#     boundGFFTable = parseTable(gffBindingFile,'\t')
#     header = boundGFFTable[0]
    
#     #convert the setList into column numbers
#     columnSet = []
#     for bindingSet in setList:
#         try:
#             columnSet.append([header.index(x) for x in bindingSet])
#         except ValueError:
#             print('ERROR: not all datasets in binding table')
#             exit()

#     for i in range(1,len(boundGFFTable),1):
        
#         line = boundGFFTable[i]
        
#         #print(columnSet)
#         #print(i)
#         #if any of these end up being true, the line gets added
#         for andColumns in columnSet:
            
#             bindingVector = [int(line[x]) for x in andColumns]
#             #print(bindingVector)
#             if bindingVector.count(1) == len(bindingVector):
#                 geneListFile.append(i)
#                 break
#     print(len(geneListFile))
#     unParseTable(geneListFile,output,'')


    


